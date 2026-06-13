"""HTTP client for OpenAI Chat Completions."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request

_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
_TIMEOUT_SECONDS = 30


class AIError(Exception):
    """Raised for any failure communicating with the upstream AI provider.

    The message must always include the operator-actionable cause
    (HTTP status, urllib error class, or missing-env-var label).
    """


def _load_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key or not key.strip():
        raise AIError("OPENAI_API_KEY environment variable is not set.")
    return key.strip()


def _sanitize_headers_for_debug(headers: dict[str, str]) -> dict[str, str]:
    sanitized = dict(headers)
    if "Authorization" in sanitized:
        sanitized["Authorization"] = "Bearer ***"
    return sanitized


def _extract_http_error_message(error: urllib.error.HTTPError) -> str:
    body = error.read().decode("utf-8", errors="replace")
    try:
        payload = json.loads(body)
        message = payload.get("error", {}).get("message")
        if message:
            return str(message)
    except json.JSONDecodeError:
        pass
    if body.strip():
        return body.strip()
    return error.reason or "unknown error"


def complete(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {_load_key()}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        url=_COMPLETIONS_URL,
        data=body,
        method="POST",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise AIError("HTTP 401 Unauthorized — check OPENAI_API_KEY.") from exc
        if exc.code == 429:
            raise AIError(
                "HTTP 429 — rate limited; retry after a short wait."
            ) from exc
        message = _extract_http_error_message(exc)
        raise AIError(f"HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        reason_name = type(reason).__name__ if reason is not None else "URLError"
        raise AIError(f"Network error ({reason_name}): {reason}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise AIError("Network error: request timed out after 30s.") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIError("Malformed response from upstream (not JSON).") from exc

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIError(
            "Upstream response missing choices[0].message.content."
        ) from exc
