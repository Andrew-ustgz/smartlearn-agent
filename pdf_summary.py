"""Summarise a text-based PDF with page-level citations via OpenRouter.

Usage:
    python pdf_summary.py <path-to-pdf>
    python pdf_summary.py <path-to-pdf> --pages START-END
"""

import argparse
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "google/gemma-4-26b-a4b-it:free"
ENV_VAR = "OPENROUTER_API_KEY"

SYSTEM_PROMPT = (
    "You are a precise document summariser. "
    "You will receive the text of a PDF document labelled page by page "
    'like "[Page 1] ...", "[Page 2] ...", and so on. '
    "Produce exactly three Markdown sections in this order:\n\n"
    "## Overview\n\n"
    "A concise one-paragraph summary of the document.\n\n"
    "## Key Points\n\n"
    "- Point one [Page X].\n"
    "- Point two [Page Y].\n"
    "- Point three [Page Z].\n"
    "- Point four [Page W].\n"
    "- Point five [Page V].\n\n"
    "You must list between three and five key points. "
    "Every key point MUST be a single Markdown bullet (starting with \"- \") "
    "and MUST end with one or more citations in the exact format [Page X]. "
    "Use only page numbers that appear in the provided text. "
    "When a point draws from multiple pages, include each as a separate "
    'citation, e.g. [Page 2] [Page 5].\n\n'
    "## Limitations\n\n"
    "Describe any extraction or context limitations, missing content, "
    "or other relevant caveats.\n\n"
    "Do not add any other headings, preamble, or closing text. "
    "Do not make up facts not present in the document."
)

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_pdf_path(path: str) -> str:
    """Check that *path* refers to a readable, non-encrypted PDF file.

    Returns the resolved path on success.  Prints a friendly message and
    calls ``sys.exit(1)`` on any failure.
    """
    # Existence and file-ness
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        sys.exit(1)

    if not os.path.isfile(path):
        print(f"Error: Not a file: {path}")
        sys.exit(1)

    # Extension check
    if not path.lower().endswith(".pdf"):
        print(f"Error: A PDF file is required. {path} does not have a .pdf extension.")
        sys.exit(1)

    # Openability — PdfReader raises for encrypted / broken files
    try:
        reader = PdfReader(path)
    except Exception as exc:
        msg = str(exc).strip()
        if "encrypted" in msg.lower() or "decrypt" in msg.lower():
            print(f"Error: The PDF is encrypted and cannot be read.")
        else:
            print(f"Error: Cannot open PDF: {msg}")
        sys.exit(1)

    # Double-check encryption flag (some PDFs raise only when you access pages)
    if reader.is_encrypted:
        print("Error: The PDF is encrypted and cannot be read.")
        sys.exit(1)

    return path


def parse_page_range(range_str: str) -> tuple[int, int]:
    """Parse and validate a ``START-END`` page range string.

    Returns ``(start, end)`` as 1-based inclusive integers on success.
    Prints a friendly message and calls ``sys.exit(1)`` on any failure.
    """
    PAGE_RANGE_RE = re.compile(r"^([1-9]\d*)-([1-9]\d*)$")
    m = PAGE_RANGE_RE.fullmatch(range_str)
    if not m:
        print(
            "Error: --pages must be START-END with positive integers, "
            f"e.g. --pages 1-5. Got: {range_str!r}"
        )
        sys.exit(1)

    start = int(m.group(1))
    end = int(m.group(2))

    if start > end:
        print(
            f"Error: START must not be greater than END in --pages {start}-{end}."
        )
        sys.exit(1)

    return start, end


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Return a list of ``(page_number, text)`` for non-empty pages.

    Page numbers are 1-based.  Pages whose extracted text is empty or
    whitespace-only are silently skipped.
    """
    reader = PdfReader(pdf_path)
    pages: list[tuple[int, str]] = []

    for idx, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text()
        except Exception:
            # Some pages may fail to extract — treat as empty.
            continue

        if raw is None:
            continue

        cleaned = raw.strip()
        if cleaned:
            pages.append((idx, cleaned))

    return pages


def build_prompt(pages: list[tuple[int, str]]) -> str:
    """Format the extracted pages into the user message sent to the model."""
    blocks = [f"[Page {num}] {text}" for num, text in pages]
    return "\n\n".join(blocks)


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


def summarise(client: OpenAI, pages_text: str) -> str:
    """Send the page-labelled text to the model and return the raw reply."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pages_text},
        ],
        max_tokens=1200,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

# Expected section headings in order
REQUIRED_HEADINGS = ["## Overview", "## Key Points", "## Limitations"]


def _find_sections(raw: str) -> dict[str, str]:
    """Locate required headings and return {heading: body}.

    Uses exact heading patterns (^## Overview$, ^## Key Points$,
    ^## Limitations$) and extracts each section body by slicing the
    text between heading positions.  Does not use dict() on regex tuples.
    """
    HEADING_SPECS: list[tuple[str, str]] = [
        (r"^## Overview$", "## Overview"),
        (r"^## Key Points$", "## Key Points"),
        (r"^## Limitations$", "## Limitations"),
    ]

    hits: list[tuple[str, int, int]] = []
    for pattern, label in HEADING_SPECS:
        m = re.search(pattern, raw, flags=re.MULTILINE)
        if m:
            hits.append((label, m.start(), m.end()))

    sections: dict[str, str] = {}
    for i, (heading, _start, end) in enumerate(hits):
        next_start = hits[i + 1][1] if i + 1 < len(hits) else len(raw)
        body = raw[end:next_start].strip()
        sections[heading] = body

    return sections


