# AI Git CLI

Git 변경사항을 코디세이 Public API로 보내 커밋 메시지와 Pull Request 초안을 생성하는 Python CLI입니다. 도구는 초안만 터미널에 출력하며 커밋, push, PR 등록을 자동으로 수행하지 않습니다.

## 요구사항

- Python 3.10 이상
- Git
- 코디세이 Public API의 virtual key
- Git 저장소 루트에서 실행

## 설치

저장소를 받은 뒤 개발 모드로 설치합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

설치하지 않고 실행하려면 프로젝트 루트에서 `PYTHONPATH=src`를 지정할 수 있습니다.

```bash
PYTHONPATH=src python3 -m ai_git_cli --help
```

## API 키 설정

코디세이 API 콘솔에서 발급한 virtual key를 `CODYSSEY_API_KEY` 환경변수로 설정합니다.

### 방법 1: `.env` 파일 사용

프로젝트 루트에 기본 `.env` 파일이 준비되어 있습니다. 다음 줄의 `=` 뒤에 발급받은 키를 입력합니다.

```dotenv
CODYSSEY_API_KEY=발급받은-virtual-key
```

새로 구성할 때는 예제 파일을 복사해도 됩니다.

```bash
cp .env.example .env
```

CLI는 실행 위치의 `.env`를 자동으로 읽습니다. `.env`는 `.gitignore`에 포함되어 커밋되지 않고, `.env.example`에는 실제 키를 넣지 않습니다.

### 방법 2: 셸 환경변수 사용

현재 터미널 세션에서 직접 설정할 수도 있습니다.

```bash
export CODYSSEY_API_KEY="발급받은-virtual-key"
```

셸 환경변수와 `.env`에 값이 모두 있으면 셸 환경변수를 우선합니다.

이 프로젝트는 다음 코디세이 OpenAI 호환 사양을 사용합니다.

| 항목 | 값 |
| --- | --- |
| Base URL | `https://copa.codyssey.kr/v1` |
| Endpoint | `POST /chat/completions` |
| 인증 | `Authorization: Bearer <virtual-key>` |
| 기본 모델 | `gpt-5-mini` |

키는 코드, 설정 파일, 로그에 저장하지 않습니다. 실제 키를 `.env`나 README에 기록하지 마세요.

## 사용법

작업 트리에 변경사항을 만든 뒤 저장소 루트에서 실행합니다.

```bash
python3 -m ai_git_cli commit
python3 -m ai_git_cli pr
```

설치한 console script도 같은 기능을 제공합니다.

```bash
ai-git commit
ai-git pr
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-5-mini` | 코디세이 모델 ID |
| `--temperature` | `0.2` | 샘플링 무작위성, 0.0~2.0 |
| `--max-tokens` | commit `400`, pr `700` | 생성 응답의 토큰 상한 |
| `--timeout` | `30` | API 요청 제한 시간(초) |
| `--safe-mode` | 꺼짐 | diff의 민감정보를 마스킹한 후 전송 |

예시:

```bash
python3 -m ai_git_cli commit --temperature 0 --max-tokens 300
python3 -m ai_git_cli pr --model gpt-5.4-mini --temperature 0.3 --timeout 45
python3 -m ai_git_cli pr --safe-mode
```

## 출력 예시

실제 문구는 diff와 모델 응답에 따라 달라지지만 출력 구조는 다음과 같습니다.

```text
=== 변경 요약 ===
변경 파일 2개
- src/ai_git_cli/cli.py
- tests/test_cli.py

=== AI 커밋 메시지 초안 ===
test: CLI 옵션 전달 검증 추가
=== 초안 끝 ===
사용 전 실제 변경사항과 표현을 직접 검토·수정하세요.
```

```text
=== AI PR 초안 ===
TITLE: 코디세이 기반 Git 초안 생성 CLI 구현

## Why
- Git 변경 설명을 반복 작성하는 작업을 줄입니다.

## What
- 변경 파일과 diff를 기반으로 커밋 및 PR 초안을 생성합니다.

## How to Test
- python3 -m unittest discover -s tests -v를 실행합니다.

=== 초안 끝 ===
사용 전 실제 변경사항과 표현을 직접 검토·수정하세요.
```

