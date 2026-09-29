# 평가 문항 14 · 프롬프트 맥락

## 답변

프롬프트에는 다음 자료가 함께 들어간다.

- `git status --short --untracked-files=all` 원문
- 정규화한 변경 파일 목록
- staged diff와 unstaged diff
- untracked 파일명(status에는 포함, 내용은 전송하지 않음)

파일 목록은 변경 범위를 알려주고, staged·unstaged diff는 실제로 추가·수정·삭제된 내용을 제공한다. 다만 Git diff에 나오지 않는 untracked 파일은 파일명만 전송하고 내용은 보내지 않는다. 시스템 프롬프트는 제공된 status와 diff에 없는 파일, 동작, 테스트 결과를 지어내지 말도록 제한한다.
