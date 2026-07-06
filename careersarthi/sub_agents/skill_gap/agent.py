"""
careersarthi/sub_agents/skill_gap/agent.py
───────────────────────────────────────────
ADK agent that calls the Career MCP server's analyze_skill_gap and
score_resume_ats tools, then synthesises a prioritised learning plan.
"""

from __future__ import annotations

import json
import os
from typing import Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, mcp_tool

from careersarthi.utils.audit_log import log_action
from careersarthi.utils.storage import kv_get, kv_set

import asyncio


# ── Wrappers around the Career MCP tools ─────────────────────────────────────
# (In production these would be called via MCP transport;
#  here we import directly so the project runs without a running MCP process.)

async def get_skill_gap(
    resume_path: str,
    jd_text: str,
    company: str = "",
    role: str = "",
) -> dict[str, Any]:
    """
    Parse the resume at *resume_path* and compute the skill gap against *jd_text*.

    Args:
        resume_path: Path to the candidate's resume PDF/DOCX.
        jd_text:     Full text of the job description.
        company:     Company name (for context).
        role:        Job title (for context).
    """
    from mcp_server.tools.resume_parser import parse_resume
    from mcp_server.tools.jd_gap_analyzer import analyze_gap
    from mcp_server.tools.ats_scorer import score_resume

    parsed = parse_resume(resume_path)
    if "error" in parsed:
        return parsed

    gap = analyze_gap(
        resume_skills=parsed.get("detected_skills", {}),
        jd_text=jd_text,
        company=company,
        role=role,
    )
    ats = score_resume(
        resume_text=parsed.get("raw_text", ""),
        jd_text=jd_text,
    )

    result = {**gap, "ats": ats, "resume_skills": parsed.get("detected_skills", {})}

    await kv_set(f"gap:{company}:{role}", result)

    log_action("skill_gap", "analyze_gap", {
        "company": company, "role": role,
        "match_score": gap.get("match_score"), "ats_grade": ats.get("grade"),
    })
    return result


async def get_all_gaps(resume_path: str) -> dict[str, Any]:
    """
    Run gap analysis against all actively tracked applications that have a JD stored.

    Args:
        resume_path: Path to the candidate's resume.
    """
    from careersarthi.utils.storage import get_all_applications
    from mcp_server.tools.resume_parser import parse_resume
    from mcp_server.tools.jd_gap_analyzer import analyze_gap

    apps = await get_all_applications()
    parsed = parse_resume(resume_path)
    if "error" in parsed:
        return parsed

    results = []
    for app in apps:
        jd = app.get("extra", {}).get("jd_text", "")
        if not jd:
            continue
        gap = analyze_gap(
            resume_skills=parsed.get("detected_skills", {}),
            jd_text=jd,
            company=app.get("company", ""),
            role=app.get("role", ""),
        )
        results.append(gap)

    from collections import Counter
    freq: Counter = Counter()
    for r in results:
        freq.update(r.get("required_missing", []))

    top_gaps = [skill for skill, _ in freq.most_common(10)]
    log_action("skill_gap", "batch_gap_analysis", {"applications": len(results), "top_gaps": top_gaps})

    return {
        "per_application": results,
        "top_missing_skills": top_gaps,
        "analysis_count": len(results),
    }


# ── ADK Agent definition ──────────────────────────────────────────────────────

from careersarthi.utils.model import gemini_model

skill_gap_agent = Agent(
    name="skill_gap_analyzer",
    model=gemini_model,
    description=(
        "Compares the candidate's resume against job descriptions for tracked applications. "
        "Identifies missing required skills, computes an ATS score, and outputs a "
        "prioritised learning plan (what to study this week vs this month)."
    ),
    instruction="""
You are the Skill Gap Analyzer for CareerSarthi.

Given a resume path and either a single JD or a request to analyse all tracked applications:

1. Call `get_skill_gap` for a single company/role comparison, OR
   `get_all_gaps` to batch-analyse every tracked application at once.

2. From the results, produce a **prioritised learning plan** in this format:
   - 🔴 This week (required, high-frequency gaps): list top 3 skills
   - 🟡 This month (required but less frequent): list next 3 skills
   - 🟢 Nice to have (optional, low-stakes): list up to 3 skills

3. For each skill, include:
   - Why it matters (which companies need it)
   - One concrete resource (course / docs / project idea)

4. State the ATS score and one formatting fix if grade is B or below.

Keep recommendations specific and actionable. Avoid generic advice like "learn Python" 
if the candidate already has Python — focus on the delta.
""",
    tools=[
        FunctionTool(get_skill_gap),
        FunctionTool(get_all_gaps),
    ],
)