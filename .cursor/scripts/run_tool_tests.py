"""Run local tool tests with verbose output and save results to agent/test-results.md.

Runs `weni run agent_definition.yaml <agent_name> <tool_name> -v` for every tool
defined in the agent (or for a specific tool if --tool is given). Output is saved
to `agent/test-results.md` so the results live alongside the agent code.

This is distinct from `weni eval run`, which runs the full evaluation suite.

Usage:
    python .cursor/scripts/run_tool_tests.py
    python .cursor/scripts/run_tool_tests.py --tool <tool_key>
"""

# Standard library
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Third-party
try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required. Run this script with the project .venv python.")

# Local
from _common import agent_dir, venv_bin


def load_agent_definition(definition_path: Path) -> dict:
    """Load and return the agent definition YAML."""
    with open(definition_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def collect_tools(definition: dict, agent_filter: str | None = None) -> list[tuple[str, str]]:
    """Return a list of (agent_key, tool_key) pairs to test.

    Each pair corresponds to one `weni run` invocation.
    """
    pairs = []
    for agent_key, agent in (definition.get("agents") or {}).items():
        if agent_filter and agent_key != agent_filter:
            continue
        for tool_entry in (agent.get("tools") or []):
            for tool_key in tool_entry:
                pairs.append((agent_key, tool_key))
    return pairs


def run_tool(weni: Path, definition_file: str, agent_key: str, tool_key: str, cwd: Path) -> tuple[str, int]:
    """Run a single tool test with verbose flag and return (output, returncode)."""
    command = [str(weni), "run", definition_file, agent_key, tool_key, "-v"]
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    combined = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return combined, result.returncode


def main() -> None:
    """Run all tool tests and write results to agent/test-results.md."""
    parser = argparse.ArgumentParser(description="Run local weni tool tests and save verbose output.")
    parser.add_argument("--tool", help="Only test this tool key.")
    parser.add_argument("--agent", help="Only test tools from this agent key.")
    args = parser.parse_args()

    root = agent_dir()
    definition_path = root / "agent_definition.yaml"
    if not definition_path.exists():
        raise SystemExit(f"agent_definition.yaml not found at {definition_path}")

    weni = venv_bin("weni")
    if not weni.exists():
        raise SystemExit("weni CLI not found in .venv. Run bootstrap_env.py first.")

    definition = load_agent_definition(definition_path)
    tool_pairs = collect_tools(definition, agent_filter=args.agent)

    if args.tool:
        tool_pairs = [(a, t) for a, t in tool_pairs if t == args.tool]

    if not tool_pairs:
        raise SystemExit("No tools found to test. Check agent_definition.yaml or your --tool/--agent filters.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = [f"# Local Tool Test Results\n\nRun at: {timestamp}\n"]
    overall_pass = True

    for agent_key, tool_key in tool_pairs:
        output, returncode = run_tool(weni, "agent_definition.yaml", agent_key, tool_key, root)
        status = "PASS" if returncode == 0 else "FAIL"
        if returncode != 0:
            overall_pass = False
        sections.append(
            f"## {agent_key} / {tool_key}  —  {status}\n\n"
            f"Command: `weni run agent_definition.yaml {agent_key} {tool_key} -v`\n\n"
            f"```\n{output.strip()}\n```\n"
        )
        print(f"  {status}  {agent_key}/{tool_key}")

    results_file = root / "test-results.md"
    results_file.write_text("\n".join(sections), encoding="utf-8")

    overall_status = "ALL_PASS" if overall_pass else "SOME_FAIL"
    print(f"\n{overall_status}")
    print(f"Results: {results_file}")
    raise SystemExit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
