# 🎯 Job Application Assistant

AI-powered CLI tool that analyzes job postings, matches them against your profile,
finds similar past postings via semantic search, generates tailored CVs via
Reactive Resume MCP, monitors application emails, and tracks applications.

## Features

- 🔍 **Job Analysis** — Extract structured requirements from any job posting (URL or file)
- 🎯 **Profile Matching** — See your fit score, strengths, and skill gaps
- 🔎 **Semantic Search** — Find similar past job postings using vector embeddings (sqlite-vec)
- 📄 **CV Generation** — AI-tailored resume pushed to Reactive Resume via MCP
- 📧 **Email Monitoring** — Scan notmuch for application updates, auto-classify and update tracker
- 📋 **Application Tracking** — SQLite-backed tracker for all your applications

## Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key (free tier at [AI Studio](https://aistudio.google.com))
- [Reactive Resume](https://rxresu.me) running locally (for CV generation)
- `notmuch` + `mbsync` (for email monitoring)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/job-application-assistant.git
cd job-application-assistant
make install
```

### Configuration

1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com)
2. Copy the environment template:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```
3. Create your profile:
   ```bash
   cp data/profile.example.yaml data/profile.yaml
   # Edit with your experience, skills, etc.
   ```
4. (Optional) Set up Reactive Resume API key for CV generation:
   - Create an API key in the RR web UI
   - Add `RR_API_KEY=your-key` to `.env`

## Usage

```bash
# Analyze a job posting
job-assistant analyze "https://company.com/careers/senior-csm"

# Match against your profile
job-assistant match "https://company.com/careers/senior-csm"

# Find similar past job postings
job-assistant similar "https://company.com/careers/senior-csm"

# Generate a tailored CV and push to Reactive Resume
job-assistant cv "https://company.com/careers/senior-csm"

# Scan emails for application updates
job-assistant mail-watch --days 7

# Track applications
job-assistant track add "Company" "Role" --url "https://..."
job-assistant track list
job-assistant track update 1 --status interview
job-assistant track show 1
job-assistant track delete 1
```

## Architecture

```
Job Posting (URL/File)
       │
       ▼
   Scraper ──→ Analyzer (Gemini structured output)
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Matcher    CV Generator   Vector Store
       │            │            │
       ▼            ▼            ▼
  Match Result   RR MCP      Semantic Search
       │         Resume          │
       │            │            ▼
       │     PDF Download    Similar Jobs
       │
       ▼
  Application Tracker (SQLite)
       ▲
       │
  Mail Watcher (notmuch → Gemini → status update)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini API (gemini-3.5-flash + embeddings) |
| CLI | Typer |
| Data Models | Pydantic |
| Terminal UI | Rich |
| Persistence | SQLite |
| Vector Search | sqlite-vec |
| Resume Generation | Reactive Resume MCP Server |
| Email Monitoring | notmuch + mbsync |
| Scraping | BeautifulSoup4 + httpx |
| Testing | pytest |

## Project Structure

```
src/job_assistant/
├── cli.py           # Typer CLI — all commands
├── models.py        # Pydantic data models
├── config.py        # Environment / API key loading
├── gemini_client.py # Gemini API wrapper (text, structured, embeddings)
├── scraper.py       # URL/file → text extraction
├── analyzer.py      # Job posting → structured analysis
├── matcher.py       # Profile vs job → fit score, gaps
├── vector_store.py  # sqlite-vec semantic search
├── rr_client.py     # Reactive Resume MCP client
├── cv_generator.py  # AI-tailored CV generation
├── mail_watcher.py  # Email scanning + classification
├── database.py      # SQLite application tracker
├── display.py       # Rich terminal output
└── profile.py       # YAML profile loader
```

## Testing

```bash
pytest -v  # 32 tests, no API keys required
```

## License

MIT
