# PDF Summary Tool PRD

## Goal

Build a command-line tool that reads a PDF file, extracts page-level text, sends the extracted content to an LLM, and prints a structured summary with page citations.

## Usage

python pdf_summary.py <path-to-pdf>

Example:

python pdf_summary.py lecture.pdf

## Required Output

The output must contain exactly these three Markdown sections:

## Overview

A concise overview of the PDF.

## Key Points

- Three to five important points.
- Every key point must end with a citation in the exact form [Page X].
- When one point depends on multiple pages, use separate citations such as [Page 2] [Page 4].

## Limitations

Describe missing text, extraction limitations, insufficient context, or other relevant caveats.

## Functional Requirements

1. Accept one PDF file path as a positional command-line argument.
2. Verify that the supplied path exists.
3. Verify that the supplied path refers to a PDF file.
4. Extract text page by page.
5. Preserve the source page number for every extracted page.
6. Ignore pages that contain no extractable text.
7. Do not send an empty prompt to the API.
8. Send the extracted page text to the LLM through OpenRouter.
9. Print Overview, Key Points, and Limitations.
10. Every Key Points bullet must end with at least one valid [Page X] citation.
11. Do not print the extracted PDF text during normal operation.
12. Do not print or expose the API key.

## API Configuration

- Provider: OpenRouter
- Base URL: https://openrouter.ai/api/v1
- Environment variable: OPENROUTER_API_KEY
- Model: google/gemma-4-26b-a4b-it:free
- Python SDK: openai

## PDF Library

The implementation agent may choose one suitable text-based PDF extraction library.

The agent must explain:

1. Which PDF library it selected
2. Why it selected that library
3. One limitation of that library

Do not add OCR.

## Error Handling

Handle these conditions with clear messages and no traceback:

- Missing command-line argument
- File does not exist
- Path is not a file
- File extension is not .pdf
- PDF cannot be opened
- PDF is encrypted or unreadable
- PDF contains no extractable text
- Missing OPENROUTER_API_KEY
- API request failure
- Empty model response
- Output missing required headings
- Key Points missing valid page citations

## Technical Constraints

- Use Python.
- Use argparse.
- Use python-dotenv.
- Use the OpenAI Python SDK.
- Load OPENROUTER_API_KEY from .env.
- Keep the main implementation in pdf_summary.py.
- Do not read, print, expose, or modify .env.
- Do not modify hello_llm.py, experiments/prompt_lab.py, or cli_qa.py.
- Do not add a web interface.
- Do not add a database.
- Do not add a vector store.
- Do not add OCR.
- Do not add deployment files.
- Do not add unrelated dependencies.

## Acceptance Tests

### Syntax Test

python -m py_compile pdf_summary.py

Expected result: exit code 0 with no syntax error.

### Missing File Test

python pdf_summary.py does-not-exist.pdf

Expected result: friendly error with no traceback and no API call.

### Non-PDF Test

python pdf_summary.py README.md

Expected result: friendly error explaining that a PDF file is required.

### Valid PDF Test

python pdf_summary.py <short-text-based-pdf>

Use a PDF under 10 pages with selectable text.

Expected output:

## Overview

A concise summary.

## Key Points

- A verifiable point from the document [Page 1].
- Another verifiable point [Page 2].

## Limitations

Any extraction or context limitations.

### Image-Only PDF Test

Use a scanned or image-only PDF.

Expected result: explain that no extractable text was found and do not call the API.

## Done When

1. pdf_summary.py passes the syntax test.
2. Missing files are handled without a traceback.
3. Non-PDF files are rejected locally.
4. A short text-based PDF produces all three required sections.
5. Every Key Points bullet ends with a valid [Page X] citation.
6. An image-only PDF is rejected before the API call.
7. .env remains ignored by Git.
8. No unrelated files are created or modified.
