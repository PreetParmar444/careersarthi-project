"""
careersarthi/sub_agents/privacy_guardian/agent.py
─────────────────────────────────────────────────────
ADK agent responsible for the security posture of the whole system:

  • Redacts PII from any payload before it's allowed to reach an LLM call
  • Tracks which OAuth scopes have been granted (scoped consent, not blanket)
  • Surfaces the audit log on request ("what did the agents do today?")
  • Can be invoked as a *gate* by the orchestrator before any external write
"""

from __future__ import annotations

from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from careersarthi.utils.pii_redactor import redact, is_safe
from careersarthi.utils.audit_log import log_action, tail, search


_GRANTED_SCOPES_DOC = {
    "gmail.readonly": "Read-only inbox scan for application emails. No send/delete permission.",
    "calendar": "Create deadline reminder events only. No access to existing personal events content beyond busy/free.",
}


def redact_text(text: str) -> dict[str, Any]:
    """
    Run PII redaction on a block of text before it is used in any external call
    (LLM prompt, log entry, or anything leaving local storage).

    Args:
        text: Raw text that may contain PII (email bodies, resume content, notes).
    """
    result = redact(text)
    log_action(
        "privacy_guardian", "redact_text",
        {"redaction_count": result.redaction_count, "categories": list(result.redacted_items.keys())},
    )
    return {
        "clean_text": result.clean_text,
        "was_redacted": result.was_redacted,
        "redaction_count": result.redaction_count,
        "categories_found": list(result.redacted_items.keys()),
    }


def check_safe(text: str) -> dict[str, bool]:
    """
    Quick boolean check — True if *text* contains no detectable PII, False otherwise.
    Use before allowing any agent to forward raw user content externally.

    Args:
        text: Text to check.
    """
    return {"is_safe": is_safe(text)}


def get_granted_scopes() -> dict[str, Any]:
    """
    Return the list of OAuth scopes CareerSarthi has been granted and what
    each one is used for. Used to answer "what can the agents access?"
    """
    return {"granted_scopes": _GRANTED_SCOPES_DOC}


def get_audit_trail(n: int = 20, agent_filter: str = "") -> dict[str, Any]:
    """
    Retrieve recent agent actions from the audit log, optionally filtered
    by which agent performed them.

    Args:
        n:            Number of recent records to return (default 20).
        agent_filter: If set, only show actions from this agent name.
    """
    records = search(agent=agent_filter or None) if agent_filter else tail(n)
    return {"records": records[-n:], "count": len(records[-n:])}


def flag_pii_violation(agent_name: str, attempted_content_preview: str) -> dict[str, Any]:
    """
    Log a blocked action where an agent attempted to send unredacted PII
    externally. This is a defensive tripwire — call it whenever check_safe
    returns False on content destined for an external API.

    Args:
        agent_name:                Name of the agent that attempted the unsafe action.
        attempted_content_preview: First ~50 chars of the offending content (for debugging,
                                    already truncated to avoid logging full PII).
    """
    preview = attempted_content_preview[:50]
    log_action(
        agent_name, "BLOCKED_pii_violation",
        {"preview": preview}, pii_safe=False,
    )
    return {"blocked": True, "agent": agent_name}


# ── ADK Agent definition ──────────────────────────────────────────────────────

from careersarthi.utils.model import gemini_model

privacy_guardian_agent = Agent(
    name="privacy_guardian",
    model=gemini_model,
    description=(
        "Security and privacy gatekeeper for CareerSarthi. Redacts PII before it "
        "leaves the system, tracks OAuth consent scopes, and maintains the audit "
        "trail of every agent action. All other agents route sensitive content "
        "through this agent before any external call."
    ),
    instruction="""
You are the Privacy Guardian for CareerSarthi — the security backstop for the
whole multi-agent system.

Your responsibilities:

1. **PII redaction**: When asked to vet content before it leaves the system,
   call `redact_text` and return the clean version. Never pass through
   unredacted emails, phone numbers, addresses, salary figures, or IDs.

2. **Safety checks**: When another agent asks "is this safe to send externally?",
   call `check_safe`. If False, call `flag_pii_violation` to log the block,
   then instruct the calling agent to use the redacted version instead.

3. **Consent transparency**: If asked what data CareerSarthi can access,
   call `get_granted_scopes` and explain each scope in plain language —
   emphasise these are narrow, read-mostly permissions, not blanket access.

4. **Audit trail**: If asked what the agents have been doing, call
   `get_audit_trail` and summarise recent actions in plain English
   (e.g. "Inbox tracker scanned 12 emails, found 3 new applications;
   Skill gap analyzer ran 2 comparisons; no PII violations detected").

Be precise and reassuring but never overstate guarantees — describe what
protections exist, not what's theoretically impossible.
""",
    tools=[
        FunctionTool(redact_text),
        FunctionTool(check_safe),
        FunctionTool(get_granted_scopes),
        FunctionTool(get_audit_trail),
        FunctionTool(flag_pii_violation),
    ],
)
