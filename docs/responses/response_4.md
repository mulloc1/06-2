# 기준 4 · 변경사항 없음

> **평가 항목:** 항목 1 · 기능·동작 검증 — 변경사항 없음  
> **질문:** Git 변경사항이 없을 때 명시적 메시지를 출력하고 정상 종료하는가?

---

## 결론

**예.** `git status`와 staged/unstaged diff가 모두 비어 있으면 `No changes detected.`를 stdout에 출력하고 **exit 0**으로 종료한다. 변경이 없는 것은 오류가 아니므로 AI를 호출하지 않는다.

---

## 구현 방식

### 1. empty 판정 — `git_io.py`

`collect()`가 status·`diff --cached`·`diff HEAD`를 모은 뒤:

```python
empty = (
    status.strip() == ""
    and staged_diff.strip() == ""
    and unstaged_diff.strip() == ""
)
```

세 값이 모두 비어 있으면 `GitSnapshot.empty == True`다.

### 2. 조기 종료 — `cli.py` + `render.py`

```python
if snapshot.empty:
    render.no_changes()  # → "No changes detected.\n"
    return EXIT_OK       # 0
```

AI 호출·프롬프트 구성 전에 return하므로 불필요한 API 비용이 발생하지 않는다.

---

## 검증 방법

```bash
# clean working tree에서
PYTHONPATH=src python3 -m ai_gitgen commit
# → No changes detected.
echo $?  # → 0
```
