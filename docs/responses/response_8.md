# 기준 8 · 책임 분리

> **평가 항목:** 항목 2 · 설계·구조 설명 — 책임 분리  
> **질문:** Git 수집과 AI 호출의 책임 분리, 그리고 유지보수·테스트 전략을 설명할 수 있는가?

---

## 결론

**예.** Git I/O(`git_io`)와 AI HTTP(`ai_client`)를 모듈로 분리해, 수집·호출·프롬프트·렌더가 서로 의존하지 않도록 했다. 테스트는 임시 Git 저장소·가짜 AI 클라이언트로 각 계층을 독립 검증한다.

---

## 책임 분리

| 모듈 | 책임 | 하지 않는 것 |
|------|------|--------------|
| `git_io` | `status` / `diff` 수집, empty·truncate | HTTP, 프롬프트 문구 |
| `ai_client` | env 키, Chat Completions 요청, 예외 래핑 | git subprocess |
| `prompts` | system/user 메시지 조립 | I/O |
| `cli` | argparse, 파이프라인 조립, exit code | 세부 규칙 문자열 |
| `render` | stdout/stderr 문구 | 비즈니스 로직 |

```
cli
 ├─ git_io.collect / truncate     ← 로컬 Git만
 ├─ prompts.build_*               ← 순수 문자열
 ├─ ai_client.complete            ← 네트워크만
 └─ render / stdout               ← 출력만
```

**왜 나누는가**

1. **유지보수:** 프롬프트만 바꿔도 `ai_client`를 건드릴 필요가 없다. 프로바이더 URL이 바뀌면 `ai_client`만 수정한다.
2. **테스트:** `git_io`는 실제 임시 저장소로, `prompts`는 스냅샷 fixture로, `ai_client`는 mock/HTTP 없이 단위 범위를 나눈다.
3. **실패 분리:** Git 실패(exit 3)와 AI/환경 실패(exit 4·5)를 코드로 구분한다.

---

## 테스트 전략

| 대상 | 파일 | 방식 |
|------|------|------|
| CLI 골격 | `test_cli_skeleton.py` | `--help`, 미구현 경로, 옵션 노출 |
| Git 수집 | `test_git_io.py` | 임시 repo에서 status/diff/empty/truncate |
| 프롬프트 | `test_prompts.py` | 포맷·파일 목록·diff 포함 여부 |

AI 실호출은 CI에서 비용·비결정성 때문에 기본 스위트에 넣지 않고, `ai_client`는 예외 메시지·키 로드 경로를 좁게 검증하는 방향이 적합하다.

---

## 한 줄 요약

**수집(Git)과 호출(AI)을 모듈 경계로 끊고**, CLI는 오케스트레이션만 담당해 유지보수·테스트를 쉽게 한다.
