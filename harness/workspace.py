"""Workspace and agent-auth preparation for Docker harness runs.

The harness always gives the coding agent a fresh, isolated checkout at
``.local/docker-harness/<run-id>/research-loop``.  This module owns that
checkout lifecycle: copy a clean source tree or resume snapshot, install the
selected evaluator, create the per-run agent runtime home, and initialize git.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from harness.config import HarnessConfig
from harness.util import SOURCE_WORKSPACE, absolute_path, copy_filtered_tree, run


FRESH_WORKSPACE_EXCLUDES = (
    (".git",),
    (".venv",),
    (".local",),
    (".uv-cache",),
    (".uv-tmp",),
    ("__pycache__",),
    ("memory",),
    ("run.log",),
)
"""Source-tree paths that must not be copied into a fresh isolated workspace."""

RESUME_WORKSPACE_EXCLUDES = (
    (".venv",),
    (".local",),
    (".uv-cache",),
    (".uv-tmp",),
    ("__pycache__",),
    ("memory", "codex"),
    ("memory", "codex_text"),
    ("memory", "claude"),
    ("memory", "claude_text"),
    ("memory", "harness"),
)
"""Resume paths that would leak caches or previous runtime logs into a new run."""


def git(args: list[str], cwd: Path) -> str:
    """Run git in ``cwd`` and return stdout, failing with git's output."""

    proc = run(["git", "-C", str(cwd), *args])
    if proc.returncode != 0:
        raise SystemExit(proc.stdout)
    return proc.stdout


def resolve_resume_source(raw: Path) -> Path:
    """Resolve an archive or workspace path to the git checkout to resume.

    New archives contain ``resume/research-loop``.  Older or ad hoc resumes may
    point directly at an archive with ``research-loop/`` or at the checkout
    itself.  Supporting these three shapes preserves practical resumability
    without exposing additional user-facing options.
    """

    source = absolute_path(raw)
    candidates = [source / "resume" / "research-loop", source / "research-loop", source]
    for candidate in candidates:
        if (candidate / ".git").is_dir():
            return candidate
    raise SystemExit("--resume-from must point at an archive or research-loop workspace")


def prepare_agent_home(config: HarnessConfig) -> None:
    """Create the per-run auth/config home mounted into Docker.

    The public interface is provider-neutral: if ``--agent-home-source`` is set,
    the source directory is copied verbatim into the runtime home.  If it is not
    set, the harness applies the conventional defaults for the selected agent:
    Codex uses ``~/.codex`` as its runtime home; Claude receives ``~/.claude``
    and ``~/.claude.json`` under the mounted home directory when they exist.
    """

    config.runtime_home.mkdir(parents=True, exist_ok=True)
    if config.agent_home_source is not None:
        copy_filtered_tree(config.agent_home_source, config.runtime_home, ())
        return

    if config.agent == "claude":
        claude_dir = Path.home() / ".claude"
        claude_config = Path.home() / ".claude.json"
        if claude_dir.is_dir():
            copy_filtered_tree(claude_dir, config.runtime_home / ".claude", ())
        if claude_config.is_file():
            shutil.copy2(claude_config, config.runtime_home / ".claude.json")


def write_workspace_gitignore(workspace: Path) -> None:
    """Write the standard ignore file for per-run generated artifacts."""

    (workspace / ".gitignore").write_text(
        ".venv\n.venv/\n__pycache__/\n*.py[cod]\n.local/\nmemory/\nrun.log\n*.log\n.uv-cache/\n.uv-tmp/\n",
        encoding="utf-8",
    )


def initialize_workspace_git(workspace: Path) -> str:
    """Ensure the isolated workspace is a git repository and return HEAD."""

    if (workspace / ".git").is_dir():
        git(["config", "user.name", "research-loop docker harness"], workspace)
        git(["config", "user.email", "research-loop-docker-harness@example.invalid"], workspace)
    else:
        git(["init", "--initial-branch=master"], workspace)
        git(["config", "user.name", "research-loop docker harness"], workspace)
        git(["config", "user.email", "research-loop-docker-harness@example.invalid"], workspace)
        git(["add", "."], workspace)
        git(["commit", "-m", "Initial research-loop workspace"], workspace)
    return git(["rev-parse", "HEAD"], workspace).strip()


def prepare_workspace(config: HarnessConfig) -> str:
    """Create the isolated workspace, runtime home, cache root, and initial git state.

    Returns the initial commit hash so the archive metadata can identify the
    baseline workspace the agent started from.
    """

    config.harness_root.mkdir(parents=True, exist_ok=True)
    (config.archive_dir / "harness").mkdir(parents=True, exist_ok=True)
    (config.archive_dir / config.agent).mkdir(parents=True, exist_ok=True)
    (config.shared_local_cache / "data").mkdir(parents=True, exist_ok=True)
    (config.shared_local_cache / "tokenizer").mkdir(parents=True, exist_ok=True)
    prepare_agent_home(config)

    if config.resume_from is not None:
        copy_filtered_tree(resolve_resume_source(config.resume_from), config.agent_workspace, RESUME_WORKSPACE_EXCLUDES)
    else:
        copy_filtered_tree(SOURCE_WORKSPACE, config.agent_workspace, FRESH_WORKSPACE_EXCLUDES)
        shutil.copy2(config.eval_source, config.agent_workspace / "immutable" / "eval.py")

    eval_copy = config.agent_workspace / "immutable" / "eval.py"
    if eval_copy.is_file():
        shutil.copy2(eval_copy, config.archive_dir / "harness" / "eval.py")

    write_workspace_gitignore(config.agent_workspace)
    return initialize_workspace_git(config.agent_workspace)
