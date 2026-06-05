# AI Git CLI Implementation Plan (plan.md)

This document is a phased implementation plan that satisfies both the requirements in `docs/subject.md` and the coding/structure rules in the repository `.cursorrules`. Following the **Minimal-First / YAGNI** principle (.cursorrules §4) and **Lightweight Plans** (.cursorrules §2), we start with the **minimum structure that meets requirements**; bonus tasks (subject §5) are separated into a later phase after the core assignment is done.

---

## 1. Goal Summary

- Build **one Python CLI** that, when run from a Git-initialized project root, collects `git status` + `git diff`, calls an AI API, and prints a **change summary, a commit message, and a PR draft** in the terminal (subject §1, §2.1, §4.1, §4.2).
- Read the API key from an **environment variable** — never hardcoded — and surface authentication / network failures with a **cause-bearing** message (subject §4.2).
- Expose **CLI options** for `--model`, `--temperature`, `--max-tokens` (with safe defaults) so the same code can be re-tuned for output quality without edits (subject §4.2).
- Provide two top-level subcommands — **`commit`** (one-line subject + optional body) and **`pr`** (title + Why / What / How to Test body) — both copy-pasteable straight from terminal output (subject §4.3, §4.4).
- Enforce output length and template rules through **post-processing** with a single regeneration retry, so the printed text always satisfies `≤72` char commit subjects, `≤80` char PR titles, and the three required PR body sections (subject §4.5).
- Wire **one ops note** into the core scope: a `--safe-mode` flag that masks obvious secrets in the diff before it leaves the machine; cost / rate-limit guidance lives in `README.md` (subject §4.6).
- Push the project to GitHub with a `README.md` that lets a reviewer install, set the env var, and reproduce both commands with sample output **from the docs alone** (subject §2.2, §2.3, §4.6).

---

## 2. Locked Decisions

Decisions for items left open in the subject ("e.g.", "your choice", etc.) and other choices that are costly to reverse later. Specific function/argument names and per-section copy are decided during implementation (.cursorrules §2).

