# SmartLearn Agent

## Project

SmartLearn Agent is an AI-powered learning assistant that parses PDF lecture slides and answers students' course-related questions.

## Tech Stack

- Backend: Python and FastAPI
- Frontend: React and Vite
- LLM API: DeepSeek through an OpenAI-compatible endpoint
- Python exercise model: deepseek-v4-flash
- Vector search: FAISS, planned for Day 3

## AI Coding Environment

- Claude Code uses DeepSeek through ANTHROPIC_BASE_URL
- Python exercises currently call DeepSeek directly through https://api.deepseek.com
- Claude Code and the Python exercises use separate API protocols
- Never place API keys in source code or documentation

## Project Commands

- Activate environment: .\venv\Scripts\Activate.ps1
- Run first API example: python hello_llm.py
- Run prompt experiment: python experiments\prompt_lab.py
- Check Python syntax: python -m py_compile <file>
- Check repository status: git status --short

## Conventions

- Store API keys only in .env
- Never commit .env
- Use venv for Python dependencies
- Use clear functions and descriptive variable names
- Handle missing configuration and API errors
- Commit messages use type: description
- Valid types include feat, fix, docs, refactor, test, and chore
- Review Git changes before every commit

## Do Not Modify

- .env
- package-lock.json
- venv
- .git directory

## Current Progress

- hello_llm.py has completed a successful DeepSeek API call
- experiments/prompt_lab.py compares three prompt specificity levels
- The next task is the command-line cited Q&A tool
