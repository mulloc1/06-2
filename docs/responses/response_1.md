# 기준 1 · 커밋 메시지 생성

`prompts.build_messages`는 `SUBJECT` 한 줄과 `BODY` 1~2개 불릿을 요구한다. `validators.validate`가 제목 최대 72자와 불릿 수를 재검사하며, 실패하면 위반 이유를 넣어 한 번 재생성한다.

성공 결과는 CLI가 `=== AI 커밋 메시지 초안 ===` 헤더와 함께 원문 그대로 stdout에 출력한다. 마지막에는 수동 검토 안내를 표시하며 실제 커밋은 수행하지 않는다.

```bash
python3 -m ai_git_cli commit
```
