"""Broker and Docker process management for the harness.

This module starts the local-only HTTP broker, launches the agent container, and
watches the hard wall-clock deadline.  The SSH private key is passed only to the
host broker process; Docker receives only the isolated workspace, the per-run
agent runtime home, and an ephemeral bearer token for broker requests.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from harness.config import HarnessConfig
from harness.util import REPO_ROOT


DEFAULT_AGENT_TOKEN_ENVS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "OPENAI_API_KEY",
)
"""Common agent credential variables passed through if present on the host."""


def start_broker(config: HarnessConfig, token: str) -> subprocess.Popen[str]:
    """Start the host-side GPU broker and wait for its health endpoint.

    The broker is launched through ``uv`` against the repository project so it
    uses the same Python environment as the rest of the repo tooling.  It binds
    to localhost and accepts only bearer-token authenticated ``/run`` requests.
    """

    log = (config.archive_dir / "harness" / "gpu-broker.log").open("w", encoding="utf-8")
    args = [
        "uv",
        "run",
        "--no-sync",
        "--project",
        str(REPO_ROOT / "research-loop"),
        "python",
        "-m",
        "harness.gpu_broker",
        "serve",
        "--workspace",
        str(config.agent_workspace),
        "--host-cache",
        str(config.shared_local_cache),
        "--ssh-host",
        config.ssh_host or "smoke.local",
        "--ssh-user",
        config.ssh_user,
        "--ssh-port",
        str(config.ssh_port),
        "--remote-root",
        config.remote_root,
        "--prepare-shards",
        str(config.prepare_shards),
        "--job-timeout-seconds",
        str(config.gpu_job_timeout_seconds),
        f"--token={token}",
        "--port",
        str(config.broker_port),
        "--run-id",
        config.run_id,
    ]
    if config.smoke:
        args.append("--smoke")
    else:
        assert config.ssh_key is not None
        args += ["--ssh-key", str(config.ssh_key)]

    proc = subprocess.Popen(args, cwd=REPO_ROOT, text=True, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(50):
        if proc.poll() is not None:
            raise SystemExit(f"GPU broker failed to start. See {config.archive_dir / 'harness' / 'gpu-broker.log'}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{config.broker_port}/health", timeout=0.2) as response:
                if response.status == 200:
                    return proc
        except Exception:
            time.sleep(0.1)
    raise SystemExit(f"GPU broker did not become healthy on port {config.broker_port}")


def stop_process(proc: subprocess.Popen[str] | None) -> None:
    """Terminate a child process and escalate to kill only if it ignores TERM."""

    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def docker_env_args(config: HarnessConfig, token: str, started_at: int) -> list[str]:
    """Build the fixed Docker arguments for the agent container.

    Only two host paths are mounted: the isolated workspace and the per-run
    agent runtime home.  Cache directories and SSH keys stay on the host side
    and are handled by the broker.
    """

    stop_at = started_at + config.agent_stop_after_seconds
    args = [
        "--rm",
        "--name",
        f"research-loop-agent-{config.run_id}",
        "--add-host=host.docker.internal:host-gateway",
        "--mount",
        f"type=bind,source={config.agent_workspace},target=/workspace",
        "--mount",
        f"type=bind,source={config.runtime_home},target={config.runtime_target}",
        "-w",
        "/workspace",
        "-e",
        f"AGENT={config.agent}",
        "-e",
        f"AGENT_MAX_LOOPS={config.loops}",
        "-e",
        f"AGENT_MODEL={config.agent_model}",
        "-e",
        f"AGENT_REASONING_EFFORT={config.reasoning_effort}",
        "-e",
        f"GPU_BROKER_URL=http://host.docker.internal:{config.broker_port}",
        "-e",
        f"GPU_BROKER_TOKEN={token}",
        "-e",
        f"HARNESS_STARTED_AT={started_at}",
        "-e",
        f"HARNESS_CODEX_STOP_AT={stop_at}",
        "-e",
        f"HARNESS_MIN_REMAINING_SECONDS={config.min_remaining_seconds}",
        "-e",
        f"RESTART_DELAY_SECONDS={config.restart_delay_seconds}",
    ]
    if config.agent == "codex":
        args += ["-e", f"CODEX_HOME={config.runtime_target}"]
    else:
        args += ["--user", f"{os.getuid()}:{os.getgid()}", "-e", f"HOME={config.runtime_target}"]

    for name in sorted(set(DEFAULT_AGENT_TOKEN_ENVS + config.agent_env)):
        if os.environ.get(name):
            args += ["-e", f"{name}={os.environ[name]}"]
    return args


def run_container(config: HarnessConfig, token: str) -> None:
    """Start Docker, watch the hard deadline, and let the container exit."""

    container_name = f"research-loop-agent-{config.run_id}"
    subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    started_at = int(time.time())
    print(
        "\n".join(
            [
                "Starting Docker research-loop harness",
                f"  run id:       {config.run_id}",
                f"  workspace:    {config.agent_workspace}",
                f"  archive:      {config.archive_dir}",
                f"  image:        {config.agent_image}",
                f"  agent:        {config.agent}",
                f"  loops:        {config.loops} ({'until stopped' if config.loops == 0 else 'fixed'})",
                f"  broker:       http://127.0.0.1:{config.broker_port}",
                f"  remote:       {'smoke mode' if config.smoke else f'{config.ssh_user}@{config.ssh_host}:{config.remote_root}'}",
                f"  cache:        {config.shared_local_cache}",
            ]
        )
    )
    proc = subprocess.Popen(
        [
            "docker",
            "run",
            *docker_env_args(config, token, started_at),
            config.agent_image,
            "bash",
            "/workspace/memory/harness/container-entrypoint.sh",
        ],
        cwd=REPO_ROOT,
    )
    deadline = started_at + config.time_limit_seconds
    while proc.poll() is None:
        if int(time.time()) >= deadline:
            print(f"hard time limit reached; stopping container {container_name}", file=sys.stderr)
            subprocess.run(["docker", "stop", "-t", "60", container_name], check=False)
            break
        time.sleep(5)
    proc.wait()
