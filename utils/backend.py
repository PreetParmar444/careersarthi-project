"""
frontend/utils/backend.py
──────────────────────────
Thin adapter layer between the Streamlit UI and the CareerSarthi ADK backend.

Priority order for each call:
  1. Try to import and call the real backend module directly (monolithic mode —
     both frontend and backend run in the same Python process, which is the
     normal `streamlit run` case).
  2. If the import fails (e.g. running the frontend standalone for demo), fall
     back to rich mock data so the UI is always fully demonstrable.

This means:
  • Demos work without a running backend
  • When the full repo is installed, real agents are called automatically
  • The UI code never branches on "real vs mock" — it just calls this module
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any

# ── Helpers ────────────────────────────────────────────────────────────────────

def _run(coro):
    """Run an async coroutine from sync Streamlit code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Mock data ──────────────────────────────────────────────────────────────────

_MOCK_APPLICATIONS = [
    {"id": "app_001", "company": "Turing", "role": "Data Engineer", "portal": "turing.com",
     "applied_on": "2025-07-01", "status": "assessment", "deadline": (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d"),
     "extra": {"notes": "PySpark take-home test"}},
    {"id": "app_002", "company": "Toptal", "role": "Backend Engineer", "portal": "toptal.com",
     "applied_on": "2025-06-28", "status": "interview", "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d"),
     "extra": {"notes": "Live coding round scheduled"}},
    {"id": "app_003", "company": "Wellfound", "role": "ML Engineer", "portal": "wellfound.com",
     "applied_on": "2025-06-25", "status": "applied", "deadline": (datetime.now(timezone.utc) + timedelta(days=12)).strftime("%Y-%m-%d"),
     "extra": {"notes": "Applied via referral"}},
    {"id": "app_004", "company": "Deloitte", "role": "Data Analyst", "portal": "deloitte.com",
     "applied_on": "2025-06-20", "status": "shortlisted", "deadline": (datetime.now(timezone.utc) + timedelta(days=8)).strftime("%Y-%m-%d"),
     "extra": {"notes": "Case study round coming"}},
    {"id": "app_005", "company": "Infosys", "role": "Data Scientist", "portal": "infosys.com",
     "applied_on": "2025-06-18", "status": "rejected", "deadline": "",
     "extra": {"notes": "Position filled internally"}},
    {"id": "app_006", "company": "Google", "role": "SWE Intern", "portal": "careers.google.com",
     "applied_on": "2025-07-03", "status": "applied", "deadline": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
     "extra": {"notes": ""}},
]

_MOCK_SKILL_GAP = {
    "match_score": 62.5,
    "grade": "B",
    "ats_score": 68.0,
    "required_missing": ["pyspark", "hive", "kafka", "airflow", "sas"],
    "nice_missing": ["terraform", "dbt", "databricks"],
    "matched": ["python", "sql", "pandas", "numpy", "docker", "git", "fastapi", "postgresql", "react"],
    "recommendations": ["pyspark", "hive", "kafka", "airflow", "sas"],
    "summary": "62.5% match for Data Engineer at Turing. Missing 5 required skills: pyspark, hive, kafka...",
    "warnings": ["Add more quantified achievements and action verbs."],
    "missing_sections": [],
}

_MOCK_AUDIT = [
    {"ts": datetime.now(timezone.utc).isoformat(), "agent": "inbox_tracker", "action": "fetch_email", "pii_safe": True, "details": {"count": 12}},
    {"ts": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(), "agent": "skill_gap_analyzer", "action": "analyze_gap", "pii_safe": True, "details": {"company": "Turing", "match_score": 62.5}},
    {"ts": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(), "agent": "privacy_guardian", "action": "redact_text", "pii_safe": True, "details": {"redaction_count": 3}},
    {"ts": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(), "agent": "deadline_guardian", "action": "get_deadlines", "pii_safe": True, "details": {"count": 4}},
    {"ts": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(), "agent": "interview_prep", "action": "get_prep_pack", "pii_safe": True, "details": {"company": "Turing"}},
]

