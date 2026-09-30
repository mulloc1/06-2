import unittest

import helpers  # noqa: F401
from ai_git_cli import git_changes, security


class TestSecurity(unittest.TestCase):
    def test_masks_supported_sensitive_patterns(self) -> None:
        source = """+EMAIL=dev@example.com
+CODYSSEY_API_KEY="secret-key"
+github_token=plain-token
+Authorization: Bearer bearer.value
+AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF"""

        masked, count = security.mask_text(source)

        self.assertEqual(count, 5)
        for secret in (
            "dev@example.com",
            "secret-key",
            "plain-token",
            "bearer.value",
            "AKIA1234567890ABCDEF",
        ):
            self.assertNotIn(secret, masked)
        self.assertIn('CODYSSEY_API_KEY="[MASKED_SECRET]"', masked)
        self.assertIn("github_token=[MASKED_SECRET]", masked)
        self.assertIn("Bearer [MASKED_BEARER_TOKEN]", masked)
        self.assertIn("[MASKED_AWS_ACCESS_KEY]", masked)
        self.assertIn("[MASKED_EMAIL]", masked)

    def test_preserves_normal_code_and_similar_words(self) -> None:
        source = "+tokenizer = build_tokenizer()\n+message = 'hello'"
        self.assertEqual(security.mask_text(source), (source, 0))

    def test_masks_json_assignment_and_multiple_emails(self) -> None:
        source = '+{"client_secret": "abc 123", "owners": "a@x.dev,b@y.dev"}'
        masked, count = security.mask_text(source)
        self.assertEqual(count, 3)
        self.assertIn('"client_secret": "[MASKED_SECRET]"', masked)
        self.assertNotIn("abc 123", masked)
        self.assertNotIn("a@x.dev", masked)
        self.assertNotIn("b@y.dev", masked)

    def test_snapshot_masks_only_diff_and_keeps_original_unchanged(self) -> None:
        secret = "dev@example.com"
        snapshot = git_changes.GitSnapshot(
            " M dev@example.com.txt",
            ("dev@example.com.txt",),
            {
                "변경 파일": "- dev@example.com.txt",
                "git status": " M dev@example.com.txt",
                "staged diff": f"+owner={secret}",
                "review notes": secret,
            },
        )

        masked, count = security.mask_snapshot(snapshot)

        self.assertEqual(count, 1)
        self.assertIn(secret, snapshot.prompt_context["staged diff"])
        self.assertNotIn(secret, masked.prompt_context["staged diff"])
        self.assertEqual(masked.prompt_context["git status"], snapshot.prompt_context["git status"])
        self.assertEqual(masked.prompt_context["review notes"], secret)
        self.assertEqual(masked.files, snapshot.files)


if __name__ == "__main__":
    unittest.main()
