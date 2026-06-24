# Weni Agent Development Harness

A Cursor-based harness for building [Weni AI agents](https://weni.ai) through a gated, multi-phase pipeline. One main chat session (the orchestrator) coordinates specialized subagents; run state and artifacts persist on disk so work survives across sessions.

A project can hold one or many **collaborator agents**. Each collaborator is an independent deploy unit with its own `agent_definition.yaml`, living in `agents/<slug>/`. Every run targets one collaborator (`--target <slug>`), so the same harness handles a single agent and a multi-collaborator project the same way.

## Quick start

1. **Copy the harness into your project root** (or start from this repo):

   ```
   your-project/
   ├── AGENTS.md          ← orchestrator instructions (main Cursor chat)
   ├── .gitignore         ← ignores .venv, secrets, run logs
   └── .cursor/
       ├── agents/        ← subagent briefs (planner, implementer, tester, reviewer, docs-writer)
       ├── scripts/     ← deterministic Python scripts (no LLM tokens)
       ├── skills/weni-agents/
       └── runs/          ← created automatically per run
   ```

2. **Open the folder in Cursor.** The root `AGENTS.md` configures the main chat as the orchestrator. Pick any model you like for that session.

3. **Describe the agent you want** in the orchestrator chat (e.g. “Build an agent that looks up orders by ID”). The orchestrator asks which collaborator to target (or to create a new one), then runs intake, plan, implement, test, review, and document. To modify an existing agent, copy its files into `agents/<slug>/` first and say you want to edit it.

4. **Authenticate once** (when prompted, in your own terminal — not by the agent):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade weni-cli
   weni login
   ```

   The token is stored in `~/.weni_cli` and reused on later runs.

## What gets generated

Each collaborator's code is written to its own folder `agents/<slug>/` (same level as `.cursor`), not mixed with harness config. A single-agent project just has one folder:

```
your-project/
├── AGENTS.md
├── .cursor/                   # harness — stays local to your dev setup
├── .gitignore
└── agents/                    # one folder per collaborator agent
    └── <slug>/                # the Weni agent — safe to push to CX Platform
        ├── agent_definition.yaml
        ├── requirements.txt
        ├── agent_evaluation.yml
        ├── test-results.md    # verbose output from local `weni run ... -v` tests
        ├── README.md
        └── tools/<tool_name>/
            ├── main.py
            ├── requirements.txt
            ├── test_definition.yaml
            ├── .env           # git-ignored credentials for local tests
            └── .globals       # git-ignored constants for local tests
```

- **CX Platform** — push one collaborator at a time: `cd agents/<slug> && weni project push agent_definition.yaml`. The harness files (`.cursor`, `AGENTS.md`, etc.) and other collaborators are not uploaded.

## Pipeline

| Phase | Who | Output |
|-------|-----|--------|
| 0 Intake | Orchestrator | `00-intake.md` |
| 1 Plan | planner | `01-plan.md` — you approve before implementation |
| 2 Implement | implementer | `agents/<slug>/` files + `02-implementation.md` |
| 3 Test | tester | test files; optional local tool tests; eval if you confirm |
| 4 Review | reviewer | `04-review.md` (read-only critique) |
| 5 Docs | docs-writer | `agents/<slug>/README.md` + `05-docs.md` |

Artifacts live under `.cursor/runs/<run-id>/artifacts/`. The orchestrator resumes unfinished runs automatically.

**Documentation produced:**
- **Per agent (always, in Docs):** `agents/<slug>/README.md` — five lean sections with a mandatory mermaid `sequenceDiagram` of the agent's logic/API flow.
- **Project README (on demand):** ask the orchestrator to generate the root `README.md`. It collects project context from you and auto-fills the skeleton (overview, collaborators, setup, deploy), leaving a mermaid `flowchart` placeholder for you to draw the high-level journey.

**Gates you control:**
- Plan must be approved before implementation.
- `weni eval run` runs only if you confirm when asked.
- `weni project push` never runs without your explicit confirmation.

## Scripts (deterministic, no tokens)

Run from the project root with the project `.venv`:

```bash
python .cursor/scripts/bootstrap_env.py                       # create .venv, install weni-cli, probe auth
python .cursor/scripts/init_run.py "feature" --target <slug>  # start a run for a collaborator (add --mode edit to modify)
python .cursor/scripts/validate_schema.py --target <slug>     # validate agents/<slug>/ after implement
python .cursor/scripts/run_tool_tests.py --target <slug>      # weni run ... -v per tool → agents/<slug>/test-results.md
python .cursor/scripts/run_eval.py --latest                   # weni eval run (target read from the run) → 03-tests.md
python .cursor/scripts/update_state.py --help                 # update run phase status
```

`--target` is optional when the project has a single collaborator; the scripts auto-detect it.

## Subagent models

Each subagent model is set in `.cursor/agents/*.md` (`model:` in the YAML frontmatter). Defaults favor cost: Opus for planning, Composer 2.5 for implement/test/review, Gemini Flash for docs. Adjust to match your Cursor plan.

## More detail

- Orchestrator behavior: [`AGENTS.md`](AGENTS.md)
- Harness usage and layout: [`.cursor/skills/weni-agents/HARNESS.md`](.cursor/skills/weni-agents/HARNESS.md)
- Weni agent rules and API reference: [`.cursor/skills/weni-agents/SKILL.md`](.cursor/skills/weni-agents/SKILL.md)
