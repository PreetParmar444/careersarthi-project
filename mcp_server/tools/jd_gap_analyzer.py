"""
mcp_server/tools/jd_gap_analyzer.py
─────────────────────────────────────
Compares candidate skills extracted from a resume against
required skills in a Job Description (JD).
Returns a gap report with missing skills, match score, and suggestions.
"""

from __future__ import annotations

import re
from typing import Any

# ── Skill extraction from JD text ─────────────────────────────────────────────

_ALL_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "scala", "go", "rust", "c++",
    "c#", "r", "sql", "bash", "shell", "php", "kotlin", "swift",
    # Data / Big Data
    "pyspark", "spark", "hive", "hadoop", "kafka", "airflow", "dbt", "flink",
    "pandas", "numpy", "polars", "databricks", "snowflake",
    # ML / AI
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "mlflow",
    "vertex ai", "sagemaker", "hugging face", "langchain", "openai",
    # Cloud
    "aws", "gcp", "azure", "cloud run", "lambda", "ec2", "s3", "bigquery",
    "cloud functions", "cloud storage", "gke", "eks",
    # DevOps
    "docker", "kubernetes", "k8s", "terraform", "ansible", "helm",
    "github actions", "jenkins", "ci/cd", "argocd",
    # Web
    "react", "angular", "vue", "django", "flask", "fastapi", "express",
    "nextjs", "graphql", "rest", "grpc",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firestore",
    # Tools / OS
    "git", "linux", "unix", "jira", "confluence", "postman", "grafana",
    "prometheus", "looker", "tableau", "power bi",
    # SAP / Enterprise (common at Deloitte-type firms)
    "sas", "spss", "stata", "sap", "oracle",
    # Business / Soft
    "agile", "scrum", "product management", "data analysis", "communication",
}

_NICE_TO_HAVE_MARKERS = re.compile(
    r"(nice\s+to\s+have|preferred|bonus|plus|advantage|desirable|good\s+to\s+have)", re.I
)
_REQUIRED_MARKERS = re.compile(
    r"(required|must\s+have|mandatory|essential|minimum|need)", re.I
)


def _extract_skills_from_text(text: str) -> set[str]:
    text_lower = text.lower()
    return {skill for skill in _ALL_SKILLS if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)}


def _score_match(candidate_skills: set[str], required: set[str], nice: set[str]) -> float:
    """Weighted match score: required skills count 2x, nice-to-have 1x."""
    if not required and not nice:
        return 0.0
    req_hits = len(candidate_skills & required)
    nice_hits = len(candidate_skills & nice)
    total_weight = len(required) * 2 + len(nice)
    if total_weight == 0:
        return 0.0
    return round((req_hits * 2 + nice_hits) / total_weight * 100, 1)


def _classify_jd_skills(jd_text: str) -> tuple[set[str], set[str]]:
    """
    Split JD skills into required vs nice-to-have by proximity to marker phrases.

    Splits text into clauses (by line, then by sentence-ending punctuation),
    so a single line like "Required: X, Y. Nice to have: Z." correctly puts
    X and Y in required and only Z in nice — rather than the nice-to-have
    marker anywhere in the line contaminating the whole line.
    """
    required: set[str] = set()
    nice: set[str] = set()

    clauses: list[str] = []
    for line in jd_text.splitlines():
        # Split each line further on sentence boundaries so mixed
        # "Required: ... . Nice to have: ..." lines classify correctly.
        clauses.extend(re.split(r"(?<=[.!;])\s+", line))

    for clause in clauses:
        clause_skills = _extract_skills_from_text(clause)
        if not clause_skills:
            continue
        if _NICE_TO_HAVE_MARKERS.search(clause):
            nice.update(clause_skills)
        else:
            required.update(clause_skills)

    # Skills found nowhere specific → assumed required
    all_jd = _extract_skills_from_text(jd_text)
    unclassified = all_jd - required - nice
    required.update(unclassified)

    return required, nice


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_gap(
    resume_skills: list[str] | dict,
    jd_text: str,
    company: str = "",
    role: str = "",
) -> dict[str, Any]:
    """
    Compute the skill gap between a candidate's resume and a job description.

    Parameters
    ----------
    resume_skills : Either a flat list of skills or the `detected_skills` dict
                    returned by resume_parser.parse_resume().
    jd_text       : Raw text of the job description.
    company       : Optional company name for context.
    role          : Optional role title for context.

    Returns
    -------
    dict with keys:
        match_score        – 0-100 weighted score
        required_missing   – skills in JD required section but not in resume
        nice_missing       – skills in JD preferred section but not in resume
        matched            – skills present in both
        recommendations    – prioritised list of skills to learn next
        company / role     – echoed back for traceability
    """
    # Normalise resume skills input
    if isinstance(resume_skills, dict):
        flat: set[str] = set()
        for v in resume_skills.values():
            flat.update(v if isinstance(v, list) else [v])
        candidate: set[str] = {s.lower() for s in flat}
    else:
        candidate = {s.lower() for s in resume_skills}

    required, nice = _classify_jd_skills(jd_text)
    score = _score_match(candidate, required, nice)

    req_missing = sorted(required - candidate)
    nice_missing = sorted(nice - candidate)
    matched = sorted((required | nice) & candidate)

    # Priority order for recommendations: required missing first, then nice-to-have
    recommendations = req_missing[:5] + nice_missing[:3]

    return {
        "company": company,
        "role": role,
        "match_score": score,
        "required_missing": req_missing,
        "nice_missing": nice_missing,
        "matched": matched,
        "recommendations": recommendations,
        "summary": (
            f"{score}% match for {role} at {company}. "
            f"Missing {len(req_missing)} required skills: {', '.join(req_missing[:3])}{'...' if len(req_missing) > 3 else ''}."
        ) if company else f"{score}% match. {len(req_missing)} required skills missing.",
    }
