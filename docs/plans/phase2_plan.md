# Phase 2 — AI Client & Prompt Builders

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 2
> Subject reference: [`docs/subject.md`](../subject.md) §3 LO 1·LO 4, §4.2, §4.3, §4.4

This phase wires the **middle two stages** of the pipeline: the `prompts` module turns a `GitSnapshot` into a system+user message pair, and the `ai_client` module performs the actual HTTP request and surfaces failures with a clear cause. After this phase, both subcommands return real model output to stdout (still unpolished — polish lands in Phase 3).

---

## 1. Goal

- Implement `prompts.build_commit(snapshot, *, truncated)` and `prompts.build_pr(snapshot, *, truncated)` returning a list of OpenAI-shaped message dicts (`[{"role": "system", "content": ...}, {"role": "user", "content": ...}]`).
- Implement `ai_client.complete(messages, *, model, temperature, max_tokens)` that POSTs to `https://api.openai.com/v1/chat/completions` via `urllib.request`, reads `OPENAI_API_KEY` once, and returns `response["choices"][0]["message"]["content"]`.
- Define `AIError` so authentication, network, HTTP, and missing-env-var failures share one exception type but carry a **cause-bearing** message (subject §4.2).
- Wire `cli.py` so `commit` and `pr` now: collect → build prompt → call client → print raw text (unpolished). Phase 3 will slot the polish step between client and print.
- Cover the prompt builders with `unittest` tests; **no network calls in tests** — the HTTP client itself is verified by hand against a real key (`plan.md` §6 Phase 2).

---

## 2. Scope (In / Out)

**In scope**
- `src/ai_gitgen/prompts.py`: shared system prompt constant + `build_commit` + `build_pr` + helper `_format_snapshot(snapshot, truncated)`.
- `src/ai_gitgen/ai_client.py`: `AIError` class, `_load_key()`, `_sanitize_headers_for_debug()`, `complete()`.
- `cli.py`: dispatch `args.subcommand → build_commit / build_pr → ai_client.complete → print to stdout`. Error mapping per `plan.md` §2: missing key → `EXIT_ENV` (5); AIError → `EXIT_AI` (4).
- `tests/test_prompts.py`: format block presence, file list, truncation notice, separation of commit vs pr templates.

**Out of scope**
- Output validation / polish / retry — Phase 3.
- Safe mode masking — Phase 4 (the prompt builders receive the raw diff for now; Phase 4 inserts `safe_mode.mask` **before** the builder is called).
- Provider switching / `--provider` flag — bonus (`bonus_plan.md`).
- Streaming / SSE — out of scope per `plan.md` §2 (non-streaming completions).

---

## 3. Tasks

### 3.1 `prompts.py`

#### 3.1.1 Shared system prompt (constant)

```python
SYSTEM_PROMPT = (
    "You are an assistant that writes Git commit messages and pull-request "
    "drafts. Always answer in the exact format requested. Never invent files, "
    "modules, or behavior that is not visible in the diff."
)
```

Reviewers should diff this constant in one file when tuning tone (`plan.md` §3 split rationale).

#### 3.1.2 `_format_snapshot(snapshot, truncated) -> str`

- Header: `Changed files (up to 10):` followed by the first 10 entries from `snapshot.files`, one per line, prefixed with `- `.
- If `snapshot.files` is longer than 10, append `- ... (+N more)`.
- A blank line, then the diff block:

```
=== diff start ===
<snapshot.diff (already truncated by caller)>
=== diff end ===
```

- If `truncated` is `True`, append a one-line notice: `Note: the diff above was truncated; do not reference files or hunks that are not visible.`

#### 3.1.3 `build_commit(snapshot, *, truncated) -> list[dict]`

User content layout:

```
{change_context}

Write a Git commit message that summarizes these changes.

Output format:
Subject: <one line, imperative mood, <=50 chars recommended, max 72 chars>

Body (optional, up to 3 bullets, each referencing a file or module):
- ...
- ...
- ...
```

Return `[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": <above>}]`.

#### 3.1.4 `build_pr(snapshot, *, truncated) -> list[dict]`

User content layout (verbatim — `polish.enforce_pr` parses these exact headers in Phase 3):

