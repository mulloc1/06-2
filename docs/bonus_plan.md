# AI Git CLI Bonus Implementation Plan (bonus_plan.md)

This document plans the **bonus tasks** in `docs/subject.md` §5. It assumes the core mission (`docs/plan.md` Phases 0–5) is **done and pushed to GitHub**, and starts a new phase on top of the working `ai_gitgen` CLI. Per `.cursorrules` §4 (YAGNI), we keep additions **minimal** and only extend modules where the existing responsibility already fits.

Subject §5 lists three optional items:

| Item | Subject text |
| ---- | ------------ |
| **One Real PR** | Pick one repo from a prior mission, make meaningful changes on a branch, use this tool to generate one commit message + one PR draft, open the real PR, and submit the PR link plus 5–10 lines on "AI draft → final PR" edits. |
| **Custom Templates** | Analyze a repo's style → define a team convention (e.g. `feat/fix/docs`, scope, PR template); reflect it in the tool via `.ai-gitgen.yml`, `--convention`, or prompt template swap (at least one). Submit: convention doc (README section) + one before/after generation comparison. |
| **Advanced Safe Mode** | With `--safe-mode`, extend masking (regex) or limit diff sent (by file/lines) with a configurable policy. |

---

## 1. Goal Summary

- Land the three bonus items **without breaking** any core flow locked in `plan.md` §2 / §4: the `commit` / `pr` subcommands, exit codes, polish rules, and stdlib-only dependency policy all stay intact.
- Treat the **Real PR** item as a process deliverable (a link + a short reflection), not a code change to `ai_gitgen` itself; the only repo artifact is a `docs/real_pr.md` (or a README subsection) capturing the link and the AI draft → final PR edits.
- Introduce **one configuration surface** — `.ai-gitgen.yml` at the project root — that drives both Custom Templates and Advanced Safe Mode. A single config module avoids two parallel knob sets (.cursorrules §4 "split after evidence").
- Make the convention layer a **prompt-template swap**: the model still receives a system + user message; only the *content* of those messages changes when `--convention <name>` (or the config default) selects a different template. No new pipeline stage, no new module besides config loading.
- Make advanced safe mode a **policy object** (regex list + file-glob include/exclude + per-file line cap) consumed by `safe_mode.mask` and `git_io.truncate`; the existing `--safe-mode` flag stays as the on/off switch, the policy decides *how* to mask.
- Ship bonus features as a **separate set of commits** behind a `feat(bonus):` prefix (or a dedicated branch) so the core grading scope is unambiguous (`.cursorrules` §6 Logical Commit Unit).
- No new third-party dependency except a **YAML parser**; even that is optional — we accept either `.ai-gitgen.yml` (PyYAML if installed) or `.ai-gitgen.toml` (stdlib `tomllib` on 3.11+). If neither parser is available and a YAML file is present, fall back to the built-in defaults with a stderr notice.

---

## 2. Locked Decisions

Decisions for items left free by subject §5 (which config format, which convention names, which masking extensions) and choices that would be painful to reverse later.

