#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - depends on local environment
    Groq = None


def load_groq_from_local_venv() -> object | None:
    if Groq is not None:
        return Groq

    repo_root = Path(__file__).resolve().parent.parent
    site_packages_dirs = sorted((repo_root / ".venv" / "lib").glob("python*/site-packages"))

    for site_packages_dir in site_packages_dirs:
        site_packages = str(site_packages_dir)
        if site_packages not in sys.path:
            sys.path.insert(0, site_packages)
        try:
            from groq import Groq as local_groq

            return local_groq
        except ImportError:
            continue

    return None


def extract_response_text(response) -> str:
    choices = getattr(response, "choices", None) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None)
        if content:
            return str(content).strip()

    raise RuntimeError("Groq response did not contain usable text content.")


def format_api_error(exc: Exception) -> str:
    message = str(exc)
    status = getattr(exc, "status", None) or getattr(exc, "code", None)
    lowered = message.lower()

    if (
        status == 429
        or "resource_exhausted" in lowered
        or "quota" in lowered
        or "rate limit" in lowered
    ):
        return (
            "Groq quota/rate limit exceeded (429). "
            "Wait and try again later; this script does not retry automatically."
        )

    return message


def main() -> int:
    local_groq = load_groq_from_local_venv()
    if local_groq is None:
        print(
            "Missing dependency: groq. Install it in the repo .venv before running this script.",
            file=sys.stderr,
        )
        return 1

    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment or .env file.")

    client = local_groq(api_key=api_key)

    persona_path = Path(__file__).resolve().parent / "persona.json"
    with persona_path.open(encoding="utf-8") as file_handle:
        persona = json.load(file_handle)

    test_prompts = [
        ("partner", "I am going to be late today, can you pick me up?"),
        ("family", "diwali pe ghar aaoge kya?"),
        ("friends", "bhai kya scene hai aaj?"),
        ("professional", "I have a new video ready when can we connect?"),
    ]

    for relationship, incoming in test_prompts:
        relationship_data = persona["relationships"][relationship]

        prompt = f"""You are replying as Aparajita on WhatsApp.

Identity:
{persona["identity"]}

Work and interests:
{persona["work_and_interests"]}

Relationship:
{relationship}

Relationship-specific tone:
{relationship_data["tone"]}

Example replies from Aparajita:
{relationship_data["example_replies"]}

Overall Hinglish ratio:
{persona["hinglish_ratio"]}

Average message length:
{persona["avg_message_length_words"]} words

Top emojis:
{persona["top_emojis"]}

Hard rules:
{persona["hard_rules"]}

Incoming WhatsApp message:
"{incoming}"

Generate ONE reply that sounds like Aparajita would naturally reply to this person.

Important:

- Match the relationship-specific tone.
- Follow the actual texting cadence shown in the examples.
- Keep the reply short and natural for WhatsApp.
- Use Hinglish only when appropriate for this relationship.
- Do not make the message sound polished, formal, or AI-generated.
- Preserve informal spelling and abbreviations when they fit the examples.
- Use emojis only when they fit the relationship and examples.
- Do not invent personal information.
- Do not make commitments or confirmations that violate the hard rules.
- Return ONLY the reply message.
"""

        try:
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            reply_text = extract_response_text(response)
        except Exception as exc:
            print(
                f"[{relationship}] {incoming} -> ERROR: {format_api_error(exc)}",
                file=sys.stderr,
            )
            return 1

        print(f"[{relationship}] {incoming} -> {reply_text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())