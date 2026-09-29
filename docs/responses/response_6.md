# 평가 문항 6 · API 파라미터 옵션

## 답변

`commit`과 `pr` 두 서브커맨드는 `--model`, `--temperature`, `--max-tokens`, `--timeout`을 제공한다. CLI가 숫자 범위와 자료형을 먼저 검사한 뒤 검증된 값을 `ai_client.complete()`에 전달하므로, 코드를 수정하지 않고 API 요청 설정을 바꿀 수 있다.

| 옵션 | 기본값 |
| --- | --- |
| model | `gpt-5-mini` |
| temperature | `0.2` |
| max-tokens | commit `400`, pr `700` |
| timeout | `30`초 |

```bash
python3 -m ai_git_cli pr --model gpt-5.4-mini --temperature 0.3 --max-tokens 900
```

`temperature`는 `0.0~2.0`, `max-tokens`와 `timeout`은 `0`보다 큰 값만 허용된다. 범위를 벗어나면 API를 호출하지 않고 CLI 사용 오류로 종료한다.
