"""Tests for job_assistant.vector_store — sqlite-vec vector similarity search."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest
import sqlite_vec

from job_assistant.models import JobAnalysis, JobRequirement, SkillCategory
from job_assistant.vector_store import VectorStore


class MockGeminiClient:
    """Deterministic mock GeminiClient with a hash-based embed method."""

    def __init__(self, dim: int = 768) -> None:
        """Configure the embedding dimension.

        Args:
            dim: Dimensionality of the produced embedding vectors.
        """
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        """Return a deterministic embedding derived from the text hash.

        Args:
            text: Text to embed.

        Returns:
            A list of floats in [0, 1) of length ``dim``.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[i % len(digest)] / 255.0 for i in range(self.dim)]


def _connect(tmp_path: Path) -> sqlite3.Connection:
    """Open a temp SQLite connection with sqlite-vec loaded."""
    conn = sqlite3.connect(tmp_path / "vec_test.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn


def _make_analysis(title: str, company: str, skills: list[str]) -> JobAnalysis:
    """Build a minimal JobAnalysis for testing."""
    return JobAnalysis(
        job_title=title,
        company=company,
        location="Berlin",
        summary=f"{title} role at {company}",
        key_responsibilities=["Build software"],
        requirements=[
            JobRequirement(skill=s, category=SkillCategory.TECHNICAL)
            for s in skills
        ],
    )


def test_store_analysis_returns_row_id(tmp_path: Path) -> None:
    """store_analysis should persist metadata and vector and return the id."""
    conn = _connect(tmp_path)
    store = VectorStore(conn, MockGeminiClient())

    analysis = _make_analysis("Backend Engineer", "Acme", ["Python", "SQL"])
    row_id = store.store_analysis(analysis, source_url="https://example.com/1")

    assert row_id >= 1
    meta = conn.execute(
        "SELECT company, role, summary, source_url, analysis_json "
        "FROM job_analyses WHERE id = ?",
        (row_id,),
    ).fetchone()
    assert meta["company"] == "Acme"
    assert meta["role"] == "Backend Engineer"
    assert meta["source_url"] == "https://example.com/1"
    assert meta["analysis_json"] is not None
    vec_count = conn.execute(
        "SELECT COUNT(*) FROM job_vectors WHERE id = ?", (row_id,)
    ).fetchone()[0]
    assert vec_count == 1
    conn.close()


def test_find_similar_returns_self_first(tmp_path: Path) -> None:
    """find_similar should rank the matching analysis first with similarity ~1."""
    conn = _connect(tmp_path)
    store = VectorStore(conn, MockGeminiClient())

    id1 = store.store_analysis(
        _make_analysis("Backend Engineer", "Acme", ["Python", "SQL"])
    )
    id2 = store.store_analysis(
        _make_analysis("Frontend Engineer", "Beta", ["JavaScript", "CSS"])
    )

    results = store.find_similar(
        _make_analysis("Backend Engineer", "Acme", ["Python", "SQL"]), limit=5
    )

    assert len(results) == 2
    assert results[0]["id"] == id1
    assert results[0]["similarity"] == pytest.approx(1.0)
    assert results[1]["id"] == id2
    for key in ("id", "company", "role", "summary", "url", "distance", "similarity"):
        assert key in results[0]
    conn.close()


def test_find_similar_respects_limit(tmp_path: Path) -> None:
    """find_similar should cap the number of returned results."""
    conn = _connect(tmp_path)
    store = VectorStore(conn, MockGeminiClient())

    for i in range(5):
        store.store_analysis(_make_analysis(f"Role {i}", f"Co {i}", ["Python"]))

    results = store.find_similar(
        _make_analysis("Role 0", "Co 0", ["Python"]), limit=3
    )

    assert len(results) == 3
    conn.close()


def test_store_analysis_without_url(tmp_path: Path) -> None:
    """store_analysis should accept a null source_url and find_similar reflects it."""
    conn = _connect(tmp_path)
    store = VectorStore(conn, MockGeminiClient())

    analysis = _make_analysis("DevOps Engineer", "Gamma", ["Docker", "Kubernetes"])
    row_id = store.store_analysis(analysis)

    results = store.find_similar(analysis, limit=5)
    assert len(results) == 1
    assert results[0]["id"] == row_id
    assert results[0]["url"] is None
    conn.close()
