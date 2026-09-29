"""Call the Codyssey OpenAI-compatible API."""

import json
import os
from pathlib import Path
import socket
from urllib import error, request


API_KEY_ENV = "CODYSSEY_API_KEY"
API_URL = "https://copa.codyssey.kr/v1/chat/completions"


class APIError(RuntimeError):
    """An API configuration, request, or response error."""


def _dotenv_value(path: Path) -> str:
    """Read CODYSSEY_API_KEY from a local .env file."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ""
    except OSError as exc:
        raise APIError(f"{path} 파일을 읽을 수 없습니다: {exc}") from exc

    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].strip()
        name, separator, value = line.partition("=")
        if separator and name.strip() == API_KEY_ENV:
            return value.strip().strip("'\"")
    return ""


def _api_key() -> str:
    key = os.environ.get(API_KEY_ENV, "").strip()
    key = key or _dotenv_value(Path.cwd() / ".env")
    if not key:
        raise APIError(
            f"{API_KEY_ENV}가 없습니다. "
            "환경변수나 저장소 루트의 .env에 키를 입력하세요."
        )
    return key


def _http_detail(exc: error.HTTPError) -> str:
    """Return a short error detail without exposing request headers."""

    try:
        data = json.loads(exc.read().decode("utf-8", errors="replace"))
        detail = data.get("error", data)
        if isinstance(detail, dict):
            detail = detail.get("message") or detail.get("detail") or detail
        return str(detail)[:300]
    except (OSError, ValueError, TypeError):
        return str(exc.reason or "응답 본문 없음")[:300]
    finally:
        exc.close()


def complete(
    messages: list[dict[str, str]],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> str:
    """Generate text with the Codyssey chat-completions endpoint."""

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    api_request = request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(api_request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = _http_detail(exc)
        if exc.code == 401:
            message = f"인증 실패(HTTP 401): {detail}"
        elif exc.code == 429:
            message = f"요청 한도 또는 할당량 초과(HTTP 429): {detail}"
        else:
            message = f"API HTTP 오류({exc.code}): {detail}"
        raise APIError(message) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise APIError(f"API 요청 시간이 {timeout:g}초를 초과했습니다.") from exc
    except error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            raise APIError(f"API 요청 시간이 {timeout:g}초를 초과했습니다.") from exc
        raise APIError(f"API 네트워크 연결 실패: {exc.reason}") from exc
    except OSError as exc:
        raise APIError(f"API 네트워크 연결 실패: {exc}") from exc

    try:
        content = json.loads(response_body)["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise APIError("API 응답에서 생성 텍스트를 찾을 수 없습니다.") from exc
    return content.strip()
