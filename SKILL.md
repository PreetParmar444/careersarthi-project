---
name: careersarthi
description: >
  ADK multi-agent career co-pilot. Tracks job applications from your inbox,
  flags skill gaps against real job descriptions, surfaces deadlines, and
  generates company-specific interview prep. Use this skill whenever the
  user mentions job applications, interview prep, resume gaps, application
  deadlines, or portals like Turing/Toptal/Wellfound/Deloitte.
version: 0.1.0
entry_point: cli/main.py
commands:
  - name: track
    description: Scan inbox, analyse skill gaps, and check deadlines in one pipeline run.
    usage: careersarthi track
  - name: gaps
    description: Compare a resume against tracked job descriptions and surface missing skills.
    usage: careersarthi gaps --resume <path> [--company <name>]
  - name: prep
    description: Generate company-specific interview preparation.
    usage: careersarthi prep <company> [--role <title>]
  - name: deadlines
    description: List upcoming application deadlines sorted by urgency.
    usage: careersarthi deadlines
  - name: audit
    description: Show the security audit trail and PII-handling status.
    usage: careersarthi audit
  - name: applications
    description: List all tracked applications in a table.
    usage: careersarthi applications
  - name: serve-mcp
    description: Start the Career MCP server (stdio or --http for Cloud Run).
    usage: careersarthi serve-mcp [--http]
requires_auth:
  - scope: gmail.readonly
    purpose: Scan for job-application emails (read-only, no send/delete).
  - scope: calendar
    purpose: Create deadline reminder events.
install: |
  pip install -e .
  cp .env.example .env   # then fill in GOOGLE_API_KEY, OAuth credentials, STORAGE_ENCRYPTION_KEY
  python -m careersarthi.auth   # one-time Gmail/Calendar OAuth consent flow
---

# CareerSarthi skill

This skill packages CareerSarthi as an installable Agents CLI skill for
Antigravity or Gemini CLI. Once installed, the `careersarthi` command and
its subcommands (`track`, `gaps`, `prep`, `deadlines`, `audit`,
`applications`, `serve-mcp`) become available directly in the CLI/agent
environment, backed by the same ADK multi-agent pipeline described in
`careersarthi/agent.py`.

See the top-level `README.md` for full architecture, security model, and
deployment instructions.
