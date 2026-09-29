# 평가 문항 3 · 환경변수와 인증

## 답변

API 키는 코드에 하드코딩하지 않고 `CODYSSEY_API_KEY` 환경변수에서 읽는다. 현재 구현은 환경변수가 없을 때 저장소 루트의 `.env`도 확인하며, 둘 다 없거나 값이 비어 있으면 API 요청 전에 실패한다.

이때 stderr에 `CODYSSEY_API_KEY가 없습니다`라는 원인과 환경변수 또는 `.env`에 설정하라는 해결 방법을 표시하고 종료 코드 `1`을 반환한다. 키 값과 `Authorization` 헤더는 로그나 오류 메시지에 출력하지 않는다.

```bash
export CODYSSEY_API_KEY="발급받은-virtual-key"
python3 -m ai_git_cli commit
```
