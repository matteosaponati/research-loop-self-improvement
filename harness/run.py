"""Top-level orchestration for one Docker harness run.

1. prepare the isolated workspace and runtime home.
2. write the generated in-container helper scripts.
3. write metadata describing the fixed harness policy and user choices.
4. start the host broker.
5. run the Docker agent container.
6. stop the broker and archive whatever state exists.
"""

from __future__ import annotations

import secrets
import stat
import subprocess
from pathlib import Path

from harness.archive import archive_run
from harness.config import HarnessConfig, iso_now
from harness.docker_run import run_container, start_broker, stop_process
from harness.scripts import CONTAINER_ENTRYPOINT, GIT_WRAPPER, UV_WRAPPER
from harness.workspace import prepare_workspace


def write_executable(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` and make it executable by all users."""

    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_runtime_files(config: HarnessConfig) -> None:
    """Install the generated wrappers and entrypoint into the isolated workspace."""

    bin_dir = config.agent_workspace / "memory" / "harness" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    write_executable(bin_dir / "uv", UV_WRAPPER)
    write_executable(bin_dir / "git", GIT_WRAPPER)
    write_executable(config.agent_workspace / "memory" / "harness" / "container-entrypoint.sh", CONTAINER_ENTRYPOINT)


def write_metadata(config: HarnessConfig, initial_commit: str) -> None:
    """Write a compact key-value manifest for auditing and resuming the run."""

    remote_cache = f"{config.remote_root}/cache"
    (config.archive_dir / "metadata.txt").write_text(
        "\n".join(
            [
                f"experiment_id={config.experiment_id}",
                f"run_id={config.run_id}",
                f"created_at={iso_now()}",
                f"agent_workspace={config.agent_workspace}",
                f"agent={config.agent}",
                f"agent_model={config.agent_model or 'default'}",
                f"reasoning_effort={config.reasoning_effort or 'default'}",
                f"loops={config.loops}",
                f"agent_runtime_home={config.runtime_home}",
                f"agent_home_source={config.agent_home_source or 'default'}",
                f"initial_commit={initial_commit}",
                f"eval_name={config.eval_name}",
                f"docker_image={config.agent_image}",
                f"time_limit_seconds={config.time_limit_seconds}",
                f"agent_stop_after_seconds={config.agent_stop_after_seconds}",
                f"agent_min_remaining_seconds={config.min_remaining_seconds}",
                f"restart_delay_seconds={config.restart_delay_seconds}",
                f"gpu_ssh_host={config.ssh_host}",
                f"gpu_ssh_user={config.ssh_user}",
                f"gpu_ssh_port={config.ssh_port}",
                f"gpu_remote_root={config.remote_root}",
                f"remote_cache={remote_cache}",
                f"prepare_shards={config.prepare_shards}",
                f"gpu_job_timeout_seconds={config.gpu_job_timeout_seconds}",
                f"gpu_broker_port={config.broker_port}",
                f"shared_local_cache={config.shared_local_cache}",
                f"smoke_mode={int(config.smoke)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_harness(config: HarnessConfig) -> int:
    """Execute one complete harness run from prepared config to final archive."""

    initial_commit = prepare_workspace(config)
    write_runtime_files(config)
    write_metadata(config, initial_commit)
    token = secrets.token_urlsafe(32)
    broker: subprocess.Popen[str] | None = None
    try:
        broker = start_broker(config, token)
        run_container(config, token)
    finally:
        stop_process(broker)
        if config.agent_workspace.exists():
            archive_run(config)
    return 0
