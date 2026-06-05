# Phase 1 — Git Capture & "No Changes" Path

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 1
> Subject reference: [`docs/subject.md`](../subject.md) §4.1

This phase implements the **first stage of the pipeline**: turning the working directory's Git state into a `GitSnapshot` value object that downstream stages (prompt builders, polish, render) can consume without touching `subprocess`. It also handles the **"no changes" early exit** end-to-end so a reviewer can already run `python -m ai_gitgen commit` on a clean repo and see the documented message.

---

## 1. Goal

- Implement `git_io.collect()` so it returns a populated `GitSnapshot(status, diff, files, empty)` for a normal repo, or sets `empty=True` when there is nothing to summarize.
- Implement `git_io.truncate(diff, limit)` returning `(truncated_diff, was_truncated)` per `plan.md` §2 (8 000-char cap, per-file head fallback).
- Wire the "no changes" branch into `cli.py`: `git_io.collect()` → if `empty` → `render.no_changes()` → exit `0`.
- Add a minimal `render.no_changes()` so the message lives where all stdout writes will eventually live (`plan.md` §3 SRP).
- Surface non-repo CWD and other git failures as a clear stderr message with exit code `3`.
- Cover the module with `unittest` tests that build tmp git repos on the fly (no network, no time dep — `.cursorrules` §6).

---

## 2. Scope (In / Out)

**In scope**
- `src/ai_gitgen/git_io.py`: `GitSnapshot` dataclass, `collect()`, `truncate()`, an internal `_run_git()` helper.
- `src/ai_gitgen/render.py`: only `no_changes()` and `error(msg)`; full commit/PR rendering is Phase 4.
- `cli.py`: replace the `commit` stub with a real flow that runs `collect()` and either prints "no changes" + exits `0` **or** prints `not implemented yet (post-collect)` and exits `2` (so Phase 2 has a clear seam).
- `tests/helpers.py`: real `make_tmp_repo(tmp_path)` factory that runs `git init`, sets `user.email` / `user.name` (so commits are possible), and returns the path.
- `tests/test_git_io.py`: empty repo, staged-only, unstaged-only, staged + unstaged, truncation at boundary, non-git CWD raises.

**Out of scope**
- Any HTTP / prompt / polish / safe-mode logic.
- `pr` subcommand wiring — still stub-fails; Phase 2 introduces the AI client and pr will be wired alongside commit at that point. (Or wire pr to the same `collect()` + "not implemented yet" message — see §3.4.)
- Final terminal layout (separators, headers) — Phase 4.

---

## 3. Tasks

### 3.1 `git_io.GitSnapshot`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class GitSnapshot:
    status: str       # raw `git status --porcelain` text
    diff: str         # concatenated staged + unstaged diff (see 3.2)
    files: tuple[str, ...]  # changed paths parsed from `status`
    empty: bool       # True iff status is empty AND diff is empty
```

- Frozen so downstream code cannot mutate a captured snapshot.
- `files` is a tuple (immutable) parsed from the first 3-char status codes in `status`.

### 3.2 `git_io.collect()`

- Call `git rev-parse --is-inside-work-tree` first. Non-zero → raise `GitError("Not a git repository (run from a git-initialized project root).")`.
- Run three commands via an internal `_run_git(args)` helper (always `argv` list, never `shell=True`; capture stdout + stderr; timeout 10s):
  - `git status --porcelain`
  - `git diff --cached` (staged)
  - `git diff HEAD` (working tree vs HEAD; falls back to `git diff` if HEAD does not exist yet, i.e. fresh repo with no commits — handle the "unknown revision HEAD" exit code by re-running `git diff`).
- Concatenate diffs with headers so the model knows which is which:

```
===== staged (git diff --cached) =====
<staged diff or "(none)">

===== unstaged (git diff HEAD) =====
<unstaged diff or "(none)">
```

- `empty = (status.strip() == "" and staged_diff.strip() == "" and unstaged_diff.strip() == "")`.
- Parse `files` from the porcelain status by taking columns 4+ of each non-empty line, deduplicated, preserving insertion order.

### 3.3 `git_io.truncate(diff, limit)`

- If `len(diff) <= limit` → return `(diff, False)`.
- Else: split on the file-section markers `git diff` produces (`diff --git a/... b/...`). For each section, keep at most `limit // max(1, num_sections)` characters of its head, separated by `\n... (truncated) ...\n`.
- Always append a final notice line `\n--- DIFF TRUNCATED at <limit> chars ---\n` so the prompt builder can disclose it.
- Return `(joined_truncated_diff, True)`.

### 3.4 `cli.py` integration

- Import `git_io`, `render`, exit-code constants.
- Replace `_handle_commit(args)`:

```python
def _handle_commit(args) -> int:
    try:
        snapshot = git_io.collect()
    except git_io.GitError as e:
        render.error(str(e))
        return EXIT_GIT
    if snapshot.empty:
        render.no_changes()
        return EXIT_OK
    # Phase 2 takes over from here.
    print("not implemented yet (post-collect)", file=sys.stderr)
    return EXIT_USAGE
```

