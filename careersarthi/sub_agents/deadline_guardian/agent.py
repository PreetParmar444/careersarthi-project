"""
careersarthi/sub_agents/deadline_guardian/agent.py
────────────────────────────────────────────────────
ADK agent that scans tracked applications for upcoming deadlines
and generates a ranked urgency list. Optionally writes Google Calendar reminders.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from careersarthi.utils.audit_log import log_action
from careersarthi.utils.storage import get_all_applications


# ── Urgency thresholds ────────────────────────────────────────────────────────

_RED_DAYS = 3       # 🔴 critical
_YELLOW_DAYS = 7    # 🟡 upcoming
_GREEN_DAYS = 14    # 🟢 on radar


def _urgency(deadline_str: str) -> tuple[str, int]:
    """Return (colour, days_remaining) for a deadline ISO string."""
    try:
        dl = datetime.fromisoformat(deadline_str).replace(tzinfo=timezone.utc)
        days = (dl - datetime.now(timezone.utc)).days
        if days < 0:
            return "⚫ overdue", days
        if days <= _RED_DAYS:
            return "🔴 critical", days
        if days <= _YELLOW_DAYS:
            return "🟡 upcoming", days
        if days <= _GREEN_DAYS:
            return "🟢 on radar", days
        return "⚪ future", days
    except Exception:
        return "❓ unknown", 999


async def get_deadlines() -> dict[str, Any]:
    """
    Return all tracked applications that have a deadline set,
    sorted by urgency (soonest first), with colour-coded urgency labels.
    """
    apps = await get_all_applications()
    deadlines = []
    for app in apps:
        dl = app.get("deadline", "")
        if not dl:
            continue
        urgency_label, days = _urgency(dl)
        deadlines.append({
            "app_id": app.get("id"),
            "company": app.get("company"),
            "role": app.get("role"),
            "status": app.get("status"),
            "deadline": dl,
            "days_remaining": days,
            "urgency": urgency_label,
        })

    deadlines.sort(key=lambda x: x["days_remaining"])
    log_action("deadline_guardian", "get_deadlines", {"count": len(deadlines)})
    return {"deadlines": deadlines, "total": len(deadlines)}


async def get_overdue() -> dict[str, Any]:
    """Return applications where the deadline has already passed."""
    all_dl = await get_deadlines()
    overdue = [d for d in all_dl["deadlines"] if d["days_remaining"] < 0]
    return {"overdue": overdue, "count": len(overdue)}


async def add_calendar_reminder(
    company: str,
    role: str,
    deadline: str,
    reminder_minutes_before: int = 1440,
) -> dict[str, Any]:
    """
    Add a Google Calendar event for an application deadline.

    Args:
        company:                  Company name.
        role:                     Job title.
        deadline:                 ISO 8601 date string (e.g. "2025-08-15T10:00:00").
        reminder_minutes_before:  Minutes before deadline to fire the reminder (default 24h = 1440).
    """
    token_path = os.getenv("GMAIL_TOKEN_PATH", ".secrets/gmail_token.json")
    if not os.path.exists(token_path):
        return {"error": "Calendar OAuth token not found. Run `python -m careersarthi.auth` first."}

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            token_path,
            ["https://www.googleapis.com/auth/calendar"],
        )
        service = build("calendar", "v3", credentials=creds)

        event_body = {
            "summary": f"[CareerSarthi] Deadline: {role} @ {company}",
            "description": f"Application deadline for {role} at {company}.",
            "start": {"dateTime": deadline, "timeZone": "Asia/Kolkata"},
            "end": {
                "dateTime": (
                    datetime.fromisoformat(deadline) + timedelta(hours=1)
                ).isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": reminder_minutes_before}],
            },
        }
        created = service.events().insert(calendarId="primary", body=event_body).execute()
        log_action("deadline_guardian", "add_calendar_reminder", {"company": company, "deadline": deadline})
        return {"created": True, "event_id": created.get("id"), "html_link": created.get("htmlLink")}

    except Exception as e:
        return {"error": str(e)}


# ── ADK Agent definition ──────────────────────────────────────────────────────

from careersarthi.utils.model import gemini_model

deadline_guardian_agent = Agent(
    name="deadline_guardian",
    model=gemini_model,
    description=(
        "Scans all tracked applications for upcoming deadlines (interviews, assessments, "
        "offer expiries). Produces a colour-coded urgency list and optionally creates "
        "Google Calendar reminders."
    ),
    instruction="""
You are the Deadline Guardian for CareerSarthi. Your job is to make sure
the candidate never misses an important date.

Steps:
1. Call `get_deadlines` to retrieve all applications with deadlines set.
2. Call `get_overdue` to flag any already-missed deadlines.
3. For any application with urgency 🔴 (≤3 days) or 🟡 (≤7 days), offer to
   call `add_calendar_reminder` with a 24-hour advance reminder.
4. Present the results as a clean, sorted list:
   - Group by urgency: 🔴 Critical → 🟡 Upcoming → 🟢 On Radar → ⚪ Future
   - Show company, role, status, deadline, and days remaining

Tone: Direct and action-oriented. If something is overdue, say so clearly
and suggest whether the candidate should follow up or move on.
""",
    tools=[
        FunctionTool(get_deadlines),
        FunctionTool(get_overdue),
        FunctionTool(add_calendar_reminder),
    ],
)