def validate_output(raw: str, valid_page_numbers: set[int]) -> str:
    """Check that *raw* matches the required structure.

    Returns the cleaned raw text on success.  Prints a friendly message
    and calls ``sys.exit(1)`` on any structural violation.
    """
    if not raw:
        print("Error: The model returned an empty response.")
        sys.exit(1)

    sections = _find_sections(raw)

    # --- Each required heading appears exactly once --------------------------

    found_headings = list(sections.keys())
    if found_headings != REQUIRED_HEADINGS:
        missing = [h for h in REQUIRED_HEADINGS if h not in found_headings]
        extra = [h for h in found_headings if h not in REQUIRED_HEADINGS]
        parts: list[str] = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if extra:
            parts.append(f"unexpected: {', '.join(extra)}")
        print(
            f"Error: The model response does not contain the required sections "
            f"({'; '.join(parts)})."
        )
        sys.exit(1)

    # --- Headings appear in the required order -------------------------------

    positions: dict[str, int] = {}
    for heading in REQUIRED_HEADINGS:
        m = re.search(r"^" + re.escape(heading) + r"$", raw, flags=re.MULTILINE)
        positions[heading] = m.start() if m else -1
    for i in range(1, len(REQUIRED_HEADINGS)):
        if positions[REQUIRED_HEADINGS[i]] < positions[REQUIRED_HEADINGS[i - 1]]:
            print(
                "Error: The model response has the required headings "
                "but in the wrong order."
            )
            sys.exit(1)

    # --- Key Points: 3-5 bullets, each ending with valid [Page X] ------------

    key_points_body = sections.get("## Key Points", "")
    bullet_lines = [
        line.strip()
        for line in key_points_body.splitlines()
        if line.strip().startswith(("- ", "* "))
    ]

    if len(bullet_lines) < 3:
        print(
            f"Error: Key Points section has {len(bullet_lines)} bullet(s); "
            f"3 to 5 are required."
        )
        sys.exit(1)

    if len(bullet_lines) > 5:
        print(
            f"Error: Key Points section has {len(bullet_lines)} bullets; "
            f"at most 5 are allowed."
        )
        sys.exit(1)

    # Every bullet must end with at least one [Page X] citing a real page
    valid_strs = {str(n) for n in valid_page_numbers}
    citation_re = re.compile(r"\[Page (\d+)\]")

    for bullet in bullet_lines:
        citations = citation_re.findall(bullet)
        if not citations:
            print(
                f"Error: A Key Point is missing a page citation: \"{bullet}\""
            )
            sys.exit(1)

        for num in citations:
            if num not in valid_strs:
                print(
                    f"Error: A Key Point cites [Page {num}], "
                    f"but that page does not exist in the document."
                )
                sys.exit(1)

    return raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise a text-based PDF with page-level citations."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to summarise.",
    )
    parser.add_argument(
        "--pages",
        metavar="START-END",
        help="Summarise only pages in the given 1-based inclusive range, "
        "e.g. --pages 1-5.",
    )
    args = parser.parse_args()

    # 1. Validate the input file ----------------------------------------------

    pdf_path = validate_pdf_path(args.pdf_path)

    # 2. Extract text page by page --------------------------------------------

    pages = extract_pages(pdf_path)

    if not pages:
        print(
            "Error: No extractable text found in the PDF. "
            "It may be image-only or scanned."
        )
        sys.exit(1)

    # 2a. Apply page-range filter if requested --------------------------------

    if args.pages is not None:
        range_start, range_end = parse_page_range(args.pages)

        # Validate against the actual page count
        actual_last = max(num for num, _ in pages)
        if range_start > actual_last or range_end > actual_last:
            print(
                f"Error: The PDF only has {actual_last} page(s) "
                f"with extractable text. "
                f"--pages {range_start}-{range_end} is out of range."
            )
            sys.exit(1)

        pages = [
            (num, text) for num, text in pages
            if range_start <= num <= range_end
        ]

        if not pages:
            print(
                f"Error: No pages with extractable text in the range "
                f"--pages {range_start}-{range_end}."
            )
            sys.exit(1)

    pages_text = build_prompt(pages)

    # Safety: the prompt must not be empty.
    if not pages_text.strip():
        print("Error: No text content to send to the API.")
        sys.exit(1)

    # 3. Create the API client ------------------------------------------------

    client = create_client()

    # 4. Call the model -------------------------------------------------------

    try:
        raw = summarise(client, pages_text)
    except Exception as exc:
        print(f"Error: API request failed: {type(exc).__name__}: {exc}")
        sys.exit(1)

    # 5. Validate the response ------------------------------------------------

    valid_page_numbers = {num for num, _ in pages}
    validated = validate_output(raw, valid_page_numbers)

    # 6. Print the result -----------------------------------------------------

    print(validated)


if __name__ == "__main__":
    main()
