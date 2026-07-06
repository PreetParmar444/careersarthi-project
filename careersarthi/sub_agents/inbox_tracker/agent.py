"""
careersarthi/sub_agents/inbox_tracker/agent.py
───────────────────────────────────────────────
ADK agent that reads the user's Gmail, finds job-related emails,
and upserts structured application records into the encrypted store.

Tools used:
  • fetch_emails_tool  – pulls recent Gmail threads (OAuth-gated)
  • save_application   – writes parsed app record to encrypted SQLite

Security: raw email bodies are PII-redacted before any LLM sees them.
"""

from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from careersarthi.utils.pii_redactor import redact
from careersarthi.utils.storage import upsert_application
from careersarthi.utils.audit_log import log_action

# ── Gmail scopes (read-only, narrowest possible) ──────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

_JOB_PATTERNS = [
    re.compile(r"application|applied|shortlisted|interview|offer|reject|assessment", re.I),
    re.compile(r"turing|toptal|wellfound|deloitte|naukri|linkedin|internshala", re.I),
]

_STATUS_MAP = {
    re.compile(r"interview", re.I): "interview",
    re.compile(r"offer", re.I): "offer",
    re.compile(r"reject|regret|not moving forward|unsuccessful", re.I): "rejected",
    re.compile(r"shortlist|selected for next", re.I): "shortlisted",
    re.compile(r"assessment|test|assignment", re.I): "assessment",
}


def _get_gmail_service():
    token_path = os.getenv("GMAIL_TOKEN_PATH", ".secrets/gmail_token.json")
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"Gmail token not found at {token_path}. "
            "Run `python -m careersarthi.auth` to authorise Gmail access."
        )
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text
    return ""


def _infer_status(text: str) -> str:
    for pattern, status in _STATUS_MAP.items():
        if pattern.search(text):
            return status
    return "applied"


def _extract_company(subject: str, snippet: str) -> str:
    """Best-effort company name extraction from subject line."""
    for m in re.finditer(r"at\s+([A-Z][A-Za-z\s&.,-]{2,40}?)(?:\s*[–\-|!,]|\s+for\s|\s+re:|\s*$)", subject):
        return m.group(1).strip()
    return "Unknown"


# ── Tool functions (registered with ADK) ─────────────────────────────────────

def fetch_emails_tool(max_results: int = 30) -> dict[str, Any]:
    """
    Scan Gmail for job-application emails (read-only OAuth scope).
    Returns a list of redacted email records ready for the orchestrator.

    Args:
        max_results: Maximum number of messages to scan (default 30).
    """
    try:
        service = _get_gmail_service()
        query = "subject:(application OR interview OR offer OR shortlisted OR assessment OR rejection)"
        messages = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
            .get("messages", [])
        )
        results = []
        for msg_ref in messages:
            msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "")
            sender = headers.get("From", "")
            date_str = headers.get("Date", "")
            snippet = msg.get("snippet", "")
            body = _decode_body(msg["payload"])[:2000]

            # Only keep job-related emails
            combined = f"{subject} {snippet} {body}"
            if not any(p.search(combined) for p in _JOB_PATTERNS):
                continue

            # PII-redact before passing to LLM
            safe = redact(combined)
            log_action("inbox_tracker", "fetch_email", {"subject_len": len(subject), "pii_found": safe.was_redacted})

            results.append({
                "id": msg_ref["id"],
                "subject": subject,
                "sender": sender,
                "date": date_str,
                "snippet": safe.clean_text[:300],
                "inferred_status": _infer_status(combined),
                "company_guess": _extract_company(subject, snippet),
            })

        return {"emails": results, "count": len(results)}

    except FileNotFoundError as e:
        return {"error": str(e), "emails": [], "count": 0}
    except Exception as e:
        return {"error": f"Gmail fetch failed: {e}", "emails": [], "count": 0}


async def save_application(
    app_id: str,
    company: str,
    role: str,
    portal: str = "",
    applied_on: str = "",
    status: str = "applied",
    deadline: str = "",
    notes: str = "",
) -> dict[str, str]:
    """
    Persist an application record to the encrypted local store.

    Args:
        app_id:     Unique identifier (e.g. Gmail message ID or manual UUID).
        company:    Company name.
        role:       Job title applied for.
        portal:     Platform used (Turing / Toptal / Wellfound / etc.).
        applied_on: ISO date string of application date.
        status:     Current status (applied/shortlisted/interview/offer/rejected).
        deadline:   ISO date string of any deadline to track.
        notes:      Free-text notes (PII must be stripped before passing here).
    """
    await upsert_application(
        app_id=app_id, company=company, role=role, portal=portal,
        applied_on=applied_on, status=status, deadline=deadline,
        extra={"notes": notes},
    )
    log_action("inbox_tracker", "save_application", {"company": company, "status": status})
    return {"saved": True, "app_id": app_id, "status": status}


# ── ADK Agent definition ──────────────────────────────────────────────────────

from careersarthi.utils.model import gemini_model

inbox_tracker_agent = Agent(
    name="inbox_tracker",
    model=gemini_model,
    description=(
        "Scans Gmail for job-application emails, extracts company name, role, "
        "status, and any deadlines, then saves records to the encrypted application store."
    ),
    instruction="""
You are the Inbox Tracker for CareerSarthi. Your job is to:

1. Call `fetch_emails_tool` to retrieve recent job-related emails from Gmail.
2. For each email returned, determine:
   - Company name (from the email metadata)
   - Role applied for (from subject or snippet)
   - Portal used (Turing / Toptal / Wellfound / Naukri / LinkedIn / etc.)
   - Current status (applied / shortlisted / assessment / interview / offer / rejected)
   - Any deadline mentioned (interview date, assessment due date, offer expiry)
3. Call `save_application` for each identified application.
4. Return a clean summary of all applications found and saved.

Rules:
- Never include raw email bodies in your response — only metadata.
- If a company name cannot be determined, use "Unknown".
- If an email covers multiple applications (e.g. a digest), create separate records.
- Always use ISO 8601 date strings (YYYY-MM-DD) for dates.
""",
    tools=[
        FunctionTool(fetch_emails_tool),
        FunctionTool(save_application),
    ],
)