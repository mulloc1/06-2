"""Terminal output helpers."""

from __future__ import annotations

import sys


def no_changes() -> None:
    sys.stdout.write("No changes detected.\n")


def error(msg: str) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
