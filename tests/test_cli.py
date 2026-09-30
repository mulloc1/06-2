import contextlib
import io
import unittest
from unittest import mock

import helpers  # noqa: F401
from ai_git_cli import ai_client, cli, git_changes


CHANGES = git_changes.GitSnapshot(" M app.py", ("app.py",), "+change")


class TestCLI(unittest.TestCase):
    def test_help_and_options(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cli.main(["commit", "--help"])
        for value in ("--model", "--temperature", "--max-tokens", "--timeout"):
            self.assertIn(value, output.getvalue())

    def test_invalid_temperature_is_usage_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            cli.main(["commit", "--temperature", "2.1"])
        self.assertEqual(caught.exception.code, 2)

    def test_no_changes_skips_api(self) -> None:
        empty = git_changes.GitSnapshot("", (), "")
        with mock.patch.object(cli, "collect", return_value=empty):
            with mock.patch.object(ai_client, "complete") as complete:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(cli.main(["commit"]), 0)
        complete.assert_not_called()
        self.assertIn("변경사항이 없습니다", output.getvalue())

    def test_commit_options_and_output(self) -> None:
        generated = "fix: app.py 변경 반영"
        with mock.patch.object(cli, "collect", return_value=CHANGES):
            with mock.patch.object(ai_client, "complete", return_value=generated) as complete:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = cli.main(
                        ["commit", "--model", "model", "--temperature", "0.4", "--max-tokens", "123", "--timeout", "9"]
                    )
        self.assertEqual(code, 0)
        self.assertEqual(complete.call_args.kwargs["model"], "model")
        self.assertEqual(complete.call_args.kwargs["max_tokens"], 123)
        self.assertIn(generated, output.getvalue())
        self.assertIn("직접 검토·수정", output.getvalue())

    def test_pr_output_has_required_sections(self) -> None:
        generated = "TITLE: 제목\n## Why\n- 이유\n## What\n- 변경\n## How to Test\n- 테스트"
        with mock.patch.object(cli, "collect", return_value=CHANGES):
            with mock.patch.object(ai_client, "complete", return_value=generated):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(cli.main(["pr"]), 0)
        for heading in ("## Why", "## What", "## How to Test"):
            self.assertIn(heading, output.getvalue())

    def test_sends_complete_diff(self) -> None:
        marker = "end-of-large-diff"
        changes = git_changes.GitSnapshot(
            " M app.py", ("app.py",), "+" + "x" * 12_000 + marker
        )
        generated = "fix: app.py 변경 반영"
        with mock.patch.object(cli, "collect", return_value=changes):
            with mock.patch.object(ai_client, "complete", return_value=generated) as complete:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(["commit"]), 0)
        self.assertIn(marker, complete.call_args.args[0][1]["content"])

    def test_retries_once_with_lower_temperature(self) -> None:
        valid = "fix: 변경 반영"
        with mock.patch.object(cli, "collect", return_value=CHANGES):
            with mock.patch.object(
                ai_client, "complete", side_effect=["SUBJECT: 잘못된 형식", valid]
            ) as complete:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(["commit", "--temperature", "0.4"]), 0)
        self.assertEqual(complete.call_count, 2)
        self.assertEqual(complete.call_args.kwargs["temperature"], 0.2)
        self.assertIn("형식 오류", complete.call_args.args[0][-1]["content"])

    def test_two_invalid_results_fail(self) -> None:
        with mock.patch.object(cli, "collect", return_value=CHANGES):
            with mock.patch.object(
                ai_client, "complete", return_value="SUBJECT: 잘못된 형식"
            ) as complete:
                error_output = io.StringIO()
                with contextlib.redirect_stderr(error_output):
                    self.assertEqual(cli.main(["commit"]), 1)
        self.assertEqual(complete.call_count, 2)
        self.assertIn("두 번", error_output.getvalue())

    def test_api_error_fails_with_cause(self) -> None:
        with mock.patch.object(cli, "collect", return_value=CHANGES):
            with mock.patch.object(ai_client, "complete", side_effect=ai_client.APIError("HTTP 429")):
                error_output = io.StringIO()
                with contextlib.redirect_stderr(error_output):
                    self.assertEqual(cli.main(["pr"]), 1)
        self.assertIn("HTTP 429", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
