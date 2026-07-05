#!/usr/bin/env python3
"""Create a repository-local Codex skill skeleton."""

from __future__ import annotations

import sys
from pathlib import Path


def _add_checkout_src_to_path() -> None:
    for parent in Path(__file__).resolve().parents:
        src = parent / "src"
        if (src / "codex_harness" / "scaffold.py").exists():
            sys.path.insert(0, str(src))
            return


_add_checkout_src_to_path()

try:
    from codex_harness.scaffold import main
except ImportError as exc:
    print(
        "ERROR: could not import codex_harness.scaffold; install harness-for-codex or run from the source checkout",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


if __name__ == "__main__":
    raise SystemExit(main())
