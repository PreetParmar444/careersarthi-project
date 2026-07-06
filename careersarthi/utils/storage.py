"""
careersarthi/utils/storage.py
────────────────────────────────
Local persistence layer for CareerSarthi.

Two tables, one SQLite file:
  • applications  – structured job-application records (company, role,
                    status, deadline, ...) used by inbox_tracker,
                    skill_gap, deadline_guardian, interview_prep, and the CLI.
  • kv_store       – generic JSON-blob cache (e.g. cached gap-analysis
                    results keyed "gap:{company}:{role}") used by skill_gap.

Encryption-at-rest: sensitive free-text fields (currently `notes`, inside
`extra`) are Fernet-encrypted with STORAGE_ENCRYPTION_KEY before being
written, and transparently decrypted on read. This is field-level
encryption, not full-disk/SQLCipher — the .db file's structural columns
(company, role, status, deadline) are stored in the clear since they're
needed for filtering/sorting, but free-text notes that may carry PII are
encrypted. If STORAGE_ENCRYPTION_KEY is unset, a key is generated and
persisted alongside the DB (fine for local dev; set the env var explicitly
in any shared/deployed environment).

All public functions are declared `async def` to match how every caller
in this codebase already invokes them (`await` / `run_until_complete` /
`asyncio.run`), even though the underlying sqlite3 driver is synchronous —
each call simply runs to completion on the calling thread. This keeps the
call sites correct without requiring a separate async driver dependency.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# ── Config ─────────────────────────────────────────────────────────────────

_DB_PATH = Path(os.getenv("DATABASE_PATH", ".data/careersarthi.db"))
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_KEY_PATH = _DB_PATH.parent / ".storage_key"


def _load_or_create_key() -> bytes:
    """
    Resolve the Fernet encryption key.

    Priority: STORAGE_ENCRYPTION_KEY env var (expected in any shared/deployed
    environment — docker-compose.yml sets this) → a key persisted on disk
    next to the DB (local dev convenience, generated once and reused).
    """
    from cryptography.fernet import Fernet

    env_key = os.getenv("STORAGE_ENCRYPTION_KEY", "")
    if env_key:
        return env_key.encode()

    if _KEY_PATH.exists():
        return _KEY_PATH.read_bytes()

    key = Fernet.generate_key()
    _KEY_PATH.write_bytes(key)
    _KEY_PATH.chmod(0o600)
    return key


def _fernet():
    from cryptography.fernet import Fernet

    return Fernet(_load_or_create_key())


def _encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    return _fernet().encrypt(plaintext.encode()).decode()


def _decrypt(token: str) -> str:
    if not token:
        return token
    try:
        return _fernet().decrypt(token.encode()).decode()
    except Exception:
        # Not a Fernet token (e.g. pre-encryption legacy row, or corrupt
        # data) — return as-is rather than raising, since this is read-path
        # display logic, not a security boundary.
        return token


# ── Connection / schema ───────────────────────────────────────────────────

@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_schema() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id          TEXT PRIMARY KEY,
                company     TEXT NOT NULL,
                role        TEXT NOT NULL,
                portal      TEXT DEFAULT '',
                applied_on  TEXT DEFAULT '',
                status      TEXT DEFAULT 'applied',
                deadline    TEXT DEFAULT '',
                extra_json  TEXT DEFAULT '{}',
                updated_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_store (
                key         TEXT PRIMARY KEY,
                value_json  TEXT NOT NULL,
                updated_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )


_init_schema()


# ── Row <-> dict helpers ───────────────────────────────────────────────────

# Keys inside `extra` that get encrypted at rest (free-text, PII-prone).
_ENCRYPTED_EXTRA_KEYS = {"notes"}


def _serialize_extra(extra: dict[str, Any]) -> str:
    safe = dict(extra or {})
    for k in _ENCRYPTED_EXTRA_KEYS:
        if k in safe and isinstance(safe[k], str):
            safe[k] = _encrypt(safe[k])
    return json.dumps(safe)


def _deserialize_extra(raw: str) -> dict[str, Any]:
    try:
        extra = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {}
    for k in _ENCRYPTED_EXTRA_KEYS:
        if k in extra and isinstance(extra[k], str):
            extra[k] = _decrypt(extra[k])
    return extra


def _row_to_app(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "company": row["company"],
        "role": row["role"],
        "portal": row["portal"],
        "applied_on": row["applied_on"],
        "status": row["status"],
        "deadline": row["deadline"],
        "extra": _deserialize_extra(row["extra_json"]),
        "updated_at": row["updated_at"],
    }


# ── Public API: applications ────────────────────────────────────────────────

async def upsert_application(
    app_id: str,
    company: str,
    role: str,
    portal: str = "",
    applied_on: str = "",
    status: str = "applied",
    deadline: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Insert or update an application record, keyed by app_id.

    Existing fields are overwritten with the values supplied here; pass the
    previously-known values back in if you only mean to update one field
    (this is a full upsert, not a partial patch).
    """
    extra_json = _serialize_extra(extra or {})
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO applications (id, company, role, portal, applied_on, status, deadline, extra_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                company=excluded.company,
                role=excluded.role,
                portal=excluded.portal,
                applied_on=excluded.applied_on,
                status=excluded.status,
                deadline=excluded.deadline,
                extra_json=excluded.extra_json,
                updated_at=datetime('now')
            """,
            (app_id, company, role, portal, applied_on, status, deadline, extra_json),
        )
    return {"saved": True, "id": app_id}


async def get_application(app_id: str) -> dict[str, Any] | None:
    """Fetch a single application record by id, or None if not found."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    return _row_to_app(row) if row else None


async def get_all_applications() -> list[dict[str, Any]]:
    """Return every tracked application, most recently updated first."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM applications ORDER BY updated_at DESC").fetchall()
    return [_row_to_app(r) for r in rows]


async def delete_application(app_id: str) -> dict[str, bool]:
    """Remove an application record (e.g. duplicate or test data cleanup)."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    return {"deleted": cur.rowcount > 0}


# ── Public API: generic kv cache ────────────────────────────────────────────

async def kv_set(key: str, value: Any) -> dict[str, bool]:
    """Store a JSON-serialisable value under *key* (overwrites if present)."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO kv_store (key, value_json, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value_json=excluded.value_json,
                updated_at=datetime('now')
            """,
            (key, json.dumps(value)),
        )
    return {"saved": True}


async def kv_get(key: str, default: Any = None) -> Any:
    """Retrieve a previously-stored value, or *default* if the key is absent."""
    with _connect() as conn:
        row = conn.execute("SELECT value_json FROM kv_store WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value_json"])
    except json.JSONDecodeError:
        return default


async def kv_delete(key: str) -> dict[str, bool]:
    """Remove a cached key."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
    return {"deleted": cur.rowcount > 0}
