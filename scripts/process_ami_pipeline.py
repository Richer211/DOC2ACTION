from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    sample_script = ROOT / "scripts" / "sample_ami.py"
    seed_script = ROOT / "scripts" / "build_seed_from_ami.py"

    run_step(["python", str(sample_script), "--count", "200"])
    run_step(["python", str(seed_script)])

    print("\nAMI pipeline completed.")
    print("Generated files:")
    print("- ml/data/external/ami/processed/ami.sample.jsonl")
    print("- ml/data/external/ami/processed/ami.seed.auto.jsonl")


if __name__ == "__main__":
    main()
