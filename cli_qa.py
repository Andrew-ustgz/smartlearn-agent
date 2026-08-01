import argparse
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemma-4-26b-a4b-it:free"
ENV_VAR = "OPENROUTER_API_KEY"

SYSTEM_PROMPT = (
    "You are a precise question-answering assistant. "
    "Answer questions using ONLY the provided reference text. "
    "Each paragraph is numbered like [Paragraph X]. "
    "If the answer is found in the text, state it clearly "
    "and cite every source paragraph like [Paragraph X]. "
    'If the text does not contain the answer, reply exactly with: '
    '"The text does not provide this information." '
    "Do not use any outside knowledge. "
    "Do not make up information."
)

FALLBACK = "The text does not provide this information."


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def read_interactive_text() -> str:
    """Read multiple lines from stdin until a line containing only 'END'."""
    print("Paste your reference text below. Type END on a new line to finish.\n")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def read_file_text(path: str) -> str:
    """Return the contents of *path* decoded as UTF-8."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Error: Cannot decode {path} as UTF-8.")
        sys.exit(1)
    except OSError as exc:
        print(f"Error: Cannot read {path}: {exc}")
        sys.exit(1)


def split_paragraphs(text: str) -> list[tuple[int, str]]:
    """Split *text* into non-empty numbered paragraphs.

    Paragraphs are separated by one or more blank lines (a blank line is
    empty or contains only whitespace).  Both ``\\n`` and ``\\r\\n`` line
    endings are supported.  Returns a list of ``(number, body)`` tuples.
    Numbering starts at 1.
    """
    # Normalise Windows CRLF → LF so splitting is consistent.
    normalised = text.replace("\r\n", "\n")
    lines = normalised.split("\n")

    paragraphs: list[tuple[int, str]] = []
    number = 0
    buffer: list[str] = []

    for line in lines:
        if line.strip() == "":
            # Blank line — flush the current paragraph if any.
            if buffer:
                number += 1
                paragraphs.append((number, " ".join(buffer).strip()))
                buffer = []
        else:
            buffer.append(line)

    # Don't forget a paragraph at the very end with no trailing blank line.
    if buffer:
        number += 1
        paragraphs.append((number, " ".join(buffer).strip()))

    return paragraphs


def build_reference(paragraphs: list[tuple[int, str]]) -> str:
    """Format numbered paragraphs into the string sent to the model."""
    lines = [f"[Paragraph {num}] {body}" for num, body in paragraphs]
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Answer validation
# ---------------------------------------------------------------------------


def validate_answer(raw: str, paragraph_count: int) -> str | None:
    """Return a safe answer string or ``None`` when the response is unusable.

    * An empty/whitespace-only response returns ``None``.
    * The exact fallback sentence is accepted unchanged.
    * A response whose ``[Paragraph X]`` citations ALL reference real
      paragraph numbers is accepted.
    * Any citation pointing outside the valid range causes rejection.
    * Everything else returns ``None`` (hallucinated / unsupported answer).
    """
    cleaned = raw.strip()
    if not cleaned:
        return None

    if cleaned == FALLBACK:
        return cleaned

    if "[Paragraph " not in cleaned:
        return None

    # Every citation must reference a real paragraph number.
    valid_numbers = {str(n) for n in range(1, paragraph_count + 1)}
    found = set(re.findall(r"\[Paragraph (\d+)\]", cleaned))

    if not found:
        return None

    if found - valid_numbers:
        # At least one citation references a non-existent paragraph.
        return None

    return cleaned


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def create_client() -> OpenAI:
    """Load ``.env``, check for the API key, and return an OpenRouter client."""
    load_dotenv(".env", override=True)
    api_key = os.getenv(ENV_VAR, "").strip()
    if not api_key:
        print(f"Error: {ENV_VAR} is missing. Add it to .env and try again.")
        sys.exit(1)
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def ask_question(client: OpenAI, reference: str, question: str) -> str:
    """Send the reference text and question to the model; return the raw reply."""
    user_message = (
        f"REFERENCE TEXT:\n\n{reference}\n\n"
        f"QUESTION: {question}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=600,
    )
    content = response.choices[0].message.content
    return content if content else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask questions about a reference text with cited answers."
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="Read reference text from a file instead of interactive input.",
    )
    args = parser.parse_args()

    # 1. Load reference text ------------------------------------------------

    if args.file:
        raw_text = read_file_text(args.file)
    else:
        raw_text = read_interactive_text()

    # 2. Split into numbered paragraphs -------------------------------------

    paragraphs = split_paragraphs(raw_text)

    if not paragraphs:
        print("Error: No non-empty paragraphs found. Please provide some text.")
        sys.exit(1)

    reference = build_reference(paragraphs)
    paragraph_count = len(paragraphs)

    print(f"\nLoaded {paragraph_count} paragraph(s).")

    # 3. Create API client --------------------------------------------------

    client = create_client()

    # 4. Question loop ------------------------------------------------------

    print("\nAsk a question or type 'quit' to exit.\n")

    while True:
        try:
            question = input("> ").strip()
        except EOFError:
            print()
            break

        if not question:
            continue

        if question.lower() == "quit":
            print("Goodbye!")
            break

        # 5. Query the model -------------------------------------------------

        try:
            raw = ask_question(client, reference, question)
        except Exception as exc:
            print(f"Error: API request failed: {type(exc).__name__}: {exc}")
            continue

        # 6. Validate and display --------------------------------------------

        answer = validate_answer(raw, paragraph_count)
        if answer is None:
            print(FALLBACK)
        else:
            print(answer)

        print()  # blank line between Q&A pairs


if __name__ == "__main__":
    main()
