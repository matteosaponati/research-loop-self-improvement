"""Runtime configuration for the Docker/SSH GPU harness.

The free entries are: 
(1) the agent.
(2) reasoning/model settings.
(3) loop count.
(4) run identity.
(5) evaluator.
(6) resume source.
(7) GPU timeout.
(8) agent auth source.
Everything else is a fixed harness policy.

GPU connection details are read from environment variables because they
describe host infrastructure rather than per-run experiment intent:

``GPU_SSH_HOST`` is required for real runs.
``GPU_SSH_KEY`` is required for real runs and is never mounted into Docker.
``GPU_SSH_USER``, ``GPU_SSH_PORT``, and ``GPU_REMOTE_ROOT`` have defaults.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from harness.util import REPO_ROOT, SOURCE_WORKSPACE, absolute_path, require_command, resolve_free_port, run


AGENT_CHOICES = ("codex", "claude")
REASONING_EFFORT_CHOICES = ("low", "medium", "high", "xhigh", "max")
DEFAULT_AGENT_IMAGE = "research-loop-agent:latest"
DEFAULT_ARCHIVE_ROOT = REPO_ROOT / "docs" / "experiments"
DEFAULT_SHARED_CACHE = REPO_ROOT / ".local" / "shared-cache" / "research-loop"
DEFAULT_REMOTE_ROOT = "/root/research-loop-runs"
DEFAULT_GPU_JOB_TIMEOUT_SECONDS = 900
DEFAULT_TIME_LIMIT_SECONDS = 4 * 3600 + 15 * 60
DEFAULT_MIN_REMAINING_SECONDS = 900
DEFAULT_RESTART_DELAY_SECONDS = 10
DEFAULT_PREPARE_SHARDS = 10
DEFAULT_BROKER_PORT = 8765


def run_id_default() -> str:
    """Return the timestamp-based run id used when the user does not supply one."""

    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def iso_now() -> str:
    """Return a stable UTC timestamp for metadata files."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nonnegative_int(raw: str) -> int:
    """Parse an integer command-line value that must be zero or greater."""

    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def positive_int(raw: str) -> int:
    """Parse an integer command-line value that must be greater than zero."""

    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def default_agent_home_source(agent: str) -> Path | None:
    """Return the conventional host auth/config source for an agent.

    The public option is agent-agnostic: ``--agent-home-source`` points at a
    directory whose contents are copied into the runtime home mounted in Docker.
    If the user omits it, we preserve the convenient defaults for the two
    supported agents.
    """

    if agent == "codex":
        return Path.home() / ".codex"
    if agent == "claude":
        return None
    raise ValueError(f"unsupported agent: {agent}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the intentionally small public harness CLI."""

    parser = argparse.ArgumentParser(
        prog="./docker_harness.sh",
        description="Run an isolated Docker coding agent while routing experiment runs to an SSH GPU.",
    )
    parser.add_argument("--agent", choices=AGENT_CHOICES, default="codex", help="Coding agent CLI to run in Docker.")
    parser.add_argument("--agent-model", default="", help="Optional model name passed to the selected agent.")
    parser.add_argument(
        "--reasoning-effort",
        choices=REASONING_EFFORT_CHOICES,
        default="",
        help="Optional reasoning effort passed to the selected agent.",
    )
    parser.add_argument("--loops", type=nonnegative_int, default=0, help="Agent sessions to run; 0 means until stopped.")
    parser.add_argument("--run-id", default=run_id_default(), help="Unique run id for workspace and archive paths.")
    parser.add_argument("--job-name", default="research-loop-agent-docker", help="Human-readable job/archive prefix.")
    parser.add_argument("--eval-name", default="val_bpb", help="Directory name under _evals/ to copy into immutable/eval.py.")
    parser.add_argument("--resume-from", type=Path, help="Previous archive or research-loop workspace to resume.")
    parser.add_argument(
        "--gpu-job-timeout-seconds",
        type=positive_int,
        default=DEFAULT_GPU_JOB_TIMEOUT_SECONDS,
        help="Timeout for each remote immutable/run_experiment.py execution.",
    )
    parser.add_argument(
        "--agent-home-source",
        type=Path,
        help="Agent-agnostic auth/config directory copied into the per-run Docker runtime home.",
    )
    parser.add_argument(
        "--agent-env",
        action="append",
        default=[],
        metavar="NAME",
        help="Environment variable to pass into Docker for agent auth/config; repeat as needed.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run without SSH/GPU and synthesize one broker result for local harness testing.",
    )
    return parser.parse_args(argv)


@dataclass(frozen=True)
class HarnessConfig:
    """Resolved harness configuration after applying defaults.

    The dataclass stores both user-selected values and fixed policy values.
    Most fields are paths or primitive values used directly by Docker, the broker, or the
    archive writer.
    """

    run_id: str
    job_name: str
    agent: str
    agent_model: str
    reasoning_effort: str
    loops: int
    eval_name: str
    resume_from: Path | None
    gpu_job_timeout_seconds: int
    agent_home_source: Path | None
    agent_env: tuple[str, ...]
    smoke: bool
    agent_image: str
    time_limit_seconds: int
    min_remaining_seconds: int
    restart_delay_seconds: int
    prepare_shards: int
    broker_port: int
    shared_local_cache: Path
    archive_root: Path
    ssh_host: str
    ssh_user: str
    ssh_port: int
    ssh_key: Path | None
    remote_root: str

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "HarnessConfig":
        """Build a fully resolved config object from parsed CLI arguments."""

        agent_home_source = args.agent_home_source or default_agent_home_source(args.agent)
        ssh_key = os.environ.get("GPU_SSH_KEY")
        return cls(
            run_id=args.run_id,
            job_name=args.job_name,
            agent=args.agent,
            agent_model=args.agent_model,
            reasoning_effort=args.reasoning_effort,
            loops=args.loops,
            eval_name=args.eval_name,
            resume_from=absolute_path(args.resume_from) if args.resume_from else None,
            gpu_job_timeout_seconds=args.gpu_job_timeout_seconds,
            agent_home_source=absolute_path(agent_home_source) if agent_home_source else None,
            agent_env=tuple(args.agent_env),
            smoke=args.smoke,
            agent_image=DEFAULT_AGENT_IMAGE,
            time_limit_seconds=DEFAULT_TIME_LIMIT_SECONDS,
            min_remaining_seconds=DEFAULT_MIN_REMAINING_SECONDS,
            restart_delay_seconds=DEFAULT_RESTART_DELAY_SECONDS,
            prepare_shards=DEFAULT_PREPARE_SHARDS,
            broker_port=resolve_free_port(DEFAULT_BROKER_PORT),
            shared_local_cache=DEFAULT_SHARED_CACHE,
            archive_root=DEFAULT_ARCHIVE_ROOT,
            ssh_host=os.environ.get("GPU_SSH_HOST", ""),
            ssh_user=os.environ.get("GPU_SSH_USER", "root"),
            ssh_port=int(os.environ.get("GPU_SSH_PORT", "22")),
            ssh_key=absolute_path(ssh_key) if ssh_key else None,
            remote_root=os.environ.get("GPU_REMOTE_ROOT", DEFAULT_REMOTE_ROOT).rstrip("/"),
        )

    @property
    def experiment_id(self) -> str:
        """Archive directory name, combining the stable job name and run id."""

        return f"{self.job_name}-{self.run_id}"

    @property
    def harness_root(self) -> Path:
        """Per-run root under ``.local/docker-harness``."""

        return REPO_ROOT / ".local" / "docker-harness" / self.run_id

    @property
    def agent_workspace(self) -> Path:
        """Isolated project workspace mounted at ``/workspace`` in Docker."""

        return self.harness_root / "research-loop"

    @property
    def runtime_home(self) -> Path:
        """Host-side copy of the agent auth/config home mounted into Docker."""

        return self.harness_root / "agent-home"

    @property
    def runtime_target(self) -> str:
        """Container path used for the selected agent's runtime home."""

        return "/agent-home"

    @property
    def archive_dir(self) -> Path:
        """Final archive directory for metadata, logs, results, and resume state."""

        return self.archive_root / self.experiment_id

    @property
    def eval_source(self) -> Path:
        """Selected evaluator copied into ``immutable/eval.py`` for fresh runs."""

        return REPO_ROOT / "_evals" / self.eval_name / "eval.py"

    @property
    def agent_stop_after_seconds(self) -> int:
        """Soft stop deadline that leaves enough time for archiving."""

        return max(self.time_limit_seconds - self.min_remaining_seconds, 1)

    def validate(self) -> None:
        """Validate host prerequisites before mutating the workspace.

        The checks are intentionally front-loaded: missing Docker, missing auth,
        an absent evaluator, or a reused run id should fail before any workspace
        or archive directory is partially created.
        """

        if not SOURCE_WORKSPACE.is_dir():
            raise SystemExit(f"Missing source workspace: {SOURCE_WORKSPACE}")
        if self.resume_from is None and not self.eval_source.is_file():
            raise SystemExit(f"Unknown --eval-name: {self.eval_name}")
        if self.agent_workspace.exists():
            raise SystemExit(f"Refusing to overwrite existing agent workspace: {self.agent_workspace}")
        if self.archive_dir.exists() and any(self.archive_dir.iterdir()):
            raise SystemExit(f"Refusing to overwrite existing archive directory: {self.archive_dir}")
        if self.gpu_job_timeout_seconds < 60:
            raise SystemExit("--gpu-job-timeout-seconds must be at least 60")
        if not self.smoke:
            if not self.ssh_host:
                raise SystemExit("Set GPU_SSH_HOST to the SSH host for the GPU machine")
            if self.ssh_key is None or not self.ssh_key.is_file():
                raise SystemExit("Set GPU_SSH_KEY to a host-side SSH private key")
        if self.agent_home_source is not None and not self.agent_home_source.is_dir():
            raise SystemExit(f"Agent home source must be a directory: {self.agent_home_source}")
        if self.agent == "codex" and self.agent_home_source is not None:
            if not (self.agent_home_source / "auth.json").is_file():
                raise SystemExit(f"Codex auth source must contain auth.json: {self.agent_home_source}")
        if self.agent == "claude" and self.agent_home_source is None:
            has_default_claude = (Path.home() / ".claude").is_dir() or (Path.home() / ".claude.json").is_file()
            has_token = any(os.environ.get(name) for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"))
            if not has_default_claude and not has_token:
                raise SystemExit("Claude needs --agent-home-source or a Claude/Anthropic token environment variable")
        for command in ("docker", "git", "uv"):
            require_command(command)
        image = run(["docker", "image", "inspect", self.agent_image])
        if image.returncode != 0:
            raise SystemExit(
                f"Docker image not found: {self.agent_image}\n"
                "Build it with: docker build -f docker/agent.Dockerfile -t research-loop-agent:latest ."
            )


def load_config(argv: list[str] | None = None) -> HarnessConfig:
    """Parse, resolve, and validate the public harness CLI."""

    config = HarnessConfig.from_args(parse_args(argv))
    config.validate()
    return config