- Apply the same body to `_handle_pr(args)` so both subcommands already short-circuit on a clean repo.
- `git_io.GitError` is a new exception class defined in `git_io.py` (single-purpose; do not reuse `RuntimeError`).

### 3.5 `render.no_changes()` and `render.error(msg)`

- `no_changes()` → `sys.stdout.write("No changes detected.\n")`. No separators yet; Phase 4 owns final layout.
- `error(msg)` → `sys.stderr.write(msg.rstrip() + "\n")`. Single-purpose; both phases reuse it.

### 3.6 `tests/helpers.py` — `make_tmp_repo`

- `def make_tmp_repo(tmp_path) -> pathlib.Path:`
  - `subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)`
  - Configure `user.email` and `user.name` via `git config --local` so commits in tests succeed.
  - Return `tmp_path`.
- Add a small helper `commit_file(repo, name, content, message)` that writes a file, `git add`, `git commit -m`.

### 3.7 `tests/test_git_io.py`

Each test uses `tempfile.TemporaryDirectory` and `helpers.make_tmp_repo`, then changes cwd via `unittest`-style `os.chdir` inside a `try/finally`, so no test leaks cwd.

- `test_empty_repo_is_empty`: fresh repo, no files → `collect().empty is True`, `files == ()`.
- `test_staged_only`: write & `git add` a file (no commit) → `collect().empty is False`, file appears in `files`, diff contains `+content`.
- `test_unstaged_only`: commit a file, modify it without staging → `collect().diff` contains the change in the unstaged section.
- `test_staged_and_unstaged`: stage one file, modify another → both sections populated, both files in `files`.
- `test_non_git_cwd_raises`: `os.chdir` to a non-repo tmp dir → `collect()` raises `GitError`.
- `test_truncate_below_limit_is_noop`: `truncate("abc", 100) == ("abc", False)`.
- `test_truncate_above_limit_marks_truncated`: input > limit → returned string contains `DIFF TRUNCATED at` and second tuple element is `True`.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `src/ai_gitgen/git_io.py` | implement (`GitSnapshot`, `GitError`, `collect`, `truncate`, `_run_git`) |
| `src/ai_gitgen/render.py` | implement minimal `no_changes`, `error` |
| `src/ai_gitgen/cli.py` | edit handlers to call `collect()` and short-circuit on empty |
| `tests/helpers.py` | implement `make_tmp_repo`, `commit_file` |
| `tests/test_git_io.py` | create (six scenarios above) |

---

## 5. Acceptance Criteria

- [ ] In a freshly `git init`'d directory with no files: `python -m ai_gitgen commit` prints `No changes detected.` to stdout and exits `0`.
- [ ] Same on `python -m ai_gitgen pr`.
- [ ] In a non-git directory: `python -m ai_gitgen commit` writes a single error line to stderr ("Not a git repository ...") and exits `3`.
- [ ] In a repo with a staged change: `python -m ai_gitgen commit` writes `not implemented yet (post-collect)` to stderr and exits `2`. (Phase 2 will replace this branch.)
- [ ] `python3 -m unittest discover -s tests -v` is green; tests do not leak cwd; tests do not require network or a real `~/.gitconfig`.
- [ ] No `print()` calls outside `render.py` and `cli.py` (`rg "\bprint\(" src/ai_gitgen/git_io.py` returns nothing).
- [ ] `git_io.py` does not import from `urllib`, `json`, or `ai_client` — `rg "(urllib|json|ai_client)" src/ai_gitgen/git_io.py` returns nothing.

---

## 6. Commit

```
feat: collect git status and diff with no-change detection
```

---

## 7. Risks / Notes

- `git diff HEAD` fails on a repo with **zero commits** because `HEAD` doesn't resolve. Detect this and fall back to `git diff` (working tree vs index) so the very first commit's pre-commit run still works. Cover this with `test_staged_only` (it uses a no-commit repo).
- `subprocess.run` must always use `argv` lists and `check=False`; inspect `returncode` explicitly so platform-specific shell quoting does not interfere (`plan.md` §8 risks).
- Keep `_run_git` private (`_` prefix). The public surface of `git_io` is only `collect`, `truncate`, `GitSnapshot`, `GitError`.
- Do not start truncating in this phase's `collect()` — `truncate()` is a **separate** function called by `prompts.build_*` in Phase 2. Mixing the two would couple capture with prompt budgeting.
- The "(none)" placeholder in the diff is read by humans, not the model — Phase 2's prompt strips empty sections when building the user message.

---

## 8. Definition of Done

- Git capture works on a real repo and surfaces a clear error on a non-repo.
- The "no changes" path is observable end-to-end with the documented exit code.
- All six `test_git_io.py` cases pass.
- Phase 2 can implement `ai_client.complete()` and `prompts.build_*` by editing existing empty modules and calling into `git_io.collect()` / `git_io.truncate()` without reshaping them.
