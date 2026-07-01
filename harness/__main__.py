"""Command-line entrypoint for the opinionated Docker/SSH GPU harness.

All meaningful behavior lives in dedicated modules: ``config`` parses the small
public CLI, ``workspace`` prepares the isolated checkout, ``docker_run`` manages
the broker and container, and ``archive`` writes the final run artifacts.  This
file should stay tiny so ``python -m harness`` is easy to audit.
"""

from __future__ import annotations

import sys

from harness.config import load_config
from harness.run import run_harness


def main(argv: list[str] | None = None) -> int:
    """Parse the harness CLI and execute one complete run."""

    return run_harness(load_config(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
