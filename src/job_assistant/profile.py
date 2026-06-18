"""Loading and validation of the user profile from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from job_assistant.models import Profile


def load_profile(path: str | Path) -> Profile:
    """Load a user profile from a YAML file and validate it via Pydantic.

    Args:
        path: Path to the YAML profile file.

    Returns:
        A validated :class:`Profile` instance.

    Raises:
        FileNotFoundError: If the file at ``path`` does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Profile file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    return Profile.model_validate(data)


def get_default_profile_path() -> Path:
    """Return the default profile path used by the application."""
    return Path("data/profile.yaml")
