# 기준 6 · API 파라미터 옵션

두 서브커맨드는 `--model`, `--temperature`, `--max-tokens`, `--timeout`을 제공하고 검증된 값을 `ai_client.complete`에 전달한다.

| 옵션 | 기본값 |
| --- | --- |
| model | `gpt-5-mini` |
| temperature | `0.2` |
| max-tokens | commit `400`, pr `700` |
| timeout | `30`초 |

```bash
python3 -m ai_git_cli pr --model gpt-5.4-mini --temperature 0.3 --max-tokens 900
```
