"""SQLite persistence layer for tracked job applications."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from job_assistant.models import Application, ApplicationStatus

DB_PATH = Path("data/applications.db")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection, ensure the schema, and return it.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Returns:
        A configured :class:`sqlite3.Connection` using the ``sqlite3.Row``
        row factory with the ``applications`` table initialized.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create the applications table if it does not already exist.

    Args:
        conn: A live SQLite connection.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT planned,
            url TEXT,
            applied_date TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def add_application(
    conn: sqlite3.Connection,
    company: str,
    role: str,
    status: ApplicationStatus = ApplicationStatus.PLANNED,
    url: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Insert a new job application and return its primary key.

    Args:
        conn: A live SQLite connection.
        company: Company the application is directed at.
        role: Role being applied for.
        status: Lifecycle stage of the application.
        url: Optional URL of the job posting.
        notes: Optional free-form notes about the application.

    Returns:
        The integer primary key of the newly inserted row.
    """
    cursor = conn.execute(
        """
        INSERT INTO applications (company, role, status, url, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (company, role, status.value, url, notes),
    )
    conn.commit()
    return int(cursor.lastrowid)


def list_applications(conn: sqlite3.Connection) -> list[Application]:
    """Return all applications, newest first.

    Args:
        conn: A live SQLite connection.

    Returns:
        A list of :class:`Application` instances ordered by ``created_at``
        descending, with higher ids breaking ties.
    """
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY created_at DESC, id DESC"
    ).fetchall()
    return [_row_to_app(row) for row in rows]


def get_application(conn: sqlite3.Connection, app_id: int) -> Optional[Application]:
    """Fetch a single application by primary key.

    Args:
        conn: A live SQLite connection.
        app_id: Primary key of the application to retrieve.

    Returns:
        An :class:`Application` instance, or ``None`` if no row matches.
    """
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_app(row)


def update_application_status(
    conn: sqlite3.Connection, app_id: int, status: ApplicationStatus
) -> bool:
    """Update the status of an application.

    Args:
        conn: A live SQLite connection.
        app_id: Primary key of the application to update.
        status: New lifecycle stage to persist.

    Returns:
        ``True`` if a row was updated, ``False`` if no matching id exists.
    """
    cursor = conn.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (status.value, app_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_application(conn: sqlite3.Connection, app_id: int) -> bool:
    """Delete an application by primary key.

    Args:
        conn: A live SQLite connection.
        app_id: Primary key of the application to delete.

    Returns:
        ``True`` if a row was deleted, ``False`` if no matching id exists.
    """
    cursor = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    return cursor.rowcount > 0


def _row_to_app(row: sqlite3.Row) -> Application:
    """Convert a :class:`sqlite3.Row` into an :class:`Application` model.

    Args:
        row: A row from the ``applications`` table.

    Returns:
        A populated :class:`Application` instance with parsed timestamps
        and normalized status enum.
    """
    created_at_raw = row["created_at"]
    applied_date_raw = row["applied_date"]
    created_at = (
        datetime.fromisoformat(created_at_raw) if created_at_raw else None
    )
    applied_date = (
        datetime.fromisoformat(applied_date_raw) if applied_date_raw else None
    )

    return Application(
        id=row["id"],
        company=row["company"],
        role=row["role"],
        status=ApplicationStatus(row["status"]),
        url=row["url"],
        applied_date=applied_date,
        notes=row["notes"],
        created_at=created_at,
    )
