"""Configuration helpers: environment loading and API key retrieval."""

from __future__ import annotations

import os
from pathlib import Path


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_env(path: str | Path = ".env") -> None:
    """Load environment variables from a ``.env`` file if it exists.

    Uses a simple line-based parser (``KEY=VALUE``) so the project does not
    depend on python-dotenv. Lines starting with ``#`` and blank lines are
    ignored. Existing environment variables are not overwritten.

    Args:
        path: Path to the ``.env`` file. Defaults to ``.env`` in the current
            working directory.
    """
    file_path = Path(path)
    if not file_path.exists():
        return

    with file_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if (
                len(value) >= 2
                and value[0] in ("'", '"')
                and value[-1] == value[0]
            ):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


def get_gemini_api_key() -> str:
    """Return the ``GEMINI_API_KEY`` environment variable.

    Returns:
        The value of the ``GEMINI_API_KEY`` environment variable.

    Raises:
        ConfigError: If the variable is not set or is empty.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )
    return api_key
