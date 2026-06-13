import os
import subprocess
import tempfile
import unittest

import helpers
from ai_gitgen import git_io


class TestGitIo(unittest.TestCase):
    def _chdir(self, path: str) -> str:
        old = os.getcwd()
        os.chdir(path)
        return old

    def test_empty_repo_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            old = self._chdir(str(repo))
            try:
                snapshot = git_io.collect()
            finally:
                os.chdir(old)
            self.assertTrue(snapshot.empty)
            self.assertEqual(snapshot.files, ())

    def test_staged_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            (repo / "new.txt").write_text("hello\n")
            subprocess.run(["git", "add", "new.txt"], cwd=repo, check=True)
            old = self._chdir(str(repo))
            try:
                snapshot = git_io.collect()
            finally:
                os.chdir(old)
            self.assertFalse(snapshot.empty)
            self.assertIn("new.txt", snapshot.files)
            self.assertIn("+hello", snapshot.diff)

    def test_unstaged_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            helpers.commit_file(repo, "file.txt", "original\n", "init")
            (repo / "file.txt").write_text("modified\n")
            old = self._chdir(str(repo))
            try:
                snapshot = git_io.collect()
            finally:
                os.chdir(old)
            self.assertFalse(snapshot.empty)
            self.assertIn("modified", snapshot.diff)
            self.assertIn("===== unstaged (git diff HEAD) =====", snapshot.diff)

    def test_staged_and_unstaged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            helpers.commit_file(repo, "staged.txt", "staged-base\n", "init")
            helpers.commit_file(repo, "unstaged.txt", "unstaged-base\n", "add unstaged")
            (repo / "staged.txt").write_text("staged-new\n")
            subprocess.run(["git", "add", "staged.txt"], cwd=repo, check=True)
            (repo / "unstaged.txt").write_text("unstaged-content\n")
            old = self._chdir(str(repo))
            try:
                snapshot = git_io.collect()
            finally:
                os.chdir(old)
            self.assertFalse(snapshot.empty)
            self.assertIn("staged.txt", snapshot.files)
            self.assertIn("unstaged.txt", snapshot.files)
            self.assertIn("staged-new", snapshot.diff)
            self.assertIn("unstaged-content", snapshot.diff)

    def test_non_git_cwd_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old = self._chdir(tmp)
            try:
                with self.assertRaises(git_io.GitError):
                    git_io.collect()
            finally:
                os.chdir(old)

    def test_truncate_below_limit_is_noop(self) -> None:
        self.assertEqual(git_io.truncate("abc", 100), ("abc", False))

    def test_truncate_above_limit_marks_truncated(self) -> None:
        diff = "x" * 200
        truncated, was_truncated = git_io.truncate(diff, 50)
        self.assertTrue(was_truncated)
        self.assertIn("DIFF TRUNCATED at 50 chars", truncated)


if __name__ == "__main__":
    unittest.main()
