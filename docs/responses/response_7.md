# 기준 7 · 출력 포맷 규칙

> **평가 항목:** 항목 1 · 기능·동작 검증 — 출력 포맷 규칙  
> **질문:** 커밋 제목 길이·본문 불릿 등 포맷 규칙이 프롬프트 또는 검증에 반영되는가?

---

## 결론

**예(프롬프트 반영).** 제목 길이(권장 ≤50, 최대 72), 불릿 개수(최대 3), PR 제목 ≤80자, Why/What/How 섹션 규칙이 `prompts.py`에 명시되어 있다. 사후 길이·구조 **검증 코드**(`polish.py`)는 아직 TODO이며, 현재는 모델이 형식을 따르도록 유도하는 방식이다.

---

## 구현 방식

### 커밋 규칙 — `build_commit`

| 규칙 | 프롬프트 문구 |
|------|---------------|
| Subject 한 줄 | `Subject: <one line, ...>` |
| 명령형 | `imperative mood` |
| 길이 | `<=50 chars recommended, max 72 chars` |
| Body | optional, up to 3 bullets |
| 불릿 내용 | each referencing a file or module |

### PR 규칙 — `build_pr`

| 규칙 | 프롬프트 문구 |
|------|---------------|
| Title 한 줄 | `Title: <one line, <=80 chars>` |
| 본문 섹션 | `## Why` / `## What` / `## How to Test` |
| 불릿 | 각 섹션에 `- ...` |

### 검증 계층의 위치

```
프롬프트(형식 요구)  →  AI 생성  →  polish(계획: 길이·섹션 검사)  →  stdout
```

`docs/plan.md`는 post-process 우선 + 필요 시 1회 재생성을 선택했다. `polish.py`가 채워지면 제목 길이·불릿 개수를 코드로 강제할 수 있다.

---

## 검증 방법

```bash
# 프롬프트에 규칙이 들어가는지 단위 테스트로 확인
PYTHONPATH=src python3 -m unittest tests.test_prompts -v
```
