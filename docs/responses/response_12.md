# 기준 12 · temperature

> **평가 항목:** 항목 3 · 핵심 개념 이해 — temperature  
> **질문:** `temperature`가 결과의 무작위성·창의성에 미치는 영향과, 언제 높거나 낮은 값을 쓰는지 설명할 수 있는가?

---

## 결론

**예.** `temperature`는 다음 토큰 분포의 **평탄함**을 조절한다. 값이 낮으면 고확률 토큰에 모여 **일관·사실 위주**가 되고, 높으면 저확률 토큰도 섞여 **다양·창의적**이 된다. 이 CLI 기본값은 **0.2**로, 커밋/PR 초안의 재현성을 우선한다.

---

## 개념

Chat Completions에서 temperature는 샘플링 소프트맥스의 스케일에 가깝다.

| 값 | 경향 | 적합한 경우 |
|----|------|-------------|
| **0 ~ 0.2** | 결정에 가깝고 반복 시 비슷한 문구 | 커밋 Subject, 사실 요약, 데모 재현 |
| **0.3 ~ 0.7** | 표현 다양성↑ | PR Why를 여러 톤으로 써 보고 싶을 때 |
| **0.8+** | 창의·일탈↑, 형식 이탈·과장 위험↑ | 브레인스토밍; 이 도구의 기본 용도에는 비권장 |

커밋 메시지는 “무엇을 바꿨는지”가 중요하고 리뷰어가 복사해 쓴다. temperature가 높으면 같은 diff에 다른 Subject가 나와 **리뷰·자동화 비교가 어렵다**.

---

## 이 프로젝트에서의 사용

```python
DEFAULT_TEMPERATURE = 0.2
# CLI: --temperature
ai_client.complete(..., temperature=args.temperature, ...)
```

### 권장 사용 예

```bash
# 재현·CI·문서 스크린샷
python -m ai_gitgen commit --temperature 0

# 기본 (권장)
python -m ai_gitgen commit --temperature 0.2

# 표현만 조금 바꿔 보고 싶을 때
python -m ai_gitgen pr --temperature 0.5
```

형식 준수는 temperature만으로 보장되지 않는다. 높은 temperature를 쓸수록 **프롬프트 형식 + (계획된) polish**의 중요도가 커진다.

---

## 한 줄 요약

낮출수록 **안정·재현**, 높일수록 **다양·위험** — 커밋/PR 초안은 낮은 값이 맞다.
