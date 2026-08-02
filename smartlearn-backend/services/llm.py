"""Grounded OpenRouter service for SmartLearn Lite."""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from services.pdf import PageRecord


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemma-4-31b-it:free",
).strip()


SYSTEM_PROMPT = """
You are a precise PDF question-answering assistant.

Use only the PDF text supplied by the user.

Rules:
1. Do not use outside knowledge.
2. Cite supporting PDF pages using the exact format [Page X].
3. Every factual claim taken from the PDF must include a page citation.
4. Use only page numbers that appear in the supplied PDF text.
5. If the PDF does not contain enough evidence, say exactly:
   The provided PDF does not contain enough information to answer this question.
6. Do not invent facts, quotations, page numbers, or sources.
7. Keep the answer concise and directly answer the question.
""".strip()


def build_document_text(pages: list[PageRecord]) -> str:
    """Format readable pages with stable one-based page labels."""
    return "\n\n".join(
        f"### [Page {page['page']}]\n{page['text']}"
        for page in pages
        if page["text"]
    )


def create_client() -> OpenAI:
    """Create an OpenRouter client using the backend-only secret."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing."
        )

    if not MODEL:
        raise RuntimeError(
            "OPENROUTER_MODEL is missing."
        )

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def answer_from_pages(
    pages: list[PageRecord],
    message: str,
) -> str:
    """Answer one question using only page-labelled PDF text."""
    document_text = build_document_text(pages)

    if not document_text:
        raise RuntimeError(
            "The document contains no readable text."
        )

    prompt = (
        "PDF text:\n"
        f"{document_text}\n\n"
        "Question:\n"
        f"{message}"
    )

    client = create_client()

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise RuntimeError(
            "The AI service returned an empty response."
        )

    return content.strip()