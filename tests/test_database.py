"""Tests for job_assistant.database — SQLite CRUD for job applications."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from job_assistant.database import (
    add_application,
    delete_application,
    get_application,
    get_connection,
    list_applications,
    update_application_status,
)
from job_assistant.models import ApplicationStatus


def _connect(tmp_path: Path) -> sqlite3.Connection:
    """Open a connection to a fresh temp database."""
    return get_connection(tmp_path / "test.db")


def test_add_and_list_application(tmp_path: Path) -> None:
    """An added application should appear in the listing with defaults."""
    conn = _connect(tmp_path)

    app_id = add_application(conn, "Acme GmbH", "Backend Engineer")

    assert app_id >= 1
    apps = list_applications(conn)
    assert len(apps) == 1
    app = apps[0]
    assert app.id == app_id
    assert app.company == "Acme GmbH"
    assert app.role == "Backend Engineer"
    assert app.status is ApplicationStatus.PLANNED
    assert app.url is None
    assert app.notes is None
    assert app.created_at is not None
    conn.close()


def test_add_application_with_optional_fields(tmp_path: Path) -> None:
    """Optional url and notes should be persisted and retrieved."""
    conn = _connect(tmp_path)

    add_application(
        conn,
        "Foo Inc.",
        "DevOps Engineer",
        url="https://example.com/jobs/1",
        notes="Recruiter: Jane",
    )

    apps = list_applications(conn)
    assert apps[0].url == "https://example.com/jobs/1"
    assert apps[0].notes == "Recruiter: Jane"
    conn.close()


def test_list_applications_newest_first(tmp_path: Path) -> None:
    """Listing should return applications newest first."""
    conn = _connect(tmp_path)

    first = add_application(conn, "A", "Role A")
    second = add_application(conn, "B", "Role B")

    apps = list_applications(conn)
    assert len(apps) == 2
    # Same-second timestamps break ties by higher id first.
    assert apps[0].id == second
    assert apps[1].id == first
    conn.close()


def test_get_application_by_id(tmp_path: Path) -> None:
    """get_application should return the matching application."""
    conn = _connect(tmp_path)

    app_id = add_application(conn, "Acme GmbH", "Backend Engineer")
    app = get_application(conn, app_id)

    assert app is not None
    assert app.id == app_id
    assert app.company == "Acme GmbH"
    conn.close()


def test_get_application_nonexistent_returns_none(tmp_path: Path) -> None:
    """get_application on a missing id should return None."""
    conn = _connect(tmp_path)

    assert get_application(conn, 999) is None
    conn.close()


def test_update_application_status(tmp_path: Path) -> None:
    """update_application_status should change the status and return True."""
    conn = _connect(tmp_path)

    app_id = add_application(conn, "Acme GmbH", "Backend Engineer")
    updated = update_application_status(conn, app_id, ApplicationStatus.INTERVIEW)

    assert updated is True
    app = get_application(conn, app_id)
    assert app is not None
    assert app.status is ApplicationStatus.INTERVIEW
    conn.close()


def test_update_application_status_nonexistent(tmp_path: Path) -> None:
    """Updating a missing application should return False."""
    conn = _connect(tmp_path)

    updated = update_application_status(conn, 999, ApplicationStatus.APPLIED)
    assert updated is False
    conn.close()


def test_delete_application(tmp_path: Path) -> None:
    """delete_application should remove the row and return True."""
    conn = _connect(tmp_path)

    app_id = add_application(conn, "Acme GmbH", "Backend Engineer")
    deleted = delete_application(conn, app_id)

    assert deleted is True
    assert get_application(conn, app_id) is None
    assert list_applications(conn) == []
    conn.close()


def test_delete_application_nonexistent(tmp_path: Path) -> None:
    """Deleting a missing application should return False."""
    conn = _connect(tmp_path)

    deleted = delete_application(conn, 999)
    assert deleted is False
    conn.close()
