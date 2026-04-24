from __future__ import annotations

import argparse
import json
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAILDIR = ROOT / "ml" / "data" / "external" / "enron" / "extracted" / "maildir"
DEFAULT_OUTPUT = ROOT / "ml" / "data" / "external" / "enron" / "processed" / "enron.sample.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample and clean emails from Enron maildir dataset.")
    parser.add_argument("--maildir", type=Path, default=DEFAULT_MAILDIR)
    parser.add_argument("--count", type=int, default=200, help="Number of output emails.")
    parser.add_argument("--offset", type=int, default=0, help="Start offset after sorting files.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def clean_body(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common forward/reply and metadata trailers.
    split_markers = [
        r"-----Original Message-----",
        r"From:\s+.*\nSent:\s+",
        r"----- Forwarded by .* -----",
    ]
    for marker in split_markers:
        match = re.search(marker, text, flags=re.IGNORECASE)
        if match:
            text = text[: match.start()]
            break

    # Keep printable and moderate length.
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")
    text = text.strip()
    return text


def parse_email(path: Path) -> dict[str, str] | None:
    try:
        with path.open("rb") as f:
            message = BytesParser(policy=policy.default).parse(f)
    except Exception:
        return None

    body = ""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    body = payload.decode("utf-8", errors="ignore") if payload else ""
                if body:
                    break
    else:
        try:
            body = message.get_content()
        except Exception:
            payload = message.get_payload(decode=True)
            body = payload.decode("utf-8", errors="ignore") if payload else ""

    cleaned = clean_body(body)
    if len(cleaned) < 80:
        return None

    return {
        "message_id": str(message.get("Message-ID", "")).strip(),
        "date": str(message.get("Date", "")).strip(),
        "from": str(message.get("From", "")).strip(),
        "to": str(message.get("To", "")).strip(),
        "subject": str(message.get("Subject", "")).strip(),
        "body": cleaned,
    }


def infer_user_and_folder(path: Path, maildir_root: Path) -> tuple[str, str]:
    relative = path.relative_to(maildir_root)
    parts = relative.parts
    user = parts[0] if len(parts) > 0 else "unknown"
    folder = "/".join(parts[1:-1]) if len(parts) > 2 else "unknown"
    return user, folder


def main() -> None:
    args = parse_args()
    if not args.maildir.exists():
        raise FileNotFoundError(f"Maildir path does not exist: {args.maildir}")

    all_files = sorted([p for p in args.maildir.rglob("*") if p.is_file()])
    start = max(args.offset, 0)
    end = min(len(all_files), start + max(args.count * 5, args.count))  # pre-scan window
    selected_files = all_files[start:end]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    exported = 0
    with args.output.open("w", encoding="utf-8") as out:
        for file_path in selected_files:
            parsed = parse_email(file_path)
            if not parsed:
                continue
            user, folder = infer_user_and_folder(file_path, args.maildir)
            row = {
                "id": f"enron-{exported + 1:05d}",
                "source_dataset": "enron_email",
                "source_file": str(file_path.relative_to(ROOT)),
                "user": user,
                "folder": folder,
                **parsed,
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            exported += 1
            if exported >= args.count:
                break

    print(f"Exported {exported} cleaned emails to {args.output}")


if __name__ == "__main__":
    main()
