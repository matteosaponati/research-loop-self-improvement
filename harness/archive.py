"""Archive completed Docker harness runs.

At the end of every run, successful or not, the harness copies the pieces that
matter for analysis and resumption into ``docs/experiments/<job-name>-<run-id>``:
raw agent logs, harness logs, latest experiment outputs, and a sanitized
workspace snapshot that can be passed back through ``--resume-from``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from harness.config import HarnessConfig
from harness.util import copy_filtered_tree
from harness.workspace import RESUME_WORKSPACE_EXCLUDES


def copy_if_exists(source: Path, target: Path) -> None:
    """Copy one file if it exists, creating the target directory first."""

    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def archive_run(config: HarnessConfig) -> None:
    """Copy logs, results, and a resumable workspace snapshot into the archive."""

    memory = config.agent_workspace / "memory"
    if (memory / config.agent).is_dir():
        shutil.copytree(memory / config.agent, config.archive_dir / config.agent, dirs_exist_ok=True)
    if (memory / "harness").is_dir():
        shutil.copytree(memory / "harness", config.archive_dir / "harness", dirs_exist_ok=True)
    copy_if_exists(memory / "results.tsv", config.archive_dir / "results.tsv")
    copy_if_exists(config.agent_workspace / "run.log", config.archive_dir / "latest-run.log")
    copy_filtered_tree(
        config.agent_workspace,
        config.archive_dir / "resume" / "research-loop",
        RESUME_WORKSPACE_EXCLUDES,
    )
    print(f"archive complete: {config.archive_dir}")