```
{change_context}

Write a pull-request draft for these changes.

Output format:
Title: <one line, <=80 chars>

## Why
- ...

## What
- ...

## How to Test
- ...
```

Return the same `[system, user]` list shape.

### 3.2 `ai_client.py`

#### 3.2.1 `AIError(Exception)`

```python
class AIError(Exception):
    """Raised for any failure communicating with the upstream AI provider.

    The message must always include the operator-actionable cause
    (HTTP status, urllib error class, or missing-env-var label).
    """
```

#### 3.2.2 `_load_key() -> str`

- Read `os.environ.get("OPENAI_API_KEY")`. If missing or empty → `raise AIError("OPENAI_API_KEY environment variable is not set.")`.
- Never log or echo the key (`plan.md` §5).

#### 3.2.3 `_sanitize_headers_for_debug(headers) -> dict`

- Return a copy of the headers dict with `Authorization` replaced by `"Bearer ***"`. Used **only** if/when we wrap an HTTPError for debugging; it is never logged unconditionally.

#### 3.2.4 `complete(messages, *, model, temperature, max_tokens) -> str`

- Build body: `{"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}`. JSON-encode with `json.dumps`.
- Build request:

```python
req = urllib.request.Request(
    url="https://api.openai.com/v1/chat/completions",
    data=body.encode("utf-8"),
    method="POST",
    headers={
        "Authorization": f"Bearer {_load_key()}",
        "Content-Type": "application/json",
    },
)
```

- `urlopen(req, timeout=30)` inside a `try/except`:
  - `urllib.error.HTTPError` → read body, attempt to extract `error.message` from JSON; raise `AIError(f"HTTP {e.code}: {message_or_reason}")`. For `401`, prefer the message `"HTTP 401 Unauthorized — check OPENAI_API_KEY."`; for `429`, prefer `"HTTP 429 — rate limited; retry after a short wait."`.
  - `urllib.error.URLError` (DNS / connection refused / timeout) → `raise AIError(f"Network error ({type(e.reason).__name__}): {e.reason}")`.
  - `TimeoutError` / `socket.timeout` → `raise AIError("Network error: request timed out after 30s.")`.
  - `json.JSONDecodeError` on the response → `raise AIError("Malformed response from upstream (not JSON).")`.
  - `KeyError` on `choices[0].message.content` → `raise AIError("Upstream response missing choices[0].message.content.")`.
- On success return the content string (no trimming yet — Phase 3 polishes).

### 3.3 `cli.py` integration

- Add `import sys`; `from ai_gitgen import ai_client, git_io, prompts, render`.
- Constant for diff cap: `DIFF_CHAR_LIMIT = 8000` (per `plan.md` §2).
- Shared pipeline helper to avoid drift between subcommands:

```python
def _run_subcommand(args, *, build_fn, default_max_tokens) -> int:
    try:
        snapshot = git_io.collect()
    except git_io.GitError as e:
        render.error(str(e)); return EXIT_GIT
    if snapshot.empty:
        render.no_changes(); return EXIT_OK
    truncated_diff, was_truncated = git_io.truncate(snapshot.diff, DIFF_CHAR_LIMIT)
    snapshot_for_prompt = dataclasses.replace(snapshot, diff=truncated_diff)
    messages = build_fn(snapshot_for_prompt, truncated=was_truncated)
    try:
        text = ai_client.complete(
            messages,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens or default_max_tokens,
        )
    except ai_client.AIError as e:
        render.error(str(e))
        return EXIT_ENV if "OPENAI_API_KEY" in str(e) else EXIT_AI
    sys.stdout.write(text.rstrip() + "\n")
    return EXIT_OK
```

- `_handle_commit` calls it with `build_fn=prompts.build_commit, default_max_tokens=DEFAULT_MAX_TOKENS_COMMIT`.
- `_handle_pr` calls it with `build_fn=prompts.build_pr, default_max_tokens=DEFAULT_MAX_TOKENS_PR`.
- `--max-tokens` default is `None` in argparse so we can detect "unset" and apply the subcommand-specific default; the help text still shows the effective default.

### 3.4 `tests/test_prompts.py`

Build small handcrafted `GitSnapshot` instances (no real git in this file — keeps tests pure):