| Item | Decision | Rationale (subject / .cursorrules) |
| ---- | -------- | ---------------------------------- |
| Language / runtime | **Python 3.10+** | Subject §1 specifies a Python CLI; 3.10 unlocks PEP 604 unions and `match` for the parser |
| Distribution shape | A package `ai_gitgen` under `src/`, run as `python -m ai_gitgen` (entry-point script `aigit` optional via `pyproject.toml`) | One canonical entry; mirrors `src/` ↔ `tests/` rule (.cursorrules §6) |
| CLI parser | **`argparse`** with subparsers (`commit`, `pr`) | Stdlib only — no `click` / `typer` (.cursorrules §4 YAGNI) |
| Option style | `--model`, `--temperature`, `--max-tokens` (GNU double-dash) | Subject §4.2 lists single-dash examples; argparse double-dash is standard and unambiguous |
| AI provider (default) | **OpenAI Chat Completions** (`POST https://api.openai.com/v1/chat/completions`) via raw HTTP | Demonstrates the REST flow explicitly (subject §3 LO 1); zero SDK dependency; provider swap is one adapter file |
| HTTP transport | **`urllib.request`** + `json` (stdlib) | No `requests` dependency; keeps install footprint to "Python only" |
| Env var name | **`OPENAI_API_KEY`** (provider-prefixed) | Matches the upstream convention; less surprising than a custom name |
| Default model | **`gpt-4o-mini`** | Cheap + capable; reviewer can swap via `--model` without code changes |
| Default `temperature` | **`0.2`** | Commit / PR drafts want determinism over creativity (subject §3 LO 2) |
| Default `max_tokens` | **`400`** for `commit`, **`700`** for `pr` | Empirically enough for a one-line subject + short body / Why·What·How sections; over-budget output is the leading source of validation failures |
| Diff scope sent to API | **Staged + unstaged tracked changes** (`git diff HEAD` for unstaged, `git diff --cached` for staged, concatenated with headers) | Subject §4.1 says "from `git diff`"; covers both pre- and post-`git add` workflows |
| Diff truncation policy | Hard cap at **8 000 characters** sent to the model; if exceeded, send a per-file head + a notice in the prompt | Protects against blowing past context windows on large refactors; predictable cost |
| "No changes" handling | If both `git status --porcelain` and the combined diff are empty → print `No changes detected.` to **stdout** and exit code **0** | Subject §4.1 ("No changes" message + exit); 0 because no error occurred |
| Error exit codes | `2` for usage errors (argparse default), `3` for git failures, `4` for AI API failures, `5` for env-var missing | Distinguish operator vs. environment vs. upstream failure |
| Output streaming | **Non-streaming** completions (single `response.choices[0].message.content`) | Simpler error handling; the polish pass needs the full text anyway |
| Validation strategy | **Post-process first; one regeneration retry only if post-process cannot fix** (e.g. PR body missing a whole section) | Subject §4.5 allows either; one retry caps cost while still recovering from format misses |
| Safe mode regexes (core) | Email addresses, `AKIA[0-9A-Z]{16}`-style AWS keys, generic `*_KEY=`/`*_TOKEN=` env lines, `sk-` prefixed strings | Subject §4.6 asks for at least one of secrets/cost/rate limits — we ship secrets masking in core |
| Color / TTY | Plain ASCII output, no `rich` / `colorama`; section separators use `=` / `-` rules | Reviewer copy-paste cleanliness; no extra dep |
| Code style | 4-space indent; `snake_case` per .cursorrules §3; type hints on every public signature | Consistency with `02-1.console_program` and `05-2.fastAPI_web` |
| Testing | **`unittest`** runnable via `python3 -m unittest discover -s tests -v`; no pytest-only imports | .cursorrules §6 Stdlib Test Runner |
| Dependency policy (core) | **Stdlib only** | No `pip install` step required; reviewer can run with a bare interpreter |

---

## 3. Directory / File Layout

Follows .cursorrules §6 "Mirroring" (`src/` ↔ `tests/`). Module split is the **minimum** needed so each file owns one responsibility (.cursorrules §5 SRP) and so the **git → prompt → API → polish → render** pipeline is readable top-to-bottom.

```
06-2/
├── README.md                       # intro · install · env vars · commands · sample output · ops notes
├── docs/
│   ├── subject.md
│   ├── plan.md                     # (this document)
│   └── bonus_plan.md
├── pyproject.toml                  # package metadata + console_scripts entry (optional script: aigit)
├── src/
│   └── ai_gitgen/
│       ├── __init__.py             # version string only
│       ├── __main__.py             # `python -m ai_gitgen` → cli.main()
│       ├── cli.py                  # argparse subparsers, top-level dispatch, exit codes
│       ├── git_io.py               # status / diff capture · "no changes" detection · truncation
│       ├── ai_client.py            # HTTP call to provider · env-var read · error wrapping
│       ├── prompts.py              # system + user prompt builders for commit / pr
│       ├── polish.py               # length / template enforcement + retry decision
│       ├── safe_mode.py            # secrets-masking regex set
│       └── render.py               # terminal output (separators, section headers)
└── tests/
    ├── helpers.py                  # tmp git repo factory, fake AI client, sys.path bootstrap
    ├── test_git_io.py              # status / diff / no-changes / truncation
    ├── test_polish.py              # subject length, PR title length, missing-section detection
    ├── test_prompts.py             # prompt builders include change context + format rules
    └── test_safe_mode.py           # regexes mask known shapes without eating real code
```

**Split rationale (.cursorrules §4·§5 SRP)**