변경사항이 없으면 API를 호출하지 않고 다음과 같이 정상 종료합니다.

```text
변경사항이 없습니다.
```

## 출력 검증과 재생성

- 커밋 메시지는 `SUBJECT` 같은 출력용 라벨이나 본문 없이 한 줄로 작성하고, 권장 50자 이하·최대 72자로 검사합니다.
- PR 제목은 최대 80자로 검사합니다.
- PR 본문은 `Why`, `What`, `How to Test`와 각 섹션의 불릿을 요구합니다.
- 첫 결과가 규칙을 위반하면 위반 이유를 포함해 한 번만 재생성합니다.
- 두 번째 결과도 잘못되면 가짜 내용을 채우지 않고 오류로 종료합니다.

## 오류와 종료 코드

| 종료 코드 | 의미 |
| --- | --- |
| `0` | 성공 또는 변경사항 없음 |
| `1` | Git, API 또는 출력 형식 오류 |
| `2` | 잘못된 CLI 사용법/옵션 |

API 오류는 원인을 구분해 표시합니다.

- `401`: 키 또는 권한 확인
- `429`: 사용량·할당량 확인 후 재시도
- 네트워크: DNS, 프록시, 인터넷 연결 확인
- 타임아웃: `--timeout` 값과 네트워크 상태 확인

## 파라미터 이해

`temperature`가 낮을수록 결과가 일관되고 형식을 지킬 가능성이 높습니다. 커밋과 PR은 창의성보다 사실성과 재현성이 중요하므로 기본값을 `0.2`로 둡니다. 값을 높이면 표현은 다양해지지만 과장이나 형식 이탈 가능성도 커집니다.

`max_tokens`는 입력 diff가 아니라 생성할 응답 길이의 상한입니다. 너무 작으면 본문이나 `How to Test`가 중간에 잘릴 수 있고, 너무 크면 비용과 지연이 늘 수 있습니다.

## 운영 및 보안 주의사항

- status와 diff는 외부의 코디세이 API로 전송됩니다. 비밀키, 개인정보, 내부 URL이 diff에 없는지 먼저 확인하세요.
- `--safe-mode`를 사용하면 staged/unstaged diff의 이메일, key/token/secret/password 할당값, Bearer 토큰, AWS access key를 마스킹한 후 전송합니다.
- 안전 모드는 diff에만 적용되며 패턴 기반 탐지가 모든 민감정보를 보장하지는 않습니다. 파일명·status와 마스킹 결과를 전송 전에 직접 검토하세요.
- untracked 파일은 이름만 변경 목록에 포함하며 내용은 API로 보내지 않습니다.
- diff 크기에 따라 입력 토큰 비용과 요청 지연이 늘어날 수 있습니다.
- 형식 실패 재호출은 최대 한 번으로 제한하지만, 그만큼 추가 토큰이 차감될 수 있습니다.
- HTTP 429를 자동 반복 호출하지 않습니다. 콘솔의 잔여 토큰과 사용량을 확인한 뒤 직접 재시도하세요.
- AI는 변경 동기, 테스트 성공 여부, 영향 범위를 잘못 추론할 수 있습니다. 출력은 항상 실제 diff와 대조하고 사람이 수정한 뒤 사용하세요.

## 테스트

자동 테스트는 실제 코디세이 API를 호출하거나 토큰을 사용하지 않습니다.

```bash
python3 -m unittest discover -s tests -v
```

테스트 범위에는 Git 상태 조합, untracked 파일명, API 요청 형식, 키 누락, HTTP 401/429, 네트워크·타임아웃, 제목 경계값, PR 섹션, 재생성, stdout/stderr가 포함됩니다.

## 구조

```text
src/ai_git_cli/
├── cli.py          # 인자와 전체 흐름
├── git_changes.py  # Git status/diff 수집
├── security.py     # safe mode 민감정보 마스킹
├── ai_client.py    # 코디세이 REST API 호출과 오류 분류
├── prompts.py      # 커밋/PR 프롬프트
└── validators.py   # 출력 형식 검증
```

Git 수집과 HTTP 호출을 분리해 네트워크 없이 Git 로직을 테스트할 수 있고, 프롬프트와 결정론적 검증을 분리해 생성 문구를 조정해도 형식 보장이 흔들리지 않도록 했습니다.
