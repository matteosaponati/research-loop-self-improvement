"""
Agent-editable training code for the autoresearch loop.

The immutable experiment runner imports train_model(), keeps the trained model
in memory, evaluates it with immutable/eval.py, and records results. Running
this file directly only trains the model; use immutable/run_experiment.py for a
complete train/evaluate/record experiment.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from editable.config_loader import CONFIG

PROJECT_NAME = "research_loops_stresstest"
RUNS_DIR = "runs"
BASELINE_NAME = "baseline"

PYTORCH_ALLOC_CONF = "expandable_segments:True"
COMPILE_MODEL = True
COMPILE_DYNAMIC = False

TIME_BUDGET_SECONDS = 180
WARMUP_STEPS_EXCLUDED_FROM_TIMING = 10
LOSS_FAIL_THRESHOLD = 100.0
EMA_BETA = 0.9
GC_FREEZE_AFTER_FIRST_STEP = True
GC_COLLECT_INTERVAL = 5000

os.environ["PYTORCH_ALLOC_CONF"] = PYTORCH_ALLOC_CONF
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = CONFIG.hf_hub_disable_progress_bars

import gc
import math
import time
from dataclasses import dataclass, asdict

import torch
import torch.nn as nn
import torch.nn.functional as F

from immutable import prepare

prepare.DATA_DIR = os.path.expanduser(str(prepare.DATA_DIR))
prepare.TOKENIZER_DIR = os.path.expanduser(str(prepare.TOKENIZER_DIR))
prepare.MAX_SEQ_LEN = CONFIG.sequence_len

# ---------------------------------------------------------------------------
# GPT Model
# ---------------------------------------------------------------------------

@dataclass
class GPTConfig:
    sequence_len: int
    vocab_size: int
    n_layer: int
    n_head: int
    n_embd: int
    mlp_hidden_multiplier: int
    rotary_seq_len_multiplier: int
    rotary_base: float
    softcap: float
    ignore_index: int
    init_wte_mean: float
    init_wte_std: float
    init_lm_head_mean: float
    init_lm_head_std: float
    init_matrix_scale: float


@dataclass
class TrainingResult:
    model: object
    tokenizer: object
    model_config: GPTConfig
    training_metrics: dict[str, float | int]


def norm(x):
    return F.rms_norm(x, (x.size(-1),))


def apply_rotary_emb(x, cos, sin):
    assert x.ndim == 4
    d = x.shape[3] // 2
    x1, x2 = x[..., :d], x[..., d:]
    y1 = x1 * cos + x2 * sin
    y2 = x1 * (-sin) + x2 * cos
    return torch.cat([y1, y2], 3)


def standard_attention(q, k, v):
    """Full causal self-attention through PyTorch SDPA."""
    q = q.transpose(1, 2)
    k = k.transpose(1, 2)
    v = v.transpose(1, 2)
    y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    return y.transpose(1, 2)


class CausalSelfAttention(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.head_dim = self.n_embd // self.n_head
        assert self.n_embd % self.n_head == 0
        self.c_q = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_k = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_v = nn.Linear(self.n_embd, self.n_head * self.head_dim, bias=False)
        self.c_proj = nn.Linear(self.n_embd, self.n_embd, bias=False)

    def forward(self, x, cos_sin):
        B, T, C = x.size()
        q = self.c_q(x).view(B, T, self.n_head, self.head_dim)
        k = self.c_k(x).view(B, T, self.n_head, self.head_dim)
        v = self.c_v(x).view(B, T, self.n_head, self.head_dim)

        cos, sin = cos_sin
        q, k = apply_rotary_emb(q, cos, sin), apply_rotary_emb(k, cos, sin)
        q, k = norm(q), norm(k)

        y = standard_attention(q, k, v)
        y = y.contiguous().view(B, T, -1)
        y = self.c_proj(y)
        return y


class MLP(nn.Module):
    def __init__(self, config):
        super().__init__()
        hidden_dim = config.mlp_hidden_multiplier * config.n_embd
        self.c_fc = nn.Linear(config.n_embd, hidden_dim, bias=False)
        self.c_proj = nn.Linear(hidden_dim, config.n_embd, bias=False)

    def forward(self, x):
        x = self.c_fc(x)
        x = F.relu(x).square()
        x = self.c_proj(x)
        return x


class Block(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.attn = CausalSelfAttention(config)
        self.mlp = MLP(config)

    def forward(self, x, cos_sin):
        x = x + self.attn(norm(x), cos_sin)
        x = x + self.mlp(norm(x))
        return x


class GPT(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.transformer = nn.ModuleDict({
            "wte": nn.Embedding(config.vocab_size, config.n_embd),
            "h": nn.ModuleList([Block(config) for _ in range(config.n_layer)]),
        })
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        head_dim = config.n_embd // config.n_head
        # Rotary embeddings
        self.rotary_seq_len = config.sequence_len * config.rotary_seq_len_multiplier
        cos, sin = self._precompute_rotary_embeddings(self.rotary_seq_len, head_dim)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

    @torch.no_grad()
    def init_weights(self):
        # Embedding and unembedding
        torch.nn.init.normal_(self.transformer.wte.weight, mean=self.config.init_wte_mean, std=self.config.init_wte_std)
        torch.nn.init.normal_(self.lm_head.weight, mean=self.config.init_lm_head_mean, std=self.config.init_lm_head_std)
        # Transformer blocks
        n_embd = self.config.n_embd
        s = self.config.init_matrix_scale * n_embd**-0.5
        for block in self.transformer.h:
            torch.nn.init.uniform_(block.attn.c_q.weight, -s, s)
            torch.nn.init.uniform_(block.attn.c_k.weight, -s, s)
            torch.nn.init.uniform_(block.attn.c_v.weight, -s, s)
            torch.nn.init.zeros_(block.attn.c_proj.weight)
            torch.nn.init.uniform_(block.mlp.c_fc.weight, -s, s)
            torch.nn.init.zeros_(block.mlp.c_proj.weight)
        # Rotary embeddings
        head_dim = self.config.n_embd // self.config.n_head
        cos, sin = self._precompute_rotary_embeddings(self.rotary_seq_len, head_dim)
        self.cos, self.sin = cos, sin
        # Cast embeddings to bf16
        self.transformer.wte.to(dtype=torch.bfloat16)

    def _precompute_rotary_embeddings(self, seq_len, head_dim, base=None, device=None):
        if base is None:
            base = self.config.rotary_base
        if device is None:
            device = self.transformer.wte.weight.device
        channel_range = torch.arange(0, head_dim, 2, dtype=torch.float32, device=device)
        inv_freq = 1.0 / (base ** (channel_range / head_dim))
        t = torch.arange(seq_len, dtype=torch.float32, device=device)
        freqs = torch.outer(t, inv_freq)
        cos, sin = freqs.cos(), freqs.sin()
        cos, sin = cos.bfloat16(), sin.bfloat16()
        cos, sin = cos[None, :, None, :], sin[None, :, None, :]
        return cos, sin

    def estimate_flops(self):
        """Estimated FLOPs per token (forward + backward)."""
        nparams = sum(p.numel() for p in self.parameters())
        nparams_exclude = self.transformer.wte.weight.numel()
        h = self.config.n_head
        q = self.config.n_embd // self.config.n_head
        t = self.config.sequence_len
        attn_flops = self.config.n_layer * 12 * h * q * t
        return 6 * (nparams - nparams_exclude) + attn_flops

    def num_scaling_params(self):
        wte = sum(p.numel() for p in self.transformer.wte.parameters())
        lm_head = sum(p.numel() for p in self.lm_head.parameters())
        transformer_matrices = sum(p.numel() for p in self.transformer.h.parameters())
        total = wte + lm_head + transformer_matrices
        return {
            'wte': wte, 'lm_head': lm_head,
            'transformer_matrices': transformer_matrices, 'total': total,
        }

    def setup_optimizer(self, unembedding_lr, embedding_lr, matrix_lr, weight_decay,
                        adam_betas, adam_eps, dmodel_lr_reference):
        model_dim = self.config.n_embd
        matrix_params = list(self.transformer.h.parameters())
        embedding_params = list(self.transformer.wte.parameters())
        lm_head_params = list(self.lm_head.parameters())
        assert len(list(self.parameters())) == (len(matrix_params) + len(embedding_params) +
            len(lm_head_params))
        # Scale LR ∝ 1/√dmodel (tuned at 768 dim)
        dmodel_lr_scale = (model_dim / dmodel_lr_reference) ** -0.5
        print(f"Scaling AdamW LRs by 1/sqrt({model_dim}/{dmodel_lr_reference}) = {dmodel_lr_scale:.6f}")
        param_groups = [
            dict(
                params=lm_head_params,
                lr=unembedding_lr * dmodel_lr_scale,
                betas=adam_betas,
                eps=adam_eps,
                weight_decay=0.0,
            ),
            dict(
                params=embedding_params,
                lr=embedding_lr * dmodel_lr_scale,
                betas=adam_betas,
                eps=adam_eps,
                weight_decay=0.0,
            ),
            dict(
                params=matrix_params,
                lr=matrix_lr,
                betas=adam_betas,
                eps=adam_eps,
                weight_decay=weight_decay,
            ),
        ]
        # Try fused AdamW when supported by this PyTorch version/device.
        try:
            optimizer = torch.optim.AdamW(param_groups, fused=True)
        except (TypeError, RuntimeError):
            optimizer = torch.optim.AdamW(param_groups)
        for group in optimizer.param_groups:
            group["initial_lr"] = group["lr"]
        return optimizer

    def forward(self, idx, targets=None, reduction='mean'):
        B, T = idx.size()
        assert T <= self.cos.size(1)
        cos_sin = self.cos[:, :T], self.sin[:, :T]

        x = self.transformer.wte(idx)
        x = norm(x)
        for block in self.transformer.h:
            x = block(x, cos_sin)
        x = norm(x)

        softcap = self.config.softcap
        logits = self.lm_head(x)
        logits = logits.float()
        logits = softcap * torch.tanh(logits / softcap)

        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1),
                                   ignore_index=self.config.ignore_index, reduction=reduction)
            return loss
        return logits

# ---------------------------------------------------------------------------
# Optimizer (standard AdamW)
# ---------------------------------------------------------------------------

def build_model_config(vocab_size: int = CONFIG.vocab_size_default):
    base_dim = CONFIG.depth * CONFIG.aspect_ratio
    model_dim = ((base_dim + CONFIG.head_dim - 1) // CONFIG.head_dim) * CONFIG.head_dim
    num_heads = model_dim // CONFIG.head_dim
    return GPTConfig(
        sequence_len=CONFIG.sequence_len, vocab_size=vocab_size,
        n_layer=CONFIG.depth, n_head=num_heads, n_embd=model_dim,
        mlp_hidden_multiplier=CONFIG.mlp_hidden_multiplier,
        rotary_seq_len_multiplier=CONFIG.rotary_seq_len_multiplier,
        rotary_base=CONFIG.rotary_base,
        softcap=CONFIG.softcap,
        ignore_index=CONFIG.ignore_index,
        init_wte_mean=CONFIG.init_wte_mean,
        init_wte_std=CONFIG.init_wte_std,
        init_lm_head_mean=CONFIG.init_lm_head_mean,
        init_lm_head_std=CONFIG.init_lm_head_std,
        init_matrix_scale=CONFIG.init_matrix_scale,
    )

# Schedules (all based on progress = training_time / TIME_BUDGET_SECONDS)

def get_lr_multiplier(progress):
    if progress < CONFIG.warmup_ratio:
        return progress / CONFIG.warmup_ratio if CONFIG.warmup_ratio > 0 else 1.0
    elif progress < 1.0 - CONFIG.warmdown_ratio:
        return 1.0
    else:
        cooldown = (1.0 - progress) / CONFIG.warmdown_ratio
        return cooldown * 1.0 + (1 - cooldown) * CONFIG.final_lr_frac

def get_weight_decay(progress):
    return CONFIG.weight_decay * (1 - progress) if CONFIG.weight_decay_decay else CONFIG.weight_decay

def build_model(model_config, device):
    with torch.device("meta"):
        model = GPT(model_config)
    model.to_empty(device=device)
    model.init_weights()
    return model


def train_model():
    # -----------------------------------------------------------------------
    # Setup: tokenizer, model, optimizer, dataloader
    # -----------------------------------------------------------------------
    t_start = time.time()
    torch.manual_seed(CONFIG.seed)
    torch.cuda.manual_seed(CONFIG.seed)
    torch.set_float32_matmul_precision(CONFIG.matmul_precision)
    device = torch.device(CONFIG.device)
    autocast_dtype = getattr(torch, CONFIG.autocast_dtype)
    autocast_ctx = torch.amp.autocast(device_type=CONFIG.device, dtype=autocast_dtype)

    tokenizer = prepare.Tokenizer.from_directory(os.path.expanduser(str(prepare.TOKENIZER_DIR)))
    vocab_size = tokenizer.get_vocab_size()
    print(f"Vocab size: {vocab_size:,}")

    config = build_model_config(vocab_size)
    print(f"Model config: {asdict(config)}")

    raw_model = build_model(config, device)

    param_counts = raw_model.num_scaling_params()
    print("Parameter counts:")
    for key, value in param_counts.items():
        print(f"  {key:24s}: {value:,}")
    num_params = param_counts['total']
    num_flops_per_token = raw_model.estimate_flops()
    print(f"Estimated FLOPs per token: {num_flops_per_token:e}")

    tokens_per_fwdbwd = CONFIG.device_batch_size * CONFIG.sequence_len
    assert CONFIG.total_batch_size % tokens_per_fwdbwd == 0
    grad_accum_steps = CONFIG.total_batch_size // tokens_per_fwdbwd

    optimizer = raw_model.setup_optimizer(
        unembedding_lr=CONFIG.unembedding_lr,
        embedding_lr=CONFIG.embedding_lr,
        adam_betas=CONFIG.adam_betas,
        matrix_lr=CONFIG.matrix_lr,
        weight_decay=CONFIG.weight_decay,
        adam_eps=CONFIG.adam_eps,
        dmodel_lr_reference=CONFIG.dmodel_lr_reference,
    )

    model = torch.compile(raw_model, dynamic=COMPILE_DYNAMIC) if COMPILE_MODEL else raw_model

    train_loader = prepare.make_dataloader(
        tokenizer,
        CONFIG.device_batch_size,
        CONFIG.sequence_len,
        "train",
        buffer_size=CONFIG.dataloader_buffer_size,
        tokenizer_batch_size=CONFIG.tokenizer_batch_size,
        device=CONFIG.device,
    )
    x, y, epoch = next(train_loader)  # prefetch first batch

    print(f"Time budget: {TIME_BUDGET_SECONDS}s")
    print(f"Gradient accumulation steps: {grad_accum_steps}")

    # -----------------------------------------------------------------------
    # Training loop
    # -----------------------------------------------------------------------
    t_start_training = time.time()
    smooth_train_loss = 0
    total_training_time = 0
    step = 0

    while True:
        torch.cuda.synchronize()
        t0 = time.time()
        for micro_step in range(grad_accum_steps):
            with autocast_ctx:
                loss = model(x, y)
            train_loss = loss.detach()
            loss = loss / grad_accum_steps
            loss.backward()
            x, y, epoch = next(train_loader)

        # Progress and schedules
        progress = min(total_training_time / TIME_BUDGET_SECONDS, 1.0)
        lrm = get_lr_multiplier(progress)
        weight_decay = get_weight_decay(progress)
        for group in optimizer.param_groups:
            group["lr"] = group["initial_lr"] * lrm
            if group["weight_decay"] > 0:
                group["weight_decay"] = weight_decay
        optimizer.step()
        raw_model.zero_grad(set_to_none=True)

        train_loss_f = train_loss.item()

        # Fast fail: abort if loss is exploding or NaN
        if math.isnan(train_loss_f) or train_loss_f > LOSS_FAIL_THRESHOLD:
            print("FAIL")
            exit(1)

        torch.cuda.synchronize()
        t1 = time.time()
        dt = t1 - t0

        if step > WARMUP_STEPS_EXCLUDED_FROM_TIMING:
            total_training_time += dt

        # Logging
        ema_beta = EMA_BETA
        smooth_train_loss = ema_beta * smooth_train_loss + (1 - ema_beta) * train_loss_f
        debiased_smooth_loss = smooth_train_loss / (1 - ema_beta**(step + 1))
        pct_done = 100 * progress
        tok_per_sec = int(CONFIG.total_batch_size / dt)
        mfu = 100 * num_flops_per_token * CONFIG.total_batch_size / dt / CONFIG.h100_bf16_peak_flops
        remaining = max(0, TIME_BUDGET_SECONDS - total_training_time)

        print(f"\rstep {step:05d} ({pct_done:.1f}%) | loss: {debiased_smooth_loss:.6f} | lrm: {lrm:.2f} | dt: {dt*1000:.0f}ms | tok/sec: {tok_per_sec:,} | mfu: {mfu:.1f}% | epoch: {epoch} | remaining: {remaining:.0f}s    ", end="", flush=True)

        # GC management (Python's GC causes ~500ms stalls)
        if step == 0 and GC_FREEZE_AFTER_FIRST_STEP:
            gc.collect()
            gc.freeze()
            gc.disable()
        elif GC_COLLECT_INTERVAL > 0 and (step + 1) % GC_COLLECT_INTERVAL == 0:
            gc.collect()

        step += 1

        # Time's up - but only stop after warmup steps so we don't count compilation
        if step > WARMUP_STEPS_EXCLUDED_FROM_TIMING and total_training_time >= TIME_BUDGET_SECONDS:
            break

    print()  # newline after \r training log

    total_tokens = step * CONFIG.total_batch_size
    t_end = time.time()
    timed_steps = step - WARMUP_STEPS_EXCLUDED_FROM_TIMING
    steady_state_mfu = 100 * num_flops_per_token * CONFIG.total_batch_size * timed_steps / total_training_time / CONFIG.h100_bf16_peak_flops if total_training_time > 0 else 0
    peak_vram_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
    metrics = {
        "training_seconds": float(total_training_time),
        "total_seconds": float(t_end - t_start),
        "peak_vram_mb": float(peak_vram_mb),
        "mfu_percent": float(steady_state_mfu),
        "total_tokens_M": float(total_tokens / 1e6),
        "num_steps": int(step),
        "num_params_M": float(num_params / 1e6),
        "depth": int(CONFIG.depth),
    }
    return TrainingResult(
        model=raw_model,
        tokenizer=tokenizer,
        model_config=config,
        training_metrics=metrics,
    )


def main():
    train_model()


if __name__ == "__main__":
    main()
