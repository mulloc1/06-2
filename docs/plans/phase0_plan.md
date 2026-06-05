# Phase 0 — Scaffolding & CLI Skeleton

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 0
> Subject reference: [`docs/subject.md`](../subject.md) §4.2

This phase lays the **bare-minimum project skeleton** so every later phase has a stable place to drop code. The package directory exists, `python -m ai_gitgen` resolves, and both subcommands parse their flags — but no real work is done yet. Following `.cursorrules` §4 (Minimal-First / YAGNI), nothing more is added here than what is needed to scaffold.

---

## 1. Goal

- Create the source/test layout exactly as locked in `plan.md` §3.
- Wire `python -m ai_gitgen` so `__main__.py` calls `cli.main()`.
- Build `cli.py` with `argparse` + two subparsers (`commit`, `pr`) that **share** the option set (`--model`, `--temperature`, `--max-tokens`, `--safe-mode`) with defaults pulled from module constants.
- Stub each subcommand handler to print `not implemented yet` to stderr and exit `2`, so the CLI contract is observable without touching git or the network.
- Result: `python -m ai_gitgen commit --help` and `python -m ai_gitgen pr --help` print the documented flag set; no `ImportError`, no `subprocess`, no HTTP.

---

## 2. Scope (In / Out)

**In scope**
- Package directory `src/ai_gitgen/` with empty module stubs for every file listed in `plan.md` §3.
- `pyproject.toml` with package metadata and (optionally) a `console_scripts` entry for `aigit`. Even without an install, `python -m ai_gitgen` must work via `__main__.py`.
- `cli.py`: argparse top-level + subparsers, shared options helper, exit-code constants, stub handlers.
- `tests/` directory with a `helpers.py` placeholder and at least one trivial passing test so `python3 -m unittest discover -s tests -v` produces a green run.

**Out of scope**
- Any `subprocess` / `git` calls — Phase 1.
- Any HTTP / `urllib` / prompt building — Phase 2.
- Any polish / retry logic — Phase 3.
- Safe-mode regexes and final render layout — Phase 4.
- README content — Phase 5.

---

## 3. Tasks

### 3.1 Directory tree

Create exactly this structure under `06-2/`:

```
pyproject.toml
src/
  ai_gitgen/
    __init__.py
    __main__.py
    cli.py
    git_io.py
    ai_client.py
    prompts.py
    polish.py
    safe_mode.py
    render.py
tests/
  helpers.py
  test_cli_skeleton.py
```

`git_io.py` / `ai_client.py` / `prompts.py` / `polish.py` / `safe_mode.py` / `render.py` are created **empty** (or with a single `"""TODO: phase N"""` docstring). Later phases own their contents (.cursorrules §6 mirroring; one phase = one concern).

### 3.2 `src/ai_gitgen/__init__.py`

- Single line: `__version__ = "0.1.0"`.
- No re-exports — keep the import surface small until other modules exist.

### 3.3 `src/ai_gitgen/__main__.py`

- Standard module entry point:

