from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORDS_DIR = ROOT / "ml" / "data" / "external" / "ami" / "extracted" / "ami_public_manual_1.6.2" / "words"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "external" / "ami" / "processed" / "ami.sample.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample and reconstruct transcripts from AMI words XML files.")
    parser.add_argument("--words-dir", type=Path, default=DEFAULT_WORDS_DIR)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def join_tokens(tokens: list[str]) -> str:
    text = ""
    punctuation = {".", ",", "!", "?", ";", ":", ")", "]", "}", "'s", "'re", "'ve", "'ll", "'m", "n't"}
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if not text:
            text = token
            continue
        if token in punctuation or re.match(r"^[\.,!?;:\)\]\}]$", token):
            text += token
        else:
            text += " " + token
    return re.sub(r"\s+", " ", text).strip()


def parse_words_file(path: Path) -> dict[str, str | float] | None:
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return None

    word_nodes = [node for node in root if node.tag.endswith("w")]
    if not word_nodes:
        return None

    tokens: list[str] = []
    start_time = None
    end_time = None

    for node in word_nodes:
        node_text = (node.text or "").strip()
        if not node_text:
            continue
        tokens.append(node_text)

        s = node.attrib.get("starttime")
        e = node.attrib.get("endtime")
        if s is not None and start_time is None:
            try:
                start_time = float(s)
            except ValueError:
                pass
        if e is not None:
            try:
                end_time = float(e)
            except ValueError:
                pass

    transcript = join_tokens(tokens)
    if len(transcript) < 120:
        return None

    stem = path.stem.replace(".words", "")
    meeting_id, speaker = (stem.split(".", 1) + ["unknown"])[:2] if "." in stem else (stem, "unknown")

    return {
        "id": stem,
        "meeting_id": meeting_id,
        "speaker": speaker,
        "source_dataset": "ami_public_manual_1.6.2",
        "source_file": str(path.relative_to(ROOT)),
        "start_time": start_time if start_time is not None else -1.0,
        "end_time": end_time if end_time is not None else -1.0,
        "transcript": transcript,
    }


def main() -> None:
    args = parse_args()
    if not args.words_dir.exists():
        raise FileNotFoundError(f"Words directory not found: {args.words_dir}")

    xml_files = sorted(args.words_dir.glob("*.words.xml"))
    start = max(args.offset, 0)
    end = min(len(xml_files), start + max(args.count * 2, args.count))
    selected = xml_files[start:end]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    exported = 0
    with args.output.open("w", encoding="utf-8") as out:
        for path in selected:
            parsed = parse_words_file(path)
            if not parsed:
                continue
            out.write(json.dumps(parsed, ensure_ascii=False) + "\n")
            exported += 1
            if exported >= args.count:
                break

    print(f"Exported {exported} AMI transcript samples to {args.output}")


if __name__ == "__main__":
    main()
