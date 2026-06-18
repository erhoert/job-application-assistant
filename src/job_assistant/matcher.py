"""Match a user Profile against a JobAnalysis and produce a MatchResult via Gemini."""

from __future__ import annotations

from job_assistant.gemini_client import GeminiClient
from job_assistant.models import JobAnalysis, MatchResult, Profile

SYSTEM_INSTRUCTION = (
    "You are an expert career advisor who evaluates how well a candidate's profile "
    "matches a job posting. Assess the alignment of skills, experience, languages, "
    "and education with the role's requirements. Provide an honest, well-calibrated "
    "match score, per-skill match status, concrete strengths, clear gaps, and "
    "actionable recommendations. Be specific and avoid speculation."
)

MATCH_PROMPT_TEMPLATE = """\
Evaluate how well the candidate's profile matches the job posting below.

Candidate profile:
Name: {name}
Title: {title}
Location: {location}
Summary: {summary}

Experience:
{experience}

Skills:
{skills}

Languages:
{languages}

Education:
{education}

Job posting:
Title: {job_title}
Company: {company}
Location: {job_location}
Remote friendly: {remote}

Key responsibilities:
{responsibilities}

Requirements:
{requirements}

Return structured data with:
- overall_match_score: A score from 0 to 100 reflecting overall fit.
- matched_skills: Per-skill match status, including whether the candidate has the skill
  and a match_level of 'exact', 'partial', or 'missing'.
- strengths: Notable strengths the candidate brings relative to the posting.
- gaps: Skill or experience gaps that may affect candidacy.
- recommendations: Actionable suggestions to improve the candidacy.
"""


class JobMatcher:
    """Matcher that scores a Profile against a JobAnalysis.

    Attributes:
        client: GeminiClient used for structured generation.
    """

    def __init__(self, client: GeminiClient | None = None) -> None:
        """Initialize the matcher.

        Args:
            client: Optional GeminiClient instance. If omitted, a default
                client is created.
        """
        self.client = client or GeminiClient()

    def match(self, profile: Profile, job: JobAnalysis) -> MatchResult:
        """Match a profile against a job analysis and return a MatchResult.

        Args:
            profile: The candidate's profile.
            job: The structured analysis of the job posting.

        Returns:
            A MatchResult populated by Gemini's structured output.
        """
        responsibilities = (
            "\n".join(f"  - {r}" for r in job.key_responsibilities)
            if job.key_responsibilities
            else "  No responsibilities listed"
        )
        requirements = (
            "\n".join(
                f"  - {r.skill} ({r.category.value}, "
                f"{'required' if r.required else 'preferred'})"
                for r in job.requirements
            )
            if job.requirements
            else "  No requirements listed"
        )
        prompt = MATCH_PROMPT_TEMPLATE.format(
            name=profile.name,
            title=profile.title,
            location=profile.location,
            summary=profile.summary or "N/A",
            experience=self._format_experience(profile.experience),
            skills=self._format_skills(profile.skills),
            languages=self._format_languages(profile.languages),
            education=self._format_education(profile.education),
            job_title=job.job_title,
            company=job.company,
            job_location=job.location,
            remote=job.remote_friendly,
            responsibilities=responsibilities,
            requirements=requirements,
        )
        return self.client.generate_structured(
            prompt,
            MatchResult,
            system_instruction=SYSTEM_INSTRUCTION,
        )

    def _format_experience(self, experience: list[dict]) -> str:
        """Format experience entries as "- Role at Company (duration)" with bullet highlights.

        Args:
            experience: List of experience dicts with keys like role, company,
                duration, and highlights.

        Returns:
            A formatted multi-line string, or "No experience listed" if empty.
        """
        if not experience:
            return "No experience listed"
        lines: list[str] = []
        for entry in experience:
            role = entry.get("role", "N/A")
            company = entry.get("company", "N/A")
            duration = entry.get("duration", "N/A")
            lines.append(f"- {role} at {company} ({duration})")
            for highlight in entry.get("highlights", []):
                lines.append(f"  - {highlight}")
        return "\n".join(lines)

    def _format_skills(self, skills: dict[str, list[str]]) -> str:
        """Format skills as indented "  category: skill1, skill2" lines.

        Args:
            skills: Dict mapping category names to lists of skill names.

        Returns:
            A formatted multi-line string, or "No skills listed" if empty.
        """
        if not skills:
            return "No skills listed"
        lines: list[str] = []
        for category, skill_list in skills.items():
            lines.append(f"  {category}: {', '.join(skill_list)}")
        return "\n".join(lines)

    def _format_languages(self, languages: list[dict]) -> str:
        """Format language entries as "- Language (level)" bullets.

        Args:
            languages: List of language dicts with keys like language and level.

        Returns:
            A formatted multi-line string, or "No languages listed" if empty.
        """
        if not languages:
            return "No languages listed"
        lines: list[str] = []
        for entry in languages:
            language = entry.get("language", "N/A")
            level = entry.get("level", "N/A")
            lines.append(f"- {language} ({level})")
        return "\n".join(lines)

    def _format_education(self, education: list[dict]) -> str:
        """Format education entries as "- Degree, Institution (year)" bullets.

        Args:
            education: List of education dicts with keys like degree,
                institution, and year.

        Returns:
            A formatted multi-line string, or "No education listed" if empty.
        """
        if not education:
            return "No education listed"
        lines: list[str] = []
        for entry in education:
            degree = entry.get("degree", "N/A")
            institution = entry.get("institution", "N/A")
            year = entry.get("year", "N/A")
            lines.append(f"- {degree}, {institution} ({year})")
        return "\n".join(lines)
