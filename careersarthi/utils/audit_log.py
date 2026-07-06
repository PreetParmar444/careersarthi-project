"""
careersarthi/utils/audit_log.py
────────────────────────────────
Append-only audit trail of every agent action.
Each line is a JSON record — easy to grep, easy to ship to Cloud Logging.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", ".data/audit.log"))
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_action(
    agent: str,
    action: str,
    details: dict[str, Any] | None = None,
    pii_safe: bool = True,
) -> None:
    """
    Write one JSON line to the audit log.

    Parameters
    ----------
    agent     : Name of the agent that performed the action.
    action    : Short verb-noun, e.g. "fetch_emails", "redact_pii".
    details   : Optional dict of non-PII context (app IDs, counts, etc.).
    pii_safe  : Set False if the action was *blocked* because PII was detected.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "pii_safe": pii_safe,
        "details": details or {},
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def tail(n: int = 20) -> list[dict]:
    """Return the last *n* audit records (most recent last)."""
    if not _LOG_PATH.exists():
        return []
    lines = _LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(l) for l in lines[-n:]]


def search(agent: str | None = None, action: str | None = None) -> list[dict]:
    """Filter audit log by agent and/or action name."""
    records = tail(n=10_000)
    if agent:
        records = [r for r in records if r["agent"] == agent]
    if action:
        records = [r for r in records if r["action"] == action]
    return records
