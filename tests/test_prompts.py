import unittest

import helpers  # noqa: F401
from ai_git_cli import git_changes, prompts


SNAPSHOT = git_changes.GitSnapshot(" M app.py", ("app.py",), "+change")


class TestPrompts(unittest.TestCase):
    def test_commit_context_and_rules(self) -> None:
        content = prompts.build_messages("commit", SNAPSHOT, truncated=False)[1]["content"]
        self.assertIn("app.py", content)
        self.assertIn("+change", content)
        self.assertIn("SUBJECT:", content)
        self.assertIn("72자", content)
        self.assertIn("1~2개", content)

    def test_pr_sections(self) -> None:
        content = prompts.build_messages("pr", SNAPSHOT, truncated=False)[1]["content"]
        for heading in ("## Why", "## What", "## How to Test"):
            self.assertIn(heading, content)
        self.assertIn("80자", content)

    def test_truncation_notice(self) -> None:
        content = prompts.build_messages("pr", SNAPSHOT, truncated=True)[1]["content"]
        self.assertIn("diff가 잘렸", content)
        self.assertIn("추측하지 마세요", content)


if __name__ == "__main__":
    unittest.main()
