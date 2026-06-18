"""Scraping and text extraction for job postings from URLs or local files."""

from __future__ import annotations

from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Browser-like User-Agent to avoid being blocked by simple bot filters.
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# Tags whose contents are not part of the job posting body.
_NOISE_TAGS = ("script", "style", "nav", "footer", "header", "aside")

# Selectors tried in order to locate the main job posting container.
_JOB_SELECTORS = (
    "article",
    "main",
    "[role=main]",
    ".job-description",
    "#job-description",
)


def scrape_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and extract the visible job posting text from its HTML.

    Sends a GET request with a browser User-Agent header and follows
    redirects. The HTML is parsed with BeautifulSoup, noise tags
    (script/style/nav/footer/header/aside) are removed, and common job
    posting containers are tried in order. The first container whose text
    exceeds 200 characters is returned; otherwise the entire body text is
    used as a fallback.

    Args:
        url: The URL of the job posting to scrape.
        timeout: Request timeout in seconds.

    Returns:
        The extracted visible text of the job posting.
    """
    headers = {"User-Agent": _USER_AGENT}
    response = httpx.get(
        url, headers=headers, timeout=timeout, follow_redirects=True
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for selector in _JOB_SELECTORS:
        for candidate in soup.select(selector):
            text = candidate.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    body = soup.body
    if body is None:
        return soup.get_text(separator="\n", strip=True)
    return body.get_text(separator="\n", strip=True)


def read_file(path: str | Path) -> str:
    """Read the contents of a UTF-8 text file.

    Args:
        path: Path to the file to read.

    Returns:
        The file content decoded as UTF-8.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.read_text(encoding="utf-8")


def get_job_text(source: str) -> tuple[str, str | None]:
    """Return job posting text and its source URL (if any) from a source string.

    Auto-detects whether ``source`` is a URL (starts with ``http://`` or
    ``https://``) or a path to a local file. URLs are scraped via
    :func:`scrape_url`; file paths are read via :func:`read_file`.

    Args:
        source: A URL or a local file path.

    Returns:
        A tuple ``(text, url_or_None)`` where ``url_or_None`` is the
        original URL when ``source`` was a URL, and ``None`` when it was a
        local file path.
    """
    if source.startswith(("http://", "https://")):
        return scrape_url(source), source
    return read_file(source), None
