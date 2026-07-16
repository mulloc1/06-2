# 기준 3 · 환경변수·인증

> **평가 항목:** 항목 1 · 기능·동작 검증 — 환경변수·인증  
> **질문:** API 키 환경변수 누락 시 원인을 포함한 오류 메시지가 출력되는가?

---

## 결론

**예.** API 키는 `OPENAI_API_KEY` 환경변수만 사용하며 코드에 하드코딩하지 않는다. 키가 없거나 비어 있으면 `AIError`로 원인을 명시하고, CLI는 이를 **환경 오류(exit 5)** 로 매핑해 stderr에 출력한다.

---

## 구현 방식

### 1. 키 로드 — `ai_client.py`

```python
def _load_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key or not key.strip():
        raise AIError("OPENAI_API_KEY environment variable is not set.")
    return key.strip()
```

`complete()`가 요청을 보내기 직전에 `_load_key()`를 호출하므로, 키가 없으면 네트워크 호출 전에 실패한다.

### 2. CLI 매핑 — `cli.py`

```python
def _ai_exit_code(exc: ai_client.AIError) -> int:
    if "environment variable is not set" in str(exc):
        return EXIT_ENV  # 5
    return EXIT_AI      # 4
```

| 상황 | 출력 | exit code |
|------|------|-----------|
| `OPENAI_API_KEY` 미설정 | stderr: `OPENAI_API_KEY environment variable is not set.` | 5 |
| HTTP/네트워크 등 AI 실패 | stderr: 원인 포함 메시지 | 4 |

사용 예시는 다음과 같다.

```bash
export OPENAI_API_KEY=sk-...
PYTHONPATH=src python3 -m ai_gitgen commit
```

---

## 검증 방법

```bash
unset OPENAI_API_KEY
PYTHONPATH=src python3 -m ai_gitgen commit
# → stderr에 환경변수 미설정 메시지, exit 5
```
