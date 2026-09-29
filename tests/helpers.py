import pathlib
import subprocess
import sys

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def make_tmp_repo(tmp_path: pathlib.Path | str) -> pathlib.Path:
    repo = pathlib.Path(tmp_path)
    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "--local", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "--local", "user.name", "Test User"],
        cwd=repo,
        check=True,
    )
    return repo


def commit_file(
    repo: pathlib.Path | str, name: str, content: str, message: str
) -> None:
    repo_path = pathlib.Path(repo)
    path = repo_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(["git", "add", name], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_path, check=True)


class Chdir:
    """Temporarily change the process working directory for a test."""

    def __init__(self, path: pathlib.Path | str) -> None:
        self.path = pathlib.Path(path)
        self.previous = pathlib.Path.cwd()

    def __enter__(self) -> pathlib.Path:
        import os

        os.chdir(self.path)
        return self.path

    def __exit__(self, *_args: object) -> None:
        import os

        os.chdir(self.previous)
