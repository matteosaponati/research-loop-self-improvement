"""Small shared utilities for the Docker harness."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
"""Absolute path to the repository root that contains ``research-loop/``."""

SOURCE_WORKSPACE = REPO_ROOT / "research-loop"
"""The source project copied into every isolated Docker-agent workspace."""


def absolute_path(raw: str | Path, *, base: Path = REPO_ROOT) -> Path:
    """Return ``raw`` as an absolute path, resolving relative paths from ``base``.

    The harness accepts several paths from the command line.  Relative paths are
    convenient for users, but all downstream Docker, rsync, and metadata code is
    simpler and less ambiguous when paths are absolute.
    """

    path = Path(raw).expanduser()
    return path if path.is_absolute() else base / path


def run(args: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    """Run a local command and capture combined stdout/stderr as text.

    The helper deliberately does not raise on non-zero exits.  Harness callers
    need to turn command failures into messages that include the context of the
    phase that failed, rather than exposing a raw ``CalledProcessError``.
    """

    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def require_command(name: str) -> None:
    """Fail early if an external command required on the host is unavailable."""

    if shutil.which(name) is None:
        raise SystemExit(f"Missing required command on PATH: {name}")


def resolve_free_port(preferred: int, tries: int = 24) -> int:
    """Return the first free localhost TCP port starting at ``preferred``.

    Multiple harness jobs can be launched from the same host.  The broker is
    local-only, so we use a small deterministic search range instead of making
    port selection a user-facing option.
    """

    for port in range(preferred, preferred + tries + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise SystemExit(f"Unable to find a free broker port in range {preferred}..{preferred + tries}")


def excluded(rel: Path, patterns: tuple[tuple[str, ...], ...]) -> bool:
    """Return whether a relative path begins with one of the excluded prefixes."""

    parts = rel.parts
    return any(parts[: len(pattern)] == pattern for pattern in patterns)


def copy_filtered_tree(source: Path, target: Path, excludes: tuple[tuple[str, ...], ...]) -> None:
    """Copy a directory tree while skipping path-prefix exclusions.

    ``shutil.copytree`` cannot express the exact resume/source filtering policy
    we need without callback state.  This helper keeps the policy explicit:
    exclude repo internals, local caches, memory logs, and run artifacts while
    preserving normal files, modes, timestamps, and symlinks.
    """

    target.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        rel_root = root_path.relative_to(source)
        dirs[:] = [name for name in dirs if not excluded(rel_root / name, excludes)]
        for name in files:
            rel = rel_root / name
            if excluded(rel, excludes):
                continue
            src = root_path / name
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_symlink():
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                os.symlink(os.readlink(src), dst)
            elif src.is_file():
                shutil.copy2(src, dst)
