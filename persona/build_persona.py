#!/usr/bin/env python3
"""Build persona/style signals from a WhatsApp export."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


HINGLISH_MARKERS = {
    "hai",
    "kya",
    "nahi",
    "yaar",
    "matlab",
    "acha",
    "theek",
    "bhai",
    "haan",
    "toh",
}

WHATSAPP_LINE_PATTERNS = (
    re.compile(
        r"^\[(?P<date>[^,]+),\s*(?P<time>[^\]]+)\]\s*(?P<sender>[^:]+):\s*(?P<message>.*)$"
    ),
    re.compile(
        r"^(?P<date>[^,]+,\s*[^-]+)\s*-\s*(?P<sender>[^:]+):\s*(?P<message>.*)$"
    ),
)

EMOJI_BASE = (
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]"
)
EMOJI_MODIFIER = "[\U0001F3FB-\U0001F3FF]"
EMOJI_SEQUENCE_PATTERN = re.compile(
    rf"(?:"
    rf"(?:{EMOJI_BASE}(?:\uFE0F)?(?:{EMOJI_MODIFIER})?)"
    rf"(?:\u200d(?:{EMOJI_BASE}(?:\uFE0F)?(?:{EMOJI_MODIFIER})?))*"
    rf"|"
    rf"[#*0-9]\uFE0F?\u20E3"
    rf"|"
    rf"[\U0001F1E6-\U0001F1FF]{{2}}"
    rf")"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build persona/style signals from a WhatsApp text export."
    )
    parser.add_argument(
        "--file",
        required=True,
        nargs="+",
        help="One or more paths to WhatsApp .txt exports",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Exact sender name as it appears in the export",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "style_signals.json"),
        help="Where to write the JSON output",
    )
    return parser.parse_args()


def parse_whatsapp_line(line: str):
    for pattern in WHATSAPP_LINE_PATTERNS:
        match = pattern.match(line)
        if match:
            sender = match.group("sender").strip()
            message = match.group("message").strip()
            return sender, message
    return None, None


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"\b[\w']+\b", text.lower())


def contains_hinglish_marker(text: str) -> bool:
    words = set(tokenize_words(text))
    return any(marker in words for marker in HINGLISH_MARKERS)


def extract_emojis(text: str) -> list[str]:
    return [match.group(0) for match in EMOJI_SEQUENCE_PATTERN.finditer(text)]


def load_matching_messages(source_files: list[Path], sender_name: str) -> list[str]:
    messages: list[str] = []
    for source_path in source_files:
        with source_path.open(encoding="utf-8", errors="ignore") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                sender, message = parse_whatsapp_line(line)
                if sender == sender_name:
                    messages.append(message)
    return messages


def build_stats(messages: list[str]) -> dict:
    total_messages = len(messages)
    total_words = sum(len(tokenize_words(message)) for message in messages)
    hinglish_messages = sum(1 for message in messages if contains_hinglish_marker(message))
    hinglish_ratio = (hinglish_messages / total_messages * 100) if total_messages else 0.0

    emoji_counter = Counter()
    for message in messages:
        emoji_counter.update(extract_emojis(message))

    top_emojis = [
        {"emoji": emoji, "count": count}
        for emoji, count in emoji_counter.most_common(15)
    ]

    return {
        "sample_size": total_messages,
        "hinglish_ratio_percent": round(hinglish_ratio, 2),
        "avg_message_length_words": round(total_words / total_messages, 2)
        if total_messages
        else 0.0,
        "top_emojis": top_emojis,
    }


def print_summary(name: str, source_file: Path, stats: dict) -> None:
    print(f"Persona stats for: {name}")
    print(f"Source: {source_file}")
    print(f"Total matching messages: {stats['sample_size']}")
    print(f"Hinglish ratio: {stats['hinglish_ratio_percent']}%")
    print(f"Average message length: {stats['avg_message_length_words']} words")
    print("Top emojis:")
    if stats["top_emojis"]:
        for item in stats["top_emojis"]:
            print(f"  {item['emoji']}  x{item['count']}")
    else:
        print("  None found")


def main() -> int:
    args = parse_args()
    source_paths = [Path(file_path) for file_path in args.file]

    messages = load_matching_messages(source_paths, args.name)

    if not messages:
        print(
            f"Warning: no messages matched sender name '{args.name}'. "
            "Double-check the exact sender name in the raw export and try again."
        )
        return 1

    stats = build_stats(messages)
    source_label = source_paths[0] if len(source_paths) == 1 else Path(
        ", ".join(str(path) for path in source_paths)
    )
    print_summary(args.name, source_label, stats)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())