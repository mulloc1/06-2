# Phase 4 — Safe Mode & Final Render

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 4
> Subject reference: [`docs/subject.md`](../subject.md) §4.5, §4.6

This phase closes the **last two stages** of the pipeline. `safe_mode.mask` redacts obvious secret shapes from the diff **before** it leaves the machine; `render.commit` / `render.pr` print the polished result with separators and section headers so the output is copy-pasteable and visually clean. After this phase the tool is feature-complete for the core mission — Phase 5 only adds documentation and the GitHub push.

---

## 1. Goal

- Implement `safe_mode.mask(text) -> str` with the four core regex shapes locked in `plan.md` §2 (emails, AWS access keys, `*_KEY=`/`*_TOKEN=` env lines, `sk-` prefixed strings).
- Wire `--safe-mode` so the diff is masked **before** `prompts.build_*` ever sees it.
- Implement `render.commit(result)` and `render.pr(result)` with the separator layouts in `plan.md` §4.6.
- Confirm `render.no_changes`, `render.error`, `render.warning` already route to the right stream (stdout for happy paths, stderr for warnings/errors).
- Cover the regex set with `tests/test_safe_mode.py` so non-secret identifiers (`MAX_TOKENS = 400`) stay untouched.

---

## 2. Scope (In / Out)

**In scope**
- `src/ai_gitgen/safe_mode.py`: `MASK_TOKEN` constant (`***`), regex tuple `_PATTERNS`, public `mask(text)`.
- `cli.py`: when `args.safe_mode` is `True`, replace `snapshot.diff` with `safe_mode.mask(snapshot.diff)` **and** mask `snapshot.status` (file names may contain secrets in path).
- `render.py`: replace plain text writes with framed output per §3.5; add `_RULE_*` constants for separator strings.
- `tests/test_safe_mode.py`: per-regex fixture matrix with both positive and negative cases.

**Out of scope**
- Configurable safe mode (`--safe-mode-policy`, YAML rules) — bonus (`bonus_plan.md` Advanced Safe Mode).
- ANSI color / `rich` / `colorama` — explicitly excluded (`plan.md` §2).
- README content — Phase 5.

---

## 3. Tasks

### 3.1 `safe_mode.py`

```python
import re

MASK_TOKEN = "***"

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # 1) emails
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), MASK_TOKEN),

    # 2) AWS access key ids (AKIA + 16 chars)
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), MASK_TOKEN),

    # 3) env-style key/token lines: NAME_KEY=value or NAME_TOKEN=value
    #    Replace only the value, not the variable name (so the diff stays readable).
    (re.compile(r"(?P<name>[A-Z][A-Z0-9_]*(?:_KEY|_TOKEN|_SECRET))\s*=\s*\S+"),
     r"\g<name>=" + MASK_TOKEN),

    # 4) sk- prefixed strings (OpenAI / Anthropic-style)
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}\b"), MASK_TOKEN),
)

def mask(text: str) -> str:
    """Return ``text`` with known secret shapes replaced by ``MASK_TOKEN``.

    Order matters: env-style assignments are masked before bare ``sk-`` strings
    so that ``OPENAI_API_KEY=sk-abc...`` keeps the variable name visible.
    """
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out
```

- Keep regexes tuple-of-(pattern, repl) so reviewers can read the masking policy in one glance.
- Do **not** add a "mask any string of ≥20 chars" catch-all — false positives would eat real code.

### 3.2 `cli.py` wiring

In `_run_subcommand`, right after `collect()` and before `truncate()`:

```python
if args.safe_mode:
    snapshot = dataclasses.replace(
        snapshot,
        diff=safe_mode.mask(snapshot.diff),
        status=safe_mode.mask(snapshot.status),
    )
```

- Masking happens **before** `git_io.truncate` so the truncated slice the prompt embeds is already redacted.
- Masking does not run when `--safe-mode` is unset; the flag is off by default (`plan.md` §5).
- If the user passes `--safe-mode` on a repo with no secrets, the call is a no-op — and that's fine.

### 3.3 `render.commit(result)`

```
================ COMMIT MESSAGE ================
<subject>

<body, if any>
=================================================
```

Implementation notes:

- Width is fixed (49 `=` characters) — no terminal-size detection.
- If `result.body` is `None`, omit the blank line and the body lines; print exactly three lines: top rule, subject, bottom rule.
- If `result.body` is present, normalize trailing whitespace; preserve bullet lines as-is.
- Always write to **stdout**; never to stderr.

### 3.4 `render.pr(result)`

```
================== PR DRAFT ==================
Title: <title>

## Why
- <bullet>
- <bullet>

## What
- <bullet>

## How to Test
- <bullet>
==============================================
```

- 46 `=` characters; same fixed-width style as `commit`.
- Iterate the bullet tuples in order; prefix each with `- ` since polish strips the marker.
- If polish injected a placeholder bullet, the warning has already been emitted to stderr in Phase 3 — `render.pr` just prints it as a normal bullet.

### 3.5 `render` constants & helpers

Add at the top of `render.py`:

```python
_COMMIT_RULE = "================ COMMIT MESSAGE ================"
_COMMIT_END  = "================================================="
_PR_RULE     = "================== PR DRAFT =================="
_PR_END      = "=============================================="
```

