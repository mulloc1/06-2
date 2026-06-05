# Phase 3 — Polish & Retry Logic

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 3
> Subject reference: [`docs/subject.md`](../subject.md) §4.3, §4.4, §4.5

This phase adds the **output validation** stage that turns raw model text into a structured result the renderer can trust. It is the only stage allowed to trigger a **single regeneration retry** with tightened constraints, and it is the only stage that produces non-blocking warnings (long subjects, post-process fallbacks) for stderr.

---

## 1. Goal

- Implement `polish.enforce_commit(text) -> CommitResult` and `polish.enforce_pr(text) -> PRResult` per `plan.md` §4.5.
- Wire a **one-retry** loop in `cli.py`: client → polish → if `needs_retry` and not already retried, build a constraint-tightening user message and call client once more with `temperature/2`.
- If the retry still fails, fall through to a deterministic post-process fallback (truncate at hard limits, inject placeholder bullets) and emit a stderr warning so the user knows the output is partially synthetic.
- Cover the polish module with `unittest` tests around the subject/title length boundaries and the PR section-detection rules.

---

## 2. Scope (In / Out)

**In scope**
- `src/ai_gitgen/polish.py`: `CommitResult`, `PRResult` dataclasses; `enforce_commit`, `enforce_pr`; internal `_extract_pr_sections`, `_normalize_subject`.
- `cli.py`: extend `_run_subcommand` with the retry loop and the warning channel.
- `prompts.py`: small helper `build_retry_message(reason)` that returns a single user message appended to the original conversation for the regeneration call.
- `tests/test_polish.py`: subject length boundaries, PR title length, missing-section detection, placeholder injection on final fallback.

**Out of scope**
- Safe mode — Phase 4.
- Final terminal layout (separators / headers) — Phase 4. `render.commit` / `render.pr` still write raw text; only `render.warning(msg)` is added here.
- Any second-retry / loop expansion — explicitly capped at one retry (`plan.md` §2).

---

## 3. Tasks

### 3.1 Result dataclasses

```python
@dataclass(frozen=True)
class CommitResult:
    subject: str
    body: str | None
    needs_retry: bool
    reason: str | None       # None on success; populated when retry is requested
    warnings: tuple[str, ...] = ()  # non-blocking; e.g. "subject is 57 chars"

@dataclass(frozen=True)
class PRResult:
    title: str
    why: tuple[str, ...]
    what: tuple[str, ...]
    how_to_test: tuple[str, ...]
    needs_retry: bool
    reason: str | None
    warnings: tuple[str, ...] = ()
```

- Frozen, immutable — renderer cannot accidentally mutate.
- Bullet sections are tuples of strings; each entry already starts without the leading `- ` (polish strips the marker).

### 3.2 `enforce_commit(text) -> CommitResult`

1. Split `text` into lines; collect leading blanks.
2. **Subject** = first non-empty line, with trailing whitespace and trailing `.` stripped. If empty → `needs_retry=True, reason="empty subject"`.
3. Strip a leading `Subject:` prefix if present (case-insensitive) so the model's literal template label doesn't end up in the subject string.
4. Length rules (`subject.md` §4.5):
   - `len(subject) > 72` → `needs_retry=True, reason=f"subject too long ({len(subject)} chars; max 72)"`.
   - `50 < len(subject) <= 72` → keep but append warning `"subject is {n} chars; consider shortening to <=50."`.
5. **Body** = everything after the first blank line following the subject; collapse trailing whitespace; treat as `None` if it is empty.
   - If body is present and has more than 5 bullet lines, truncate to the first 5 and add a warning.
   - Reject (set `needs_retry`) if the body is a single very long paragraph **AND** the subject was also flagged — otherwise accept paragraphs as-is.
6. Return `CommitResult(subject, body, needs_retry, reason, warnings)`.

### 3.3 `enforce_pr(text) -> PRResult`

