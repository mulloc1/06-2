import contextlib
import io
import unittest

import helpers  # noqa: F401 — bootstrap sys.path

from ai_gitgen import cli


class TestCliSkeleton(unittest.TestCase):
    def test_top_level_help_lists_subcommands(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                cli.main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        help_text = buf.getvalue()
        self.assertIn("commit", help_text)
        self.assertIn("pr", help_text)

    def test_commit_help_lists_shared_options(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                cli.main(["commit", "--help"])
        self.assertEqual(cm.exception.code, 0)
        help_text = buf.getvalue()
        for flag in ("--model", "--temperature", "--max-tokens", "--safe-mode"):
            self.assertIn(flag, help_text)

    def test_unknown_subcommand_exits_2(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            cli.main(["nope"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
