import unittest

import helpers  # noqa: F401
from ai_git_cli import validators


class TestValidators(unittest.TestCase):
    def test_commit_length_boundaries(self) -> None:
        for length in (50, 51, 72):
            with self.subTest(length=length):
                text = "가" * length
                self.assertEqual(validators.validate("commit", text), [])
        errors = validators.validate("commit", "가" * 73)
        self.assertIn("커밋 메시지가 72자를 초과했습니다", errors)

    def test_commit_requires_plain_single_line(self) -> None:
        self.assertTrue(validators.validate("commit", ""))
        self.assertTrue(validators.validate("commit", "제목\n본문"))
        self.assertTrue(validators.validate("commit", "SUBJECT: 제목"))
        self.assertEqual(validators.validate("commit", "feat: 기능 추가"), [])

    def test_valid_pr(self) -> None:
        text = "TITLE: 제목\n## Why\n- 이유\n## What\n- 변경\n## How to Test\n- 테스트"
        self.assertEqual(validators.validate("pr", text), [])

    def test_pr_title_boundaries(self) -> None:
        body = "\n## Why\n- 이유\n## What\n- 변경\n## How to Test\n- 테스트"
        self.assertEqual(validators.validate("pr", f"TITLE: {'가' * 80}{body}"), [])
        self.assertIn(
            "TITLE이 80자를 초과했습니다",
            validators.validate("pr", f"TITLE: {'가' * 81}{body}"),
        )

    def test_pr_reports_missing_sections(self) -> None:
        errors = validators.validate("pr", "TITLE: 제목\n## What\n- 변경")
        self.assertIn("Why 섹션에 불릿이 없습니다", errors)
        self.assertIn("How to Test 섹션에 불릿이 없습니다", errors)


if __name__ == "__main__":
    unittest.main()