1. Locate `Title:` line (case-insensitive, allow leading whitespace). Missing → `needs_retry=True, reason="missing Title: line"`.
2. Strip `Title:` prefix and surrounding quotes; trim trailing punctuation.
3. Length rules:
   - `len(title) > 80` and over by **>10** chars → `needs_retry`.
   - `80 < len(title) <= 90` → post-process truncate to 80 chars at the last word boundary and append `"title was {n} chars; truncated to 80"` warning.
4. Section parsing — call `_extract_pr_sections(text)` which:
   - Walks the text line-by-line looking for headers `## Why`, `## What`, `## How to Test` (case- and whitespace-insensitive; accept extra spaces and the variants `## How To Test`, `## How-to-test`).
   - For each section, collect subsequent lines starting with `- ` or `* ` (bullet markers) until the next `##` header or end of text. Strip the marker and trailing whitespace.
   - Return a dict with the three section lists.
5. For each of the three required sections, if missing entirely → `needs_retry=True, reason=f"missing section: ## {Name}"`. If header present but **zero** bullets → same.
6. If `needs_retry` is True after all checks, return now (caller decides on retry vs fallback).
7. Otherwise return `PRResult(...)` populated.

### 3.4 `polish.fallback_pr(text) -> PRResult`

- Same parsing as `enforce_pr` but never sets `needs_retry`.
- Hard-truncates the title at 80 chars (last word boundary if possible).
- For each missing or empty section, inject the placeholder bullet `"(Missing — please fill in.)"` and append a warning `f"## {Name} was missing; inserted placeholder."`.

### 3.5 `polish.fallback_commit(text) -> CommitResult`

- Subject is truncated to 72 chars at the last word boundary; warning `"subject was {n} chars; hard-truncated to 72."` appended.
- Body is taken as-is or set to `None`; never raises.

### 3.6 `prompts.build_retry_message(reason) -> dict`

```python
def build_retry_message(reason: str) -> dict:
    return {
        "role": "user",
        "content": (
            f"Your previous answer violated this rule: {reason}. "
            "Regenerate the entire response, respecting ALL format rules from "
            "the previous instruction. Do not apologize or explain."
        ),
    }
```

### 3.7 `cli.py` integration

Replace the trailing `sys.stdout.write(text.rstrip() + "\n")` in `_run_subcommand` with a polish loop. Sketch (commit branch shown; the pr branch is symmetric):

```python
text = ai_client.complete(messages, ...)
result = polish.enforce_commit(text)
if result.needs_retry:
    retry_messages = messages + [
        {"role": "assistant", "content": text},
        prompts.build_retry_message(result.reason),
    ]
    text = ai_client.complete(
        retry_messages,
        model=args.model,
        temperature=max(args.temperature / 2, 0.0),
        max_tokens=args.max_tokens or default_max_tokens,
    )
    result = polish.enforce_commit(text)
    if result.needs_retry:
        result = polish.fallback_commit(text)
        render.warning(f"Output fell back to deterministic post-process: {result.reason or 'format rules not met after retry'}")

for w in result.warnings:
    render.warning(w)
sys.stdout.write(<for now, plain text composition: result.subject + body>)
```

- The same shape is applied to the `pr` branch using `enforce_pr` / `fallback_pr`.
- `render.warning(msg)` is added as a thin wrapper around `sys.stderr.write("warning: " + msg + "\n")`.
- The retry path **calls `ai_client.complete` at most twice per invocation**; no third call ever, even on fallback (`plan.md` §8 — validation failure loop).

### 3.8 `tests/test_polish.py`

Pure functions → cheap to test exhaustively:

