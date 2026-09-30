# 평가 문항 8 · Git 수집과 AI 호출의 책임 분리

## 답변

Git 수집과 AI 호출은 `GitSnapshot`과 `messages`를 경계로 분리한다. `git_changes.collect()`은 저장소 루트를 확인하고 `git status`와 staged·unstaged diff를 수집해 `GitSnapshot`을 반환한다. 이 모듈은 API 키, 모델, HTTP 요청 형식을 알지 못한다. 반대로 `ai_client.complete()`는 이미 조립된 `messages`와 생성 옵션을 받아 인증, HTTP POST, JSON 응답 파싱, 예외 분류만 담당하며 Git 저장소나 subprocess를 알지 못한다. `cli.py`는 두 기능을 순서대로 호출하는 조합 책임만 가진다.

이 경계 덕분에 Git 명령, 상태 파싱, 수집 항목이 바뀌면 `git_changes.py`만 중심으로 수정하고, API 주소, 인증 방식, 요청·응답 스키마가 바뀌면 `ai_client.py`만 중심으로 수정할 수 있다. 새 Git 정보는 `GitSnapshot.prompt_context`에 항목을 추가하는 방식으로 확장하며, 프롬프트는 이 매핑을 일반적으로 펼쳐내므로 수집 채널이 늘어나도 프롬프트 코드를 함께 고칠 필요가 없다.

테스트도 각 경계에 맞춰 분리한다. Git 수집은 임시 Git 저장소에 실제 staged·unstaged·untracked 상태를 만들어 `GitSnapshot`을 검증하며 네트워크를 사용하지 않는다. AI 호출은 `urlopen`과 환경변수를 mock하여 요청 payload, Authorization 헤더, 응답 파싱, HTTP 401·429, 네트워크, 타임아웃 처리를 Git 없이 검증한다. 마지막으로 CLI 테스트에서 `collect()`과 `complete()`를 각각 mock해 변경사항 없음, 옵션 전달, API 오류 전파 같은 두 계층의 조합만 확인한다.
