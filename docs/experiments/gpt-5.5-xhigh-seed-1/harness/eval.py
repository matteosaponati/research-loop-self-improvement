"""Evaluation metrics."""

from __future__ import annotations

import math

EVAL_TOKENS = 20_971_520


def evaluate_bpb(
    model,
    tokenizer,
    batch_size,
    *,
    split,
    sequence_len,
    eval_tokens=EVAL_TOKENS,
    buffer_size,
    tokenizer_batch_size,
    device,
):
    """
    Bits per byte (BPB): vocab size-independent evaluation metric.
    Sums per-token cross-entropy in nats, sums target byte lengths, then
    converts nats/byte to bits/byte. Special tokens have byte length 0 and
    are excluded from both sums.
    """
    import torch

    with torch.no_grad():
        from immutable import prepare

        token_bytes = prepare.get_token_bytes(device=device)
        data_loader = prepare.make_dataloader(
            tokenizer,
            batch_size,
            sequence_len,
            split,
            buffer_size=buffer_size,
            tokenizer_batch_size=tokenizer_batch_size,
            device=device,
        )
        steps = eval_tokens // (batch_size * sequence_len)
        if steps < 1:
            raise ValueError("eval_tokens must cover at least one evaluation batch")

        total_nats = 0.0
        total_bytes = 0
        for _ in range(steps):
            x, y, _ = next(data_loader)
            loss_flat = model(x, y, reduction="none").view(-1)
            y_flat = y.view(-1)
            nbytes = token_bytes[y_flat]
            mask = nbytes > 0
            total_nats += (loss_flat * mask).sum().item()
            total_bytes += nbytes.sum().item()

        return total_nats / (math.log(2) * total_bytes)


def evaluate_model(
    model,
    tokenizer,
    batch_size,
    *,
    sequence_len,
    eval_tokens=EVAL_TOKENS,
    buffer_size,
    tokenizer_batch_size,
    device,
):
    """Evaluate a trained model on validation BPB."""
    return evaluate_bpb(
        model=model,
        tokenizer=tokenizer,
        batch_size=batch_size,
        split="val",
        sequence_len=sequence_len,
        eval_tokens=eval_tokens,
        buffer_size=buffer_size,
        tokenizer_batch_size=tokenizer_batch_size,
        device=device,
    )
