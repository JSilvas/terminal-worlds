---
tracker: github-issues
repo: JSilvas/terminal-worlds
workspace: ~/.terminal-worlds-agents
agent: claude-code
max_concurrent: 3
labels:
  todo: "todo"
  claimed: "in-progress"
  review: "in-review"
  done: "done"
---

# Terminal Worlds — Agent Workflow

This file defines how background Claude Code agents should operate on this project.
It is modeled on the [Symphony](https://github.com/openai/symphony) orchestration
spec: a central source of truth for agent behavior, proof-of-work requirements, and
team collaboration conventions.

---

## Overview

Agents are dispatched to GitHub Issues. Each issue represents one unit of work.
Issues progress through states via labels:

```
todo → in-progress → [CI gate] → in-review → done
```

A human or orchestrating agent assigns `todo` issues. Background agents claim issues
by flipping the label to `in-progress`. The agent opens a PR, waits for CI, and
self-remediates any failures before flipping to `in-review`. A human then reviews
and merges; GitHub auto-closes the issue.

---

## Agent Lifecycle

### 1. Claim

```bash
# List claimable issues
gh issue list --label todo --json number,title,labels

# Claim the highest-priority (lowest-number) todo issue
gh issue edit <N> --add-label in-progress --remove-label todo
gh issue edit <N> --assignee @me
```

Only claim **one issue at a time**. Do not claim if you cannot complete the work
in this session.

### 2. Workspace

```bash
# Create an isolated workspace
mkdir -p ~/.terminal-worlds-agents/<issue-number>
cd /home/user/terminal-worlds

# Create your branch
git checkout main
git pull origin main
git checkout -b claude/<slug>-<session-id>
```

Each agent works in the main repo checkout on its own branch. Branches are
isolated by git, not by filesystem.

### 3. Implement

- Read the full issue before writing a single line of code
- Consult `CLAUDE.md` for architecture, conventions, and testing guidance
- Write code; write or update tests; run `uv run pytest` until green
- Use small, focused commits — one logical change per commit

### 4. Validate (Proof of Work)

Before opening a PR an agent MUST verify:

- [ ] `uv run pytest tests/ -v` passes with no failures
- [ ] The generated landscape for all 4 biomes completes without Python exceptions
- [ ] No new linting errors introduced (run `uv run ruff check . --select E,F` if ruff available)
- [ ] PR diff is scoped to the issue — no unrelated cleanups

### 5. Submit

```bash
git push -u origin claude/<slug>-<session-id>

# GitHub will pre-fill the body from .github/PULL_REQUEST_TEMPLATE.md
gh pr create --title "<Issue title>" --body-file .github/PULL_REQUEST_TEMPLATE.md
```

**Do not flip to `in-review` yet.** Proceed to step 6.

### 6. Monitor CI and self-remediate

Block until all checks finish (usually 1–2 min):

```bash
gh pr checks --watch
```

CI will post a comment on the PR with the full test output — pass or fail.
The agent must read that comment and act on it before a human ever sees the PR.

**If any check fails:**

```bash
# Reproduce the failure locally first
uv run pytest tests/ -v --tb=short

# Fix, commit, push — CI reruns automatically on each push
git commit -m "fix: ..."
git push

# Confirm green before continuing
gh pr checks --watch
```

Repeat until all checks pass. Only then flip the label:

```bash
gh issue edit <N> --add-label in-review --remove-label in-progress
```

---

## Issue Conventions

Issues must have one of the following labels set by the team before agents can
pick them up:

| Label | Meaning |
|-------|---------|
| `todo` | Ready for an agent to claim |
| `in-progress` | Claimed and being worked on |
| `in-review` | PR open, awaiting CI + human review |
| `done` | Merged and complete |
| `blocked` | Cannot proceed — human input required |
| `enhancement` | New feature |
| `bug` | Regression or defect |
| `harness` | Improvements to test/CI infrastructure |
| `documentation` | Docs-only changes |

Issues without a `todo` label should not be claimed by agents.

### Issue Format Requirements

For an issue to be agent-ready it should include:

1. **Context**: What is the current behavior? Why is this change needed?
2. **Acceptance criteria**: Explicit, testable conditions the PR must satisfy
3. **Out of scope**: What the agent should NOT touch
4. **References**: Links to relevant code (file:line), prior PRs, or discussion

Use the issue templates in `.github/ISSUE_TEMPLATE/` when creating new issues.

---

## Concurrency Rules

- Max **3 agents** running simultaneously
- Each agent works on a **different issue** — no two agents on the same issue
- Agents communicate through **git + GitHub issues only** — no shared memory
- If CI is broken on `main`, all agents should stop and surface the blocker as a
  comment on the blocking PR before continuing with their own work

---

## Human–Agent Collaboration

### What humans do

- Create and prioritize issues (apply `todo` label when ready for agents)
- Review PRs opened by agents
- Resolve `blocked` issues (remove `blocked`, add `todo` when unblocked)
- Merge approved PRs

### What agents do

- Claim `todo` issues and implement them end-to-end
- Open PRs with proof of work (tests passing, visual verification)
- Comment on issues when blocked or when assumptions need confirmation
- Never merge their own PRs

### When agents should ask humans

An agent should leave a comment and add the `blocked` label (removing `in-progress`)
when it encounters any of the following:

- Acceptance criteria are ambiguous or contradictory
- The required change touches architectural decisions not covered in CLAUDE.md
- Tests cannot be made to pass without changes outside the issue's scope
- A dependency upgrade is required that hasn't been approved

---

## Harness Engineering Principles

This project follows harness engineering conventions so that autonomous agents can
work with confidence:

1. **Deterministic tests**: `SmoothNoise(seed)` ensures reproducible outputs.
   Tests that generate landscapes use fixed seeds so they are not flaky.

2. **Isolated side effects**: `generate_landscape` writes to a path argument.
   Tests pass `tmp_path` (pytest fixture) so no test pollutes the filesystem.

3. **Fast feedback**: The full test suite must run in under 60 seconds. Landscape
   generation tests use a reduced resolution or a smoke-test biome to stay fast.

4. **CI as gate**: No PR lands without green CI. This protects `main` from regressions
   that would block other agents.

5. **Collision mask as contract**: The `cols` dict is the public interface between
   rendering stages. Any new stage must read and write this mask correctly.

6. **One function, one job**: Keep rendering stages as standalone functions.
   This makes them individually testable and replaceable.

---

## Roadmap Labels (for team planning)

Use these labels to communicate priority and grouping:

| Label | Description |
|-------|-------------|
| `p0` | Critical — blocks other work or production issue |
| `p1` | High — should be in the next sprint |
| `p2` | Medium — nice to have soon |
| `p3` | Low — backlog |
| `biome` | New or modified biome |
| `fx` | Visual effect improvement |
| `perf` | Performance improvement to generator or pool |
| `platform` | Non-macOS support, terminal compatibility |
