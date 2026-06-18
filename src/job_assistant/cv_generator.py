"""CV Generator — generates tailored resume data and pushes to Reactive Resume."""

from __future__ import annotations

import json
import uuid
from typing import Any

from job_assistant.gemini_client import GeminiClient
from job_assistant.models import JobAnalysis, MatchResult, Profile
from job_assistant.rr_client import ReactiveResumeClient


SYSTEM_INSTRUCTION = """You are an expert resume writer who creates tailored,
professional resumes. You adapt the candidate's experience to highlight
relevance to the specific job. You write in a natural, achievement-focused style.
You never fabricate experience — you only reframe and reorder existing information."""


GENERATE_CV_PROMPT = """Create a tailored resume for this job application.

## Candidate Profile
Name: {name}
Title: {title}
Location: {location}
Email: {email}
Phone: {phone}
Summary: {summary}

Experience:
{experience}

Skills:
{skills}

Languages:
{languages}

Education:
{education}

## Target Job
Title: {job_title}
Company: {company}
Location: {job_location}
Remote: {remote}

Key Responsibilities:
{responsibilities}

Requirements:
{requirements}

## Match Analysis
Match Score: {match_score}/100
Strengths: {strengths}
Gaps: {gaps}

## Instructions
Create a professional summary (2-3 sentences) tailored to this role.
Select and order the most relevant experience highlights.
Reorder skills to put the most relevant ones first.
Return a JSON object with this exact structure:

{{
  "basics": {{
    "name": "{name}",
    "headline": "A tailored headline for this role",
    "email": "{email}",
    "phone": "{phone}",
    "location": "{location}"
  }},
  "summary": "Tailored professional summary",
  "experience_highlights": ["Top 4-6 most relevant achievement bullets"],
  "skills_ordered": ["Skill1", "Skill2", ...],
  "sections_to_emphasize": ["which sections to highlight"]
}}
"""


class CVGenerator:
    """Generates tailored CV data and pushes to Reactive Resume via MCP."""

    def __init__(
        self,
        gemini_client: GeminiClient | None = None,
        rr_client: ReactiveResumeClient | None = None,
    ):
        self.gemini = gemini_client or GeminiClient()
        self.rr = rr_client or ReactiveResumeClient()

    def _generate_tailored_data(
        self,
        profile: Profile,
        job: JobAnalysis,
        match: MatchResult | None = None,
    ) -> dict[str, Any]:
        """Use Gemini to generate tailored resume content."""
        prompt = GENERATE_CV_PROMPT.format(
            name=profile.name,
            title=profile.title,
            location=profile.location,
            email=profile.email,
            phone=profile.phone or "N/A",
            summary=profile.summary,
            experience=self._format_experience(profile.experience),
            skills=self._format_skills(profile.skills),
            languages=self._format_languages(profile.languages),
            education=self._format_education(profile.education),
            job_title=job.job_title,
            company=job.company,
            job_location=job.location,
            remote=job.remote_friendly,
            responsibilities="\n".join(f"- {r}" for r in job.key_responsibilities),
            requirements="\n".join(f"- {r.skill}" for r in job.requirements),
            match_score=match.overall_match_score if match else "N/A",
            strengths=", ".join(match.strengths) if match else "N/A",
            gaps=", ".join(match.gaps) if match else "N/A",
        )
        response = self.gemini.generate_text(
            prompt, system_instruction=SYSTEM_INSTRUCTION
        )
        return json.loads(response)

    def _build_patch_operations(
        self, tailored: dict[str, Any], profile: Profile
    ) -> list[dict[str, Any]]:
        """Build JSON Patch operations to populate a new RR resume."""
        ops: list[dict[str, Any]] = []
        basics = tailored.get("basics", {})

        # Set basics
        for field, path in [
            ("name", "/basics/name"),
            ("headline", "/basics/headline"),
            ("email", "/basics/email"),
            ("phone", "/basics/phone"),
            ("location", "/basics/location"),
        ]:
            if basics.get(field):
                ops.append({"op": "replace", "path": path, "value": basics[field]})

        # Set summary
        if tailored.get("summary"):
            ops.append(
                {"op": "replace", "path": "/summary/content", "value": tailored["summary"]}
            )

        return ops

    async def generate(
        self,
        profile: Profile,
        job: JobAnalysis,
        match: MatchResult | None = None,
        resume_name: str | None = None,
    ) -> dict[str, Any]:
        """Full pipeline: generate tailored CV and push to Reactive Resume.

        Returns dict with resume_id, pdf_url, and tailored_data.
        """
        # Generate tailored content
        tailored = self._generate_tailored_data(profile, job, match)

        # Create resume in RR
        name = resume_name or f"{job.job_title} — {job.company}"
        slug = f"cv-{job.company.lower().replace(' ', '-')}-{job.job_title.lower().replace(' ', '-')}"
        resume_id = await self.rr.create_resume(name=name, slug=slug)

        # Patch it with tailored data
        operations = self._build_patch_operations(tailored, profile)
        if operations:
            await self.rr.patch_resume(resume_id, operations)

        # Get PDF URL
        pdf_info = await self.rr.get_pdf_url(resume_id)

        return {
            "resume_id": resume_id,
            "pdf_url": pdf_info.get("downloadUrl"),
            "tailored": tailored,
        }

    def _format_experience(self, experience: list[dict]) -> str:
        lines = []
        for exp in experience:
            lines.append(
                f"- {exp.get('role', '?')} at {exp.get('company', '?')} ({exp.get('duration', '')})"
            )
            for h in exp.get("highlights", []):
                lines.append(f"  • {h}")
        return "\n".join(lines) or "N/A"

    def _format_skills(self, skills: dict[str, list[str]]) -> str:
        return "\n".join(
            f"  {cat}: {', '.join(s)}" for cat, s in skills.items()
        ) or "N/A"

    def _format_languages(self, languages: list[dict]) -> str:
        return "\n".join(
            f"- {l.get('language', '?')}: {l.get('level', '?')}" for l in languages
        ) or "N/A"

    def _format_education(self, education: list[dict]) -> str:
        return "\n".join(
            f"- {e.get('degree', '?')}, {e.get('institution', '?')} ({e.get('year', '')})"
            for e in education
        ) or "N/A"
