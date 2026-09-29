# 평가 문항 4 · 변경사항 없음

## 답변

`git_changes.collect()`은 `git status --short --untracked-files=all`의 결과가 비어 있으면 빈 `GitSnapshot`을 반환한다. CLI는 이 상태를 API 키 확인과 API 호출보다 먼저 처리하여 `변경사항이 없습니다.`를 stdout에 출력한다.

변경이 없는 상태는 오류가 아니므로 종료 코드는 `0`이다. `tests/test_cli.py` 역시 이 경우 안내 문구가 출력되고 AI API가 호출되지 않는지 검증한다.
