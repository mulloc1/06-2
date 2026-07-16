# 기준 13 · max_tokens

> **평가 항목:** 항목 3 · 핵심 개념 이해 — max_tokens  
> **질문:** `max_tokens`가 출력 길이·컨텍스트 유지·절단 위험에 미치는 영향을 설명할 수 있는가?

---

## 결론

**예.** `max_tokens`는 **모델이 생성할 수 있는 응답 토큰 상한**이다. 너무 작으면 문장이 중간에 잘리고, 너무 크면 비용·지연만 늘고 불필요하게 장황해질 수 있다. 이 CLI는 commit **400** / pr **700**을 기본으로 두고 `--max-tokens`로 덮어쓴다.

---

## 개념

| 측면 | 영향 |
|------|------|
| **출력 길이** | 응답이 상한에 닿으면 생성이 멈춤 → Subject만 나오고 Body가 비거나, PR 마지막 섹션이 잘릴 수 있음 |
| **컨텍스트** | 요청 토큰(프롬프트+diff)과 응답 토큰을 합쳐 모델 컨텍스트를 소비. diff truncate(8000자)와 함께 예산을 관리 |
| **절단 위험** | max_tokens가 짧으면 **형식 미완성**(How to Test 누락 등). 길면 형식은 채우기 쉽지만 비용↑ |

입력(diff) truncate와 출력 max_tokens는 다르다.

- **입력 truncate:** 모델이 **못 보는** 변경이 생김 → hallucination 방지 노트 필요.
- **출력 max_tokens:** 모델이 **쓰다 마는** 경우 → 초안이 불완전.

---

## 이 프로젝트에서의 사용

```python
DEFAULT_MAX_TOKENS_COMMIT = 400
DEFAULT_MAX_TOKENS_PR = 700
```

PR은 Why/What/How 세 블록이 필요해 commit보다 여유를 둔다.

```bash
# 잘림이 의심될 때
python -m ai_gitgen pr --max-tokens 1200

# 짧게만 필요할 때 (비용·속도)
python -m ai_gitgen commit --max-tokens 150
```

---

## 권장

1. 기본값으로 먼저 생성해 본다.
2. Body/섹션이 중간에 끊기면 `--max-tokens`를 올린다.
3. 장황하기만 하면 값을 내리거나, 프롬프트의 “up to 3 bullets” 규칙을 유지한다.
4. 입력 diff가 크면 `DIFF_CHAR_LIMIT` truncate가 먼저 걸리므로, 출력만 키워도 **안 보낸 hunk**는 반영되지 않는다.

---

## 한 줄 요약

`max_tokens`는 **응답 예산** — 부족하면 절단, 과하면 비용·장황함이다.
