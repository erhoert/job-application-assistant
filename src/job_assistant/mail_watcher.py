"""Mail Watcher — scans notmuch for application-related emails and updates tracker."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from typing import Any

from rich.console import Console

from job_assistant.database import get_connection, list_applications, update_application_status
from job_assistant.gemini_client import GeminiClient
from job_assistant.models import ApplicationStatus

console = Console()

# Keywords that indicate application-related emails
SEARCH_KEYWORDS = [
    "bewerbung",
    "application",
    "interview",
    "vorstellungsgespräch",
    "job offer",
    "angebot",
    "rejected",
    "absage",
    "position",
    "candidate",
    "recruiting",
    "hiring",
]

# Gemini classification prompt
CLASSIFY_PROMPT = """You are an email classifier for job applications.
Read this email and determine what application status it represents.

Email Subject: {subject}
Email From: {sender}
Email Snippet: {snippet}

Classify into exactly ONE of these statuses:
- "applied" — confirmation that application was received
- "phone_screen" — phone screening invitation
- "interview" — interview invitation or scheduling
- "offer" — job offer
- "rejected" — rejection or "moved forward with other candidates"
- "withdrawn" — candidate withdrew (rare)
- "unknown" — cannot determine or not application-related

Respond with ONLY the status word, nothing else."""


def sync_mail() -> None:
    """Sync local mail via margarete-mail-sync."""
    try:
        subprocess.run(
            ["/home/erik/.local/bin/margarete-mail-sync"],
            capture_output=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[dim]Mail sync skipped (timeout or not available)[/]")


def search_application_emails(days: int = 7) -> list[dict[str, Any]]:
    """Search notmuch for application-related emails in the last N days."""
    date_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query_parts = [f"date:{date_str}.."]
    query_parts.append(f"({' OR '.join(f'subject:{kw}' for kw in SEARCH_KEYWORDS)})")

    # Also search body for keywords but keep it broad
    full_query = f"date:{date_str}.. and (subject:bewerbung OR subject:application OR subject:interview OR subject:offer OR subject:absage OR subject:position)"

    try:
        result = subprocess.run(
            ["notmuch", "search", "--format=json", full_query],
            capture_output=True,
            text=True,
            timeout=30,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []

    emails = []
    for item in data:
        emails.append(
            {
                "thread_id": item.get("thread", ""),
                "subject": item.get("subject", ""),
                "authors": item.get("authors", ""),
                "date_relative": item.get("date_relative", ""),
                "timestamp": item.get("timestamp", 0),
            }
        )
    return emails


def classify_email(
    email: dict[str, Any], gemini: GeminiClient
) -> ApplicationStatus | None:
    """Use Gemini to classify an email into an application status."""
    prompt = CLASSIFY_PROMPT.format(
        subject=email.get("subject", ""),
        sender=email.get("authors", ""),
        snippet=email.get("subject", ""),  # notmuch search only gives subject
    )
    try:
        result = gemini.generate_text(prompt, system_instruction=None).strip().lower()
        status_map = {
            "applied": ApplicationStatus.APPLIED,
            "phone_screen": ApplicationStatus.PHONE_SCREEN,
            "interview": ApplicationStatus.INTERVIEW,
            "offer": ApplicationStatus.OFFER,
            "rejected": ApplicationStatus.REJECTED,
            "withdrawn": ApplicationStatus.WITHDRAWN,
        }
        return status_map.get(result)
    except Exception:
        return None


def match_email_to_application(
    email: dict[str, Any], applications: list
) -> int | None:
    """Match an email to a tracked application by company name in subject/sender.

    Returns the application ID if matched, None otherwise.
    """
    text = f"{email.get('subject', '')} {email.get('authors', '')}".lower()
    best_match = None
    best_score = 0

    for app in applications:
        company = app.company.lower()
        if len(company) < 3:
            continue
        # Simple fuzzy: check if company name appears in email text
        if company in text:
            score = len(company)
            if score > best_score:
                best_score = score
                best_match = app.id

    return best_match


def watch_mail(
    days: int = 7,
    db_path: str = "data/applications.db",
    gemini: GeminiClient | None = None,
) -> list[dict[str, Any]]:
    """Full mail watch pipeline: sync, search, classify, update tracker.

    Returns list of updates made.
    """
    sync_mail()
    emails = search_application_emails(days)

    if not emails:
        console.print("[dim]No application-related emails found.[/]")
        return []

    conn = get_connection(db_path)
    applications = list_applications(conn)
    updates: list[dict[str, Any]] = []

    if not applications:
        console.print("[dim]No tracked applications to match against.[/]")
        conn.close()
        return []

    client = gemini or GeminiClient()

    for email in emails:
        app_id = match_email_to_application(email, applications)
        if not app_id:
            continue

        status = classify_email(email, client)
        if not status:
            continue

        # Update the application
        update_application_status(conn, app_id, status)
        updates.append(
            {
                "app_id": app_id,
                "status": status.value,
                "email_subject": email.get("subject", ""),
                "email_date": email.get("date_relative", ""),
            }
        )

    conn.close()
    return updates
