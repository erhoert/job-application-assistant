# 🎯 Job Application Assistant

AI-powered CLI tool that analyzes job postings, matches them against your profile,
finds similar past postings via semantic search, and tracks applications.

## Features

- 🔍 **Job Analysis** — Extract structured requirements from any job posting (URL or file)
- 🎯 **Profile Matching** — See your fit score, strengths, and skill gaps
- 🔎 **Semantic Search** — Find similar past job postings using vector embeddings
- 📋 **Application Tracking** — SQLite-backed tracker for all your applications

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/job-application-assistant.git
cd job-application-assistant
make install
cp .env.example .env  # Add your GEMINI_API_KEY
cp data/profile.example.yaml data/profile.yaml  # Add your profile
```

## Usage

```bash
job-assistant analyze "https://company.com/careers/senior-csm"
job-assistant match "https://company.com/careers/senior-csm"
job-assistant similar "https://company.com/careers/senior-csm"
job-assistant track add "Company" "Role" --url "https://..."
job-assistant track list
```

## Tech Stack

Google Gemini API · Typer · Pydantic · Rich · SQLite + sqlite-vec · BeautifulSoup4

## License

MIT
