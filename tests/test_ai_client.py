import io
import json
import os
import socket
import tempfile
import unittest
from unittest import mock
from urllib import error

import helpers
from ai_git_cli import ai_client


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.body = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class TestAPIClient(unittest.TestCase):
    def call(self) -> str:
        return ai_client.complete(
            [{"role": "user", "content": "hello"}],
            model="gpt-5-mini",
            temperature=0.2,
            max_tokens=100,
            timeout=3,
        )

    def test_missing_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, helpers.Chdir(tmp):
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ai_client.APIError, "CODYSSEY_API_KEY"):
                    self.call()

    def test_reads_dotenv_and_environment_takes_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, helpers.Chdir(tmp):
            with open(".env", "w", encoding="utf-8") as file:
                file.write("CODYSSEY_API_KEY=file-key\n")
            response = FakeResponse({"choices": [{"message": {"content": "ok"}}]})
            with mock.patch.dict(os.environ, {"CODYSSEY_API_KEY": "env-key"}, clear=True):
                with mock.patch.object(ai_client.request, "urlopen", return_value=response) as opened:
                    self.assertEqual(self.call(), "ok")
        self.assertEqual(opened.call_args.args[0].get_header("Authorization"), "Bearer env-key")

    def test_request_parameters(self) -> None:
        response = FakeResponse({"choices": [{"message": {"content": "ok"}}]})
        with mock.patch.dict(os.environ, {"CODYSSEY_API_KEY": "key"}, clear=True):
            with mock.patch.object(ai_client.request, "urlopen", return_value=response) as opened:
                self.call()
        sent = opened.call_args.args[0]
        payload = json.loads(sent.data.decode())
        self.assertEqual(sent.full_url, ai_client.API_URL)
        self.assertEqual(payload["model"], "gpt-5-mini")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["max_tokens"], 100)

    def http_error(self, code: int) -> error.HTTPError:
        body = io.BytesIO(json.dumps({"error": {"message": "cause"}}).encode())
        return error.HTTPError("url", code, "failure", None, body)

    def test_http_errors_have_distinct_messages(self) -> None:
        with mock.patch.dict(os.environ, {"CODYSSEY_API_KEY": "key"}, clear=True):
            for code, expected in ((401, "인증 실패"), (429, "할당량"), (500, "500")):
                with self.subTest(code=code):
                    with mock.patch.object(
                        ai_client.request, "urlopen", side_effect=self.http_error(code)
                    ):
                        with self.assertRaisesRegex(ai_client.APIError, expected):
                            self.call()

    def test_network_and_timeout_messages(self) -> None:
        with mock.patch.dict(os.environ, {"CODYSSEY_API_KEY": "key"}, clear=True):
            with mock.patch.object(
                ai_client.request, "urlopen", side_effect=error.URLError("offline")
            ):
                with self.assertRaisesRegex(ai_client.APIError, "offline"):
                    self.call()
            with mock.patch.object(
                ai_client.request, "urlopen", side_effect=socket.timeout("slow")
            ):
                with self.assertRaisesRegex(ai_client.APIError, "3초"):
                    self.call()

    def test_invalid_response(self) -> None:
        with mock.patch.dict(os.environ, {"CODYSSEY_API_KEY": "key"}, clear=True):
            with mock.patch.object(
                ai_client.request, "urlopen", return_value=FakeResponse({"choices": []})
            ):
                with self.assertRaisesRegex(ai_client.APIError, "생성 텍스트"):
                    self.call()


if __name__ == "__main__":
    unittest.main()
