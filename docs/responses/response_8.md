# 평가 문항 8 · 책임 분리

## 답변

| 모듈 | 책임 |
| --- | --- |
| `git_changes.py` | 저장소 루트 확인, status, staged/unstaged diff 수집 |
| `ai_client.py` | API 키 로드, HTTP 요청·응답 파싱, 예외 분류 |
| `prompts.py` | commit/PR별 지시문과 Git 변경 맥락 조립 |
| `validators.py` | 제목 길이, 헤더, 불릿 수의 결정적 검증 |
| `cli.py` | 옵션 파싱, 전체 흐름 조합, 재생성, 터미널 출력 |

이 분리 덕분에 Git 명령이 바뀌면 수집 모듈만, API 사양이 바뀌면 클라이언트만 수정할 수 있다. Git 로직은 임시 저장소로, HTTP 로직은 mock 응답으로, 프롬프트와 검증기는 순수 입출력 테스트로 독립 검증할 수 있어 실패 원인도 쉽게 고립된다.
