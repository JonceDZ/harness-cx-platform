"""Initialize or resume a harness run.

Creates a new run directory with a fresh STATE.md (all phases pending), an empty
artifacts folder, and a logs folder. With --latest-open it instead resolves the
most recent run that still has open phases, enabling cross-session resume.

Usage:
    python .cursor/scripts/init_run.py "add order tracking tool"
    python .cursor/scripts/init_run.py --latest-open
"""

# Standard library
import argparse
import copy
from datetime import datetime

# Local
from _common import (
    PHASES,
    latest_open_run,
    runs_dir,
    save_state,
    slugify,
)


def build_initial_state(run_id: str, feature: str, mode: str) -> dict:
    """Build the initial run state with every phase set to pending."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    phases = []
    for phase in copy.deepcopy(PHASES):
        phase["status"] = "pending"
        phases.append(phase)
    return {
        "run_id": run_id,
        "feature": feature,
        "mode": mode,
        "started": now,
        "updated": now,
        "checkpoint": "—",
        "focus": "Run initialized. Waiting for intake.",
        "blockers": [],
        "resume_hint": "Start from phase 0 (Intake).",
        "phases": phases,
    }


def create_run(feature: str, mode: str) -> str:
    """Create a new run directory and write its initial state."""
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(feature)}"
    run_dir = runs_dir() / run_id
    (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    save_state(run_dir, build_initial_state(run_id, feature, mode))
    return str(run_dir)


def main() -> None:
    """Parse arguments and create or resolve a run."""
    parser = argparse.ArgumentParser(description="Initialize or resume a harness run.")
    parser.add_argument("description", nargs="?", help="Feature description for a new run.")
    parser.add_argument("--mode", default="standard", help="Run mode label (default: standard).")
    parser.add_argument(
        "--latest-open",
        action="store_true",
        help="Resolve the most recent run with open phases instead of creating one.",
    )
    args = parser.parse_args()

    if args.latest_open:
        run_dir = latest_open_run()
        if run_dir is None:
            print("NO_OPEN_RUN")
            raise SystemExit(1)
        print(str(run_dir))
        return

    if not args.description:
        parser.error("a feature description is required when not using --latest-open")

    print(create_run(args.description, args.mode))


if __name__ == "__main__":
    main()
