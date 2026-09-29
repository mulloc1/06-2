"""Validate the format of AI-generated drafts."""

import re


def _section_bullets(text: str, heading: str, next_heading: str | None) -> list[str]:
    end = rf"(?=^##\s+{re.escape(next_heading)}\s*$|\Z)" if next_heading else r"\Z"
    match = re.search(
        rf"(?ims)^##\s+{re.escape(heading)}\s*$\s*(.*?){end}", text
    )
    if not match:
        return []
    return [
        line for line in match.group(1).splitlines() if line.strip().startswith(("- ", "* "))
    ]


def validate(command: str, text: str) -> list[str]:
    """Return all format errors found in a commit or PR draft."""

    errors: list[str] = []
    if command == "commit":
        subject = re.search(r"(?im)^SUBJECT:\s*(.+)$", text)
        if not subject:
            errors.append("SUBJECT 한 줄이 없습니다")
        elif len(subject.group(1).strip()) > 72:
            errors.append("SUBJECT가 72자를 초과했습니다")

        body = re.search(r"(?ims)^BODY:\s*(.*)$", text)
        bullets = [] if not body else [
            line
            for line in body.group(1).splitlines()
            if line.strip().startswith(("- ", "* "))
        ]
        if len(bullets) not in (1, 2):
            errors.append("BODY에는 1~2개의 불릿이 필요합니다")
        return errors

    title = re.search(r"(?im)^TITLE:\s*(.+)$", text)
    if not title:
        errors.append("TITLE 한 줄이 없습니다")
    elif len(title.group(1).strip()) > 80:
        errors.append("TITLE이 80자를 초과했습니다")

    sections = (
        ("Why", "What"),
        ("What", "How to Test"),
        ("How to Test", None),
    )
    for heading, next_heading in sections:
        if not _section_bullets(text, heading, next_heading):
            errors.append(f"{heading} 섹션에 불릿이 없습니다")
    return errors