- `commit(result)` and `pr(result)` are the only writers using these constants.
- `warning(msg)` and `error(msg)` keep using `sys.stderr`; `no_changes()` keeps using `sys.stdout` (no separator — it's a single line).

### 3.6 `cli.py` final wiring

Replace the placeholder `sys.stdout.write(...)` at the end of each branch with `render.commit(result)` / `render.pr(result)`. The post-polish warning loop stays where it is (warnings on stderr come **before** the framed stdout block).

### 3.7 `tests/test_safe_mode.py`

Matrix of (input, expected_substring_present, expected_substring_absent):

- `test_email_masked`: `"Contact alice@example.com for keys"` → `"alice@example.com"` not in output; `"***"` is.
- `test_email_in_diff_line_masked`: a typical `+ # author: bob.smith@corp.io` line.
- `test_aws_key_masked`: `"AKIAABCDEFGHIJKLMNOP"` → masked.
- `test_aws_key_too_short_not_masked`: `"AKIASHORT"` → unchanged (15 chars).
- `test_env_assignment_keeps_name_masks_value`: `"OPENAI_API_KEY=sk-abc123def456ghi789"` → starts with `"OPENAI_API_KEY=***"`, does not contain `"sk-abc"`.
- `test_env_assignment_with_quotes`: `"AWS_SECRET=\"abc\""` → value masked.
- `test_sk_string_masked`: `"sk-1234567890abc"` → masked.
- `test_short_sk_not_masked`: `"sk-short"` → unchanged (we require ≥10 chars after the prefix).
- `test_max_tokens_constant_unchanged`: `"MAX_TOKENS = 400"` → unchanged (we mask `_KEY=` / `_TOKEN=` / `_SECRET=` but not `_TOKENS=`).
- `test_identifier_with_at_unchanged`: `"@override"` → unchanged.
- `test_idempotent`: `mask(mask(x)) == mask(x)` for a representative input.

All tests live in `tests/test_safe_mode.py` and use `unittest`. No fixtures live in files; inputs are inline strings.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `src/ai_gitgen/safe_mode.py` | implement (`MASK_TOKEN`, `_PATTERNS`, `mask`) |
| `src/ai_gitgen/cli.py` | edit (apply `safe_mode.mask` when `--safe-mode`, call `render.commit` / `render.pr`) |
| `src/ai_gitgen/render.py` | implement (`commit`, `pr`, rule constants) |
| `tests/test_safe_mode.py` | create (regex matrix above) |

---

## 5. Acceptance Criteria

- [ ] Run `python -m ai_gitgen commit` on a real change → terminal shows the framed `================ COMMIT MESSAGE ================` block; subject and (optional) body inside; bottom rule visible.
- [ ] Run `python -m ai_gitgen pr` → terminal shows the framed `================== PR DRAFT ==================` block with `Title:` then `## Why` / `## What` / `## How to Test` and ≥1 bullet each.
- [ ] Run with `--safe-mode` on a repo whose diff contains `OPENAI_API_KEY=sk-aaaaaaaaaaaaaaaaaa`: the printed change summary (and the request body sent upstream if you log it during a dry run) shows `OPENAI_API_KEY=***`; the original key never appears.
- [ ] `MAX_TOKENS = 400` in a Python file's diff is **not** masked.
- [ ] Without `--safe-mode`, the diff sent to the model is exactly what `git_io` produced.
- [ ] `python3 -m unittest discover -s tests -v` is green; `tests/test_safe_mode.py` covers every pattern with at least one positive and one negative case.
- [ ] `rg "print\(|sys.stdout" src/ai_gitgen/polish.py src/ai_gitgen/git_io.py src/ai_gitgen/ai_client.py src/ai_gitgen/safe_mode.py` returns nothing — all stdout writes go through `render.py`.

---

## 6. Commit

```
feat: add safe mode masking and final terminal rendering
```

---

## 7. Risks / Notes

- **Order of patterns matters**: the `*_KEY=…`/`*_TOKEN=…` rule must run before the bare `sk-` rule so `OPENAI_API_KEY=sk-abc…` keeps the variable name visible (`OPENAI_API_KEY=***` rather than `OPENAI_API_KEY=sk-***`).
- **Mask token choice**: keep `***` (three asterisks). A reviewer scanning diff for the redaction marker should hit it immediately; longer tokens like `[REDACTED]` are noisy in compact diffs.
- **False positives are worse than false negatives** here: subject §4.6 only requires "at least one" ops note, and we ship secret masking voluntarily. Eating a legitimate `_KEY` identifier would burn reviewer trust faster than missing a secret would.
- **No regex against the full `Authorization: Bearer …` line** — that header never appears in `git diff`; it only appears in `ai_client._sanitize_headers_for_debug`, which already strips it.
- **Width-fixed separators**: if a future bonus phase wants terminal-width separators, that's a one-place change. For core, fixed width is plenty and predictable in piped output.
- **Tests are pure regex** — no `subprocess`, no env vars, no time. Keep them that way.

---

## 8. Definition of Done

- `safe_mode.mask` is implemented, ordered, and tested against the documented matrix.
- `--safe-mode` masks the diff before any prompt is built; the masked diff is what reaches the model.
- Both subcommands print their framed output blocks; warnings/errors stay on stderr so piping works.
- All five tests files (`test_cli_skeleton`, `test_git_io`, `test_prompts`, `test_polish`, `test_safe_mode`) pass with stdlib only.
- The tool is feature-complete for subject §4.1–§4.6; Phase 5 only adds README and the GitHub push.