- `test_commit_prompt_contains_format_block`: built messages contain `"Subject:"` and the body bullet template.
- `test_pr_prompt_contains_all_section_headers`: user content contains `## Why`, `## What`, `## How to Test`.
- `test_file_list_truncated_to_ten`: snapshot with 15 files → user content lists 10 + a `(+5 more)` line.
- `test_truncation_notice_present_when_flag_set`: `build_commit(snap, truncated=True)` injects the disclosed-truncation sentence; `truncated=False` does not.
- `test_system_prompt_is_shared`: `build_commit` and `build_pr` produce the **same** system message string (constant identity check).
- `test_no_secret_in_prompts`: the prompt module does not embed the env-var name literal `OPENAI_API_KEY` (a guard against accidental leakage into model context).

No HTTP, no mocks.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `src/ai_gitgen/prompts.py` | implement (`SYSTEM_PROMPT`, `_format_snapshot`, `build_commit`, `build_pr`) |
| `src/ai_gitgen/ai_client.py` | implement (`AIError`, `_load_key`, `_sanitize_headers_for_debug`, `complete`) |
| `src/ai_gitgen/cli.py` | edit (`_run_subcommand` helper, both handlers, `DIFF_CHAR_LIMIT` constant) |
| `tests/test_prompts.py` | create (six prompt-shape tests) |

---

## 5. Acceptance Criteria

- [ ] With a valid `OPENAI_API_KEY` exported and a tracked change in the repo, `python -m ai_gitgen commit` prints real model output and exits `0`.
- [ ] Same with `pr`.
- [ ] With `OPENAI_API_KEY` **unset**: `python -m ai_gitgen commit` writes `OPENAI_API_KEY environment variable is not set.` to stderr and exits `5`.
- [ ] With an obviously bad key (`export OPENAI_API_KEY=sk-invalid`): error message mentions `HTTP 401` (or upstream's verbatim message), exit code `4`.
- [ ] With network blocked (OS firewall / airplane mode): error message mentions `Network error` with the urllib reason class, exit code `4`.
- [ ] `python3 -m unittest discover -s tests -v` is green; no network calls; `tests/test_prompts.py` does not import `urllib` or `ai_client`.
- [ ] `rg "OPENAI_API_KEY" src/ai_gitgen/prompts.py` returns no matches.
- [ ] `rg "import requests|from requests" src/` returns no matches (stdlib-only).
- [ ] `rg "print\(" src/ai_gitgen/ai_client.py` returns no matches (no accidental debug prints with headers).

---

## 6. Commit

```
feat: add openai chat completions client and prompt builders
```

---

## 7. Risks / Notes

- **Key leakage**: the `Authorization` header value must never be passed to `print`, `repr`, or an exception's `args`. Wrap any debug dump through `_sanitize_headers_for_debug`. Phase 2 review should grep for `Bearer` outside `ai_client.py`.
- **`HTTPError` body decoding**: `urllib.error.HTTPError` exposes the body via `.read()` — call it once, decode as UTF-8 with `errors="replace"`, attempt `json.loads`. If that fails, fall back to the raw text in the error message; never let a `json.JSONDecodeError` surface as `AIError`'s cause when the real problem is `429`.
- **Timeouts**: 30s is enough for `gpt-4o-mini` on small prompts; raise (don't lower) only with evidence. Document the constant near `complete()`.
- **Determinism in tests**: keep the prompt module a pure string function. If a test needs randomness or time, it belongs in `test_polish.py` (Phase 3) or stays out (.cursorrules §6 Testing Determinism).
- **Why no mocked HTTP test for `complete`**: `plan.md` §7 explicitly says network flows are verified manually; mocking HTTP here doubles the maintenance surface without buying confidence in real failure modes.

---

## 8. Definition of Done

- Both subcommands now print real model output end-to-end on a real repo with a real key.
- All three failure modes (missing key / bad key / no network) print cause-bearing messages and use the documented exit codes.
- `unittest discover` is green; `tests/test_prompts.py` covers the six prompt-shape invariants.
- Phase 3 can drop `polish.enforce_*` between `ai_client.complete` and `sys.stdout.write` with no other changes to `_run_subcommand`.
