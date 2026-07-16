# 기준 5 · PR 본문 구조

> **평가 항목:** 항목 1 · 기능·동작 검증 — PR 본문 구조  
> **질문:** PR 본문에 Why / What / How to Test 섹션이 포함되는가?

---

## 결론

**예.** `build_pr` 유저 프롬프트가 `## Why`, `## What`, `## How to Test` 헤더와 각 섹션 불릿을 **필수 출력 형식**으로 요구한다. 현재는 프롬프트로 형식을 유도하며, `polish.py`의 구조 검증은 아직 스텁이다.

---

## 구현 방식

### 프롬프트 템플릿 — `prompts.py`

```python
"Output format:\n"
"Title: <one line, <=80 chars>\n\n"
"## Why\n"
"- ...\n\n"
"## What\n"
"- ...\n\n"
"## How to Test\n"
"- ..."
```

| 섹션 | 역할 |
|------|------|
| **Why** | 변경 동기·문제 |
| **What** | 실제 변경 내용 |
| **How to Test** | 리뷰어 검증 절차 |

시스템 프롬프트의 “Always answer in the exact format requested”와 맞춰, 모델이 이 세 헤더를 포함한 초안을 내도록 한다.

### 후속 검증 (계획)

`docs/plan.md`에서는 `polish.enforce_pr`이 섹션 누락 시 재시도하도록 설계되어 있다. 현재 `polish.py`는 TODO이므로, 구조 보장은 **프롬프트 준수**에 의존한다.

---

## 검증 방법

```bash
PYTHONPATH=src python3 -m ai_gitgen pr
# 출력에 ## Why / ## What / ## How to Test 가 각각 있는지 확인
```