- `git_io.py` / `ai_client.py` / `polish.py` / `render.py` are the four phases of the pipeline; each owns exactly one I/O surface or transformation. Folding any two together would couple `subprocess` with HTTP, or HTTP with terminal layout — both already different concerns.
- `prompts.py` is its own module because prompt copy is the **primary tuning knob** of this assignment (subject §3 LO 4); keeping it isolated makes prompt edits a one-file diff and the bonus "template swap" plug-in clean.
- `safe_mode.py` lives outside `git_io.py` so the masking rule set can grow in `bonus_plan.md` (Advanced Safe Mode) without touching git capture.
- `cli.py` is the only module aware of `sys.argv`, exit codes, and stdout writes via `render`; everything below is a pure function over strings → strings (subject §3 LO 1, .cursorrules §5 "separate pure logic from I/O").

---

## 4. Architecture Overview

### 4.1 Command Surface (subject §4.2, §4.3, §4.4)

```
python -m ai_gitgen commit [--model M] [--temperature T] [--max-tokens N] [--safe-mode]
python -m ai_gitgen pr     [--model M] [--temperature T] [--max-tokens N] [--safe-mode]
```

- Both subcommands share the same option set; `cli.py` builds them from one helper to avoid drift.
- `--help` / `-h` on either subcommand explains the flag plus its default; defaults come from constants in `cli.py` (no magic literals, .cursorrules §3).

### 4.2 Pipeline (subject §3 LO 3, §4)

```
argparse parse
    │
    ▼
git_io.collect()  ───►  if no changes → render.no_changes() ; exit 0
    │
    ▼
safe_mode.mask(diff)             (only if --safe-mode)
    │
    ▼
prompts.build_commit / build_pr  (system + user messages, includes status summary + diff slice)
    │
    ▼
ai_client.complete(messages, model, temperature, max_tokens)   ───►  AIError → render.error() ; exit 4
    │
    ▼
polish.enforce_commit / enforce_pr
    │   ├─ pass → return text
    │   └─ unfixable → ai_client.complete() once more with stricter constraints
    │
    ▼
render.commit() / render.pr()  → stdout with separators & headers
```

### 4.3 Module Contracts (subject §3 LO 1, .cursorrules §5)

| Module | Public function | Returns |
| ------ | --------------- | ------- |
| `git_io` | `collect() -> GitSnapshot` | `GitSnapshot(status: str, diff: str, files: list[str], empty: bool)` |
| `git_io` | `truncate(diff: str, limit: int) -> tuple[str, bool]` | Truncated text + whether truncation happened (so prompt can disclose it) |
| `safe_mode` | `mask(text: str) -> str` | Same text with matched secret shapes replaced by `***` |
| `prompts` | `build_commit(snapshot, *, truncated) -> list[Message]` | System + user messages |
| `prompts` | `build_pr(snapshot, *, truncated) -> list[Message]` | Same shape |
| `ai_client` | `complete(messages, *, model, temperature, max_tokens) -> str` | Raw assistant content; raises `AIError(cause)` on network/auth/HTTP errors |
| `polish` | `enforce_commit(text) -> CommitResult` | `CommitResult(subject, body, needs_retry: bool, reason: str \| None)` |
| `polish` | `enforce_pr(text) -> PRResult` | `PRResult(title, why, what, how_to_test, needs_retry, reason)` |
| `render` | `commit(result)` / `pr(result)` / `no_changes()` / `error(msg)` | Writes to stdout (or stderr for errors) |

All non-trivial functions carry type hints and a one-line docstring describing return value + preconditions (.cursorrules §5 "Public Docstrings").

### 4.4 Prompt Strategy (subject §3 LO 4, §4.3, §4.4)

A single **system prompt** anchors the model on output format; the **user prompt** carries the change context. Both prompts live in `prompts.py` as module constants so reviewers can diff them in one file.

System prompt (shared, both subcommands):

> You are an assistant that writes Git commit messages and pull-request drafts. Always answer in the exact format requested. Never invent files, modules, or behavior that is not visible in the diff.

Commit-specific user prompt includes:

- A short header listing changed files (from `git status --porcelain`, max 10 names).
- The diff slice (truncated per §2).
- An explicit format block: `Subject: <≤50 chars, imperative mood>` newline `Body (optional): up to 3 bullets, each referencing a file or module`.