- `test_commit_subject_50_passes_no_warning`: subject exactly 50 chars → `needs_retry is False`, `warnings == ()`.
- `test_commit_subject_72_passes_with_warning`: subject exactly 72 chars → pass with a `consider shortening` warning.
- `test_commit_subject_73_requests_retry`: subject 73 chars → `needs_retry is True, reason="subject too long"`.
- `test_commit_empty_subject_requests_retry`.
- `test_commit_strips_subject_prefix`: input `"Subject: do thing\n\n- file"` → result subject `"do thing"`.
- `test_pr_title_80_passes`: title at 80 → pass.
- `test_pr_title_81_post_processed_with_warning`: 81-char title → truncated to 80, warning emitted, no retry.
- `test_pr_title_91_requests_retry`.
- `test_pr_missing_how_to_test_requests_retry`.
- `test_pr_section_present_empty_requests_retry`: header present, zero bullets.
- `test_pr_section_aliases`: `## How To Test` parses to the `how_to_test` field.
- `test_fallback_pr_injects_placeholders`: missing sections become `(Missing — please fill in.)`.
- `test_fallback_commit_hard_truncates_subject`.

All tests use raw strings; no `ai_client`, no `git_io`, no network.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `src/ai_gitgen/polish.py` | implement (`CommitResult`, `PRResult`, `enforce_commit`, `enforce_pr`, `fallback_commit`, `fallback_pr`, internal helpers) |
| `src/ai_gitgen/prompts.py` | edit (`build_retry_message`) |
| `src/ai_gitgen/cli.py` | edit (`_run_subcommand` retry loop + warnings) |
| `src/ai_gitgen/render.py` | edit (add `warning(msg)`) |
| `tests/test_polish.py` | create (length boundaries, sections, fallback) |

---

## 5. Acceptance Criteria

- [ ] On a normal change with valid `OPENAI_API_KEY`: `python -m ai_gitgen commit` always prints a subject ≤72 chars and an optional body.
- [ ] Same for `pr` — title ≤80 chars; body always contains `## Why`, `## What`, `## How to Test` with ≥1 bullet each (subject §4.5).
- [ ] When the model produces a long subject (force it with `--max-tokens 10` so it truncates oddly), one retry is observed in the logs and the final printed subject is ≤72 chars.
- [ ] When two consecutive responses violate the rules, stderr shows the fallback warning **and** stdout still emits a copy-pasteable result (no hard fail).
- [ ] No invocation triggers more than two upstream calls — verify by counting `ai_client.complete` calls in a debugger / temporary `print` (remove before commit).
- [ ] `python3 -m unittest discover -s tests -v` is green; `tests/test_polish.py` covers all listed boundaries.
- [ ] `rg "subprocess|urllib|os\.environ" src/ai_gitgen/polish.py` returns nothing — polish is pure string → result.

---

## 6. Commit

```
feat: enforce commit and pr format rules with single retry
```

---

## 7. Risks / Notes

- **One-retry cap is non-negotiable** — surface it in the code as `MAX_RETRIES = 1` rather than a literal `1` so the constraint is visible (.cursorrules §3 — no magic literals).
- **Warning fatigue**: every warning costs reviewer attention. Combine related warnings (e.g. two missing sections → one warning that lists both) rather than emitting three separate lines.
- **Header alias matrix**: the regex-free walker in `_extract_pr_sections` should normalize header text by lowercasing + stripping non-word chars before comparing to `{"why", "what", "howtotest"}`. Keep that normalization in **one** place.
- **Determinism on retry**: halving `temperature` is the only mutation; the second call uses the same model + max-tokens so cost is bounded.
- **Body parsing is intentionally loose**: subject §4.3 says body is optional and only requires *one* of "1–3 file mentions" or "1–2 bullet core changes". We do not enforce that distribution mechanically — we just truncate to 5 bullets and otherwise pass through.
- **Cli still owns I/O**: `polish` must not import `sys` or `render`. The retry loop and warnings flow through `cli.py` calling `render.warning`.

---

## 8. Definition of Done

- `enforce_commit` and `enforce_pr` are pure, deterministic, fully tested at the documented boundaries.
- Cli triggers at most one regeneration per invocation; the fallback never produces a third upstream call.
- Every printed commit/PR satisfies the length and section rules in subject §4.5 — verified by manual run plus the test suite.
- Phase 4 can wrap the final output with separators and add safe-mode masking without touching the polish module.
