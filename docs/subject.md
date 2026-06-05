# AI API Integration & Git Commit/PR Auto-Generation CLI Mission

---

## 1. Mission Overview

“AI API integration” sounds big, but the core is **what input you give**. Pass `git diff` and design **prompts** so you get meaningful **commit messages** and **PR descriptions**. This mission is about **controlling AI output quality**, not just calling an API.

An AI API lets your app call an external model for text generation—support replies, summaries, dev log drafts, etc.—as **input → generated output**.

You build a **Python CLI** that calls an AI API, takes Git changes as input, and auto-generates **commit messages** and **PR description drafts**. Tune API parameters and context (commit/PR format, change rationale) for the quality you want. Wire Git command output into the program and apply results to real commit/PR workflows in one **integration · validation · automation** flow.

---

## 2. Final Deliverable

Complete the following **three deliverables**.

### 2.1 AI API Integration & Automation Flow

| Part | Description |
|------|-------------|
| **Input** | Set API key via **environment variable**, run commit/PR CLI from project root |
| **Output** | Collect `git status`, `git diff` → AI call → change summary, commit message, PR draft printed in **terminal**. **Single run** verifies end-to-end |

### 2.2 GitHub Repository

- Create GitHub repo, **push** project source
- Code, structure, commits, and branches reviewable

### 2.3 User Guide (`README.md`)

- Install, env vars (API key), run examples, sample output, ops notes → **runnable from docs alone**

---

## 3. Learning Objectives

After completing this assignment, learners should be able to explain the following on their own.

1. End-to-end **REST** AI API flow: request, response handling, exceptions.
2. How `temperature`, `max_tokens`, etc. affect **output quality**.
3. Wiring `git status` and `git diff` into the program and the **automation flow**.
4. Building **prompts** with commit/PR format and change **context** for on-spec summaries.
5. Why and how to **validate and polish** generated text for length and templates.

---

## 4. Functional Requirements

You must satisfy **all** of the following.

### 4.1 Collect Git Changes

| Item | Requirement |
|------|-------------|
| **Location** | Run CLI from **Git-initialized project root** |
| **Collect** | Changed files from `git status`, diff text from `git diff` |
| **No changes** | Message like “No changes” and exit |

### 4.2 AI API Integration

| Item | Requirement |
|------|-------------|
| **Key** | Environment variable; **no** hardcoding in code |
| **Output** | Commit message or PR draft to **terminal** after call |
| **Failure** | Message **including cause** on network/auth errors |
| **Parameters** | Model, `temperature`, `max_tokens`, etc. changeable via **CLI options** (e.g. `-model`, `-temperature`, `-max-tokens`, with defaults) |

### 4.3 Auto-Generate Commit Message

| Item | Requirement |
|------|-------------|
| **Command** | e.g. `commit` generates and prints commit message |
| **Content** | Based on change summary |
| **Subject** | **One line** required |
| **Body** | Optional (your choice) |
| **Body quality (if included)** | At least **one** of: mention **1–3** changed files/modules; **1–2** bullet core changes |
| **Apply** | Terminal output → user can **copy and use** |

### 4.4 Auto-Generate PR Title & Body

| Item | Requirement |
|------|-------------|
| **Command** | Command exists for PR draft |
| **Body sections** | **Why**, **What**, **How to Test** — with **headers** |
| **Bullets** | At least **one** bullet per section |
| **Title** | **One line**, viewable with body in terminal |

### 4.5 Output Validation & Polish

Apply length/format rules below to generated text (**regenerate or post-process**, pick one).

| Target | Rule |
|--------|------|
| Commit subject | **≤50 chars recommended** (max 72) |
| PR title | Max **80** chars |
| PR body | Why/What/How to Test **required** + min **1 bullet** each |

- Final output with clear **separators/headers**

### 4.6 Repository & Documentation

| Item | Requirement |
|------|-------------|
| **GitHub** | **push** deliverable |
| **README** | Install/run, env vars, commit/PR command examples, **sample output** |
| **Ops** | At least **one** of: secrets/masking/safe mode / cost, rate limits, recommended usage |

---

## 5. Bonus (Optional)

### Complete One Real PR on a Repository

1. Pick **one** GitHub repo from a prior mission  
2. Meaningful changes on a branch  
3. Use this tool for **one commit message + one PR draft**, then open the real PR  

**Submit**: PR link + **5–10 lines** on “AI draft → final PR” edits

### Customize Commit/PR Templates

- Analyze repo style → define **team convention** (e.g. `feat/fix/docs`, scope, PR template)
- Reflect in tool: `.ai-gitgen.yml`, `--convention`, prompt template swap, etc. (**one+**)

**Submit**: Convention doc (README section) + **one** before/after generation comparison

### Advanced Safe Mode

- With `--safe-mode`, extend masking (regex) or limit diff sent (by file/lines); **configurable policy**
