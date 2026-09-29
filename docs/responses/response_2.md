# 기준 2 · PR 초안 생성

`pr` 명령은 제목과 본문을 파싱·검증한 뒤 `=== AI PR 초안 ===`으로 명시해 stdout에 출력한다. 본문은 GitHub에 붙여 넣을 수 있는 `## Why`, `## What`, `## How to Test` 구조다.

출력 끝에는 사실관계와 테스트 절차를 사람이 검토·수정하라는 안내가 표시된다.

```bash
python3 -m ai_git_cli pr
```
