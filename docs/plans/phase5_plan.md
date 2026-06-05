# Phase 5 — README & GitHub Push

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 5
> Subject reference: [`docs/subject.md`](../subject.md) §2.2, §2.3, §4.6

This is the **last core phase**. Code is feature-complete; this phase makes the project reviewable from the docs alone, then pushes it to GitHub. After Phase 5 the project meets all three deliverables in subject §2 (integration & automation flow / GitHub repo / README).

---

## 1. Goal

- Write `README.md` so a reviewer can install, set `OPENAI_API_KEY`, and reproduce both commands with **real sample output** from the docs alone (subject §2.3).
- Document the ops note (secrets masking via `--safe-mode`) and the cost / rate-limit guidance (subject §4.6).
- Include a **subject-mapping table** so a grader sees at a glance which §§ are covered where (mirrors the pattern in `04-1.my_project/README.md` per repo convention).
- Create the GitHub repository, push the project, and verify both commands work on a fresh clone after `export OPENAI_API_KEY=…`.

---

## 2. Scope (In / Out)

**In scope**
- `06-2/README.md` (single new file owning the whole user guide).
- Optional `.gitignore` additions if any test artifact ends up in the worktree (none expected — tests use `tempfile`).
- GitHub repo creation (`gh repo create` or web UI), remote add, initial push.
- A final manual end-to-end pass on a fresh clone.

**Out of scope**
- Any code change — if Phase 5 needs to edit `src/` or `tests/`, the fix belongs to the earlier phase that owns it.
- The bonus PR run / convention layer / advanced safe mode — those live in `bonus_plan.md` and are pushed as separate commits after Phase 5.
- CI configuration (GitHub Actions) — not required by subject §2.

---

## 3. Tasks

### 3.1 `README.md` outline

The README must be self-sufficient — a reviewer with no prior context should run the commands and see the same shape of output. Recommended section order:

1. **Overview** (2–4 lines): what the tool does, why it exists.
2. **Requirements**: Python 3.10+, Git on PATH, a network-reachable OpenAI account.
3. **Install**:
   - Quick path: `python -m ai_gitgen` works directly from a clone — no install step.
   - Optional path: `pip install -e .` exposes the `aigit` script.
4. **Environment**: `export OPENAI_API_KEY=sk-…`; one-line warning that the key is never logged.
5. **Commands**:
   - `python -m ai_gitgen commit [--model M] [--temperature T] [--max-tokens N] [--safe-mode]`
   - `python -m ai_gitgen pr     [--model M] [--temperature T] [--max-tokens N] [--safe-mode]`
6. **Sample output**: paste **real** stdout from a small change in this repo for both subcommands, framed exactly as `render.commit` / `render.pr` produced it.
7. **Options table**: flag, default, description, applies-to.
8. **Exit codes table**: `0` ok, `2` usage, `3` git, `4` ai, `5` env (matches `plan.md` §2).
9. **Ops notes** (subject §4.6):
   - Secrets masking: `--safe-mode` and the four shapes it covers.
   - Cost guidance: rough token cost on `gpt-4o-mini`, one-retry cap, 8 000-char diff cap.
   - Rate limits: behavior on HTTP 429 (no auto-retry; exit `4` with the cause line).
10. **Subject mapping**: a table that points every subject §§ to the code/doc that satisfies it.
11. **Development**: how to run the test suite (`python3 -m unittest discover -s tests -v`), no third-party tooling required.
12. **License / Author**: minimal.

### 3.2 Sample-output authoring rule

Sample blocks must be **reproducible**:

- Use a tiny seed change (e.g. `echo "note" >> README.md`) right before generating each sample so the diff is small and the output is short.
- Capture stdout verbatim — do not hand-edit the model's wording.
- If you regenerate later, the wording will drift; that's acceptable. The framing (separators, headers, section labels) must match Phase 4 exactly.

### 3.3 Options table (minimum content)

| Flag | Default | Description | Subcommands |
| ---- | ------- | ----------- | ----------- |
| `--model` | `gpt-4o-mini` | OpenAI chat completion model id | `commit`, `pr` |
| `--temperature` | `0.2` | Sampling temperature `[0.0, 2.0]` | `commit`, `pr` |
| `--max-tokens` | `400` (`commit`) / `700` (`pr`) | Upper bound on response tokens | `commit`, `pr` |
| `--safe-mode` | off | Mask emails / AWS keys / `*_KEY=…`/`*_TOKEN=…` / `sk-…` in the diff before sending | `commit`, `pr` |

### 3.4 Subject mapping table (minimum content)

