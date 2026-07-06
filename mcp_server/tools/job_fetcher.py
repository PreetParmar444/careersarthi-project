"""
mcp_server/tools/job_fetcher.py
────────────────────────────────
Fetches live job listings for a given role + location.
Primary source: Adzuna API. Fallback: Wellfound public listings scrape.
Returns a list of structured job objects ready for gap analysis.
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

_ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
_ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
_JSEARCH_KEY = os.getenv("JSEARCH_API_KEY", "")

_TIMEOUT = 10.0


# ── Adzuna ────────────────────────────────────────────────────────────────────

async def _fetch_adzuna(role: str, location: str = "india", n: int = 5) -> list[dict]:
    if not _ADZUNA_APP_ID or not _ADZUNA_APP_KEY:
        return []
    url = (
        f"https://api.adzuna.com/v1/api/jobs/in/search/1"
        f"?app_id={_ADZUNA_APP_ID}&app_key={_ADZUNA_APP_KEY}"
        f"&what={role.replace(' ', '+')}&where={location}&results_per_page={n}"
        f"&content-type=application/json"
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": j.get("title", ""),
                    "company": j.get("company", {}).get("display_name", ""),
                    "location": j.get("location", {}).get("display_name", ""),
                    "description": j.get("description", ""),
                    "url": j.get("redirect_url", ""),
                    "source": "adzuna",
                    "salary_min": j.get("salary_min"),
                    "salary_max": j.get("salary_max"),
                }
                for j in data.get("results", [])
            ]
    except Exception:
        return []


# ── JSearch (RapidAPI) ────────────────────────────────────────────────────────

async def _fetch_jsearch(role: str, location: str = "india", n: int = 5) -> list[dict]:
    if not _JSEARCH_KEY:
        return []
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": _JSEARCH_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {"query": f"{role} in {location}", "num_pages": "1", "page": "1"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": j.get("job_title", ""),
                    "company": j.get("employer_name", ""),
                    "location": j.get("job_city", "") + ", " + j.get("job_country", ""),
                    "description": (j.get("job_description", "") or "")[:1500],
                    "url": j.get("job_apply_link", ""),
                    "source": "jsearch",
                    "salary_min": j.get("job_min_salary"),
                    "salary_max": j.get("job_max_salary"),
                }
                for j in (data.get("data") or [])[:n]
            ]
    except Exception:
        return []


# ── Mock fallback (for demo / offline use) ────────────────────────────────────

_MOCK_JOBS = [
    {
        "title": "Data Engineer",
        "company": "Turing",
        "location": "Remote (India)",
        "description": (
            "Required: Python, PySpark, SQL, Airflow, AWS, Docker. "
            "Nice to have: Kafka, dbt, Terraform. "
            "Must have 2+ years experience with big data pipelines."
        ),
        "url": "https://turing.com/jobs/data-engineer",
        "source": "mock",
    },
    {
        "title": "Senior Software Engineer",
        "company": "Toptal",
        "location": "Remote (Global)",
        "description": (
            "Required: Python or Node.js, REST APIs, PostgreSQL, Docker, Kubernetes. "
            "Preferred: React, AWS, CI/CD pipelines."
        ),
        "url": "https://toptal.com/jobs/senior-software-engineer",
        "source": "mock",
    },
    {
        "title": "Backend Engineer",
        "company": "Wellfound Startup",
        "location": "Bengaluru / Remote",
        "description": (
            "Required: Python, FastAPI, PostgreSQL, Redis, Docker. "
            "Experience with microservices and message queues (Kafka). "
            "Nice to have: Kubernetes, Terraform."
        ),
        "url": "https://wellfound.com/jobs/backend-engineer",
        "source": "mock",
    },
]


# ── Public API ────────────────────────────────────────────────────────────────

async def fetch_jobs(
    role: str,
    location: str = "india",
    n: int = 5,
    use_mock_if_empty: bool = True,
) -> list[dict[str, Any]]:
    """
    Fetch job listings for *role* in *location*.

    Tries Adzuna first, then JSearch, then returns mock data for demo.

    Parameters
    ----------
    role              : Job title to search for (e.g. "Data Engineer").
    location          : City or country string.
    n                 : Max results to return.
    use_mock_if_empty : If True, returns curated mock data when all APIs fail.

    Returns
    -------
    List of job dicts with: title, company, location, description, url, source.
    """
    results = await _fetch_adzuna(role, location, n)
    if not results:
        results = await _fetch_jsearch(role, location, n)
    if not results and use_mock_if_empty:
        results = _MOCK_JOBS[:n]

    return results[:n]