| Item | Decision | Rationale |
| ---- | -------- | --------- |
| Real PR target | A **prior mission repo** from this course (e.g. `04-1.my_project` or `04-2.react_basic`); meaningful change = README polish, accessibility fix, or a small refactor that touches ≥2 files | Subject §5 picks "one prior mission"; small-but-real change keeps the AI-draft comparison honest |
| Real PR deliverable | `docs/real_pr.md` in **this** repo, containing the PR URL + a 5–10 line section "AI draft → final PR edits" | Centralizes the bonus evidence; reviewer follows one link |
| Config file format | **TOML preferred** (`.ai-gitgen.toml`, stdlib `tomllib`); YAML supported when `PyYAML` is importable | Stdlib-first per .cursorrules §4; YAML kept because subject explicitly names `.ai-gitgen.yml` |
| Config file location | Project root (CWD where the CLI is run), single file; no global `~/.config/...` lookup in this phase | One source of truth; YAGNI |
| Config CLI override | `--config <path>` to point at a non-default file; `--convention <name>` overrides the active convention; `--no-config` skips loading entirely | Reviewers can A/B without editing files |
| Convention model | **Named templates** (`conventional`, `gitmoji`, `scoped`, `freeform`) each with a `system_prompt` + `commit_user_template` + `pr_user_template` triplet stored in `prompts.py` | All conventions ship in code so the tool works without a config file; config can also inline a custom template |
| Default convention | **`conventional`** (Conventional Commits: `feat:` / `fix:` / `docs:` / `refactor:` / `test:` / `chore:`) | Matches `.cursorrules` §6 "Conventional Commits"; sane default if no config |
| Convention contract | Templates use named `{placeholders}`: `{file_list}`, `{diff}`, `{truncated_notice}`, `{scope_hint}`. Missing placeholders are filled with empty strings, not errors | Forward-compatible with new placeholders |
| Safe-mode policy schema | `[safe_mode]` table with `regexes: list[str]`, `include_globs: list[str]`, `exclude_globs: list[str]`, `max_lines_per_file: int`, `mask_token: str = "***"` | Each subject-listed extension (regex / file limit / line limit) maps to one key; one schema covers all three |
| Default policy | Same regex set as core §2 (emails, AWS keys, `sk-` tokens, `*_KEY=`/`*_TOKEN=` lines); `exclude_globs = [".env*", "*.pem", "*.key", "*.p12"]`; `max_lines_per_file = 200` | "Sensible by default" — turning on `--safe-mode` should never need a config file |
| Policy precedence | CLI flag > config file > built-in defaults; flags **add** to (don't replace) config regex/glob lists | Lets reviewers extend masking without re-typing the whole list |
| Convention vs. safe mode interaction | Independent. `--convention conventional --safe-mode` is a valid combination | Avoids matrix coupling |
| Logging of policy in effect | When `--safe-mode` is on, print one stderr line: `Safe mode: <N> regexes, <K> exclude globs, max <L> lines/file` | Reviewer can see which policy was applied without guessing |
| New tests | One file per new module/branch: `tests/test_config.py`, `tests/test_conventions.py`, `tests/test_safe_mode_policy.py`. All stdlib `unittest` | .cursorrules §6 Stdlib Test Runner |
| Bonus branch / commits | Branch `bonus` off the deployed core; each phase = one commit with `feat(bonus):` / `docs(bonus):` prefix | Keeps core history clean for grading |

> All other free choices follow `docs/plan.md` §2 (Python 3.10+, argparse, urllib, OpenAI default, etc.). This file does **not** override any decision locked there.

---

## 3. Affected Files (Minimal Footprint)

Edit existing modules rather than introduce new layers. Two new files are justified because no current module owns config loading or PR-link evidence.

| File | Change |
| ---- | ------ |
| `src/ai_gitgen/cli.py` | Add `--config`, `--convention`, `--no-config` flags; call `config.load()` early; pass `Convention` + `SafeModePolicy` down the pipeline |
| `src/ai_gitgen/prompts.py` | Replace single template constants with a `CONVENTIONS: dict[str, ConventionTemplate]` mapping; `build_commit` / `build_pr` accept a `convention` argument |
| `src/ai_gitgen/safe_mode.py` | `mask(text, policy)` consumes a `SafeModePolicy` dataclass instead of a hardcoded regex list; legacy zero-arg form still works (defaults to built-in policy) |
| `src/ai_gitgen/git_io.py` | `collect(policy)` applies `include_globs` / `exclude_globs` and `max_lines_per_file` from the policy when building the diff slice |
| `src/ai_gitgen/config.py` *(new)* | Loads `.ai-gitgen.toml` or `.ai-gitgen.yml`; returns `AppConfig(convention: str, safe_mode: SafeModePolicy, custom_templates: dict[str, ConventionTemplate])`; emits stderr notice on missing parser |
| `src/ai_gitgen/render.py` | Add `render.policy_banner(policy)` for the one-line stderr summary |
| `tests/test_config.py` *(new)* | Round-trip TOML + YAML (skip YAML if `PyYAML` not importable); precedence rules; missing-file fallback |
| `tests/test_conventions.py` *(new)* | Each shipped convention produces the right prefix / scope placement; custom template from config wins over built-in |
| `tests/test_safe_mode_policy.py` *(new)* | Adding a regex extends (does not replace) defaults; excluded glob skips a whole file; line cap truncates with notice |
| `docs/real_pr.md` *(new)* | PR link + "AI draft → final PR edits" reflection (5–10 lines) |
| `README.md` | Append a "Bonus Features" section: config file example, convention list with before/after comparison, advanced safe-mode policy table, link to `docs/real_pr.md` |

> `config.py` is justified because configuration parsing + precedence resolution is a distinct responsibility that does not belong in `cli.py` (argparse) or `prompts.py` (template content). `docs/real_pr.md` is justified because the README would otherwise grow a long process-narrative section that has no operational value to a future user.

---

## 4. Real PR Run (subject §5 — One Real PR)

### 4.1 Plan

1. **Pick the target.** Default choice: `04-1.my_project` (responsive portfolio site) — README polish + a small accessibility fix touches multiple files, which makes the AI commit / PR draft non-trivial.
2. **Branch.** `git switch -c bonus/ai-draft-demo` in the target repo.
3. **Make the change.** Examples (any one, scoped to ~30 changed lines): improve `<img alt>` text, add `prefers-reduced-motion` guard, rewrite a README section, factor a CSS token. The change must be real (passes existing checks).
4. **Generate the drafts.** From the target repo root:
   ```
   export OPENAI_API_KEY=...
   python -m ai_gitgen commit > /tmp/commit.txt
   python -m ai_gitgen pr     > /tmp/pr.txt
   ```
5. **Edit minimally.** Apply human edits on top of the AI draft (fix wording, tighten bullets). Save **both** the raw AI output and the final committed text — that diff is the reflection.
6. **Open the PR.** Push the branch; use the polished title/body for the actual PR.

### 4.2 Reflection (`docs/real_pr.md`)

Required sections:

- **PR link.** URL to the opened PR (kept open or merged; either is fine for the assignment).
- **AI draft vs. final, 5–10 lines.** A short list of the concrete edits: e.g. "shortened subject from 58 → 47 chars", "rephrased one Why bullet that hallucinated a non-existent test step", "added a How-to-Test bullet covering the CSS variable I renamed".
- **One takeaway.** A sentence on what surprised you (subject §3 LO 5 — validation/polish in practice).

### 4.3 Acceptance

- The PR link resolves to a real GitHub PR with a meaningful diff and the AI-assisted commit / PR description.
- `docs/real_pr.md` is in this repo; the README "Bonus Features" section links to it.

---

## 5. Custom Commit / PR Templates (subject §5 — Customize Templates)

### 5.1 Convention contract

A convention is a triplet stored in `prompts.py`:

```py
@dataclass(frozen=True)
class ConventionTemplate:
    system_prompt: str
    commit_user_template: str   # uses {file_list} {diff} {truncated_notice} {scope_hint}
    pr_user_template: str       # same placeholder set
```

Shipped conventions:

| Name | Subject format hint | PR format hint |
| ---- | ------------------- | -------------- |
| `conventional` | `type(scope): subject` where `type ∈ {feat, fix, docs, refactor, test, chore}` | Same Why / What / How sections as core |
| `gitmoji` | `:emoji: subject` (e.g. `:sparkles: add filter chips`) | Same body, with one emoji at the title head |
| `scoped` | `[area] subject` (no Conventional type) | Body adds a `## Scope` section above `## Why` |
| `freeform` | No prefix rule; just a one-line imperative subject | Body identical to core |

### 5.2 Configuration

`.ai-gitgen.toml` example (the recommended form):

```toml
convention = "conventional"

[conventions.feat-first]
system_prompt = "You are a release-notes-style commit writer..."
commit_user_template = "..."
pr_user_template = "..."
```

- `convention` selects the active template (built-in name **or** a key under `[conventions.*]`).
- A `[conventions.<name>]` table can override any single field; missing fields fall back to the `conventional` defaults.

### 5.3 CLI surface

```
python -m ai_gitgen commit --convention gitmoji
python -m ai_gitgen pr     --convention feat-first --config ./team.toml
```

- `--convention` is parsed in `cli.py` and overrides the config's `convention` key.
- The polish rules (length caps, required PR sections) are **unchanged** — they live in `polish.py` and operate on the model's output regardless of which template generated it. A convention that breaks `## Why / ## What / ## How to Test` is rejected at load time with a clear error.

### 5.4 Before / After deliverable

Required in the README "Bonus Features" section:

- One real `git diff` (small, ~20 lines) committed to a scratch branch.
- The `commit` and `pr` output **before** the convention change (`conventional`, the default).
- The `commit` and `pr` output **after** switching to one of `gitmoji` / `scoped` / a custom team convention.
- A one-sentence note on why the team would pick one over the other.

### 5.5 Acceptance

- All four built-in conventions produce output that still passes `polish.enforce_commit` and `polish.enforce_pr`.
- A `.ai-gitgen.toml` with a custom `[conventions.<name>]` table actually changes the generated subject style in the before/after demo.
- Running without a config file leaves the tool at `conventional` defaults — no regression for core users.

---

## 6. Advanced Safe Mode (subject §5 — Advanced Safe Mode)

### 6.1 Policy schema

```py
@dataclass(frozen=True)
class SafeModePolicy:
    regexes: tuple[str, ...]           # compiled lazily in safe_mode.py
    include_globs: tuple[str, ...]      # if non-empty, ONLY these files participate
    exclude_globs: tuple[str, ...]      # always wins over include
    max_lines_per_file: int             # per-file diff cap; 0 = unlimited
    mask_token: str                     # default "***"
```

Default policy (used whenever `--safe-mode` is on with no config):

| Field | Value |
| ----- | ----- |
| `regexes` | `[r"[\w.+-]+@[\w-]+\.[\w.-]+", r"AKIA[0-9A-Z]{16}", r"\b[A-Z][A-Z0-9_]*_(?:KEY\|TOKEN\|SECRET)=\S+", r"\bsk-[A-Za-z0-9]{20,}\b"]` |
| `include_globs` | `()` (empty → all files allowed) |
| `exclude_globs` | `(".env*", "*.pem", "*.key", "*.p12", "**/secrets/**")` |
| `max_lines_per_file` | `200` |
| `mask_token` | `"***"` |

### 6.2 Behavior

- `git_io.collect(policy)` walks the change list and:
  1. Drops files whose path matches `exclude_globs` entirely (their diffs never reach the prompt).
  2. If `include_globs` is non-empty, keeps **only** files matching it.
  3. For surviving files, trims each file's diff to `max_lines_per_file` (head); if trimmed, prepends a one-line notice that the model can mention in the PR draft.
- `safe_mode.mask(text, policy)` applies the compiled regex set to whatever survived the file-level filter.
- The final prompt always includes a `{truncated_notice}` placeholder value reflecting the *combined* truncation (size cap from §2 + per-file line cap from this policy).

### 6.3 CLI surface

```
python -m ai_gitgen pr \
    --safe-mode \
    --safe-mode-add-regex 'INTERNAL_[A-Z_]+=' \
    --safe-mode-exclude 'config/**' \
    --safe-mode-max-lines 50
```

- `--safe-mode-add-regex` / `--safe-mode-exclude` are **repeatable**; each occurrence appends to the policy list.
- `--safe-mode-max-lines 0` lifts the per-file cap (still subject to the global truncation in §2 of `plan.md`).
- Without `--safe-mode`, every safe-mode flag is **ignored** with a one-line stderr warning so users do not silently think masking is on.

### 6.4 Acceptance

- A diff that includes a `.env` change is fully excluded from what the model sees (verified by inspecting the request body in a dry-run mode or via a local proxy).
- A diff that includes a 600-line file is trimmed to 200 lines (or whatever the policy says) with a "truncated" notice in the prompt.
- Adding `--safe-mode-add-regex 'INTERNAL_[A-Z_]+='` masks `INTERNAL_FOO=bar` without disabling any default regex.
- Running with `--safe-mode` prints the one-line policy banner to stderr (§2 "Logging of policy in effect").

---

## 7. Phased Plan

Each phase = **one logical change = one commit** (`.cursorrules` §6). Conventional Commits prefix; bonus commits use `feat(bonus):` / `docs(bonus):` so the scope is unambiguous in `git log`.

### Phase B0 — Branch off & docs

- Branch off `bonus` from the deployed core.
- Add this file as `docs/bonus_plan.md`.
- Commit: `docs(bonus): plan bonus tasks (real pr, conventions, advanced safe mode)`

### Phase B1 — Config loader

- Add `src/ai_gitgen/config.py` with `AppConfig`, TOML parsing via `tomllib`, optional YAML via `PyYAML`.
- Wire `--config` / `--no-config` flags in `cli.py`; default lookup is `./.ai-gitgen.toml` then `./.ai-gitgen.yml`.
- `tests/test_config.py` covers: missing file → defaults; TOML round-trip; YAML round-trip (skipped if `PyYAML` absent); precedence with CLI overrides.
- Commit: `feat(bonus): load .ai-gitgen.toml/yml for conventions and safe mode`

### Phase B2 — Conventions

- Refactor `prompts.py` to expose `CONVENTIONS: dict[str, ConventionTemplate]` + `build_commit(convention, ...)` / `build_pr(convention, ...)`.
- Implement the four shipped conventions in §5.1.
- Add `--convention` to both subparsers; resolution order: CLI > config > built-in default `conventional`.
- `tests/test_conventions.py` covers prefix shape per convention and custom-template overrides via config.
- Commit: `feat(bonus): add commit/pr convention templates with --convention`

### Phase B3 — Advanced safe mode

- Refactor `safe_mode.py` to consume `SafeModePolicy`; add the default policy described in §6.1.
- Extend `git_io.collect()` to apply include/exclude globs and per-file line caps.
- Add `--safe-mode-add-regex` / `--safe-mode-exclude` / `--safe-mode-max-lines` flags.
- Add `render.policy_banner(policy)`; print it whenever `--safe-mode` is on.
- `tests/test_safe_mode_policy.py` covers default policy, regex append, glob exclusion, line cap with notice.
- Commit: `feat(bonus): configurable safe mode with regex, glob, and line policies`

### Phase B4 — Real PR run

- Run the real PR workflow in §4 against a prior-mission repo; capture raw drafts and final text.
- Add `docs/real_pr.md` with the PR URL, the 5–10 line "AI draft → final PR" reflection, and the one takeaway sentence.
- Commit (in this repo): `docs(bonus): document real pr run with ai draft comparison`

### Phase B5 — README sync

- Append a "Bonus Features" section to `README.md` covering: config file location and example, convention list with the before/after generation comparison from §5.4, safe-mode policy table from §6.1, and a link to `docs/real_pr.md`.
- Commit: `docs(bonus): document conventions, advanced safe mode, and real pr link`

---

## 8. Verification Strategy

Same posture as `plan.md` §7 (automated `unittest` for pure logic + a manual checklist for shell / network surfaces). New checks layered on top of the core checklist:

Automated (`python3 -m unittest discover -s tests -v`):

- `test_config`: defaults when no file present · TOML key precedence · CLI overrides config · `--no-config` skips file even when present · YAML skipped cleanly without `PyYAML`.
- `test_conventions`: each built-in convention produces an output whose subject matches its expected prefix shape; custom template from a fake config wins over built-ins; missing placeholders in a custom template are filled with empty strings (no `KeyError`).
- `test_safe_mode_policy`: default policy + CLI flag → combined regex list; exclude glob removes whole file; `max_lines_per_file=10` trims and emits notice; `--safe-mode` off → flags ignored with stderr warning.

Manual checklist:

- [ ] **Conventions**: `--convention gitmoji` on a small change → subject starts with an emoji shortcode; polish still accepts it.
- [ ] **Custom convention**: a `[conventions.team]` block in `.ai-gitgen.toml` actually changes the subject style on the same diff.
- [ ] **Convention precedence**: CLI `--convention freeform` overrides a config that says `convention = "scoped"`.
- [ ] **Safe mode default**: `--safe-mode` on a diff containing `MY_API_KEY=xxxxx` and `user@example.com` → both replaced in the request body.
- [ ] **Safe mode include / exclude**: `.env.local` change is dropped entirely when `exclude_globs` matches it (verify with dry-run / proxy).
- [ ] **Safe mode line cap**: a 1 000-line file diff with `max_lines_per_file = 100` → prompt sees first 100 lines + truncation notice; PR draft does not reference content from the dropped tail.
- [ ] **Policy banner**: `--safe-mode` prints `Safe mode: N regexes, K exclude globs, max L lines/file` to stderr, never stdout.
- [ ] **Real PR**: `docs/real_pr.md` contains a working PR URL and a reflection between 5 and 10 lines.
- [ ] **Regressions**: every checklist item in `plan.md` §7 still passes; running with no config file and no convention flag is byte-identical to core output for the same diff (modulo model nondeterminism).

---

## 9. Risks / Open Points

| Risk | Mitigation |
| ---- | ---------- |
| Adding YAML pulls in a runtime dep | TOML is primary; YAML branch is guarded by `try: import yaml`; README documents both with TOML as default |
| Convention authors break polish rules in a custom template | Validate templates at load time: enforce presence of `## Why / ## What / ## How to Test` literals in `pr_user_template`; fail fast with a clear error |
| Regex list grows unbounded via repeated `--safe-mode-add-regex` | Deduplicate after parsing; cap at 50 regexes with a stderr warning if exceeded |
| Real PR target repo is private or external | Limit examples to public course-mission repos owned by the learner; mention this in README |
| Safe-mode policy disagrees between CLI and config | Document precedence (CLI ADDS to config; only `convention` and scalar fields **override**) directly in `--help` output and README |
| Confusion between core `--safe-mode` and bonus safe-mode flags | All bonus flags carry the `--safe-mode-` prefix; running any of them without `--safe-mode` itself prints a warning |
| Bonus commits leak into a `main` rebase that grading uses | Bonus work lives on the `bonus` branch; the README "Bonus Features" section is the only signal on `main` until merged intentionally |
| YAML parser absent on reviewer machine | TOML fallback always works on Python 3.11+; for 3.10 with YAML-only config, error message instructs the reviewer to either install `PyYAML` or convert the file to TOML (one-line equivalence shown in README) |

---

## 10. Definition of Done

- A `.ai-gitgen.toml` at the project root configures the default convention and the safe-mode policy; `--config` / `--convention` / `--no-config` CLI flags override it as documented; with no file present, the tool behaves byte-identically to the core build.
- Four built-in conventions (`conventional`, `gitmoji`, `scoped`, `freeform`) all pass `polish.enforce_commit` / `polish.enforce_pr`; one custom convention defined in a config file produces a visibly different subject style in the README before/after comparison.
- Advanced safe mode supports configurable regex list, include / exclude globs, and per-file line cap; the policy banner is printed to stderr whenever `--safe-mode` is on; CLI flags compose additively with the config policy.
- `docs/real_pr.md` exists in this repo with a working PR URL, a 5–10 line "AI draft → final PR edits" reflection, and one takeaway sentence; the README "Bonus Features" section links to it.
- All bonus tests (`tests/test_config.py`, `tests/test_conventions.py`, `tests/test_safe_mode_policy.py`) pass under `python3 -m unittest discover -s tests -v` with stdlib only; the YAML branch is skipped cleanly when `PyYAML` is absent.
- No new third-party runtime dependencies beyond an **optional** `PyYAML`; the tool still runs end-to-end with only the standard library.
- All core flows from `plan.md` §9 still pass on the bonus branch; running with no config and no convention flag does not change exit codes, error messages, or stdout / stderr separation.
