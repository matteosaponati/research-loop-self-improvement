#!/usr/bin/env python3
"""Narrow host broker that runs immutable experiments on an SSH GPU host.

The Docker container never receives SSH credentials.  Instead, the generated
``uv`` wrapper inside the container POSTs experiment arguments to this local
HTTP server.  The broker accepts only ``immutable/run_experiment.py`` requests,
syncs the isolated workspace to the configured SSH host, runs the immutable
experiment there, and copies back only the artifacts the local agent expects:
``run.log`` and ``memory/results.tsv``.

This file intentionally has its own CLI because it is also useful to test or run
the broker directly. The public harness entrypoint normally starts it as a
child process with an ephemeral bearer token.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import shlex
import subprocess
import sys
import threading
import tomllib
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


RUN_EXPERIMENT = "immutable/run_experiment.py"
MAX_REQUEST_BYTES = 64 * 1024


@dataclass(frozen=True)
class BrokerConfig:
    """Complete configuration for one broker process.

    ``workspace`` is the host-side isolated checkout.  ``host_cache`` points at
    the shared local data/tokenizer cache, or ``None`` when cache sync is
    disabled by a direct broker caller.  SSH fields identify a generic remote GPU
    machine; no Vast.ai-specific assumption is baked into this config.
    """

    workspace: Path
    host_cache: Path | None
    ssh_host: str
    ssh_user: str
    ssh_port: int
    ssh_key: Path | None
    remote_root: str
    prepare_shards: int
    job_timeout_seconds: int
    token: str
    bind_host: str
    port: int
    run_id: str
    smoke: bool


def is_run_experiment_args(args: list[str]) -> bool:
    """Return whether a command targets the immutable experiment runner."""

    return any(arg == RUN_EXPERIMENT or arg.endswith("/" + RUN_EXPERIMENT) for arg in args)


def parse_description(args: list[str]) -> str:
    """Extract the experiment description from runner arguments."""

    for index, arg in enumerate(args):
        if arg == "--description" and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith("--description="):
            return arg.split("=", 1)[1]
    return os.environ.get("EXPERIMENT_SUMMARY", "unspecified")


def sanitize_description(description: str) -> str:
    """Normalize a description so it is safe for logs and shell arguments."""

    return " ".join(description.replace("\t", " ").replace("\n", " ").split())[:240] or "unspecified"


def run_local(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a host command and capture combined output without raising."""

    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class GpuBroker:
    """Broker implementation that serializes remote GPU experiment requests.

    Remote experiment runs mutate the same workspace and cache paths, so the
    broker processes one request at a time under ``self.lock``.  That keeps the
    agent-visible result stream deterministic even if multiple container
    processes accidentally POST at once.
    """

    def __init__(self, config: BrokerConfig) -> None:
        """Store config and initialize request sequencing state."""

        self.config = config
        self.lock = threading.Lock()
        self.sequence = 0

    @property
    def ssh_target(self) -> str:
        """Return the ``user@host`` string used by ssh and rsync."""

        return f"{self.config.ssh_user}@{self.config.ssh_host}"

    def ssh_base(self) -> list[str]:
        """Build the base ssh command with strict non-interactive settings."""

        if self.config.ssh_key is None:
            raise RuntimeError("SSH key is required outside smoke mode")
        return [
            "ssh",
            "-i",
            str(self.config.ssh_key),
            "-p",
            str(self.config.ssh_port),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            self.ssh_target,
        ]

    def rsync_ssh(self) -> str:
        """Return the quoted ssh transport string used by rsync ``-e``."""

        if self.config.ssh_key is None:
            raise RuntimeError("SSH key is required outside smoke mode")
        return (
            "ssh "
            f"-i {shlex.quote(str(self.config.ssh_key))} "
            f"-p {self.config.ssh_port} "
            "-o BatchMode=yes "
            "-o StrictHostKeyChecking=accept-new"
        )

    def remote_workspace(self) -> str:
        """Return the remote workspace path for this run id."""

        return posixpath.join(self.config.remote_root, self.config.run_id, "research-loop")

    def remote_cache(self) -> str:
        """Return the shared remote cache root under the remote run root."""

        return posixpath.join(self.config.remote_root, "cache")

    def host_cache_has_files(self) -> bool:
        """Return whether the local shared cache has useful files to sync."""

        if self.config.host_cache is None:
            return False
        data = self.config.host_cache / "data"
        tokenizer = self.config.host_cache / "tokenizer"
        return (data.is_dir() and any(data.glob("shard_*.parquet"))) or (
            tokenizer.is_dir() and any(tokenizer.iterdir())
        )

    def workspace_uses_cuda(self) -> bool:
        """Verify that the agent has not changed config away from CUDA."""

        path = self.config.workspace / "editable" / "config.toml"
        try:
            with path.open("rb") as handle:
                config = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError):
            return False
        return config.get("device") == "cuda"

    def run_ssh(self, remote_script: str) -> subprocess.CompletedProcess[str]:
        """Run a bash script on the remote GPU host through ssh."""

        return run_local(self.ssh_base() + [shlex.join(["bash", "-lc", remote_script])])

    def ensure_remote_dirs(self) -> None:
        """Create the remote workspace and cache directories if needed."""

        script = "mkdir -p {workspace} {cache}/data {cache}/tokenizer".format(
            workspace=shlex.quote(self.remote_workspace()),
            cache=shlex.quote(self.remote_cache()),
        )
        proc = self.run_ssh(script)
        if proc.returncode != 0:
            raise RuntimeError(f"failed to create remote directories:\n{proc.stdout}")

    def sync_workspace_to_remote(self) -> None:
        """Rsync the isolated workspace to the remote GPU host.

        Runtime logs, local caches, virtual environments, and harness internals
        are intentionally excluded.  The remote receives only the code and state
        needed to run the immutable experiment.
        """

        self.ensure_remote_dirs()
        args = [
            "rsync",
            "-az",
            "--delete",
            "-e",
            self.rsync_ssh(),
            "--exclude",
            ".venv",
            "--exclude",
            ".local",
            "--exclude",
            "memory/codex",
            "--exclude",
            "memory/codex_text",
            "--exclude",
            "memory/claude",
            "--exclude",
            "memory/claude_text",
            "--exclude",
            "memory/harness",
            "--exclude",
            "run.log",
            f"{self.config.workspace}/",
            f"{self.ssh_target}:{self.remote_workspace()}/",
        ]
        proc = run_local(args)
        if proc.returncode != 0:
            raise RuntimeError(f"failed to sync workspace to remote GPU:\n{proc.stdout}")

    def sync_host_cache_to_remote(self) -> None:
        """Send a populated local data/tokenizer cache to the remote cache."""

        if self.config.host_cache is None or not self.host_cache_has_files():
            return
        self.ensure_remote_dirs()
        for name in ("data", "tokenizer"):
            source = self.config.host_cache / name
            source.mkdir(parents=True, exist_ok=True)
            proc = run_local(
                [
                    "rsync",
                    "-az",
                    "--delete",
                    "-e",
                    self.rsync_ssh(),
                    f"{source}/",
                    f"{self.ssh_target}:{posixpath.join(self.remote_cache(), name)}/",
                ]
            )
            if proc.returncode != 0:
                raise RuntimeError(f"failed to sync host {name} cache to remote GPU:\n{proc.stdout}")

    def remote_cache_is_ready(self) -> bool:
        """Return whether remote preparation produced enough cache artifacts."""

        remote_cache = self.remote_cache()
        script = f"""
set -euo pipefail
data_dir={shlex.quote(posixpath.join(remote_cache, "data"))}
tokenizer_dir={shlex.quote(posixpath.join(remote_cache, "tokenizer"))}
data_count="$(find "${{data_dir}}" -maxdepth 1 -type f -name 'shard_*.parquet' | wc -l)"
tokenizer_count="$(find "${{tokenizer_dir}}" -maxdepth 1 -type f | wc -l)"
test "${{data_count}}" -ge {self.config.prepare_shards}
test "${{tokenizer_count}}" -gt 0
"""
        return self.run_ssh(script).returncode == 0

    def fetch_remote_cache_to_host(self) -> None:
        """Fetch prepared data/tokenizer cache back to the local shared cache."""

        if self.config.host_cache is None:
            return
        if not self.remote_cache_is_ready():
            return
        self.config.host_cache.mkdir(parents=True, exist_ok=True)
        for name in ("data", "tokenizer"):
            target = self.config.host_cache / name
            target.mkdir(parents=True, exist_ok=True)
            proc = run_local(
                [
                    "rsync",
                    "-az",
                    "--delete",
                    "-e",
                    self.rsync_ssh(),
                    f"{self.ssh_target}:{posixpath.join(self.remote_cache(), name)}/",
                    f"{target}/",
                ]
            )
            if proc.returncode != 0:
                raise RuntimeError(f"failed to fetch remote {name} cache from GPU:\n{proc.stdout}")

    def fetch_artifacts(self) -> None:
        """Fetch only run artifacts that should be visible to the local agent."""

        (self.config.workspace / "memory").mkdir(parents=True, exist_ok=True)
        proc = run_local(
            [
                "rsync",
                "-az",
                "-e",
                self.rsync_ssh(),
                "--include",
                "run.log",
                "--include",
                "memory/",
                "--include",
                "memory/results.tsv",
                "--exclude",
                "*",
                f"{self.ssh_target}:{self.remote_workspace()}/",
                f"{self.config.workspace}/",
            ]
        )
        if proc.returncode != 0:
            raise RuntimeError(f"failed to fetch artifacts from remote GPU:\n{proc.stdout}")

    def run_remote_experiment(self, description: str) -> tuple[int, str]:
        """Run sync, preparation, and immutable experiment on the remote GPU."""

        remote_workspace = self.remote_workspace()
        remote_cache = self.remote_cache()
        quoted_description = shlex.quote(description)
        script = f"""
set -euo pipefail
cd {shlex.quote(remote_workspace)}
mkdir -p memory .local {shlex.quote(remote_cache)}/data {shlex.quote(remote_cache)}/tokenizer
: > run.log
printf 'experiment_start=%s description=%s\\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" {quoted_description} | tee -a run.log
ln -sfn {shlex.quote(remote_cache)}/data .local/data
ln -sfn {shlex.quote(remote_cache)}/tokenizer .local/tokenizer
uv sync --extra research
uv run --extra research python immutable/prepare.py --num-shards {self.config.prepare_shards}
set +e
timeout --preserve-status {self.config.job_timeout_seconds} \\
  uv run --extra research python immutable/run_experiment.py --description {quoted_description} 2>&1 | tee -a run.log
status=${{PIPESTATUS[0]}}
printf 'experiment_exit_status=%s\\n' "${{status}}" | tee -a run.log
exit "${{status}}"
"""
        proc = self.run_ssh(script)
        return proc.returncode, proc.stdout

    def run_smoke_experiment(self, description: str) -> tuple[int, str]:
        """Produce a synthetic successful run without SSH or GPU access."""

        memory = self.config.workspace / "memory"
        memory.mkdir(parents=True, exist_ok=True)
        commit_proc = run_local(["git", "rev-parse", "--short", "HEAD"], cwd=self.config.workspace)
        commit = commit_proc.stdout.strip() if commit_proc.returncode == 0 else "unknown"
        stdout = "\n".join(
            [
                "---",
                "val_bpb:          1.234000",
                "training_seconds: 0.1",
                "total_seconds:    0.2",
                "peak_vram_mb:     0.0",
                "mfu_percent:      0.00",
                "total_tokens_M:   0.0",
                "num_steps:        0",
                "num_params_M:     0.0",
                "depth:            0",
                "status:           keep",
                "SMOKE_MODE: remote GPU execution skipped",
                "",
            ]
        )
        (self.config.workspace / "run.log").write_text(stdout, encoding="utf-8")
        results = memory / "results.tsv"
        if not results.exists() or results.stat().st_size == 0:
            results.write_text(
                "commit\tval_bpb\ttraining_seconds\ttotal_seconds\tpeak_vram_mb\tmfu_percent\t"
                "total_tokens_M\tnum_steps\tnum_params_M\tdepth\tstatus\tdescription\n",
                encoding="utf-8",
            )
        with results.open("a", encoding="utf-8") as handle:
            handle.write(
                f"{commit}\t1.234000\t0.1\t0.2\t0.0\t0.00\t0.0\t0\t0.0\t0\tkeep\t"
                f"smoke: {description}\n"
            )
        return 0, stdout

    def submit(self, args: list[str]) -> dict[str, Any]:
        """Validate and execute one broker request, returning JSON data."""

        if not is_run_experiment_args(args):
            return {
                "returncode": 64,
                "stdout": "",
                "stderr": "gpu broker only accepts immutable/run_experiment.py requests\n",
            }

        description = sanitize_description(parse_description(args))
        with self.lock:
            self.sequence += 1
            sequence = self.sequence
            try:
                if self.config.smoke:
                    returncode, stdout = self.run_smoke_experiment(description)
                else:
                    if not self.workspace_uses_cuda():
                        return {
                            "returncode": 75,
                            "stdout": "",
                            "stderr": 'gpu broker requires editable/config.toml device = "cuda"\n',
                            "sequence": sequence,
                            "description": description,
                        }
                    self.sync_workspace_to_remote()
                    self.sync_host_cache_to_remote()
                    returncode, stdout = self.run_remote_experiment(description)
                    self.fetch_artifacts()
                    self.fetch_remote_cache_to_host()
                return {
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": "",
                    "sequence": sequence,
                    "description": description,
                }
            except Exception as exc:
                return {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"gpu broker failed: {exc}\n",
                    "sequence": sequence,
                    "description": description,
                }


