"""Load experiment defaults from research-loop/editable/config.toml."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    tomllib = None

CONFIG_PATH = Path(__file__).with_name("config.toml")


@dataclass(frozen=True)
class ExperimentConfig:
    hf_hub_disable_progress_bars: str
    seed: int
    device: str
    matmul_precision: str
    autocast_dtype: str
    h100_bf16_peak_flops: float
    sequence_len: int
    total_batch_size: int
    device_batch_size: int
    dataloader_buffer_size: int
    tokenizer_batch_size: int
    vocab_size_default: int
    depth: int
    aspect_ratio: int
    head_dim: int
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
    embedding_lr: float
    unembedding_lr: float
    matrix_lr: float
    weight_decay: float
    adam_beta1: float
    adam_beta2: float
    adam_eps: float
    dmodel_lr_reference: int
    muon_initial_momentum: float
    muon_ns_steps: int
    muon_beta2: float
    warmup_ratio: float
    warmdown_ratio: float
    final_lr_frac: float
    muon_momentum_warmup_steps: int
    muon_momentum_start: float
    muon_momentum_end: float
    weight_decay_decay: bool

    @property
    def adam_betas(self) -> tuple[float, float]:
        return self.adam_beta1, self.adam_beta2

    def to_jsonable(self) -> dict[str, object]:
        return asdict(self)


def parse_flat_toml(text: str) -> dict[str, Any]:
    """Parse the flat key/value TOML subset used by research-loop/editable/config.toml."""
    values: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        key, raw_value = [part.strip() for part in line.split("=", 1)]
        if raw_value.startswith('"') and raw_value.endswith('"'):
            values[key] = raw_value[1:-1]
        elif raw_value.lower() in {"true", "false"}:
            values[key] = raw_value.lower() == "true"
        elif "." in raw_value or "e" in raw_value.lower():
            values[key] = float(raw_value)
        else:
            values[key] = int(raw_value)
    return values


def load_config(path: Path = CONFIG_PATH) -> ExperimentConfig:
    text = path.read_text(encoding="utf-8")
    raw: dict[str, Any] = tomllib.loads(text) if tomllib else parse_flat_toml(text)
    return ExperimentConfig(**raw)


CONFIG = load_config()
