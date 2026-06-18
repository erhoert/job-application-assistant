"""Pydantic data models for job postings, analysis, matching, and applications."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    """Categories a skill can belong to."""

    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"


class ApplicationStatus(str, Enum):
    """Lifecycle stages of a job application."""

    PLANNED = "planned"
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobRequirement(BaseModel):
    """A single requirement extracted from a job posting."""

    skill: str = Field(..., description="Name of the required skill or competency")
    category: SkillCategory = Field(
        ..., description="Category the skill belongs to (technical, soft, language)"
    )
    required: bool = Field(
        True, description="Whether the skill is mandatory or just preferred"
    )


class JobAnalysis(BaseModel):
    """Structured analysis of a job posting produced by Gemini."""

    job_title: str = Field(..., description="Title of the advertised role")
    company: str = Field(..., description="Hiring company name")
    location: str = Field(..., description="Job location (city/region or 'remote')")
    summary: str = Field(..., description="One-paragraph summary of the role")
    key_responsibilities: list[str] = Field(
        default_factory=list,
        description="Main responsibilities of the position",
    )
    requirements: list[JobRequirement] = Field(
        default_factory=list,
        description="Skills and qualifications requested in the posting",
    )
    salary_range: Optional[str] = Field(
        None, description="Salary range as stated in the posting, if any"
    )
    remote_friendly: bool = Field(
        False, description="Whether remote work is allowed or supported"
    )


class SkillMatch(BaseModel):
    """Result of comparing a single job requirement against the user profile."""

    skill: str = Field(..., description="Name of the skill being matched")
    required: bool = Field(
        ..., description="Whether the skill was mandatory in the posting"
    )
    has_skill: bool = Field(
        ..., description="Whether the user possesses this skill"
    )
    match_level: str = Field(
        ...,
        description=(
            "Quality of the match: 'exact', 'partial', or 'missing'"
        ),
    )


class MatchResult(BaseModel):
    """Overall match assessment between a job posting and the user profile."""

    overall_match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Aggregate match score between 0 and 100",
    )
    matched_skills: list[SkillMatch] = Field(
        default_factory=list,
        description="Per-skill match details",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Highlighted strengths relative to the posting",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified skill or experience gaps",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions to improve the candidacy",
    )


class Application(BaseModel):
    """A tracked job application persisted in SQLite."""

    id: Optional[int] = Field(None, description="Primary key assigned by the database")
    company: str = Field(..., description="Company the application is directed at")
    role: str = Field(..., description="Role being applied for")
    status: ApplicationStatus = Field(
        ApplicationStatus.PLANNED,
        description="Current stage in the application lifecycle",
    )
    url: Optional[str] = Field(None, description="URL of the job posting")
    applied_date: Optional[datetime] = Field(
        None, description="Date the application was submitted"
    )
    notes: Optional[str] = Field(None, description="Free-form notes about the application")
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when the record was created"
    )


class Profile(BaseModel):
    """User profile loaded from data/profile.yaml."""

    name: str = Field(..., description="Full name of the user")
    title: str = Field(..., description="Professional title or headline")
    location: str = Field(..., description="User's city and country")
    email: str = Field(..., description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number, if provided")
    summary: str = Field("", description="Short professional summary")
    experience: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of past work experiences",
    )
    skills: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Skills grouped by category (e.g. technical, soft)",
    )
    languages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Spoken languages with proficiency levels",
    )
    education: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Academic and professional education entries",
    )
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences such as cover-letter tone or language",
    )
