# 선택 과제 구현 계획

이 문서는 `subject.md` 5장의 선택 과제를 위한 후속 계획이다. 현재 필수 CLI의 테스트와 실제 코디세이 API 검증, GitHub push가 모두 끝난 뒤 별도 브랜치에서 진행한다.

## 1. 실제 PR 생성

1. 이전 미션 저장소에서 의미 있는 작은 변경을 선택한다.
2. 작업 브랜치를 만들고 변경·테스트를 완료한다.
3. `python3 -m ai_git_cli commit`과 `pr`로 각각 초안을 생성한다.
4. AI 초안을 실제 diff와 비교해 사람이 수정한다.
5. 최종 커밋과 PR을 생성하고 링크를 `docs/real_pr.md`에 기록한다.
6. AI 초안에서 최종 PR까지 바꾼 내용과 이유를 5~10줄로 정리한다.

AI가 만든 제목·본문은 그대로 제출하지 않고 변경 동기, 테스트 결과, 범위를 수동 확인한다.

## 2. 팀 규칙과 템플릿

프로젝트 루트의 `.ai-git-cli.toml`을 선택적으로 읽도록 확장한다.

```toml
convention = "conventional"

[commit]
types = ["feat", "fix", "docs", "test", "refactor", "chore"]
include_scope = true

[pull_request]
extra_sections = ["Risks"]
```

구현 항목:

- `config.py`: 표준 라이브러리 `tomllib`로 설정 파싱·검증
- `--config`, `--convention`, `--no-config` 옵션
- `prompts.py`: 규칙별 템플릿 선택
- `validators.py`: 핵심 제목 길이와 PR 필수 섹션은 규칙과 무관하게 유지
- README: 규칙 문서와 설정 전/후 출력 비교 한 쌍

설정 파일이 없을 때는 현재 필수 구현과 동일하게 동작해야 한다.

## 3. 고급 Safe Mode

diff가 코디세이 API로 전송되기 전에 적용되는 정책 계층을 추가한다.

최소 정책:

- `.env*`, `*.pem`, `*.key`, `*.p12` 내용 제외
- 이메일, 일반적인 API key/token 할당문, AWS access key, bearer token 마스킹
- 파일별 최대 줄 수 설정
- 사용자 정규식 추가
- 적용된 정책과 제외 파일 수를 stderr에 표시

CLI 예시:

```bash
python3 -m ai_git_cli pr \
  --safe-mode \
  --safe-mode-exclude 'config/**' \
  --safe-mode-max-lines 100
```

정규식은 잘못된 패턴을 명확히 거부하고 개수·길이를 제한한다. 마스킹된 값이나 원래 비밀 값은 로그와 예외에 포함하지 않는다.

## 4. 테스트

- 설정 없음, 정상 설정, 잘못된 TOML, 알 수 없는 convention
- 기본 규칙과 사용자 규칙의 우선순위
- safe mode의 각 마스킹 패턴과 오탐 방지
- 제외 glob과 파일별 줄 제한
- safe mode가 켜진 요청 본문에 원래 비밀 값이 없는지 검사
- 필수 구현의 기존 34개 테스트가 그대로 통과하는지 회귀 확인

## 5. 완료 조건

- 실제 PR 링크와 5~10줄 수정 기록 존재
- 팀 규칙 설명과 생성 결과 전/후 비교 존재
- 설정 가능한 safe mode와 보안 테스트 존재
- README만으로 세 선택 기능을 재현 가능
- 코디세이 virtual key가 코드, 문서, Git 이력에 포함되지 않음
