"""Run training, evaluation, and result recording as one immutable experiment."""

from __future__ import annotations

import argparse
import csv
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


RESULTS_PATH = Path("memory") / "results.tsv"
RESULT_COLUMNS = [
    "commit",
    "val_bpb",
    "training_seconds",
    "total_seconds",
    "peak_vram_mb",
    "mfu_percent",
    "total_tokens_M",
    "num_steps",
    "num_params_M",
    "depth",
    "status",
    "description",
]
NUMERIC_ZEROES = {
    "val_bpb": 0.0,
    "training_seconds": 0.0,
    "total_seconds": 0.0,
    "peak_vram_mb": 0.0,
    "mfu_percent": 0.0,
    "total_tokens_M": 0.0,
    "num_steps": 0,
    "num_params_M": 0.0,
    "depth": 0,
}
MAX_TOTAL_SECONDS = 600
TRAINING_SECONDS_TOLERANCE = 30


class ExperimentTimeout(TimeoutError):
    pass


def timeout_handler(signum, frame):
    raise ExperimentTimeout(f"experiment exceeded {MAX_TOTAL_SECONDS}s")


def short_commit() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def read_result_rows(path: Path = RESULTS_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [row for row in reader if row]


def ensure_results_file(path: Path = RESULTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        path.write_text("\t".join(RESULT_COLUMNS) + "\n", encoding="utf-8")


def best_previous_val(rows: list[dict[str, str]]) -> float | None:
    values: list[float] = []
    for row in rows:
        if row.get("status") != "keep":
            continue
        try:
            values.append(float(row["val_bpb"]))
        except (KeyError, TypeError, ValueError):
            continue
    return min(values) if values else None


def infer_status(val_bpb: float, rows: list[dict[str, str]]) -> str:
    best = best_previous_val(rows)
    if best is None or val_bpb < best:
        return "keep"
    return "discard"


def format_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "commit": str(row["commit"]),
        "val_bpb": f"{float(row['val_bpb']):.6f}",
        "training_seconds": f"{float(row['training_seconds']):.1f}",
        "total_seconds": f"{float(row['total_seconds']):.1f}",
        "peak_vram_mb": f"{float(row['peak_vram_mb']):.1f}",
        "mfu_percent": f"{float(row['mfu_percent']):.2f}",
        "total_tokens_M": f"{float(row['total_tokens_M']):.1f}",
        "num_steps": str(int(row["num_steps"])),
        "num_params_M": f"{float(row['num_params_M']):.1f}",
        "depth": str(int(row["depth"])),
        "status": str(row["status"]),
        "description": str(row["description"]).replace("\t", " ").replace("\n", " "),
    }


def append_result(row: dict[str, Any], path: Path = RESULTS_PATH) -> None:
    ensure_results_file(path)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writerow(format_row(row))


def print_summary(row: dict[str, Any]) -> None:
    print("---")
    print(f"{'val_bpb:':18s}{float(row['val_bpb']):.6f}")
    print(f"training_seconds: {float(row['training_seconds']):.1f}")
    print(f"total_seconds:    {float(row['total_seconds']):.1f}")
    print(f"peak_vram_mb:     {float(row['peak_vram_mb']):.1f}")
    print(f"mfu_percent:      {float(row['mfu_percent']):.2f}")
    print(f"total_tokens_M:   {float(row['total_tokens_M']):.1f}")
    print(f"num_steps:        {int(row['num_steps'])}")
    print(f"num_params_M:     {float(row['num_params_M']):.1f}")
    print(f"depth:            {int(row['depth'])}")
    print(f"status:           {row['status']}")


def crash_row(description: str, total_seconds: float) -> dict[str, Any]:
    return {
        "commit": short_commit(),
        **NUMERIC_ZEROES,
        "total_seconds": total_seconds,
        "status": "crash",
        "description": description,
    }


def validate_training_duration(training_seconds: float, budget_seconds: float) -> None:
    if training_seconds > budget_seconds + TRAINING_SECONDS_TOLERANCE:
        raise RuntimeError(
            f"training_seconds={training_seconds:.1f} exceeded budget {budget_seconds:.1f}s"
        )


def run_successful_experiment(description: str, started_at: float) -> dict[str, Any]:
    import torch
    from editable import train as train_module
    from immutable.eval import evaluate_model

    result = train_module.train_model()
    metrics = result.training_metrics
    validate_training_duration(
        float(metrics["training_seconds"]),
        float(train_module.TIME_BUDGET_SECONDS),
    )

    result.model.eval()
    autocast_dtype = getattr(torch, train_module.CONFIG.autocast_dtype)
    autocast_ctx = torch.amp.autocast(device_type=train_module.CONFIG.device, dtype=autocast_dtype)
    with autocast_ctx:
        metric_value = evaluate_model(
            result.model,
            result.tokenizer,
            train_module.CONFIG.device_batch_size,
            sequence_len=result.model_config.sequence_len,
            buffer_size=train_module.CONFIG.dataloader_buffer_size,
            tokenizer_batch_size=train_module.CONFIG.tokenizer_batch_size,
            device=train_module.CONFIG.device,
        )

    total_seconds = time.time() - started_at
    peak_vram_mb = max(float(metrics["peak_vram_mb"]), torch.cuda.max_memory_allocated() / 1024 / 1024)
    rows = read_result_rows()
    status = infer_status(float(metric_value), rows)
    return {
        "commit": short_commit(),
        "val_bpb": float(metric_value),
        "training_seconds": float(metrics["training_seconds"]),
        "total_seconds": float(total_seconds),
        "peak_vram_mb": float(peak_vram_mb),
        "mfu_percent": float(metrics["mfu_percent"]),
        "total_tokens_M": float(metrics["total_tokens_M"]),
        "num_steps": int(metrics["num_steps"]),
        "num_params_M": float(metrics["num_params_M"]),
        "depth": int(metrics["depth"]),
        "status": status,
        "description": description,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--description",
        default=os.environ.get("EXPERIMENT_SUMMARY", "unspecified"),
        help="Short one-line summary of the experiment.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started_at = time.time()
    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_TOTAL_SECONDS)
    try:
        row = run_successful_experiment(args.description, started_at)
    except BaseException as exc:
        row = crash_row(f"{args.description} ({type(exc).__name__})", time.time() - started_at)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

    append_result(row)
    print_summary(row)
    return 0 if row["status"] != "crash" else 1


if __name__ == "__main__":
    raise SystemExit(main())