class BrokerHandler(BaseHTTPRequestHandler):
    """HTTP request handler exposing ``/health`` and authenticated ``/run``."""

    server: "BrokerServer"

    def log_message(self, fmt: str, *args: Any) -> None:
        """Write HTTP server logs with a broker prefix."""

        sys.stderr.write(f"[gpu-broker] {self.address_string()} {fmt % args}\n")

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        """Send a JSON response with explicit content length."""

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self) -> bool:
        """Return whether the request bearer token matches broker config."""

        return self.headers.get("Authorization") == f"Bearer {self.server.broker.config.token}"

    def do_GET(self) -> None:
        """Serve the health check endpoint."""

        if self.path == "/health":
            self.send_json(HTTPStatus.OK, {"ok": True})
        else:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        """Serve authenticated experiment execution requests."""

        if self.path != "/run":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self.authorized():
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            args = payload["args"]
            if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
                raise ValueError("args must be a list of strings")
        except Exception as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self.send_json(HTTPStatus.OK, self.server.broker.submit(args))


class BrokerServer(ThreadingHTTPServer):
    """HTTP server that carries a ``GpuBroker`` instance for handlers."""

    def __init__(self, server_address: tuple[str, int], broker: GpuBroker) -> None:
        """Initialize the HTTP server and attach broker state."""

        super().__init__(server_address, BrokerHandler)
        self.broker = broker


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the direct broker CLI used by the harness child process."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve", help="Run the HTTP broker.")
    serve.add_argument("--workspace", type=Path, required=True)
    serve.add_argument("--host-cache", type=Path)
    serve.add_argument("--ssh-host", required=True)
    serve.add_argument("--ssh-user", default="root")
    serve.add_argument("--ssh-port", type=int, default=22)
    serve.add_argument("--ssh-key", type=Path)
    serve.add_argument("--remote-root", default="/tmp/research-loop-runs")
    serve.add_argument("--prepare-shards", type=int, default=10)
    serve.add_argument("--job-timeout-seconds", type=int, default=900)
    serve.add_argument("--token", required=True)
    serve.add_argument("--bind-host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--run-id", required=True)
    serve.add_argument("--smoke", action="store_true", help="Skip SSH/GPU and write a synthetic result locally.")
    return parser.parse_args(argv)


