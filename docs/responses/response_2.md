# 기준 2 · PR 초안 생성

> **평가 항목:** 항목 1 · 기능·동작 검증 — PR 초안 생성  
> **질문:** PR 제목·본문 형식의 초안이 터미널에 출력되고, 초안임이 명시되는가?

---

## 결론

**예(제목·본문 형식·터미널 출력).** `prompts.build_pr`이 Title과 Why/What/How to Test 섹션을 요구하고, `pr` 서브커맨드가 결과를 stdout에 출력한다. “초안”이라는 사용자-facing 라벨은 아직 없고, 출력 헤더에 한 줄 명시하면 보완된다.

---

## 구현 방식

### 1. PR 출력 포맷 — `prompts.py`

```text
Title: <one line, <=80 chars>

## Why
- ...

## What
- ...

## How to Test
- ...
```

GitHub PR에 그대로 붙여 넣을 수 있는 **초안 템플릿**이다. 각 섹션에 최소 1개 불릿을 요구한다.

### 2. CLI 진입점 — `cli.py`

```bash
python -m ai_gitgen pr [--model ...] [--temperature ...] [--max-tokens ...]
```

`_handle_pr` → `_run_subcommand(..., build_fn=prompts.build_pr)`로 커밋과 동일한 파이프라인을 쓰고, 프롬프트만 PR용으로 바꾼다. 결과는 `sys.stdout.write`로 터미널에 표시된다.

### 3. “초안” 명시 (보완 포인트)

프롬프트 문구에 “pull-request draft”가 있지만, 사용자에게 보이는 stdout에는 “초안” 표시가 없다. 예를 들어 다음을 앞에 붙이면 된다.

```text
=== PR Draft (검토 후 GitHub에 붙여 넣으세요) ===
```

---

## 검증 방법

```bash
PYTHONPATH=src python3 -m ai_gitgen pr
# → Title / ## Why / ## What / ## How to Test 가 stdout에 나오는지 확인
```
