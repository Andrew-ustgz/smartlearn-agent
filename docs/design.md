# SmartLearn Agent: Product Design

## Product Goal

SmartLearn Agent is an AI study assistant that helps students understand PDF lecture materials by extracting document content and answering questions with verifiable page citations.

## User Stories

1. As a student, I want to upload a PDF and ask questions about it, so that I can study course materials more efficiently.

2. As a student, I want answers with page citations, so that I can quickly verify the original information in the PDF.

3. As a student, I want to ask follow-up questions in a conversation, so that I can deepen my understanding of difficult topics.

## Feature List

| Priority | Feature | Planned Day |
|----------|---------|-------------|
| P0 | PDF text extraction with source-page preservation | Day 2 |
| P0 | LLM question answering with page citations | Day 2 |
| P1 | RAG pipeline for long PDF documents | Day 3 |
| P1 | Web interface for PDF upload and questions | Day 3 |
| P2 | Conversation history and follow-up questions | Day 3 |

## Priority Definitions

- P0: Required for the core product to work.
- P1: Important for usability and handling larger documents.
- P2: Useful enhancement that can be postponed if time is limited.

## What We Will NOT Build

- User authentication or account management
- Multiple-PDF upload and cross-document search
- Native mobile application
- OCR for scanned or image-only PDFs
- Cloud deployment during the workshop

## Data Flow

### Day 2: Simple Mode

    PDF File
      -> PDF parser and text extraction
      -> pages[] with source page numbers
      -> build prompt from pages and user question
      -> LLM
      -> answer with [Page X] citations

In Simple Mode, the complete extracted PDF text is combined with the user question and sent to the LLM. This approach is suitable for short documents that fit within the model context window.

### Day 3: RAG Mode

    PDF File
      -> extract text
      -> pages
      -> split into chunks
      -> chunks with source_page
      -> create embeddings
      -> vector store using FAISS

    User Question
      -> encode question
      -> similarity search
      -> retrieve relevant chunks
      -> build grounded prompt
      -> LLM
      -> answer with [Page X] citations

RAG Mode sends only the most relevant chunks to the LLM. This reduces irrelevant context and allows the system to handle longer PDF documents more efficiently.

## Planned Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| PDF parser | Extract text and preserve page numbers |
| Chunker | Divide long page text into smaller searchable units |
| Embedding module | Convert chunks and questions into numeric vectors |
| FAISS vector store | Store vectors and retrieve similar chunks |
| Prompt builder | Combine retrieved evidence with the user question |
| LLM client | Generate a grounded answer |
| Web interface | Accept PDF uploads and display cited answers |

## Success Criteria

1. A user can provide a text-based PDF.
2. The system can extract readable content with source page numbers.
3. The user can ask a question about the document.
4. The generated answer is grounded in the document.
5. Important claims include citations in the form [Page X].
6. Long documents can be handled through chunking and similarity retrieval.
