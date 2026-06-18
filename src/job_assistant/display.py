"""Rich-based terminal display for job analyses, match results, and applications."""

from __future__ import annotations

from job_assistant.models import Application, ApplicationStatus, JobAnalysis, MatchResult
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()

_STATUS_COLORS: dict[ApplicationStatus, str] = {
    ApplicationStatus.PLANNED: "cyan",
    ApplicationStatus.APPLIED: "blue",
    ApplicationStatus.PHONE_SCREEN: "magenta",
    ApplicationStatus.INTERVIEW: "yellow",
    ApplicationStatus.OFFER: "green",
    ApplicationStatus.REJECTED: "red",
    ApplicationStatus.WITHDRAWN: "dim",
}


def _score_color(score: float) -> str:
    """Return a Rich color name based on a match score.

    Args:
        score: Match score between 0 and 100.

    Returns:
        ``'green'`` for scores >= 75, ``'yellow'`` for >= 50, else ``'red'``.
    """
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _similarity_color(similarity: float) -> str:
    """Return a Rich color name based on a similarity percentage.

    Args:
        similarity: Similarity percentage between 0 and 100.

    Returns:
        ``'green'`` for similarity > 70, ``'yellow'`` for > 50, else ``'red'``.
    """
    if similarity > 70:
        return "green"
    if similarity > 50:
        return "yellow"
    return "red"


def _status_color(status: ApplicationStatus) -> str:
    """Return a Rich color name for an application status.

    Args:
        status: The application lifecycle status.

    Returns:
        A Rich color name associated with the status, defaulting to ``'white'``.
    """
    return _STATUS_COLORS.get(status, "white")


def display_job_analysis(analysis: JobAnalysis) -> None:
    """Render a JobAnalysis as a panel with info table, summary, and requirements.

    Args:
        analysis: The structured job posting analysis to display.
    """
    info = Table.grid(padding=(0, 1))
    info.add_column(style="bold")
    info.add_column()
    info.add_row("Location", analysis.location)
    info.add_row("Remote", "Yes" if analysis.remote_friendly else "No")
    info.add_row("Salary", analysis.salary_range or "Not specified")

    responsibilities = "\n".join(f"- {r}" for r in analysis.key_responsibilities)

    requirements = Table(title="Requirements", show_header=True, header_style="bold")
    requirements.add_column("Skill")
    requirements.add_column("Category")
    requirements.add_column("Level")
    for req in analysis.requirements:
        requirements.add_row(
            req.skill,
            req.category.value,
            "Required" if req.required else "Preferred",
        )

    console.print(
        Panel(
            f"[bold]{analysis.job_title}[/bold] @ {analysis.company}",
            title="Job Analysis",
        )
    )
    console.print(info)
    console.print(Panel(Markdown(analysis.summary), title="Summary"))
    if responsibilities:
        console.print(Panel(responsibilities, title="Key Responsibilities"))
    if analysis.requirements:
        console.print(requirements)


def display_match_result(result: MatchResult) -> None:
    """Render a MatchResult with color-coded score, strengths, gaps, and recommendations.

    Args:
        result: The match assessment to display.
    """
    color = _score_color(result.overall_match_score)
    console.print(
        Panel(
            f"[{color}]Match Score: {result.overall_match_score:.1f}/100[/{color}]",
            title="Match Result",
        )
    )
    if result.strengths:
        console.print(
            Panel(
                "\n".join(f"[green]\u2713 {s}[/green]" for s in result.strengths),
                title="Strengths",
            )
        )
    if result.gaps:
        console.print(
            Panel(
                "\n".join(f"[red]\u2717 {g}[/red]" for g in result.gaps),
                title="Gaps",
            )
        )
    if result.recommendations:
        console.print(
            Panel(
                "\n".join(
                    f"[yellow]\U0001f4a1 {r}[/yellow]" for r in result.recommendations
                ),
                title="Recommendations",
            )
        )


def display_similar_jobs(results: list[dict]) -> None:
    """Render a table of similar jobs with color-coded similarity percentages.

    Args:
        results: List of dicts with keys ``id``, ``company``, ``role``, and
            ``similarity``.
    """
    table = Table(title="Similar Jobs", show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Company")
    table.add_column("Role")
    table.add_column("Similarity %", justify="right")
    for row in results:
        similarity = float(row.get("similarity", 0.0))
        color = _similarity_color(similarity)
        table.add_row(
            str(row.get("id", "")),
            str(row.get("company", "")),
            str(row.get("role", "")),
            f"[{color}]{similarity:.1f}%[/{color}]",
        )
    console.print(table)


def display_applications(applications: list[Application]) -> None:
    """Render a table of applications with color-coded status.

    Args:
        applications: List of Application instances to display. If empty, an
            informational message is printed instead.
    """
    if not applications:
        console.print("No applications tracked yet.")
        return
    table = Table(title="Applications", show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Company")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Created")
    for app in applications:
        color = _status_color(app.status)
        created = app.created_at.strftime("%Y-%m-%d") if app.created_at else "N/A"
        table.add_row(
            str(app.id) if app.id is not None else "-",
            app.company,
            app.role,
            f"[{color}]{app.status.value}[/{color}]",
            created,
        )
    console.print(table)


def display_application_detail(app: Application) -> None:
    """Render a single Application's full details inside a panel.

    Args:
        app: The Application instance to display.
    """
    color = _status_color(app.status)
    applied = (
        app.applied_date.strftime("%Y-%m-%d") if app.applied_date else "N/A"
    )
    created = (
        app.created_at.strftime("%Y-%m-%d %H:%M") if app.created_at else "N/A"
    )
    lines = [
        f"[bold]Company:[/bold] {app.company}",
        f"[bold]Role:[/bold] {app.role}",
        f"[bold]Status:[/bold] [{color}]{app.status.value}[/{color}]",
        f"[bold]URL:[/bold] {app.url or 'N/A'}",
        f"[bold]Applied:[/bold] {applied}",
        f"[bold]Created:[/bold] {created}",
        f"[bold]Notes:[/bold] {app.notes or 'None'}",
    ]
    console.print(Panel("\n".join(lines), title=f"Application #{app.id}"))
