from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    sample_script = ROOT / "scripts" / "sample_jira.py"
    seed_script = ROOT / "scripts" / "build_seed_from_jira.py"

    run_step(["python", str(sample_script), "--count", "400"])
    run_step(["python", str(seed_script)])

    print("\nJira pipeline completed.")
    print("Generated files:")
    print("- ml/data/external/jira/processed/jira.sample.jsonl")
    print("- ml/data/external/jira/processed/jira.seed.auto.jsonl")


if __name__ == "__main__":
    main()
