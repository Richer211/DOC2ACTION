from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(command: list[str]) -> None:
    print("Running:", " ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    sample_script = ROOT / "scripts" / "sample_meetingbank.py"
    seed_script = ROOT / "scripts" / "build_seed_from_meetingbank.py"

    run_step(["python", str(sample_script), "--split", "train", "--count", "200"])
    run_step(["python", str(seed_script)])

    print("\nMeetingBank pipeline completed.")
    print("Generated files:")
    print("- ml/data/external/meetingbank/processed/meetingbank.sample.jsonl")
    print("- ml/data/external/meetingbank/processed/meetingbank.seed.auto.jsonl")


if __name__ == "__main__":
    main()
