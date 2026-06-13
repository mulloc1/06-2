"""Git status and diff capture."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


class GitError(Exception):
    """Raised when git commands fail or the CWD is not inside a repository."""


@dataclass(frozen=True)
class GitSnapshot:
    status: str
    diff: str
    files: tuple[str, ...]
    empty: bool


def _run_git(args: list[str], *, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def _parse_files(status: str) -> tuple[str, ...]:
    seen: set[str] = set()
    files: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path not in seen:
            seen.add(path)
            files.append(path)
    return tuple(files)


def collect() -> GitSnapshot:
    inside = _run_git(["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise GitError(
            "Not a git repository (run from a git-initialized project root)."
        )

    status_result = _run_git(["status", "--porcelain"])
    if status_result.returncode != 0:
        raise GitError(status_result.stderr.strip() or "git status failed.")

    staged_result = _run_git(["diff", "--cached"])
    if staged_result.returncode != 0:
        raise GitError(staged_result.stderr.strip() or "git diff --cached failed.")

    unstaged_result = _run_git(["diff", "HEAD"])
    if unstaged_result.returncode != 0:
        unstaged_result = _run_git(["diff"])
        if unstaged_result.returncode != 0:
            raise GitError(unstaged_result.stderr.strip() or "git diff failed.")

    status = status_result.stdout
    staged_diff = staged_result.stdout
    unstaged_diff = unstaged_result.stdout

    staged_part = staged_diff if staged_diff.strip() else "(none)"
    unstaged_part = unstaged_diff if unstaged_diff.strip() else "(none)"
    combined_diff = (
        "===== staged (git diff --cached) =====\n"
        f"{staged_part}\n\n"
        "===== unstaged (git diff HEAD) =====\n"
        f"{unstaged_part}\n"
    )

    empty = (
        status.strip() == ""
        and staged_diff.strip() == ""
        and unstaged_diff.strip() == ""
    )

    return GitSnapshot(
        status=status,
        diff=combined_diff,
        files=_parse_files(status),
        empty=empty,
    )


def truncate(diff: str, limit: int) -> tuple[str, bool]:
    if len(diff) <= limit:
        return diff, False

    parts = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    header = ""
    sections: list[str]
    if parts and not parts[0].startswith("diff --git "):
        header = parts[0]
        sections = parts[1:] if len(parts) > 1 else [diff]
    else:
        sections = parts if parts else [diff]

    num_sections = max(1, len(sections))
    per_section = limit // num_sections

    truncated_sections: list[str] = []
    for section in sections:
        if len(section) <= per_section:
            truncated_sections.append(section)
        else:
            truncated_sections.append(
                section[:per_section] + "\n... (truncated) ...\n"
            )

    joined = header + "".join(truncated_sections)
    joined += f"\n--- DIFF TRUNCATED at {limit} chars ---\n"
    return joined, True
