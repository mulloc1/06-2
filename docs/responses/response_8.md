# 기준 8 · 책임 분리

| 모듈 | 책임 |
| --- | --- |
| `git_changes.py` | Git 저장소·status·diff 수집 |
| `ai_client.py` | 코디세이 HTTP 요청과 오류 분류 |
| `prompts.py` | 목적별 생성 지시와 변경 맥락 조립 |
| `validators.py` | 결정론적 형식 검증 |
| `cli.py` | 옵션, 전체 흐름, 터미널 출력 |

따라서 Git 로직은 임시 저장소로, HTTP 로직은 mock 응답으로 독립 테스트할 수 있다. API 제공자 사양이 바뀌어도 Git 수집 코드는 수정하지 않는다.
