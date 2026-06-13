"""Prompt builders for commit and PR generation."""

from __future__ import annotations

from ai_gitgen.git_io import GitSnapshot

SYSTEM_PROMPT = (
    "You are an assistant that writes Git commit messages and pull-request "
    "drafts. Always answer in the exact format requested. Never invent files, "
    "modules, or behavior that is not visible in the diff."
)


def _format_snapshot(snapshot: GitSnapshot, truncated: bool) -> str:
    lines = ["Changed files (up to 10):"]
    for path in snapshot.files[:10]:
        lines.append(f"- {path}")
    if len(snapshot.files) > 10:
        lines.append(f"- ... (+{len(snapshot.files) - 10} more)")
    lines.append("")
    lines.append("=== diff start ===")
    lines.append(snapshot.diff)
    lines.append("=== diff end ===")
    if truncated:
        lines.append(
            "Note: the diff above was truncated; do not reference files or "
            "hunks that are not visible."
        )
    return "\n".join(lines)


def build_commit(snapshot: GitSnapshot, *, truncated: bool) -> list[dict[str, str]]:
    change_context = _format_snapshot(snapshot, truncated)
    user_content = (
        f"{change_context}\n\n"
        "Write a Git commit message that summarizes these changes.\n\n"
        "Output format:\n"
        "Subject: <one line, imperative mood, <=50 chars recommended, max 72 chars>\n\n"
        "Body (optional, up to 3 bullets, each referencing a file or module):\n"
        "- ...\n"
        "- ...\n"
        "- ..."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_pr(snapshot: GitSnapshot, *, truncated: bool) -> list[dict[str, str]]:
    change_context = _format_snapshot(snapshot, truncated)
    user_content = (
        f"{change_context}\n\n"
        "Write a pull-request draft for these changes.\n\n"
        "Output format:\n"
        "Title: <one line, <=80 chars>\n\n"
        "## Why\n"
        "- ...\n\n"
        "## What\n"
        "- ...\n\n"
        "## How to Test\n"
        "- ..."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
