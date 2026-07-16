# 기준 14 · 프롬프트 맥락

> **평가 항목:** 항목 1 · 기능·동작 검증 — 프롬프트 맥락  
> **질문:** 프롬프트에 변경 파일 목록과 diff를 포함해 충분한 맥락을 제공하는가?

---

## 결론

**예.** `_format_snapshot`이 변경 파일(최대 10개)과 `=== diff start/end ===`로 감싼 diff를 유저 메시지에 넣고, 시스템 프롬프트로 “diff에 없는 내용을 지어내지 말 것”을 고정한다. diff가 길면 8000자로 truncate하고 잘림을 프롬프트에 알린다.

---

## 구현 방식

### 1. 맥락 블록 — `prompts.py`

```text
Changed files (up to 10):
- path/a.py
- path/b.py

=== diff start ===
===== staged ... =====
...
===== unstaged ... =====
...
=== diff end ===
```

truncate된 경우:

```text
Note: the diff above was truncated; do not reference files or
hunks that are not visible.
```

### 2. 역할 분담

| 구성 | 내용 |
|------|------|
| System | 커밋/PR 작성 어시스턴트, 형식 준수, hallucination 금지 |
| User | 파일 목록 + diff + 출력 포맷 |

파일 목록만 있으면 “무엇을 고쳤는지”가 부족하고, diff만 있으면 큰 변경에서 초점이 흐려질 수 있어 **둘 다** 넣는다.

### 3. truncate — `git_io.truncate` + `cli.py`

```python
truncated_diff, was_truncated = git_io.truncate(snapshot.diff, DIFF_CHAR_LIMIT)  # 8000
messages = build_fn(snapshot_for_prompt, truncated=was_truncated)
```

비용·컨텍스트 한도를 지키면서, 모델이 잘린 부분을 추측하지 않도록 노트를 붙인다.

---

## 검증 방법

```bash
PYTHONPATH=src python3 -m unittest tests.test_prompts -v
# 프롬프트에 Changed files / diff start / 포맷 블록 포함 여부 확인
```
