# 기준 5 · PR 본문 구조

`prompts.build_messages("pr", ...)`는 다음 구조를 모델에 요구한다.

```text
TITLE: <최대 80자>
## Why
- ...
## What
- ...
## How to Test
- ...
```

`validators.validate`는 세 헤더와 각 섹션의 최소 한 개 불릿을 코드로 검증한다. 누락 시 최대 한 번 재생성하고, 그래도 실패하면 가짜 내용을 넣지 않고 종료 코드 1로 끝낸다.
