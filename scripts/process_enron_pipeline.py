from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    sample_script = ROOT / "scripts" / "sample_enron.py"
    seed_script = ROOT / "scripts" / "build_seed_from_enron.py"

    run_step(["python", str(sample_script), "--count", "200"])
    run_step(["python", str(seed_script)])

    print("\nEnron pipeline completed.")
    print("Generated files:")
    print("- ml/data/external/enron/processed/enron.sample.jsonl")
    print("- ml/data/external/enron/processed/enron.seed.auto.jsonl")


if __name__ == "__main__":
    main()
