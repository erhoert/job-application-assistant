"""Tests for job_assistant.matcher — formatting helpers (no API calls)."""

from __future__ import annotations

from job_assistant.matcher import JobMatcher


def _make_matcher() -> JobMatcher:
    """Create a JobMatcher without invoking __init__ (no GeminiClient needed)."""
    return JobMatcher.__new__(JobMatcher)


def test_format_skills_with_data() -> None:
    """_format_skills should render each category as an indented comma-joined line."""
    matcher = _make_matcher()

    result = matcher._format_skills(
        {
            "technical": ["Python", "SQL", "LLM API integration"],
            "soft": ["Technical writing", "Project management"],
        }
    )

    lines = result.splitlines()
    assert lines[0] == "  technical: Python, SQL, LLM API integration"
    assert lines[1] == "  soft: Technical writing, Project management"


def test_format_skills_empty() -> None:
    """_format_skills should return the empty-state message for an empty dict."""
    matcher = _make_matcher()

    assert matcher._format_skills({}) == "No skills listed"


def test_format_experience_with_data() -> None:
    """_format_experience should render role/company/duration and indented highlights."""
    matcher = _make_matcher()

    result = matcher._format_experience(
        [
            {
                "company": "Acme GmbH",
                "role": "Backend Engineer",
                "duration": "2023 - present",
                "highlights": ["Built event-driven pricing service"],
            }
        ]
    )

    lines = result.splitlines()
    assert lines[0] == "- Backend Engineer at Acme GmbH (2023 - present)"
    assert lines[1] == "  - Built event-driven pricing service"
