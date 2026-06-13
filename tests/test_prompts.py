import pathlib
import unittest

import helpers  # noqa: F401 — bootstrap sys.path

from ai_gitgen import git_io, prompts


def _snapshot(
    *,
    files: tuple[str, ...] = (),
    diff: str = "sample diff",
) -> git_io.GitSnapshot:
    return git_io.GitSnapshot(status="", diff=diff, files=files, empty=False)


class TestPrompts(unittest.TestCase):
    def test_commit_prompt_contains_format_block(self) -> None:
        messages = prompts.build_commit(_snapshot(), truncated=False)
        user_content = messages[1]["content"]
        self.assertIn("Subject:", user_content)
        self.assertIn("Body (optional, up to 3 bullets", user_content)
        self.assertIn("- ...", user_content)

    def test_pr_prompt_contains_all_section_headers(self) -> None:
        messages = prompts.build_pr(_snapshot(), truncated=False)
        user_content = messages[1]["content"]
        self.assertIn("## Why", user_content)
        self.assertIn("## What", user_content)
        self.assertIn("## How to Test", user_content)

    def test_file_list_truncated_to_ten(self) -> None:
        files = tuple(f"file{i}.txt" for i in range(15))
        messages = prompts.build_commit(_snapshot(files=files), truncated=False)
        user_content = messages[1]["content"]
        self.assertIn("file0.txt", user_content)
        self.assertIn("file9.txt", user_content)
        self.assertNotIn("file10.txt", user_content)
        self.assertIn("(+5 more)", user_content)

    def test_truncation_notice_present_when_flag_set(self) -> None:
        with_notice = prompts.build_commit(_snapshot(), truncated=True)[1]["content"]
        without_notice = prompts.build_commit(_snapshot(), truncated=False)[1]["content"]
        self.assertIn("truncated", with_notice)
        self.assertNotIn(
            "do not reference files or hunks that are not visible.",
            without_notice,
        )

    def test_system_prompt_is_shared(self) -> None:
        commit_system = prompts.build_commit(_snapshot(), truncated=False)[0]["content"]
        pr_system = prompts.build_pr(_snapshot(), truncated=False)[0]["content"]
        self.assertEqual(commit_system, pr_system)
        self.assertEqual(commit_system, prompts.SYSTEM_PROMPT)

    def test_no_secret_in_prompts(self) -> None:
        source = pathlib.Path(prompts.__file__).read_text(encoding="utf-8")
        self.assertNotIn("OPENAI_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
