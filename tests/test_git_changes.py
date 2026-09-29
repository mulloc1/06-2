import subprocess
import tempfile
import unittest

import helpers
from ai_git_cli import git_changes


class TestGitChanges(unittest.TestCase):
    def test_clean_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            with helpers.Chdir(repo):
                snapshot = git_changes.collect()
        self.assertTrue(snapshot.empty)

    def test_staged_and_unstaged_diffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            helpers.commit_file(repo, "a.txt", "old\n", "init")
            helpers.commit_file(repo, "b.txt", "old\n", "add b")
            (repo / "a.txt").write_text("staged\n")
            subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
            (repo / "b.txt").write_text("unstaged\n")
            with helpers.Chdir(repo):
                snapshot = git_changes.collect()
        self.assertEqual(snapshot.files, ("a.txt", "b.txt"))
        self.assertIn("+staged", snapshot.diff)
        self.assertIn("+unstaged", snapshot.diff)

    def test_untracked_file_name_but_not_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            (repo / "new.txt").write_text("secret content")
            with helpers.Chdir(repo):
                snapshot = git_changes.collect()
        self.assertEqual(snapshot.files, ("new.txt",))
        self.assertNotIn("secret content", snapshot.diff)

    def test_requires_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = helpers.make_tmp_repo(tmp)
            child = repo / "child"
            child.mkdir()
            with helpers.Chdir(child):
                with self.assertRaisesRegex(git_changes.GitError, "루트"):
                    git_changes.collect()

    def test_rejects_non_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, helpers.Chdir(tmp):
            with self.assertRaisesRegex(git_changes.GitError, "Git 저장소"):
                git_changes.collect()


if __name__ == "__main__":
    unittest.main()
