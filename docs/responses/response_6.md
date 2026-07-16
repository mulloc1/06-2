# 기준 6 · API 파라미터 옵션

> **평가 항목:** 항목 1 · 기능·동작 검증 — API 파라미터 옵션  
> **질문:** `temperature`, `max_tokens` 등 API 파라미터를 CLI 옵션으로 변경할 수 있는가?

---

## 결론

**예.** `commit` / `pr` 공통으로 `--model`, `--temperature`, `--max-tokens`, `--safe-mode`를 제공하며, 값은 `ai_client.complete`에 그대로 전달된다. 코드 수정 없이 품질·길이를 실험할 수 있다.

---

## 구현 방식

### 1. 공유 옵션 — `cli.py`

| 옵션 | 기본값 | 의미 |
|------|--------|------|
| `--model` | `gpt-4o-mini` | 모델 이름 |
| `--temperature` | `0.2` | 샘플링 temperature |
| `--max-tokens` | commit `400` / pr `700` | 응답 토큰 상한 |
| `--safe-mode` | off | diff 시크릿 마스킹 (플래그) |

```python
subparser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, ...)
subparser.add_argument("--max-tokens", type=int, default=None, ...)
```

### 2. API 전달

```python
text = ai_client.complete(
    messages,
    model=args.model,
    temperature=args.temperature,
    max_tokens=args.max_tokens or default_max_tokens,
)
```

`--max-tokens`를 생략하면 서브커맨드별 기본값을 쓴다.

### 3. 사용 예시 (출력 차이 비교)

```bash
# 결정성에 가깝게
PYTHONPATH=src python3 -m ai_gitgen commit --temperature 0.0

# 표현을 더 다양하게
PYTHONPATH=src python3 -m ai_gitgen commit --temperature 0.8

# PR 본문을 더 길게
PYTHONPATH=src python3 -m ai_gitgen pr --max-tokens 1200
```

같은 diff라도 temperature를 바꾸면 문장·표현이 달라지고, max-tokens를 줄이면 본문이 짧아지거나 잘릴 수 있다.

---

## 검증 방법

```bash
PYTHONPATH=src python3 -m ai_gitgen commit --help
# → --model / --temperature / --max-tokens / --safe-mode 표시
```
