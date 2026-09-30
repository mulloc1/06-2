"""Build commit and pull-request prompts."""

from collections.abc import Mapping

from .git_changes import GitSnapshot


SYSTEM_PROMPT = """You write factual Git commit messages and pull request drafts.
Use only the supplied Git context. Never invent tests, files, or behavior.
Follow the requested format exactly and write the draft in Korean."""


def _render_context(context: Mapping[str, str]) -> str:
    """Render every non-empty snapshot context entry as a prompt section."""

    return "\n\n".join(
        f"{name}:\n{value}" for name, value in context.items() if value.strip()
    )


def build_messages(command: str, snapshot: GitSnapshot) -> list[dict[str, str]]:
    """Build API messages for a commit or PR draft."""

    if command == "commit":
        rules = """커밋 메시지 초안을 작성하세요.
- 한 줄로만 작성하고 권장 50자 이하, 최대 72자를 지키세요.
- `SUBJECT:` 같은 라벨이나 본문을 붙이지 마세요.
- 커밋 메시지 외의 내용은 출력하지 마세요."""
    else:
        rules = """Pull Request 초안을 작성하세요.
- TITLE은 한 줄이며 최대 80자입니다.
- Why, What, How to Test에 각각 한 개 이상의 불릿을 작성하세요.
- 실행하지 않은 테스트가 통과했다고 주장하지 마세요.
- 다음 형식 외의 내용은 출력하지 마세요.

TITLE: <제목>
## Why
- <필요성>
## What
- <변경 내용>
## How to Test
- <검증 방법>"""

    context = _render_context(snapshot.prompt_context)
    user_prompt = f"{rules}\n\n{context}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