_MOCK_PREP = {
    "turing": {
        "format": "Live coding + async video screen + vetting test",
        "focus": ["Data structures & algorithms", "PySpark / SQL at scale", "System design basics"],
        "tips": "Turing's vetting is automated first — expect a timed coding test before any human round.",
        "questions": {
            "technical": [
                "Implement a distributed word count in PySpark.",
                "Design a data pipeline that ingests 10M events/day.",
                "Optimise a slow SQL query on a 50M-row table.",
                "Explain CAP theorem and where you'd sacrifice consistency.",
            ],
            "behavioral": [
                "Tell me about a time you debugged a production issue under pressure.",
                "Describe a project you built end-to-end. What would you redo?",
            ],
            "coding": [
                "Two Sum (LeetCode #1)",
                "LRU Cache (LeetCode #146)",
                "Merge K Sorted Lists (LeetCode #23)",
            ],
        },
        "resources": ["PySpark official docs", "Designing Data-Intensive Applications (book)", "LeetCode Top 100"],
    },
    "toptal": {
        "format": "English screen → Skills test → Live interview → Test project",
        "focus": ["Strong communication in English screen", "Live problem-solving under observation", "Polished test project"],
        "tips": "Toptal's pass rate is ~3% — the test project is where most candidates lose on edge cases and code quality.",
        "questions": {
            "technical": [
                "Walk through the architecture of your largest production system.",
                "How would you design a rate limiter for an API?",
                "Explain async/await and the Python GIL.",
            ],
            "behavioral": [
                "Why do you want to work remotely? How do you stay productive?",
                "Describe a time you delivered under a tight deadline.",
            ],
            "coding": [
                "Valid Parentheses (LeetCode #20)",
                "Binary Tree Level Order Traversal (LeetCode #102)",
                "Design Twitter (System Design)",
            ],
        },
        "resources": ["Toptal Engineering Blog", "Clean Code (book)", "Pramp for mock interviews"],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_applications() -> list[dict[str, Any]]:
    """Fetch all tracked applications from the backend or mock data."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from careersarthi.utils.storage import get_all_applications
        apps = _run(get_all_applications())
        return apps if apps else _MOCK_APPLICATIONS
    except Exception:
        return _MOCK_APPLICATIONS


def get_deadlines() -> list[dict[str, Any]]:
    """Return applications with upcoming deadlines, with urgency labels."""
    apps = get_applications()
    deadlines = []
    now = datetime.now(timezone.utc)
    for app in apps:
        dl_str = app.get("deadline", "")
        if not dl_str:
            continue
        try:
            dl = datetime.fromisoformat(dl_str).replace(tzinfo=timezone.utc)
            days = (dl - now).days
            if days < 0:
                urgency = "⚫ overdue"
            elif days <= 3:
                urgency = "🔴 critical"
            elif days <= 7:
                urgency = "🟡 upcoming"
            elif days <= 14:
                urgency = "🟢 on radar"
            else:
                urgency = "⚪ future"
            deadlines.append({**app, "days_remaining": days, "urgency": urgency, "deadline_date": dl})
        except Exception:
            continue
    return sorted(deadlines, key=lambda x: x["days_remaining"])


def get_skill_gap(resume_path: str = "", jd_text: str = "") -> dict[str, Any]:
    """Run skill gap analysis, falling back to mock data."""
    if not resume_path:
        return _MOCK_SKILL_GAP
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from mcp_server.tools.resume_parser import parse_resume
        from mcp_server.tools.jd_gap_analyzer import analyze_gap
        from mcp_server.tools.ats_scorer import score_resume

        parsed = parse_resume(resume_path)
        if "error" in parsed:
            return {**_MOCK_SKILL_GAP, "error": parsed["error"]}

        gap = analyze_gap(
            resume_skills=parsed.get("detected_skills", {}),
            jd_text=jd_text or "Required: Python, SQL, Machine Learning, Data Analysis, Docker, AWS.",
        )
        ats = score_resume(resume_text=parsed.get("raw_text", ""), jd_text=jd_text)
        return {**gap, "ats_score": ats.get("ats_score", 0), "grade": ats.get("grade", "C"),
                "warnings": ats.get("warnings", []), "missing_sections": ats.get("missing_sections", [])}
    except Exception:
        return _MOCK_SKILL_GAP


def get_audit_log(n: int = 20) -> list[dict[str, Any]]:
    """Return recent audit log entries."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from careersarthi.utils.audit_log import tail
        records = tail(n)
        return records if records else _MOCK_AUDIT
    except Exception:
        return _MOCK_AUDIT


def get_interview_prep(company: str, role: str = "") -> dict[str, Any]:
    """Get company-specific interview prep pack."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from careersarthi.sub_agents.interview_prep.agent import get_interview_prep_pack, get_targeted_questions
        pack = get_interview_prep_pack(company=company, role=role)
        questions = get_targeted_questions(company=company, role=role)
        return {**pack, "question_categories": questions.get("question_categories", {})}
    except Exception:
        key = company.strip().lower()
        mock = _MOCK_PREP.get(key, {
            "format": "HR screen → Technical round → Final interview",
            "focus": ["Core CS fundamentals", "Domain-specific skills", "Behavioral STAR stories"],
            "tips": f"Research {company}'s interview process on Glassdoor before your round.",
            "questions": {"technical": ["Describe your most challenging technical project."],
                         "behavioral": ["Why do you want to work at this company?"],
                         "coding": ["Practice LeetCode medium-level problems."]},
            "resources": ["Glassdoor", "LeetCode", "Pramp"],
        })
        return mock


def run_agent_pipeline(prompt: str) -> tuple[str, list[dict]]:
    """
    Run the CareerSarthi root agent with a text prompt.
    Returns (response_text, tool_steps_list).
    """
    steps = []

    # Determine which agents will run based on the prompt
    prompt_lower = prompt.lower()
    if any(k in prompt_lower for k in ["scan", "inbox", "gmail", "check application", "what's new"]):
        steps = [
            {"label": "Scanning Gmail inbox...", "agent": "Inbox Tracker", "done": False},
            {"label": "Analyzing skill gaps...", "agent": "Skill Gap Agent", "done": False},
            {"label": "Checking deadlines...", "agent": "Deadline Guardian", "done": False},
            {"label": "Running privacy audit...", "agent": "Privacy Guardian", "done": False},
        ]
    elif any(k in prompt_lower for k in ["gap", "skill", "resume", "ats"]):
        steps = [
            {"label": "Parsing resume...", "agent": "Skill Gap Agent", "done": False},
            {"label": "Comparing against JDs...", "agent": "Skill Gap Agent", "done": False},
        ]
    elif any(k in prompt_lower for k in ["deadline", "urgent", "expir"]):
        steps = [{"label": "Fetching application deadlines...", "agent": "Deadline Guardian", "done": False}]
    elif any(k in prompt_lower for k in ["prep", "interview", "question"]):
        steps = [
            {"label": "Loading company patterns...", "agent": "Interview Prep", "done": False},
            {"label": "Generating targeted questions...", "agent": "Interview Prep", "done": False},
        ]
    elif any(k in prompt_lower for k in ["audit", "safe", "privacy", "secure"]):
        steps = [{"label": "Reading audit trail...", "agent": "Privacy Guardian", "done": False}]

    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from google.adk.runners import InMemoryRunner
        from careersarthi.agent import careersarthi_pipeline

        runner = InMemoryRunner(agent=careersarthi_pipeline, app_name="careersarthi-ui")
        session = _run(runner.session_service.create_session(app_name="careersarthi-ui", user_id="ui_user"))

        parts: list[str] = []

        async def _go():
            from google.genai import types as genai_types
            content = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])
            async for event in runner.run_async(user_id="ui_user", session_id=session.id, new_message=content):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            parts.append(part.text)

        _run(_go())
        response = "\n".join(parts) or _mock_response(prompt)
        for s in steps:
            s["done"] = True
        return response, steps

    except Exception:
        time.sleep(1.5)  # simulate processing
        for s in steps:
            s["done"] = True
        return _mock_response(prompt), steps


def _mock_response(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(k in prompt_lower for k in ["scan", "inbox", "gmail"]):
        return """**Inbox scan complete!** Found **6 job-related emails** in the last 7 days.

📥 **New updates:**
- **Turing** — Assessment ready: PySpark data pipeline challenge (⏰ due in 2 days)
- **Toptal** — Live interview scheduled for next Tuesday
- **Deloitte** — Shortlisted for Data Analyst — case study round coming

📊 **Status summary:** 2 active assessments, 1 interview, 3 applications pending review.

💡 **Tip:** Your PySpark gap is blocking Turing's assessment — run `careersarthi gaps` for a focused study plan."""

    elif any(k in prompt_lower for k in ["gap", "skill", "ats"]):
        return """**Skill Gap Analysis — Turing Data Engineer:**

📊 **ATS Score:** 68/100 (Grade B)
🎯 **Match Score:** 62.5%

**🔴 Missing required skills (study this week):**
- PySpark — needed by Turing, Wellfound, and 3 others
- Hive — needed for Turing's data pipeline role
- Kafka — needed by Wellfound ML Engineer

**🟡 Nice-to-have (study this month):**
- Terraform, dbt, Databricks

**✅ Skills you already have:**
Python, SQL, Pandas, NumPy, Docker, FastAPI, Git, PostgreSQL

**📚 Recommended resources:** PySpark official docs, Databricks Academy (free tier)"""

    elif any(k in prompt_lower for k in ["deadline", "urgent"]):
        return """**Upcoming deadlines — sorted by urgency:**

🔴 **CRITICAL (≤ 3 days):**
- Turing — Data Engineer assessment · **2 days left**

🟡 **UPCOMING (≤ 7 days):**  
- Toptal — Live interview · **5 days left**
- Deloitte — Case study submission · **8 days left**

🟢 **ON RADAR (≤ 14 days):**
- Wellfound — ML Engineer · **12 days left**

⚡ **Action:** Start the Turing assessment today — it's the most urgent."""

    elif any(k in prompt_lower for k in ["prep", "interview"]):
        company = "Turing"
        for c in ["toptal", "wellfound", "deloitte", "google", "amazon", "microsoft"]:
            if c in prompt_lower:
                company = c.title()
        return f"""**Interview Prep — {company}:**

📋 **Format:** Live coding + async video screen + vetting test

**🎯 Top 3 focus areas:**
1. Data structures & algorithms (LeetCode medium)
2. PySpark / distributed computing fundamentals
3. System design basics (data pipelines)

**💬 Likely questions:**
- *Technical:* "Implement a word count in PySpark" / "Design a 10M event/day pipeline"
- *Behavioral:* "Describe a project you built end-to-end — what would you redo?"

**💡 {company}-specific tip:** Turing's vetting is automated first — nail the async coding test before worrying about the human rounds."""

    elif any(k in prompt_lower for k in ["audit", "privacy", "safe", "secure"]):
        return """**Privacy & Security Audit:**

🔒 **Data protection status:** ✅ All clear

**Recent agent actions (last 24h):**
- Inbox Tracker: scanned 12 emails, extracted 3 new applications
- Privacy Guardian: redacted PII from 3 email bodies (3 email addresses removed)
- Skill Gap: ran 2 JD comparisons — no external data sent
- Deadline Guardian: checked 4 applications with deadlines

**🔐 OAuth scopes active:**
- `gmail.readonly` — read-only inbox scan (no send/delete)
- `calendar` — create deadline reminders only

**💾 Storage:** SQLite with Fernet encryption at rest · 6 applications stored"""

    else:
        return """Hi! I'm **CareerSarthi**, your AI career co-pilot. 🚀

Here's what I can help you with:

- 📧 **"Scan my Gmail"** — Find and track new application updates
- 📊 **"Analyze my skill gaps"** — See what's blocking your applications  
- ⏰ **"Any deadlines?"** — Get a urgency-sorted deadline list
- 🎤 **"Prep me for Turing"** — Company-specific interview prep
- 🔒 **"Show audit log"** — Review what data I've accessed

What would you like to do?"""


def get_kpis() -> dict[str, Any]:
    """Return dashboard KPI values."""
    apps = get_applications()
    deadlines = get_deadlines()
    critical = [d for d in deadlines if "critical" in d.get("urgency", "")]
    interviews = [a for a in apps if a.get("status") == "interview"]
    gap = get_skill_gap()
    return {
        "total_applications": len(apps),
        "critical_deadlines": len(critical),
        "ats_score": gap.get("ats_score", 68),
        "interviews_scheduled": len(interviews),
        "active_statuses": {s: len([a for a in apps if a.get("status") == s])
                           for s in ["applied", "assessment", "shortlisted", "interview", "offer", "rejected"]},
    }