def validate_config(config: BrokerConfig) -> None:
    """Validate broker config before starting the HTTP server."""

    if not config.workspace.is_dir():
        raise SystemExit(f"workspace does not exist: {config.workspace}")
    if not config.smoke and config.ssh_key is None:
        raise SystemExit("--ssh-key is required unless --smoke is set")
    if config.ssh_key is not None and not config.ssh_key.is_file():
        raise SystemExit(f"SSH key does not exist: {config.ssh_key}")
    if config.prepare_shards < 1:
        raise SystemExit("--prepare-shards must be at least 1")
    if config.job_timeout_seconds < 60:
        raise SystemExit("--job-timeout-seconds must be at least 60")
    if not config.token:
        raise SystemExit("--token must not be empty")
    if not config.remote_root.startswith("/"):
        raise SystemExit("--remote-root must be an absolute remote path")


def main(argv: list[str] | None = None) -> int:
    """Run the direct broker CLI."""

    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "serve":
        config = BrokerConfig(
            workspace=args.workspace.resolve(),
            host_cache=args.host_cache.expanduser().resolve() if args.host_cache else None,
            ssh_host=args.ssh_host,
            ssh_user=args.ssh_user,
            ssh_port=args.ssh_port,
            ssh_key=args.ssh_key.expanduser().resolve() if args.ssh_key else None,
            remote_root=args.remote_root.rstrip("/"),
            prepare_shards=args.prepare_shards,
            job_timeout_seconds=args.job_timeout_seconds,
            token=args.token,
            bind_host=args.bind_host,
            port=args.port,
            run_id=args.run_id,
            smoke=args.smoke,
        )
        validate_config(config)
        server = BrokerServer((config.bind_host, config.port), GpuBroker(config))
        print(f"gpu broker listening on http://{config.bind_host}:{config.port}", flush=True)
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
