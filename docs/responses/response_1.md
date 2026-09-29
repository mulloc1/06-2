# 평가 문항 1 · 커밋 메시지 생성

## 답변

`commit` 명령은 Git 변경 내용을 바탕으로 커밋 메시지 초안을 생성한다. `prompts.build_messages()`가 `SUBJECT` 한 줄과 `BODY` 1~2개 불릿 형식을 모델에 지시하고, `validators.validate()`가 제목이 72자를 초과하는지와 본문 불릿 수를 다시 검증한다.

유효한 결과는 `=== AI 커밋 메시지 초안 ===`이라는 헤더 아래 표준출력에 그대로 표시된다. 도구는 실제 `git commit`을 수행하지 않고, 출력 끝에 실제 변경사항과 표현을 사용자가 직접 검토·수정하라는 안내를 추가한다.

```bash
python3 -m ai_git_cli commit
```
