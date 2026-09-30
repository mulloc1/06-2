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
        message = text.strip()
        if not message:
            errors.append("커밋 메시지가 없습니다")
            return errors
        if len(message.splitlines()) != 1:
            errors.append("커밋 메시지는 한 줄이어야 합니다")
        if re.match(r"(?i)^SUBJECT\s*:", message):
            errors.append("SUBJECT 라벨 없이 메시지만 작성해야 합니다")
        if len(message) > 72:
            errors.append("커밋 메시지가 72자를 초과했습니다")
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
