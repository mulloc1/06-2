# 기준 3 · 환경변수와 인증

API 키는 코디세이 API 콘솔에서 발급한 virtual key이며 `CODYSSEY_API_KEY` 환경변수 또는 `.env`에서 읽는다. 누락 또는 공백이면 네트워크 호출 전에 `APIError`가 발생하고 환경변수 이름과 설정 원인을 stderr에 출력한 뒤 종료 코드 1을 반환한다.

```bash
export CODYSSEY_API_KEY="발급받은-virtual-key"
python3 -m ai_git_cli commit
```

키 값과 Authorization 헤더는 로그나 오류 메시지에 출력하지 않는다.
