# Agent Instructions

## Project: Job Application Assistant

A CLI tool that analyzes job postings, matches them against a user profile,
and finds similar past postings via semantic search — powered by Google Gemini.

## Tech Stack

- Python 3.11+, pip for deps
- google-genai SDK (Gemini 3.5 Flash model + Embeddings API)
- Typer (CLI), Rich (terminal UI), Pydantic (data models)
- SQLite + sqlite-vec (persistence + vector search)
- BeautifulSoup4 + httpx (scraping)
- pytest (testing)

## Architecture Rules

- One responsibility per module
- Pydantic models for ALL structured data
- Gemini structured output (response_schema) for LLM calls
- SQLite for all persistence (applications + vectors)
- Never commit .env, *.db, or output/
- Tests alongside each module

## Code Style

- Use `from __future__ import annotations` in every module
- Type hints everywhere
- Docstrings on all public functions/classes
- Keep functions under 40 lines
- Use Pydantic Field descriptions on all model fields

## Key Conventions

- Profile is loaded from `data/profile.yaml` (gitignored)
- Example profile at `data/profile.example.yaml` (committed)
- DB at `data/applications.db` (gitignored)
- Generated output goes to `output/` (gitignored)
- GEMINI_API_KEY from .env or environment

## Testing

- `pytest -v` runs all tests
- Tests should not require API keys (mock Gemini client)
- SQLite tests use temp files
