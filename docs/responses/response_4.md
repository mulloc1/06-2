# 기준 4 · 변경사항 없음

`git_changes.collect`에서 `git status --short`가 비어 있으면 `GitSnapshot.empty`가 참이 된다. CLI는 키 확인과 API 호출보다 먼저 `변경사항이 없습니다.`를 stdout에 출력하고 종료 코드 0으로 끝난다.

`tests/test_cli.py`는 이 경로에서 가짜 API 함수가 호출되지 않았음을 함께 검증한다.