PR-specific user prompt includes the same change context plus a format block:

```
Title: <≤80 chars>

## Why
- ...

## What
- ...

## How to Test
- ...
```

The format block is verbatim what `polish.enforce_pr` parses, so the model has no ambiguity about delimiters.

### 4.5 Output Validation & Polish (subject §4.5)

Both polish functions are **pure** string → result transforms; no I/O.

`enforce_commit`:

- Parse first non-empty line as subject; strip trailing punctuation; reject if empty.
- If `len(subject) > 72` → flag `needs_retry` with `reason="subject too long"`.
- If `50 < len(subject) <= 72` → keep but record a non-blocking warning (printed dimmed by `render`).
- Body (everything after the blank line) is optional; if present, accept either a paragraph or up to 5 bullet lines.

`enforce_pr`:

- Extract `Title:` line (case-insensitive), truncate to 80 if 1–10 chars over (post-process), else `needs_retry`.
- Locate `## Why`, `## What`, `## How to Test` headers (case- and whitespace-insensitive). Missing any → `needs_retry`.
- Each section must have **≥1 bullet line** (`- ` or `* `). Missing → `needs_retry`.

Retry policy (called from `cli.py`):

- If `needs_retry` and we have not retried → call `ai_client.complete()` once more with a stricter user message appended ("Your previous answer broke rule X; regenerate respecting all format rules."), `temperature` halved.
- If still failing → fall back to post-process: truncate the subject/title at the hard limit, insert a placeholder bullet (`- (Missing — please fill in.)`) under any empty section, and print a warning so the user knows the output is partially synthetic.

### 4.6 Terminal Output (subject §4.5 "clear separators / headers")

`render.commit(result)` prints:

```
================ COMMIT MESSAGE ================
<subject>

<body, if any>
=================================================
```

`render.pr(result)` prints:

```
================== PR DRAFT ==================
Title: <title>

## Why
- ...

## What
- ...

## How to Test
- ...
==============================================
```

Warnings (e.g. "Subject is 57 chars; consider shortening to ≤50.") go to **stderr** so piping the output to a file does not pollute it.

---

## 5. Configuration & Secrets

- **API key** is read once in `ai_client._load_key()` from `os.environ["OPENAI_API_KEY"]`. Missing → raise `AIError("OPENAI_API_KEY environment variable is not set.")` → `cli.py` translates to exit code `5` with the same message on stderr.
- The key is never logged, never echoed, and never included in errors that wrap upstream responses (`ai_client.complete` strips `Authorization` from any debug dump).
- `--safe-mode` is **off by default** in core scope. When on, the diff string is run through `safe_mode.mask` **before** `prompts.build_*` ever sees it, so the prompt the model receives is already redacted.
- No `.env` loader in core scope; the README points reviewers at `export OPENAI_API_KEY=...` (or `direnv`) so we keep the dependency surface at zero (.cursorrules §4).

---

## 6. Phased Implementation Plan

Each phase = **one logical change = one commit** (.cursorrules §6 Logical Commit Unit), with Conventional Commits prefixes. (.cursorrules §2 "coarse steps: 3–7")

### Phase 0 — Scaffolding & CLI Skeleton

- Create `src/ai_gitgen/` package with empty modules and a `__main__.py` that wires `cli.main()`.
- Build `cli.py`: argparse with `commit` / `pr` subparsers, `--model` / `--temperature` / `--max-tokens` / `--safe-mode` flags, defaults pulled from module constants.
- Stub each subcommand to print "not implemented yet" and exit `2`.
- Commit: `chore: scaffold ai_gitgen package and argparse subcommands`

### Phase 1 — Git Capture & "No Changes" Path

