"""Tests for job_assistant.profile — YAML loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from job_assistant.profile import get_default_profile_path, load_profile


VALID_YAML = """\
name: "Jane Doe"
title: "Backend Engineer"
location: "Berlin, Germany"
email: "jane.doe@example.com"
phone: "+49-30-1234567"
summary: "Python backend engineer with 5 years of experience."
experience:
  - company: "Acme GmbH"
    role: "Backend Engineer"
    duration: "2023 - present"
    highlights:
      - "Built event-driven pricing service"
skills:
  technical:
    - "Python"
    - "SQL"
    - "LLM API integration"
  soft:
    - "Technical writing"
    - "Project management"
languages:
  - language: "German"
    level: "native"
  - language: "English"
    level: "C2"
education:
  - degree: "B.Sc. Computer Science"
    institution: "TU Berlin"
    year: "2020"
preferences:
  cover_letter_tone: "professional_warm"
  cover_letter_language: "english"
"""


def test_load_profile_valid_yaml(tmp_path: Path) -> None:
    """A well-formed YAML profile should load and validate into a Profile."""
    profile_file = tmp_path / "profile.yaml"
    profile_file.write_text(VALID_YAML, encoding="utf-8")

    profile = load_profile(profile_file)

    assert profile.name == "Jane Doe"
    assert profile.title == "Backend Engineer"
    assert profile.location == "Berlin, Germany"
    assert profile.email == "jane.doe@example.com"
    assert profile.phone == "+49-30-1234567"
    assert profile.summary.startswith("Python backend")
    assert len(profile.experience) == 1
    assert profile.experience[0]["company"] == "Acme GmbH"
    assert profile.languages[0]["language"] == "German"
    assert profile.education[0]["degree"] == "B.Sc. Computer Science"
    assert profile.preferences["cover_letter_tone"] == "professional_warm"


def test_load_profile_missing_file_raises(tmp_path: Path) -> None:
    """Loading a non-existent file should raise FileNotFoundError."""
    missing = tmp_path / "does_not_exist.yaml"

    with pytest.raises(FileNotFoundError):
        load_profile(missing)


def test_load_profile_skills_dict_parsed(tmp_path: Path) -> None:
    """The skills mapping should be parsed into a dict of lists keyed by category."""
    profile_file = tmp_path / "profile.yaml"
    profile_file.write_text(VALID_YAML, encoding="utf-8")

    profile = load_profile(profile_file)

    assert isinstance(profile.skills, dict)
    assert set(profile.skills.keys()) == {"technical", "soft"}
    assert profile.skills["technical"] == ["Python", "SQL", "LLM API integration"]
    assert profile.skills["soft"] == ["Technical writing", "Project management"]


def test_get_default_profile_path() -> None:
    """The default profile path should point at data/profile.yaml."""
    assert get_default_profile_path() == Path("data/profile.yaml")
