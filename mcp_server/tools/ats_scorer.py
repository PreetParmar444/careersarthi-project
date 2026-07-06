"""
mcp_server/tools/ats_scorer.py
────────────────────────────────
Heuristic ATS (Applicant Tracking System) score.
Measures keyword density, section completeness, formatting red flags,
and action-verb usage — the four axes most ATS scanners weight.
"""

from __future__ import annotations

import re
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

_ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "led", "managed",
    "optimised", "optimized", "improved", "reduced", "increased", "deployed",
    "architected", "automated", "delivered", "migrated", "launched",
    "mentored", "collaborated", "analysed", "analyzed", "created",
}

_FORMAT_RED_FLAGS = [
    (re.compile(r"<[^>]+>"), "HTML tags detected — ATS may not parse correctly"),
    (re.compile(r"\t{3,}"), "Excessive tabs — may indicate table-based formatting"),
    (re.compile(r"[│┃|]{2,}"), "Box-drawing characters detected"),
    (re.compile(r"[\u2022\u25cf\u25cb\u2713]"), "Fancy bullet characters — prefer plain hyphens"),
]

_REQUIRED_SECTIONS = ["experience", "education", "skills", "project"]


def _keyword_density(resume_text: str, jd_text: str) -> float:
    """What fraction of unique JD words appear in the resume?"""
    jd_words = {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", jd_text)}
    if not jd_words:
        return 0.0
    resume_lower = resume_text.lower()
    hits = sum(1 for w in jd_words if w in resume_lower)
    return round(hits / len(jd_words) * 100, 1)


def _section_score(resume_text: str) -> tuple[float, list[str]]:
    present = [sec for sec in _REQUIRED_SECTIONS if sec in resume_text.lower()]
    missing = [sec for sec in _REQUIRED_SECTIONS if sec not in resume_text.lower()]
    return len(present) / len(_REQUIRED_SECTIONS) * 100, missing


def _action_verb_score(resume_text: str) -> float:
    words = {w.lower() for w in re.findall(r"\b[a-z]+\b", resume_text.lower())}
    hits = words & _ACTION_VERBS
    # Ideal: at least 8 distinct action verbs
    return min(len(hits) / 8 * 100, 100)


def _format_score(resume_text: str) -> tuple[float, list[str]]:
    warnings: list[str] = []
    for pattern, msg in _FORMAT_RED_FLAGS:
        if pattern.search(resume_text):
            warnings.append(msg)
    return max(0.0, 100 - len(warnings) * 20), warnings


# ── Public API ────────────────────────────────────────────────────────────────

def score_resume(resume_text: str, jd_text: str = "") -> dict[str, Any]:
    """
    Compute an ATS compatibility score for a resume against an optional JD.

    Parameters
    ----------
    resume_text : Plain text extracted from the candidate's resume.
    jd_text     : Plain text of the job description (can be empty).

    Returns
    -------
    dict with:
        ats_score      – 0-100 overall score
        keyword_score  – keyword density vs JD
        section_score  – completeness of standard sections
        verb_score     – action verb richness
        format_score   – formatting cleanliness
        warnings       – list of formatting issues
        missing_sections – sections not detected
        grade          – A / B / C / D
    """
    kw_score = _keyword_density(resume_text, jd_text) if jd_text else 50.0
    sec_score, missing_sec = _section_score(resume_text)
    verb_score = _action_verb_score(resume_text)
    fmt_score, warnings = _format_score(resume_text)

    # Weighted aggregate
    overall = round(
        kw_score * 0.35 + sec_score * 0.25 + verb_score * 0.20 + fmt_score * 0.20, 1
    )

    grade = "A" if overall >= 80 else "B" if overall >= 65 else "C" if overall >= 50 else "D"

    return {
        "ats_score": overall,
        "grade": grade,
        "keyword_score": kw_score,
        "section_score": sec_score,
        "verb_score": verb_score,
        "format_score": fmt_score,
        "warnings": warnings,
        "missing_sections": missing_sec,
        "tip": (
            "Strong ATS profile — focus on role-specific keywords."
            if overall >= 80
            else "Add more quantified achievements and action verbs."
            if overall >= 60
            else "Resume needs structural rework — missing key sections and keywords."
        ),
    }
