"""Vector similarity search over stored job analyses using sqlite-vec."""

from __future__ import annotations

import json
import sqlite3
import struct
from typing import Any

import sqlite_vec

from job_assistant.gemini_client import GeminiClient
from job_assistant.models import JobAnalysis

EMBEDDING_DIM = 3072


class VectorStore:
    """Persists job analyses and searches them by embedding similarity.

    Attributes:
        conn: SQLite connection with the sqlite-vec extension loaded.
        client: GeminiClient used to produce text embeddings.
    """

    def __init__(self, conn: sqlite3.Connection, client: GeminiClient) -> None:
        """Initialize the store, loading the schema and extension.

        Args:
            conn: A live SQLite connection (will load the sqlite-vec
                extension and create the required tables).
            client: GeminiClient used for embedding generation.
        """
        self.conn = conn
        self.client = client
        self._init_schema()

    def _init_schema(self) -> None:
        """Load the sqlite-vec extension and create tables if absent."""
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS job_vectors USING vec0(
                id INTEGER PRIMARY KEY,
                embedding FLOAT[3072]
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_analyses (
                id INTEGER PRIMARY KEY,
                company TEXT,
                role TEXT,
                summary TEXT,
                source_url TEXT,
                analysis_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def _embed_analysis(self, analysis: JobAnalysis) -> list[float]:
        """Build a text representation of the analysis and embed it.

        Args:
            analysis: The job analysis to embed.

        Returns:
            The embedding vector produced by the Gemini client.
        """
        skills = [req.skill for req in analysis.requirements]
        text = " ".join(
            [
                analysis.job_title,
                analysis.company,
                analysis.summary,
                *skills,
            ]
        )
        return self.client.embed(text)

    def store_analysis(
        self, analysis: JobAnalysis, source_url: str | None = None
    ) -> int:
        """Embed, persist metadata and vector, and return the new row id.

        Args:
            analysis: The job analysis to store.
            source_url: Optional URL of the source posting.

        Returns:
            The integer primary key of the newly stored analysis.
        """
        embedding = self._embed_analysis(analysis)
        cursor = self.conn.execute(
            """
            INSERT INTO job_analyses (company, role, summary, source_url, analysis_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                analysis.company,
                analysis.job_title,
                analysis.summary,
                source_url,
                json.dumps(analysis.model_dump()),
            ),
        )
        row_id = int(cursor.lastrowid)
        self.conn.execute(
            "INSERT INTO job_vectors (id, embedding) VALUES (?, ?)",
            (row_id, self._serialize_vector(embedding)),
        )
        self.conn.commit()
        return row_id

    def find_similar(
        self, analysis: JobAnalysis, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find stored analyses most similar to the given analysis.

        Args:
            analysis: The query job analysis.
            limit: Maximum number of results to return.

        Returns:
            A list of dicts with keys: id, company, role, summary, url,
            distance, and similarity (1 - distance), ordered by ascending
            distance.
        """
        query_bytes = self._serialize_vector(self._embed_analysis(analysis))
        rows = self.conn.execute(
            """
            SELECT j.id, j.company, j.role, j.summary, j.source_url, v.distance
            FROM job_vectors v
            JOIN job_analyses j ON j.id = v.id
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance
            """,
            (query_bytes, limit),
        ).fetchall()
        return [
            {
                "id": row[0],
                "company": row[1],
                "role": row[2],
                "summary": row[3],
                "url": row[4],
                "distance": row[5],
                "similarity": 1.0 - row[5],
            }
            for row in rows
        ]

    def _serialize_vector(self, embedding: list[float]) -> bytes:
        """Pack a float vector into the binary format sqlite-vec expects.

        Args:
            embedding: The embedding vector to serialize.

        Returns:
            Packed bytes ready for insertion into a vec0 FLOAT[] column.
        """
        return struct.pack(f"{len(embedding)}f", *embedding)
