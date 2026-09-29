"""Collect Git status and diffs from the repository root."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitError(RuntimeError):
    """A Git repository or command error."""


@dataclass(frozen=True)
class GitSnapshot:
    status: str
    files: tuple[str, ...]
    diff: str

    @property
    def empty(self) -> bool:
        return not self.status.strip()


def _git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise GitError(f"Git 명령을 실행할 수 없습니다: {exc}") from exc
    if result.returncode != 0:
        cause = result.stderr.strip() or result.stdout.strip() or "알 수 없는 오류"
        raise GitError(f"git {' '.join(args)} 실패: {cause}")
    return result.stdout


def _files(status: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].split(" -> ")[-1].strip('"')
        paths.append(path)
    return tuple(dict.fromkeys(paths))


def collect(cwd: Path | None = None) -> GitSnapshot:
    """Collect status and staged/unstaged diffs from a Git repository root."""

    current = (cwd or Path.cwd()).resolve()
    try:
        root = Path(_git(["rev-parse", "--show-toplevel"], current).strip()).resolve()
    except GitError as exc:
        raise GitError("현재 위치가 Git 저장소가 아닙니다.") from exc
    if current != root:
        raise GitError(f"Git 저장소 루트에서 실행하세요: {root}")

    status = _git(["status", "--short", "--untracked-files=all"], root).rstrip()
    if not status:
        return GitSnapshot("", (), "")

    staged = _git(["diff", "--cached", "--no-ext-diff"], root).strip()
    unstaged = _git(["diff", "--no-ext-diff"], root).strip()
    parts: list[str] = []
    if staged:
        parts.append("===== staged changes =====\n" + staged)
    if unstaged:
        parts.append("===== unstaged changes =====\n" + unstaged)
    return GitSnapshot(status, _files(status), "\n\n".join(parts))
