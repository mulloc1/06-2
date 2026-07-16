# 기준 11 · API 예외 처리

> **평가 항목:** 항목 1 · 기능·동작 검증 — API 예외 처리  
> **질문:** API 키 누락, HTTP 에러(401/429), 네트워크·타임아웃을 구분해 처리하는가?

---

## 결론

**예.** `ai_client.complete`가 실패 유형별로 `AIError` 메시지를 만들고, CLI는 환경변수 누락(exit 5)과 그 외 AI 실패(exit 4)를 나눈다. 메시지에 원인과 간단한 조치 힌트가 포함된다.

---

## 구현 방식

### 예외 분기 — `ai_client.py`

| 상황 | 메시지 요지 | 조치 힌트 |
|------|-------------|-----------|
| 키 없음/공백 | `OPENAI_API_KEY environment variable is not set.` | export로 키 설정 |
| HTTP 401 | `HTTP 401 Unauthorized — check OPENAI_API_KEY.` | 키 유효성 확인 |
| HTTP 429 | `HTTP 429 — rate limited; retry after a short wait.` | 잠시 후 재시도 |
| 기타 HTTP | `HTTP {code}: {upstream message}` | 상태·본문 확인 |
| URLError | `Network error ({reason_name}): ...` | 연결·DNS·프록시 |
| Timeout | `Network error: request timed out after 30s.` | 네트워크·재시도 |

```python
except urllib.error.HTTPError as exc:
    if exc.code == 401: ...
    if exc.code == 429: ...
    raise AIError(f"HTTP {exc.code}: {message}") from exc
except urllib.error.URLError as exc: ...
except (TimeoutError, socket.timeout) as exc: ...
```

타임아웃은 `_TIMEOUT_SECONDS = 30`이다.

### CLI — `cli.py`

```python
except ai_client.AIError as exc:
    render.error(str(exc))          # stderr
    return _ai_exit_code(exc)       # 5 or 4
```

스크립트/CI에서 exit code로 “설정 문제인지 / 업스트림·네트워크인지”를 구분할 수 있다.

---

## 검증 방법

```bash
unset OPENAI_API_KEY
PYTHONPATH=src python3 -m ai_gitgen commit   # exit 5, 키 미설정

export OPENAI_API_KEY=invalid
PYTHONPATH=src python3 -m ai_gitgen commit   # 보통 401 → exit 4
```
