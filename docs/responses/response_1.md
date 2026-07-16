# 기준 1 · 커밋 메시지 생성

> **평가 항목:** 항목 1 · 기능·동작 검증 — 커밋 메시지 생성  
> **질문:** 커밋 포맷이 프롬프트에 반영되고, AI 결과가 표준출력으로 출력되며, 검토 후 적용하라는 안내가 있는가?

---

## 결론

**예(포맷·표준출력).** 커밋 Subject/Body 규칙을 `prompts.build_commit`에 명시하고, AI 응답을 `cli.py`에서 **표준출력**으로 내보낸다. 검토 안내 문구는 아직 출력에 붙어 있지 않으며, 아래처럼 한 줄 안내를 추가하는 것이 권장된다.

---

## 구현 방식

### 1. 프롬프트에 커밋 포맷 명시 — `prompts.py`

`build_commit`이 모델에 요구하는 출력 형식은 다음과 같다.

```text
Subject: <one line, imperative mood, <=50 chars recommended, max 72 chars>

Body (optional, up to 3 bullets, each referencing a file or module):
- ...
```

- Subject는 **한 줄·명령형**이며, 권장 50자 / 최대 72자다.
- Body는 **선택**이며, 파일·모듈을 가리키는 불릿 최대 3개다.
- 시스템 프롬프트는 diff에 없는 파일을 지어내지 말라고 고정한다.

### 2. 표준출력으로 결과 출력 — `cli.py`

파이프라인은 `git 수집 → 프롬프트 구성 → AI 호출 → stdout`이다.

```python
text = ai_client.complete(...)
sys.stdout.write(text.rstrip() + "\n")
```

사용자는 터미널에 찍힌 메시지를 복사해 `git commit -m`에 넣을 수 있다. 도구가 커밋을 **자동 실행하지 않는다**.

### 3. 검토 안내 (보완 포인트)

현재는 AI 텍스트만 출력한다. 자동 적용으로 오해되지 않도록, 출력 앞에 예를 들어 다음을 붙이면 기준을 더 명확히 충족한다.

```text
[안내] AI 제안입니다. 검토 후 적용하세요.
```

---

## 검증 방법

```bash
# 변경이 있는 저장소에서
PYTHONPATH=src python3 -m ai_gitgen commit
# → Subject: ... / Body 불릿이 stdout에 출력되는지 확인
```
