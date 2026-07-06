"""
mcp_server/server.py
──────────────────────
The Career MCP server — the custom MCP server CareerSarthi's agents (and
any other MCP-aware client, e.g. Antigravity or Gemini CLI) talk to for
resume parsing, ATS scoring, JD-gap analysis, and live job fetching.

Exposes four tools, each a thin wrapper around the corresponding module
in mcp_server/tools/ — the wrapping here is intentionally minimal: all
real logic stays in the tool modules so it's unit-testable without spinning
up a server (see tests/test_core.py).

Transports:
  • stdio (default) – for local agent processes / Gemini CLI / Antigravity
        python -m mcp_server.server
  • streamable-http  – for containerised/Cloud Run deployment
        python -m mcp_server.server --http
    Host/port are configurable via MCP_HTTP_HOST / MCP_HTTP_PORT (default
    0.0.0.0:8080, matching docker-compose.yml's exposed port).

Requires the official MCP Python SDK: `pip install mcp`.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.resume_parser import parse_resume
from mcp_server.tools.jd_gap_analyzer import analyze_gap
from mcp_server.tools.ats_scorer import score_resume
from mcp_server.tools.job_fetcher import fetch_jobs

mcp = FastMCP("career-mcp")


# ── Tool: resume parsing ─────────────────────────────────────────────────────

@mcp.tool()
def parse_resume_tool(resume_path: str) -> dict[str, Any]:
    """
    Extract raw text and categorised skills from a resume file.

    Args:
        resume_path: Path to a .pdf, .docx, or .txt resume file, readable
            from the MCP server's filesystem.

    Returns a dict with raw_text, detected_skills (by category),
    skill_count, years_experience, and word_count — or an "error" key
    if the file is missing, unsupported, or has no extractable text.
    """
    return parse_resume(resume_path)


# ── Tool: JD gap analysis ────────────────────────────────────────────────────

@mcp.tool()
def analyze_skill_gap(
    resume_skills: dict[str, list[str]] | list[str],
    jd_text: str,
    company: str = "",
    role: str = "",
) -> dict[str, Any]:
    """
    Compare candidate skills against a job description and return the gap.

    Args:
        resume_skills: Either the `detected_skills` dict returned by
            parse_resume_tool, or a flat list of skill strings.
        jd_text: Raw job description text.
        company: Optional company name, echoed back for traceability.
        role: Optional role title, echoed back for traceability.

    Returns match_score (0-100), required_missing, nice_missing, matched,
    recommendations, and a one-line summary.
    """
    return analyze_gap(resume_skills=resume_skills, jd_text=jd_text, company=company, role=role)


# ── Tool: ATS scoring ─────────────────────────────────────────────────────────

@mcp.tool()
def score_resume_ats(resume_text: str, jd_text: str = "") -> dict[str, Any]:
    """
    Score a resume's ATS (Applicant Tracking System) compatibility.

    Args:
        resume_text: Plain text extracted from the candidate's resume
            (e.g. the raw_text field from parse_resume_tool).
        jd_text: Optional job description text, used to compute keyword
            density against this specific role. If omitted, keyword_score
            defaults to a neutral 50.0.

    Returns ats_score (0-100 overall), grade (A-D), and the four
    component scores (keyword, section, verb, format) plus warnings.
    """
    return score_resume(resume_text=resume_text, jd_text=jd_text)


# ── Tool: live job fetching ───────────────────────────────────────────────────

@mcp.tool()
async def fetch_job_listings(
    role: str,
    location: str = "india",
    n: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch live job listings for a role + location.

    Tries Adzuna, then JSearch, then falls back to curated mock listings
    if no API keys are configured or both providers fail — so this tool
    always returns usable JD text for gap analysis, even offline/in a demo.

    Args:
        role: Job title to search for (e.g. "Data Engineer").
        location: City or country string (default "india").
        n: Maximum number of listings to return (default 5).
    """
    return await fetch_jobs(role=role, location=location, n=n)


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Career MCP server")
    parser.add_argument(
        "--http", action="store_true",
        help="Serve over streamable HTTP instead of stdio (for Cloud Run / containerised deployment).",
    )
    args = parser.parse_args()

    if args.http:
        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_HTTP_PORT", "8080"))
        mcp.settings.host = host
        mcp.settings.port = port
        print(f"Career MCP server listening on http://{host}:{port} (streamable-http)")
        mcp.run(transport="streamable-http")
    else:
        # stdio: no print to stdout — the protocol itself uses stdout as the
        # transport, so any extra print() here would corrupt the stream.
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
