"""CLI entry point — Typer commands wiring everything together."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from job_assistant.config import load_env
from job_assistant.database import (
    add_application,
    delete_application,
    get_application,
    get_connection,
    list_applications,
    update_application_status,
)
from job_assistant.display import (
    display_application_detail,
    display_applications,
    display_job_analysis,
    display_match_result,
    display_similar_jobs,
)
from job_assistant.models import ApplicationStatus

app = typer.Typer(
    name="job-assistant",
    help="AI-powered job application assistant.",
    no_args_is_help=True,
)
track_app = typer.Typer(help="Track job applications.")
app.add_typer(track_app, name="track")

console = Console()


def _get_gemini():
    from job_assistant.gemini_client import GeminiClient

    return GeminiClient()


def _get_profile(profile_path: str | None = None):
    from job_assistant.profile import get_default_profile_path, load_profile

    path = Path(profile_path) if profile_path else get_default_profile_path()
    return load_profile(path)


@app.command()
def analyze(
    source: str = typer.Argument(help="Job posting URL or file path"),
    save: bool = typer.Option(False, "--save", help="Save analysis to file"),
):
    """Analyze a job posting and extract structured requirements."""
    load_env()
    from job_assistant.analyzer import JobAnalyzer
    from job_assistant.database import get_connection
    from job_assistant.gemini_client import GeminiClient
    from job_assistant.scraper import get_job_text
    from job_assistant.vector_store import VectorStore

    job_text, url = get_job_text(source)
    client = GeminiClient()
    analyzer = JobAnalyzer(client)
    analysis = analyzer.analyze(job_text)
    display_job_analysis(analysis)

    # Store in vector DB
    conn = get_connection()
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        vs = VectorStore(conn, client)
        vs.store_analysis(analysis, source_url=url)
        console.print("\n[dim]Stored in vector database for semantic search.[/]")
    except Exception as e:
        console.print(f"\n[dim]Vector store skipped: {e}[/]")
    conn.close()

    if save:
        out = Path(
            f"output/analysis_{analysis.company}_{analysis.job_title}.json".replace(
                " ", "_"
            )
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(analysis.model_dump_json(indent=2))
        console.print(f"\n[dim]Saved to {out}[/]")


@app.command()
def match(
    source: str = typer.Argument(help="Job posting URL or file path"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile YAML path"),
):
    """Match a job posting against your profile."""
    load_env()
    from job_assistant.analyzer import JobAnalyzer
    from job_assistant.gemini_client import GeminiClient
    from job_assistant.matcher import JobMatcher
    from job_assistant.scraper import get_job_text

    job_text, _ = get_job_text(source)
    prof = _get_profile(profile)

    client = GeminiClient()
    analyzer = JobAnalyzer(client)
    analysis = analyzer.analyze(job_text)

    matcher = JobMatcher(client)
    result = matcher.match(prof, analysis)

    display_job_analysis(analysis)
    console.print()
    display_match_result(result)


@app.command()
def similar(
    source: str = typer.Argument(help="Job posting URL or file path"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of results"),
):
    """Find similar past job postings via semantic search."""
    load_env()
    from job_assistant.analyzer import JobAnalyzer
    from job_assistant.database import get_connection
    from job_assistant.gemini_client import GeminiClient
    from job_assistant.scraper import get_job_text
    from job_assistant.vector_store import VectorStore

    job_text, _ = get_job_text(source)
    client = GeminiClient()
    analyzer = JobAnalyzer(client)
    analysis = analyzer.analyze(job_text)

    conn = get_connection()
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        vs = VectorStore(conn, client)
        results = vs.find_similar(analysis, limit=limit)
        if results:
            display_similar_jobs(results)
        else:
            console.print(
                "[dim]No stored jobs to compare. Run 'analyze' first to build the database.[/]"
            )
    except Exception as e:
        console.print(f"[red]Vector search failed: {e}[/]")
    conn.close()


@app.command()
def cv(
    source: str = typer.Argument(help="Job posting URL or file path"),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile YAML path"),
):
    """Generate a tailored CV and push to Reactive Resume."""
    load_env()
    from job_assistant.analyzer import JobAnalyzer
    from job_assistant.cv_generator import CVGenerator
    from job_assistant.gemini_client import GeminiClient
    from job_assistant.matcher import JobMatcher
    from job_assistant.scraper import get_job_text

    job_text, _ = get_job_text(source)
    prof = _get_profile(profile)

    client = GeminiClient()
    analyzer = JobAnalyzer(client)
    analysis = analyzer.analyze(job_text)

    matcher = JobMatcher(client)
    match_result = matcher.match(prof, analysis)

    display_job_analysis(analysis)
    console.print()
    display_match_result(match_result)
    console.print("\n[bold magenta]Generating tailored CV...[/]")

    generator = CVGenerator(client, rr_client=None)
    result = asyncio.run(generator.generate(prof, analysis, match_result))

    console.print(
        f"\n[green]✅ Resume created in Reactive Resume![/]"
        f"\n  Resume ID: {result.get('resume_id', 'N/A')}"
        f"\n  PDF URL: {result.get('pdf_url', 'N/A')}"
    )


@app.command(name="mail-watch")
def mail_watch(
    days: int = typer.Option(7, "--days", "-d", help="Days to look back"),
):
    """Scan emails for application updates and update tracker."""
    load_env()
    from job_assistant.mail_watcher import watch_mail

    updates = watch_mail(days=days)

    if not updates:
        console.print("[dim]No application-related email updates found.[/]")
        return

    console.print(f"\n[green]Found {len(updates)} update(s):[/]")
    for u in updates:
        console.print(
            f"  App #{u['app_id']} → [yellow]{u['status']}[/]"
            f"  ({u['email_subject'][:60]})"
        )


@track_app.command("add")
def track_add(
    company: str = typer.Argument(help="Company name"),
    role: str = typer.Argument(help="Job title/role"),
    url: Optional[str] = typer.Option(None, "--url", help="Job posting URL"),
    status: ApplicationStatus = typer.Option(
        ApplicationStatus.PLANNED, "--status", "-s", help="Initial status"
    ),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes"),
):
    """Add a new application to track."""
    conn = get_connection()
    app_id = add_application(conn, company, role, status, url, notes)
    console.print(f"[green]✅ Added application #{app_id}: {role} at {company}[/]")
    conn.close()


@track_app.command("list")
def track_list():
    """List all tracked applications."""
    conn = get_connection()
    apps = list_applications(conn)
    display_applications(apps)
    conn.close()


@track_app.command("update")
def track_update(
    app_id: int = typer.Argument(help="Application ID"),
    status: ApplicationStatus = typer.Option(
        None, "--status", "-s", help="New status"
    ),
):
    """Update an application's status."""
    if status is None:
        console.print("[red]Please provide --status[/]")
        raise typer.Exit(1)
    conn = get_connection()
    if update_application_status(conn, app_id, status):
        console.print(
            f"[green]✅ Updated application #{app_id} to '{status.value}'[/]"
        )
    else:
        console.print(f"[red]Application #{app_id} not found[/]")
    conn.close()


@track_app.command("show")
def track_show(
    app_id: int = typer.Argument(help="Application ID"),
):
    """Show details of a specific application."""
    conn = get_connection()
    app = get_application(conn, app_id)
    if app:
        display_application_detail(app)
    else:
        console.print(f"[red]Application #{app_id} not found[/]")
    conn.close()


@track_app.command("delete")
def track_delete(
    app_id: int = typer.Argument(help="Application ID"),
):
    """Delete a tracked application."""
    conn = get_connection()
    if delete_application(conn, app_id):
        console.print(f"[green]✅ Deleted application #{app_id}[/]")
    else:
        console.print(f"[red]Application #{app_id} not found[/]")
    conn.close()


if __name__ == "__main__":
    app()
