"""SmartLearn Lite FastAPI entry point."""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf.errors import PdfReadError

from services.llm import answer_from_pages
from services.pdf import PageRecord, extract_pages


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPOSITORY_ROOT / ".env")


def parse_allowed_origins() -> list[str]:
    """Read and normalize the browser-origin allowlist."""
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173",
    )

    origins = [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]

    if not origins:
        origins = ["http://localhost:5173"]

    if any(origin == "*" for origin in origins):
        raise RuntimeError(
            "Wildcard CORS origins are not allowed."
        )

    return origins


ALLOWED_ORIGINS = parse_allowed_origins()


app = FastAPI(
    title="SmartLearn Lite API",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# Temporary Day 2 storage.
# Each chat_id maps to page-aware text records.
# The state is cleared whenever the server restarts.
documents: dict[str, list[PageRecord]] = {}


PAGE_TAG = re.compile(
    r"\[Page\s+(\d+)\]",
    re.IGNORECASE,
)


class ChatRequest(BaseModel):
    """Validated JSON body accepted by POST /chat."""

    chat_id: str = Field(
        default="day2-demo",
        min_length=1,
        max_length=200,
    )

    message: str = Field(
        min_length=2,
        max_length=2000,
    )


def available_page_numbers(
    pages: list[PageRecord],
) -> set[int]:
    """Return page numbers that exist in the current PDF."""
    return {
        int(page["page"])
        for page in pages
    }


def valid_citations(
    answer: str,
    pages: list[PageRecord],
) -> list[int]:
    """Return sorted, distinct cited pages that really exist."""
    available = available_page_numbers(pages)

    mentioned = {
        int(match.group(1))
        for match in PAGE_TAG.finditer(answer)
    }

    return sorted(
        mentioned & available
    )


def remove_invalid_page_tags(
    answer: str,
    pages: list[PageRecord],
) -> str:
    """Remove page tags whose page does not exist."""
    available = available_page_numbers(pages)

    def replace(match: re.Match[str]) -> str:
        page_number = int(match.group(1))

        if page_number in available:
            return f"[Page {page_number}]"

        return ""

    cleaned = PAGE_TAG.sub(replace, answer)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        cleaned,
    )

    return cleaned.strip()


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple API identification response."""
    return {"message": "SmartLearn Lite API"}


@app.get("/health")
def health() -> dict[str, bool]:
    """Return liveness without performing PDF or AI work."""
    return {"ok": True}


@app.post("/upload")
async def upload(
    chat_id: str = Query(
        ...,
        min_length=1,
        description="Temporary identifier connecting upload and chat.",
    ),
    file: UploadFile = File(...),
) -> dict[str, str | int]:
    """Parse a text-based PDF and store page records in memory."""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    try:
        pages = extract_pages(pdf_bytes)
    except (ValueError, PdfReadError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    characters = sum(
        len(page["text"])
        for page in pages
    )

    if characters == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was found in the PDF. "
                "OCR is not supported."
            ),
        )

    documents[chat_id] = pages

    return {
        "status": "ok",
        "filename": file.filename or "uploaded.pdf",
        "pages": len(pages),
        "characters": characters,
    }


@app.post("/chat")
def chat(
    request: ChatRequest,
) -> dict[str, str | list[int]]:
    """Answer one question using an uploaded page-aware document."""
    pages = documents.get(request.chat_id)

    if pages is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "chat_id not found. "
                "Upload a PDF with this chat_id first."
            ),
        )

    try:
        raw_answer = answer_from_pages(
            pages,
            request.message,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI service is temporarily unavailable."
            ),
        ) from error

    citations = valid_citations(
        raw_answer,
        pages,
    )

    answer = remove_invalid_page_tags(
        raw_answer,
        pages,
    )

    return {
        "answer": answer,
        "citations": citations,
    }