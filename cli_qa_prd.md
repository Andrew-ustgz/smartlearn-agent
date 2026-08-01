# CLI Cited Q&A Tool PRD

## Goal

Build a command-line question-answering tool that accepts reference text and answers questions using only that text.

## Usage Modes

### Interactive text input

Run:

python cli_qa.py

The user pastes one or more paragraphs and enters END on a separate line to finish the reference text.

### File input

Run:

python cli_qa.py --file sample.txt

The tool loads reference text from the specified UTF-8 text file.

## Functional Requirements

1. Accept multiple paragraphs of reference text.
2. Number all non-empty paragraphs starting from Paragraph 1.
3. Allow the user to ask multiple questions.
4. Continue accepting questions until the user enters quit.
5. Answer using only the supplied reference text.
6. Every supported answer must contain one or more citations in the exact form [Paragraph X].
7. When the reference text does not contain the requested information, return exactly:

The text does not provide this information.

8. Empty reference text must produce a friendly error.
9. Empty reference text must not trigger an API call.
10. A missing file path must produce a friendly error without a traceback.

## Technical Requirements

- Use Python.
- Use python-dotenv to load OPENROUTER_API_KEY from .env.
- Use the OpenAI Python SDK pointed at the OpenRouter base URL.
- Provider: OpenRouter
- Base URL: https://openrouter.ai/api/v1
- Model: google/gemma-4-26b-a4b-it:free
- Never print or expose the API key.
- Keep the implementation in cli_qa.py.
- Do not add a web interface, database, vector store, OCR, or deployment files.

## Error Handling

Handle these cases with clear messages:

- Missing API key
- Empty text
- Missing input file
- Empty input file
- File decoding error
- API request failure
- Empty model response

## Acceptance Tests

### Syntax test

python -m py_compile cli_qa.py

### Citation test

Given a reference text where Paragraph 1 states who created Python, the answer must cite [Paragraph 1].

### Multiple paragraph test

Questions about different paragraphs must cite the corresponding paragraph numbers.

### Unsupported question test

A question whose answer is absent must return exactly:

The text does not provide this information.

### Multi-turn test

The user can ask several questions in one run and enter quit to exit.

### File mode test

python cli_qa.py --file sample.txt

must load the file and support multiple questions.

### Empty input test

Entering END before any text must show a friendly error without calling the API.

## Done When

1. cli_qa.py passes the syntax test.
2. Interactive text input works.
3. File input works.
4. Multi-turn questions work.
5. Supported answers include paragraph citations.
6. Unsupported questions return the exact fallback sentence.
7. Empty input is handled locally.
8. .env remains ignored by Git.
