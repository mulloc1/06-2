"""Build commit and pull-request prompts."""

from .git_changes import GitSnapshot


SYSTEM_PROMPT = """You write factual Git commit messages and pull request drafts.
Use only the supplied status and diff. Never invent tests, files, or behavior.
Follow the requested format exactly and write the draft in Korean."""


def build_messages(command: str, snapshot: GitSnapshot) -> list[dict[str, str]]:
    """Build API messages for a commit or PR draft."""

    if command == "commit":
        rules = """커밋 메시지 초안을 작성하세요.
- SUBJECT는 한 줄이며 권장 50자 이하, 최대 72자입니다.
- BODY에는 핵심 변경을 1~2개 불릿으로 작성하세요.
- 다음 형식 외의 내용은 출력하지 마세요.

SUBJECT: <제목>
BODY:
- <핵심 변경>"""
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

    files = "\n".join(f"- {path}" for path in snapshot.files)
    user_prompt = f"""{rules}

변경 파일:
{files or "- 없음"}

git status:
{snapshot.status}

git diff:
{snapshot.diff or "(diff 없음: status와 파일 목록만 사용)"}"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
