"""Page-aware PDF text extraction for SmartLearn Lite."""

from io import BytesIO
from typing import TypedDict

from pypdf import PdfReader


MAX_PAGES = 30


class PageRecord(TypedDict):
    """Text extracted from one original PDF page."""

    page: int
    text: str


def extract_pages(pdf_bytes: bytes) -> list[PageRecord]:
    """Extract page-numbered text records from PDF bytes.

    Page numbers are one-based so that they match the page numbers
    normally shown to a reader.
    """
    reader = PdfReader(BytesIO(pdf_bytes))

    if len(reader.pages) > MAX_PAGES:
        raise ValueError(
            f"PDF must contain at most {MAX_PAGES} pages."
        )

    pages: list[PageRecord] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    return pages