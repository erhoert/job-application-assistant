"""Tests for job_assistant.scraper — file reading and source detection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from job_assistant.scraper import get_job_text, read_file


def test_read_file_returns_content(tmp_path: Path) -> None:
    """read_file should return the UTF-8 content of an existing file."""
    file = tmp_path / "posting.txt"
    file.write_text(
        "Senior Backend Engineer\nBerlin, Germany\n", encoding="utf-8"
    )

    content = read_file(file)

    assert "Senior Backend Engineer" in content
    assert "Berlin, Germany" in content


def test_read_file_missing_raises(tmp_path: Path) -> None:
    """read_file should raise FileNotFoundError for a missing path."""
    missing = tmp_path / "nope.txt"

    with pytest.raises(FileNotFoundError):
        read_file(missing)


def test_get_job_text_from_file_returns_text_and_none(tmp_path: Path) -> None:
    """A file path source should return (text, None) without a URL."""
    file = tmp_path / "posting.txt"
    file.write_text("Some job description text.", encoding="utf-8")

    text, url = get_job_text(str(file))

    assert text == "Some job description text."
    assert url is None


def test_get_job_text_url_detection_uses_scrape_url() -> None:
    """URL sources (http and https) should route through scrape_url.

    The real HTTP client is not exercised; scrape_url is patched so no
    network call is made. Verifies both that the URL is forwarded to
    scrape_url and that the original URL is returned as the second element.
    """
    for url in ("https://example.com/jobs/123", "http://example.com/jobs/abc"):
        with patch(
            "job_assistant.scraper.scrape_url", return_value="scraped job text"
        ) as mock_scrape:
            text, returned_url = get_job_text(url)

        mock_scrape.assert_called_once_with(url)
        assert text == "scraped job text"
        assert returned_url == url