```python
from ai_gitgen.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- `SystemExit` propagates the int exit code returned by `cli.main()`; no `print` here (.cursorrules §5 — `cli` owns I/O).

### 3.4 `src/ai_gitgen/cli.py`

- Module constants for defaults (no magic literals — .cursorrules §3):

```python
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS_COMMIT = 400
DEFAULT_MAX_TOKENS_PR = 700

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GIT = 3
EXIT_AI = 4
EXIT_ENV = 5
```

- One helper `_add_shared_options(subparser, *, default_max_tokens)` adds `--model`, `--temperature`, `--max-tokens`, `--safe-mode` so both subparsers stay in lock-step. (`plan.md` §4.1 "one helper to avoid drift".)
- `main(argv: list[str] | None = None) -> int` builds the parser, dispatches, and returns an int. Stub handlers `_handle_commit(args) -> int` and `_handle_pr(args) -> int` write `"not implemented yet"` to **stderr** and return `EXIT_USAGE` (2).
- Type hint every public signature; one-line docstring on `main()` (.cursorrules §5).

### 3.5 `pyproject.toml`

- `[project]` block with name `ai-gitgen`, version `0.1.0`, Python `>=3.10` (`plan.md` §2 locked decision).
- `[project.scripts]` optionally exposes `aigit = "ai_gitgen.cli:main"` — keep it commented out if you don't want to require `pip install -e .` for review.
- **No runtime dependencies** — stdlib only (`plan.md` §2 dependency policy).

### 3.6 `tests/helpers.py`

- Placeholder module: a `sys.path` shim so tests can import `ai_gitgen` without an install, plus a function stub `def make_tmp_repo(tmp_path): ...` left as `raise NotImplementedError` (real body lands in Phase 1).

```python
import sys, pathlib

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
```

### 3.7 `tests/test_cli_skeleton.py`

One trivial-but-real test that exercises the parser without invoking any handler I/O:

- `test_top_level_help_lists_subcommands`: `cli.main(["--help"])` raises `SystemExit(0)` (argparse default). Capture stderr/stdout via `contextlib.redirect_stdout`.
- `test_commit_help_lists_shared_options`: `cli.main(["commit", "--help"])` raises `SystemExit(0)` and the captured help text contains `--model`, `--temperature`, `--max-tokens`, `--safe-mode`.
- `test_unknown_subcommand_exits_2`: `cli.main(["nope"])` raises `SystemExit(2)`.

Use `unittest.TestCase`; no pytest features (.cursorrules §6 stdlib test runner).

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `pyproject.toml` | create (metadata, py>=3.10, no runtime deps) |
| `src/ai_gitgen/__init__.py` | create (`__version__`) |
| `src/ai_gitgen/__main__.py` | create (calls `cli.main`) |
| `src/ai_gitgen/cli.py` | create (argparse + stub handlers) |
| `src/ai_gitgen/git_io.py` | create (empty docstring) |
| `src/ai_gitgen/ai_client.py` | create (empty docstring) |
| `src/ai_gitgen/prompts.py` | create (empty docstring) |
| `src/ai_gitgen/polish.py` | create (empty docstring) |
| `src/ai_gitgen/safe_mode.py` | create (empty docstring) |
| `src/ai_gitgen/render.py` | create (empty docstring) |
| `tests/helpers.py` | create (`sys.path` shim) |
| `tests/test_cli_skeleton.py` | create (parser smoke tests) |

---

## 5. Acceptance Criteria

- [ ] `python -m ai_gitgen --help` exits `0` and prints both `commit` and `pr` in the subcommand list.
- [ ] `python -m ai_gitgen commit --help` exits `0` and the help text mentions `--model`, `--temperature`, `--max-tokens`, `--safe-mode`.
- [ ] `python -m ai_gitgen pr --help` likewise.
- [ ] `python -m ai_gitgen commit` writes `not implemented yet` to **stderr** and exits `2`.
- [ ] `python -m ai_gitgen nope` exits `2` (argparse usage error).
- [ ] `python3 -m unittest discover -s tests -v` runs `tests/test_cli_skeleton.py` to green.
- [ ] No import of `subprocess`, `urllib`, or `json` anywhere in `src/ai_gitgen/` yet — verify with `rg "import (subprocess|urllib|json)" src/ai_gitgen/`.
- [ ] No third-party imports anywhere — verify with `rg "^(from |import )(click|typer|requests|httpx|rich|colorama)" src/`.

---

## 6. Commit

```
chore: scaffold ai_gitgen package and argparse subcommands
```

One commit covers the whole scaffold per `.cursorrules` §6 Logical Commit Unit.

---

## 7. Risks / Notes

- Resist adding any real logic to `git_io.py` / `ai_client.py` here — the whole point of Phase 0 is that later phases edit existing files instead of creating structure.
- Defaults live as module constants in `cli.py`, not as literal arguments to `add_argument`. Phase 2/3 will read them from the same constants so a single edit retunes the CLI (.cursorrules §3 — no magic literals).
- `pyproject.toml` is included now so `pip install -e .` works for reviewers who want the `aigit` script later; keeping it out would force every later phase to bolt it on.
- The `sys.path` shim in `tests/helpers.py` is deliberately the only test-only knowledge of the `src/` layout, so tests stay portable if we later switch to an installed package.

---

## 8. Definition of Done

- All files in `plan.md` §3 directory tree exist.
- `python -m ai_gitgen` resolves to `cli.main()` without import errors.
- Both subcommands parse their full option set and stub-fail with the documented exit code.
- `unittest discover` is green; no network, no `subprocess`, no time dependency in tests.
- Phase 1 can implement `git_io.collect()` by editing the existing empty module.
