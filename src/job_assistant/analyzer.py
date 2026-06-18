"""Analyze job postings into structured JobAnalysis objects via Gemini."""

from __future__ import annotations

from job_assistant.gemini_client import GeminiClient
from job_assistant.models import JobAnalysis

SYSTEM_INSTRUCTION = (
    "You are an expert career coach who analyzes job postings. "
    "Read each posting carefully and extract structured, accurate information. "
    "Distinguish mandatory requirements from preferred ones, categorize skills as "
    "technical, soft, or language, and infer remote-friendliness from explicit "
    "statements or strong signals. Be concise and avoid speculation."
)

ANALYZE_PROMPT_TEMPLATE = """\
Analyze the following job posting and extract its key details.

Return structured data with:
- job_title: The advertised role title.
- company: Hiring company name.
- location: City/region, or "remote" if fully remote.
- remote_friendly: Whether remote work is allowed or supported.
- summary: A single concise paragraph summarizing the role.
- key_responsibilities: The main responsibilities of the position.
- requirements: Skills and qualifications, each categorized as technical, soft, or language,
  and marked as required (mandatory) or preferred (nice-to-have).
- salary_range: Salary range as stated in the posting, if any.

Job posting:
{job_text}
"""


class JobAnalyzer:
    """Analyzer that turns raw job posting text into a JobAnalysis.

    Attributes:
        client: GeminiClient used for structured generation.
    """

    def __init__(self, client: GeminiClient | None = None) -> None:
        """Initialize the analyzer.

        Args:
            client: Optional GeminiClient instance. If omitted, a default
                client is created.
        """
        self.client = client or GeminiClient()

    def analyze(self, job_text: str) -> JobAnalysis:
        """Analyze a job posting and return a structured JobAnalysis.

        Args:
            job_text: Raw text of the job posting to analyze.

        Returns:
            A JobAnalysis populated by Gemini's structured output.
        """
        prompt = ANALYZE_PROMPT_TEMPLATE.format(job_text=job_text)
        return self.client.generate_structured(
            prompt,
            JobAnalysis,
            system_instruction=SYSTEM_INSTRUCTION,
        )