- Implement `git_io.collect()` via `subprocess.run(["git", "status", "--porcelain"])` and `subprocess.run(["git", "diff", "HEAD"])` (plus `--cached`); fail with a clear message when CWD is not a Git repo.
- Implement `git_io.truncate()` and the "no changes" early exit through `render.no_changes()`.
- Tests in `tests/test_git_io.py` use a tmp dir + `git init` + seed commits (no network, no time dep — .cursorrules §6 Testing Determinism).
- Commit: `feat: collect git status and diff with no-change detection`

### Phase 2 — AI Client & Prompt Builders

- Implement `ai_client.complete()` using `urllib.request.Request` with `Authorization: Bearer …`, JSON body, and a 30 s timeout. Raise `AIError` with the original exception's class name and message attached.
- Implement `prompts.build_commit` / `build_pr` returning the message list described in §4.4.
- `tests/test_prompts.py` asserts that the format block, file list, and truncation notice all appear in the user message when applicable; **no network call in tests** — the AI client itself is exercised manually.
- Commit: `feat: add openai chat completions client and prompt builders`

### Phase 3 — Polish & Retry Logic

- Implement `polish.enforce_commit` / `enforce_pr` per §4.5; build `CommitResult` / `PRResult` dataclasses.
- Wire the **one-retry** loop in `cli.py`: call client → polish → if needs_retry and `not retried`, build a constraint-tightening message and call client once more.
- `tests/test_polish.py` covers: 73-char subject → retry; 72-char subject → pass; PR missing `## How to Test` → retry; PR with empty body → retry; PR title 79 chars → pass.
- Commit: `feat: enforce commit and pr format rules with single retry`

### Phase 4 — Safe Mode & Final Render

- Implement `safe_mode.mask` with the regex set in §2; verify it does not eat valid identifiers (e.g. `MAX_TOKENS = 400` stays intact while `OPENAI_API_KEY=sk-abc...` is masked).
- Implement `render.commit` / `render.pr` separators per §4.6; route warnings to stderr.
- `tests/test_safe_mode.py` covers the regex set with a small fixture matrix.
- Commit: `feat: add safe mode masking and final terminal rendering`

### Phase 5 — README & GitHub Push

- `README.md` sections: Overview · Install (`pip install -e .` optional; `python -m ai_gitgen` always works) · Environment (`OPENAI_API_KEY`) · Commands (with **real sample output** for both `commit` and `pr`) · Options table · Ops notes (secrets masking, cost guidance, rate-limit behavior) · Subject mapping (which §§ are covered where).
- Create the GitHub repo, push, verify `python -m ai_gitgen commit` and `python -m ai_gitgen pr` both work on a fresh clone after `export OPENAI_API_KEY=...`.
- Commit: `docs: add readme with install, env, commands, and sample output`

### Phase 6 (Optional) — Bonus (subject §5)

- Only after core passes, in separate commits (.cursorrules §4 YAGNI).
- See `docs/bonus_plan.md` for the real-PR run, template/convention layer, and advanced safe mode.

---

## 7. Verification Strategy

This assignment has no graded automated suite; we use **`unittest` for pure logic** (.cursorrules §6) and a **manual checklist** for everything that touches the network or the user's shell. Network-dependent flows are verified by hand, not by mocked HTTP in tests (.cursorrules §6 Testing Determinism).

Automated (`python3 -m unittest discover -s tests -v`):

- `git_io`: empty repo · staged only · unstaged only · staged + unstaged · truncation at boundary · non-git CWD raises.
- `prompts`: commit prompt contains file list and format block; PR prompt contains all three section headers; truncation notice appears when input is shortened.
- `polish`: subject length boundaries (50 / 72 / 73) · PR title length (80 / 81) · missing section detection · placeholder injection on final fallback.
- `safe_mode`: each regex shape masks; non-matching code stays untouched.

Manual checklist:

