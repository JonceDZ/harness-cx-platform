# Weni Agent Development Harness — Usage Guide

A disk-backed, multi-agent harness for building Weni AI agents inside Cursor. The
main session acts as the orchestrator (configured by the root `AGENTS.md`) and
dispatches five specialized subagents through a sequential, gated pipeline. Run
state persists on disk so work survives across sessions.

## How it works

```
You  <->  Orchestrator (main session, AGENTS.md, your chosen model)
              |
              |  one phase at a time, passing only the RUN_DIR
              v
   planner → implementer → tester → reviewer → docs-writer
              |
              v
   .cursor/runs/<run-id>/  (STATE.md + artifacts/ + logs/)
```

- STATE.md is a live snapshot, rewritten whole on each update (never a log).
- artifacts/ holds one immutable file per phase. Downstream agents read upstream
  artifacts from disk instead of re-pasting content, keeping context small.
- Deterministic Python scripts handle run setup, state, schema validation, and the
  eval run, so mechanical work consumes no model tokens.

## Layout

```
AGENTS.md                          # orchestrator instructions (main session)
.cursor/
  agents/                          # the 5 subagents
    planner.md  implementer.md  tester.md  reviewer.md  docs-writer.md
  skills/weni-agents/
    SKILL.md  constitution.md  HARNESS.md
  scripts/                         # deterministic, token-free layer
    bootstrap_env.py  init_run.py  update_state.py  validate_schema.py  run_eval.py
    _common.py
  templates/STATE.template.md
  runs/<run-id>/STATE.md, artifacts/, logs/
agents/                            # one folder per collaborator agent
  <slug>/                          # generated agent code (isolated from harness)
    agent_definition.yaml  requirements.txt  agent_evaluation.yml  README.md
    tools/<tool_name>/main.py, requirements.txt, test_definition.yaml, .env, .globals
```

Each collaborator lives in its own `agents/<slug>/` folder at the same level as
`.cursor` so its code stays separate from the harness config and from other
collaborators. A project with a single agent just has one folder. The repo tracks
everything, but you push one collaborator at a time by running
`weni project push agent_definition.yaml` from inside `agents/<slug>/`. Every run
targets one collaborator (`--target <slug>`, auto-detected when there is only one).

## Getting started

1. Open the project in Cursor and pick the orchestrator model in the model picker
   (Claude Sonnet 4.6 is a good cost-effective default).
2. Tell the orchestrator what agent you want to build. It will:
   - create or resume a run,
   - bootstrap `.venv` and `weni-cli`, and probe authentication,
   - run the planner (which asks you any missing questions),
   - implement, validate, test, review, and document.
3. The first time only, when prompted, authenticate once in your terminal:
   ```bash
   source .venv/bin/activate
   weni login
   ```
   The token is stored in `~/.weni_cli` and reused on later runs.

## Phases and gates

| Phase | Subagent | Gate to advance |
|-------|----------|-----------------|
| 0 Intake | orchestrator | Requirements captured |
| 1 Plan | planner | User approves the plan |
| 2 Implement | implementer | `validate_schema.py` -> `SCHEMA_VALID` |
| 3 Test | tester | User confirms + `run_eval.py` -> `EVAL_PASS` |
| 4 Review | reviewer | Verdict `APPROVE` (read-only) |
| 5 Docs | docs-writer | `agents/<slug>/README.md` written (with mermaid sequence diagram) |

The pipeline stops at Docs. It never deploys (`weni project push`).

Each collaborator README is lean (purpose, sequence diagram, tools, configuration,
external integrations) and always includes a mermaid `sequenceDiagram` of its
logic/API flow. The project-level root README is generated only on demand: the
orchestrator collects project context and the docs-writer auto-fills it, leaving a
mermaid `flowchart` placeholder for you to draw the high-level journey.

## Resuming

At the start of any session the orchestrator runs
`init_run.py --latest-open`. If an unfinished run exists, it reads that run's
STATE.md and continues from the first phase that is `pending` or `in-progress`.

## Models

The orchestrator model is your choice (model picker). Subagent models are set per
file: the planner uses Opus (high-leverage reasoning), implementer, tester, and
reviewer use Composer 2.5 (fast coding and tool use), docs-writer uses Gemini 3
Flash (low-cost documentation). Adjust the `model` field in each
`.cursor/agents/*.md` if your plan exposes different model IDs.

## Conventions

- Everything generated is in English, including the agent's end-user messages,
  unless you explicitly ask otherwise.
- Per-tool dependency file is `requirements.txt`.
- Secrets for local tests live in git-ignored `agents/<slug>/tools/<tool>/.env` and `.globals`.
