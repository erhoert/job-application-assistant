"""Thin wrapper around the Google Gemini SDK for text, structured output, and embeddings."""

from __future__ import annotations

from typing import Type, TypeVar

from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel

from job_assistant.config import get_gemini_api_key

DEFAULT_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """High-level client for Gemini text generation, structured output, and embeddings.

    Attributes:
        model: Default model used for content generation.
        client: Underlying ``google.genai.Client`` instance.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Gemini client.

        Args:
            model: Name of the Gemini model to use for generation.
            api_key: Gemini API key. If omitted, retrieved from the environment
                via :func:`job_assistant.config.get_gemini_api_key`.
        """
        self.model = model
        self.client = genai.Client(api_key=api_key or get_gemini_api_key())

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Generate free-form text from a prompt.

        Args:
            prompt: The user prompt to send to the model.
            system_instruction: Optional system instruction guiding behavior.

        Returns:
            The generated text response.
        """
        config = GenerateContentConfig(
            temperature=0.7,
            system_instruction=system_instruction,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response.text

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_instruction: str | None = None,
    ) -> T:
        """Generate structured output validated against a Pydantic model.

        Args:
            prompt: The user prompt to send to the model.
            response_model: Pydantic model class used as the response schema.
            system_instruction: Optional system instruction guiding behavior.

        Returns:
            An instance of ``response_model`` populated from the model output.
        """
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_model,
            temperature=0.3,
            system_instruction=system_instruction,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        except Exception:
            config = GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_model.model_json_schema(),
                temperature=0.3,
                system_instruction=system_instruction,
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        return response_model.model_validate_json(response.text)

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: Text to embed.

        Returns:
            The embedding vector as a list of floats.
        """
        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values
