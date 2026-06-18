"""Tests for the Pydantic data models in job_assistant.models."""

from __future__ import annotations

from datetime import datetime

import pytest

from job_assistant.models import (
    Application,
    ApplicationStatus,
    JobAnalysis,
    JobRequirement,
    MatchResult,
    Profile,
    SkillCategory,
    SkillMatch,
)


def test_job_analysis_creation_with_requirements() -> None:
    """JobAnalysis should store all fields and nested requirements."""
    requirements = [
        JobRequirement(skill="Python", category=SkillCategory.TECHNICAL, required=True),
        JobRequirement(
            skill="Cross-functional communication",
            category=SkillCategory.SOFT,
            required=False,
        ),
        JobRequirement(skill="German", category=SkillCategory.LANGUAGE, required=True),
    ]

    analysis = JobAnalysis(
        job_title="Backend Engineer",
        company="Acme GmbH",
        location="Berlin, Germany",
        summary="Build and operate Python services.",
        key_responsibilities=["Design APIs", "Maintain CI/CD"],
        requirements=requirements,
        salary_range="€70k-€90k",
        remote_friendly=True,
    )

    assert analysis.job_title == "Backend Engineer"
    assert analysis.company == "Acme GmbH"
    assert analysis.remote_friendly is True
    assert analysis.salary_range == "€70k-€90k"
    assert len(analysis.requirements) == 3

    python_req = analysis.requirements[0]
    assert python_req.skill == "Python"
    assert python_req.category is SkillCategory.TECHNICAL
    assert python_req.required is True

    soft_req = analysis.requirements[1]
    assert soft_req.category is SkillCategory.SOFT
    assert soft_req.required is False


def test_job_analysis_defaults() -> None:
    """Optional and defaulted fields should have sensible defaults."""
    analysis = JobAnalysis(
        job_title="DevOps Engineer",
        company="Foo Inc.",
        location="Remote",
        summary="Keep the platform running.",
    )

    assert analysis.requirements == []
    assert analysis.key_responsibilities == []
    assert analysis.salary_range is None
    assert analysis.remote_friendly is False


def test_application_defaults() -> None:
    """A freshly created Application should default to PLANNED and empty optionals."""
    application = Application(company="Acme GmbH", role="Backend Engineer")

    assert application.id is None
    assert application.status is ApplicationStatus.PLANNED
    assert application.url is None
    assert application.applied_date is None
    assert application.notes is None
    assert application.created_at is None


def test_application_with_explicit_values() -> None:
    """Application should accept explicit values for all fields."""
    applied = datetime(2026, 6, 18, 9, 30)
    created = datetime(2026, 6, 18, 8, 0)

    application = Application(
        id=42,
        company="Acme GmbH",
        role="Backend Engineer",
        status=ApplicationStatus.INTERVIEW,
        url="https://example.com/jobs/42",
        applied_date=applied,
        notes="Recruiter: Jane Doe",
        created_at=created,
    )

    assert application.id == 42
    assert application.status is ApplicationStatus.INTERVIEW
    assert application.url == "https://example.com/jobs/42"
    assert application.applied_date == applied
    assert application.created_at == created


def test_profile_from_dict() -> None:
    """Profile should be constructible from a dict like the example YAML."""
    data = {
        "name": "Jane Doe",
        "title": "Backend Engineer",
        "location": "Berlin, Germany",
        "email": "jane.doe@example.com",
        "phone": "+49-30-1234567",
        "summary": "Python backend engineer with 5 years of experience.",
        "experience": [
            {
                "company": "Acme GmbH",
                "role": "Backend Engineer",
                "duration": "2023 - present",
                "highlights": ["Built event-driven pricing service"],
            }
        ],
        "skills": {
            "technical": ["Python", "SQL", "LLM API integration"],
            "soft": ["Technical writing", "Project management"],
        },
        "languages": [
            {"language": "German", "level": "native"},
            {"language": "English", "level": "C2"},
        ],
        "education": [
            {
                "degree": "B.Sc. Computer Science",
                "institution": "TU Berlin",
                "year": "2020",
            }
        ],
        "preferences": {
            "cover_letter_tone": "professional_warm",
            "cover_letter_language": "english",
        },
    }

    profile = Profile(**data)

    assert profile.name == "Jane Doe"
    assert profile.title == "Backend Engineer"
    assert profile.email == "jane.doe@example.com"
    assert profile.phone == "+49-30-1234567"
    assert profile.summary.startswith("Python backend")
    assert len(profile.experience) == 1
    assert profile.experience[0]["company"] == "Acme GmbH"
    assert profile.skills["technical"] == ["Python", "SQL", "LLM API integration"]
    assert profile.languages[0]["language"] == "German"
    assert profile.education[0]["degree"] == "B.Sc. Computer Science"
    assert profile.preferences["cover_letter_tone"] == "professional_warm"


def test_profile_defaults() -> None:
    """Profile optional collections should default to empty containers."""
    profile = Profile(
        name="Jane Doe",
        title="Backend Engineer",
        location="Berlin, Germany",
        email="jane.doe@example.com",
    )

    assert profile.phone is None
    assert profile.summary == ""
    assert profile.experience == []
    assert profile.skills == {}
    assert profile.languages == []
    assert profile.education == []
    assert profile.preferences == {}


def test_match_result_score_bounds() -> None:
    """MatchResult overall_match_score must accept the documented bounds."""
    result = MatchResult(
        overall_match_score=87.5,
        matched_skills=[
            SkillMatch(skill="Python", required=True, has_skill=True, match_level="exact"),
            SkillMatch(
                skill="Rust", required=True, has_skill=False, match_level="missing"
            ),
        ],
        strengths=["Strong Python background"],
        gaps=["No Rust experience"],
        recommendations=["Highlight transferable systems knowledge"],
    )

    assert result.overall_match_score == 87.5
    assert result.matched_skills[0].match_level == "exact"
    assert result.matched_skills[1].match_level == "missing"
    assert result.gaps == ["No Rust experience"]


def test_match_result_score_out_of_bounds_rejected() -> None:
    """Scores outside 0-100 should be rejected by Pydantic validation."""
    with pytest.raises(ValueError):
        MatchResult(overall_match_score=120.0)

    with pytest.raises(ValueError):
        MatchResult(overall_match_score=-5.0)