| Subject § | Requirement | Implementation |
| --------- | ----------- | -------------- |
| §2.1 | Integration & automation flow | `src/ai_gitgen/cli.py` `_run_subcommand` pipeline |
| §2.2 | GitHub repo | This repository, pushed in Phase 5 |
| §2.3 | README runnable from docs alone | This file (`README.md`) |
| §4.1 | Collect changes / "no changes" exit | `git_io.collect`, `render.no_changes` |
| §4.2 | API key via env var; CLI options; cause-bearing failures | `ai_client._load_key`, `cli._add_shared_options`, `AIError` |
| §4.3 | `commit` subcommand: one-line subject + optional body | `prompts.build_commit`, `polish.enforce_commit`, `render.commit` |
| §4.4 | `pr` subcommand: title + Why/What/How sections | `prompts.build_pr`, `polish.enforce_pr`, `render.pr` |
| §4.5 | Output validation: ≤72 subject, ≤80 title, ≥1 bullet per PR section | `polish.enforce_commit`, `polish.enforce_pr`, retry+fallback in `cli._run_subcommand` |
| §4.6 | At least one ops note | `--safe-mode` (`safe_mode.mask`) + cost/rate-limit guidance in README |

### 3.5 GitHub push

1. Create the repo on GitHub (`gh repo create <name> --public --source=. --remote=origin` or via web UI).
2. Ensure `.gitignore` excludes any local artifacts (`.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`).
3. Push: `git push -u origin main`.
4. Open the GitHub page and confirm:
   - `README.md` renders correctly (the framed code blocks display as code).
   - Both sample output blocks are present.
   - The folder structure matches `plan.md` §3.
5. Record the repo URL somewhere visible (top of README, optional).

### 3.6 Fresh-clone verification

On a sibling directory (or another machine):

```
git clone <repo>
cd <repo>/06-2
python -m ai_gitgen commit --help
echo "fresh" >> README.md
export OPENAI_API_KEY=sk-...
python -m ai_gitgen commit
python -m ai_gitgen pr
```

Both runs must produce framed output without modification to any source file.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `06-2/README.md` | create (full user guide, sample outputs, tables) |
| `06-2/.gitignore` | create or edit if needed (`__pycache__/`, `*.pyc`, `.venv/`, `.DS_Score` etc.) |
| GitHub remote | create + push |

---

## 5. Acceptance Criteria

- [ ] `README.md` has all twelve sections in §3.1 above, in that order.
- [ ] **Real sample output** for both `commit` and `pr` is embedded (not pseudo-code, not "expected output").
- [ ] Options table and exit-codes table render correctly on GitHub (no broken pipes / misaligned columns).
- [ ] Ops notes name the four masking shapes, the 8 000-char diff cap, and the no-auto-retry-on-429 policy.
- [ ] Subject-mapping table covers §2.1, §2.2, §2.3, §4.1–§4.6 with at least one code reference each.
- [ ] `git push -u origin main` succeeds; GitHub page renders the README with all code blocks formatted.
- [ ] Fresh-clone walkthrough (§3.6) succeeds without editing any file.
- [ ] No code change in this phase — `git log` shows only the docs commit and (if needed) a tiny `.gitignore` commit.

---

## 6. Commit

```
docs: add readme with install, env, commands, and sample output
```

If `.gitignore` is touched separately, that goes in its own commit:

```
chore: ignore pycache and venv artifacts
```

---

## 7. Risks / Notes

- **Sample-output drift**: model wording is non-deterministic. Capture the sample once at the end of the phase; do not regenerate during reviews. The framing (separators, `## Why` / `## What` / `## How to Test`) is what reviewers grade against, not the prose.
- **Key in screenshots**: when capturing terminal output for the README, **never** paste an actual `sk-…` key. If your shell's history or prompt shows it, scrub it before committing.
- **Markdown collisions**: the framed render blocks contain `=` runs and `##` markers — wrap them in fenced code blocks so GitHub does not interpret `##` as a heading.
- **`pip install -e .` is optional, not required**: the README must show the no-install path first; otherwise reviewers without a venv habit get blocked on tooling.
- **Subject §2.3 "runnable from docs alone"** is the highest-leverage line in this whole phase — every cut you make in the README should be tested against "can a stranger run this without asking me a question?".
- **Bonus stays out of the core README**: bonus content lives in `bonus_plan.md` and (when implemented) appends a separate "Bonus Features" section in a later commit, mirroring the pattern in `06-1/README.md`.

---

## 8. Definition of Done

- The three deliverables in subject §2 are visibly satisfied: code is on GitHub, both commands work end-to-end, and the README walks a stranger through install → env var → command → sample output.
- All `plan.md` §9 Definition-of-Done items hold: `--help` documents the flags, exit codes are distinct, `## Why` / `## What` / `## How to Test` always have ≥1 bullet, `unittest discover` passes with stdlib only.
- The five learning objectives in subject §3 can each be pointed to in code and explained from the README + plan combination.
- Bonus work (`bonus_plan.md`) can start in a new branch without touching anything Phase 5 produced.