- [ ] `OPENAI_API_KEY` unset → `python -m ai_gitgen commit` prints the env-var error on stderr and exits `5`.
- [ ] Bad key (`export OPENAI_API_KEY=sk-invalid`) → error message **names the cause** ("401 Unauthorized" or upstream message) and exits `4`.
- [ ] Network blocked in OS firewall → error message names the cause (timeout / connection refused) and exits `4`.
- [ ] Fresh repo with no changes → `No changes detected.` on stdout, exit `0`.
- [ ] Trivial change (`echo x >> README.md`) → `commit` prints a one-line subject ≤72 chars + optional body; `pr` prints title ≤80 chars + Why / What / How sections each with ≥1 bullet.
- [ ] `--temperature 1.5` and `--max-tokens 10` both round-trip and visibly affect output / truncate (sanity check that flags are wired, subject §3 LO 2).
- [ ] `--safe-mode` on a diff containing `OPENAI_API_KEY=sk-abc...` → masked in the request body (verify with a local proxy or by inspecting the request before send during a dry run).
- [ ] Large refactor (>8 000 char diff) → output mentions only files actually present in the truncated slice; no hallucinated paths.
- [ ] Output of both commands can be piped to `git commit -F -` and `gh pr create --body-file -` without further editing.
- [ ] `README.md` install + commands can be followed end-to-end on a sibling machine; the sample output in the README is reproducible (modulo wording).

---

## 8. Risks / Deferred Decisions

| Item | Risk | Mitigation |
| ---- | ---- | ---------- |
| Provider lock-in to OpenAI | A reviewer using Anthropic / Gemini cannot run the tool | `ai_client` is small and isolated; document the swap (endpoint + body shape) in README; bonus phase can add a `--provider` flag |
| Diff size > context window | Even with 8 000-char cap, very wide diffs may still cost more than expected | Truncate by file (head N lines per file) + always disclose truncation in the prompt so the model does not invent omitted content |
| Validation failure loop | Two model calls per invocation if format slips | Hard cap at **one** retry; final fallback is deterministic post-process, never a third call |
| API key leakage in logs | Accidental `print(request)` in debug | `ai_client._sanitize()` strips `Authorization` from any debug dump; no `print()` outside `render` |
| Rate-limit / 429 storms | Repeated test runs during dev hit the per-minute cap | Detect HTTP 429 → render the rate-limit hint and exit `4`; do not auto-retry on 429 in core |
| `subprocess` git errors on Windows | Path / shell quoting differences | Always pass argv as a list (no `shell=True`); document POSIX shell as primary in README; Windows is best-effort |
| Secrets masking false negatives | Subject only asks for "at least one" ops note, but a leaked key is high-impact | Regex set in §2 covers the most common shapes; bonus phase extends with configurable policy |
| Bonus vs plan drift | Later choices (convention layer, advanced safe mode) may change defaults | Update §2 table when starting bonus; note plan changes in commit message |

---

## 9. Definition of Done

- All three deliverables in subject §2 are met (integration & automation flow / GitHub repo / README).
- `python -m ai_gitgen commit` and `python -m ai_gitgen pr` both run end-to-end from a Git-initialized project root with a valid `OPENAI_API_KEY`, producing copy-pasteable output (subject §2.1, §4.3, §4.4).
- `--model`, `--temperature`, `--max-tokens` flags are wired on both subcommands with safe defaults; `--help` documents them (subject §4.2).
- "No changes" path prints the documented message and exits `0`; auth / network / git failures print a **cause-bearing** message and use a distinct exit code (subject §4.1, §4.2).
- Commit subjects are ≤72 chars (≤50 preferred with a stderr warning); PR titles are ≤80 chars; PR bodies always contain `## Why`, `## What`, `## How to Test` with ≥1 bullet each (subject §4.5).
- One ops note (secrets masking via `--safe-mode`) is implemented; cost and rate-limit guidance is documented in `README.md` (subject §4.6).
- `README.md` includes install, env var setup, both command examples, **real sample output**, and a subject-mapping table; a reviewer can run the tool from the docs alone (subject §2.3).
- `python3 -m unittest discover -s tests -v` passes with stdlib only; no network and no time dependencies in tests (.cursorrules §6).
- All five learning objectives in subject §3 can be explained from this plan §3–§4 and the implementation.
