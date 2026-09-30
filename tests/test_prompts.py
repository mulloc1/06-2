import unittest

import helpers  # noqa: F401
from ai_git_cli import git_changes, prompts


SNAPSHOT = git_changes.GitSnapshot(" M app.py", ("app.py",), "+change")


class TestPrompts(unittest.TestCase):
    def test_commit_context_and_rules(self) -> None:
        content = prompts.build_messages("commit", SNAPSHOT)[1]["content"]
        self.assertIn("app.py", content)
        self.assertIn("+change", content)
        self.assertIn("한 줄로만", content)
        self.assertIn("72자", content)
        self.assertIn("본문을 붙이지 마세요", content)

    def test_pr_sections(self) -> None:
        content = prompts.build_messages("pr", SNAPSHOT)[1]["content"]
        for heading in ("## Why", "## What", "## How to Test"):
            self.assertIn(heading, content)
        self.assertIn("80자", content)

if __name__ == "__main__":
    unittest.main()
