"""
tests/test_core.py
─────────────────────
Fast unit tests covering the security layer and MCP tool logic.
No network or OAuth required — safe to run in CI.

Run: pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from careersarthi.utils.pii_redactor import redact, is_safe
from mcp_server.tools.jd_gap_analyzer import analyze_gap
from mcp_server.tools.ats_scorer import score_resume


# ── PII redaction ──────────────────────────────────────────────────────────────

def test_redacts_email():
    res = redact("Contact me at rahul.sharma@gmail.com for details.")
    assert "[EMAIL]" in res.clean_text
    assert "rahul.sharma@gmail.com" not in res.clean_text
    assert res.was_redacted


def test_redacts_indian_phone():
    res = redact("Call +91 98765 43210 anytime.")
    assert "[PHONE]" in res.clean_text


def test_redacts_pan():
    res = redact("My PAN is ABCDE1234F.")
    assert "[PAN]" in res.clean_text


def test_is_safe_true_for_clean_text():
    assert is_safe("This is a generic sentence with no personal data.")


def test_is_safe_false_for_pii():
    assert not is_safe("Email me at test@example.com")


# ── JD gap analyzer ────────────────────────────────────────────────────────────

def test_gap_analysis_finds_missing_required_skill():
    jd = "Required: Python, PySpark, Hive, SQL. Nice to have: Kafka."
    result = analyze_gap(resume_skills=["python", "sql"], jd_text=jd, company="Turing", role="Data Engineer")
    assert "pyspark" in result["required_missing"]
    assert "hive" in result["required_missing"]
    assert "python" in result["matched"]


def test_gap_analysis_full_match_scores_high():
    jd = "Required: Python, SQL."
    result = analyze_gap(resume_skills=["python", "sql"], jd_text=jd)
    assert result["match_score"] == 100.0


def test_gap_analysis_accepts_dict_input():
    jd = "Required: Python, Docker."
    skills_dict = {"languages": ["python"], "devops": ["docker"]}
    result = analyze_gap(resume_skills=skills_dict, jd_text=jd)
    assert result["match_score"] == 100.0


# ── ATS scorer ──────────────────────────────────────────────────────────────────

def test_ats_score_penalises_missing_sections():
    minimal_resume = "John Doe\nA short bio with no clear sections."
    result = score_resume(minimal_resume)
    assert result["section_score"] < 50
    assert result["grade"] in ("C", "D")


def test_ats_score_rewards_action_verbs():
    rich_resume = (
        "Experience: Built, developed, designed, implemented, led, managed, "
        "optimized, deployed multiple production systems.\n"
        "Education: B.Tech CS\nSkills: Python, SQL\nProjects: Built a pipeline."
    )
    result = score_resume(rich_resume)
    assert result["verb_score"] >= 90


def test_ats_score_flags_html_tags():
    bad_resume = "Experience: <b>Built</b> things.\nEducation: BTech\nSkills: Python\nProjects: X"
    result = score_resume(bad_resume)
    assert any("HTML" in w for w in result["warnings"])
