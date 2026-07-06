"""
careersarthi/sub_agents/interview_prep/agent.py
──────────────────────────────────────────────────
ADK agent that generates company-specific interview preparation:
likely questions, topics to revise, and a STAR-format story bank prompt.
Runs independently of inbox_tracker / deadline_guardian (parallel branch).
"""

from __future__ import annotations

import asyncio
from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from careersarthi.utils.audit_log import log_action
from careersarthi.utils.storage import get_application, kv_get


# ── Company-pattern prep packs (seeded knowledge, expandable) ────────────────

_COMPANY_PATTERNS = {
    "turing": {
        "format": "Live coding + async video screen + vetting test",
        "focus": ["Data structures & algorithms", "System design basics", "Take-home async screening"],
        "tips": "Turing's vetting is automated first — expect a timed coding test before any human round.",
    },
    "toptal": {
        "format": "English screen → Skills test → Live interview → Test project",
        "focus": ["Strong communication in English screen", "Live problem-solving under observation", "A polished test project"],
        "tips": "Toptal's pass rate is famously low (~3%) — the test project is where most candidates lose points on edge cases and code quality.",
    },
    "wellfound": {
        "format": "Varies by startup — usually founder/hiring-manager call then technical round",
        "focus": ["Product sense", "Ownership stories", "Why this startup specifically"],
        "tips": "Startups on Wellfound weight culture-fit and initiative heavily — have 2-3 'I shipped X end-to-end' stories ready.",
    },
    "deloitte": {
        "format": "HR screen → Technical/case round → Partner/Director round",
        "focus": ["Case-study structuring", "Client-communication scenarios", "Domain knowledge (consulting/tech)"],
        "tips": "Big-4 interviews weight structured thinking (MECE, frameworks) as much as raw technical depth.",
    },
}


def get_interview_prep_pack(company: str, role: str = "") -> dict[str, Any]:
    """
    Return a company-specific interview prep pack: format, focus areas, and tips.
    Falls back to generic prep guidance if the company isn't in the seeded pattern set.

    Args:
        company: Company name (case-insensitive match against known patterns).
        role:    Job title (used for generic fallback framing).
    """
    key = company.strip().lower()
    pack = _COMPANY_PATTERNS.get(key)
    if not pack:
        pack = {
            "format": "Unknown — recommend researching on Glassdoor/LeetCode Discuss",
            "focus": ["Core DSA fundamentals", "Role-specific technical depth", "Behavioral STAR stories"],
            "tips": f"No seeded pattern for {company}. Search recent interview experiences before the call.",
        }
    log_action("interview_prep", "get_prep_pack", {"company": company, "role": role})
    return {"company": company, "role": role, **pack}


def get_targeted_questions(company: str, role: str, skill_gaps: list[str] | None = None) -> dict[str, Any]:
    """
    Generate a list of likely interview question categories tailored to the
    role and any known skill gaps (so prep time goes to weak spots).

    Args:
        company:    Company name.
        role:       Job title.
        skill_gaps: Optional list of skills the candidate is weak on (from skill_gap_analyzer).
    """
    gaps = skill_gaps or []
    categories = {
        "technical_core": [
            f"Walk through a project where you used the core stack for {role}",
            "Explain a system design trade-off you made recently",
        ],
        "behavioral": [
            "Tell me about a time you disagreed with a teammate",
            "Describe a project that failed and what you learned",
        ],
        "gap_focused": [
            f"Be ready to discuss your exposure to {g}" for g in gaps[:3]
        ] or ["No major gaps flagged — focus on depth over breadth"],
    }
    log_action("interview_prep", "targeted_questions", {"company": company, "gap_count": len(gaps)})
    return {"company": company, "role": role, "question_categories": categories}


async def get_application_context(app_id: str) -> dict[str, Any]:
    """
    Pull the stored application record (company, role, JD, status) to ground
    interview prep in the actual application, not a generic template.

    Args:
        app_id: The application ID to look up.
    """
    app = await get_application(app_id)
    if not app:
        return {"error": f"No application found with id {app_id}"}
    return app


# ── ADK Agent definition ──────────────────────────────────────────────────────

from careersarthi.utils.model import gemini_model

interview_prep_agent = Agent(
    name="interview_prep",
    model=gemini_model,
    description=(
        "Generates company-specific interview preparation: likely format, focus areas, "
        "targeted questions weighted toward known skill gaps, and practical tips. "
        "Runs independently in parallel with inbox tracking and deadline checks."
    ),
    instruction="""
You are the Interview Prep agent for CareerSarthi.

Given a company (and optionally an app_id or known skill gaps):

1. Call `get_application_context` if an app_id is provided, to ground prep in the real JD/role.
2. Call `get_interview_prep_pack` for the company's known interview format and tips.
3. Call `get_targeted_questions`, passing any skill gaps so weak areas get extra prep questions.

Produce a prep brief with:
- **Interview format**: what rounds to expect
- **Focus areas**: top 3 things to prioritise studying
- **Sample questions**: grouped by technical / behavioral / gap-focused
- **One specific tip** for this company

Keep it tight — a candidate should be able to read this in under 2 minutes
and walk away knowing exactly what to do next.
""",
    tools=[
        FunctionTool(get_interview_prep_pack),
        FunctionTool(get_targeted_questions),
        FunctionTool(get_application_context),
    ],
)
