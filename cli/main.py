"""
cli/main.py
────────────
CareerSarthi Agents CLI.

Installable as a standalone skill into Gemini CLI / Antigravity, or run
directly. Wraps the ADK agent pipeline behind ergonomic subcommands.

Usage:
    careersarthi track                       # run inbox scan + gap + deadline pipeline
    careersarthi gaps --resume resume.pdf     # skill gap analysis only
    careersarthi prep <company> [--role ROLE] # interview prep for one company
    careersarthi deadlines                    # list upcoming deadlines
    careersarthi audit                        # show recent agent actions / PII safety
    careersarthi serve-mcp [--http]           # start the Career MCP server
"""

from __future__ import annotations

import asyncio
import sys

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
app = typer.Typer(
    name="careersarthi",
    help="CareerSarthi — ADK multi-agent career co-pilot CLI.",
    no_args_is_help=True,
)
console = Console()


async def _run_agent_query(prompt: str) -> str:
    """
    Thin wrapper that runs the root ADK agent with a single text prompt
    and returns its final text response. Uses ADK's Runner under the hood.
    """
    from google.adk.runners import InMemoryRunner
    from careersarthi.agent import careersarthi_pipeline

    runner = InMemoryRunner(agent=careersarthi_pipeline, app_name="careersarthi-cli")
    session = await runner.session_service.create_session(
        app_name="careersarthi-cli",
        user_id="cli_user",
    )

    final_text_parts: list[str] = []

    async def _go():
        from google.genai import types as genai_types
        content = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])
        async for event in runner.run_async(
            user_id="cli_user", session_id=session.id, new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text_parts.append(part.text)

    await _go()
    return "\n".join(final_text_parts) or "(no response)"


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def track():
    """Run the full pipeline: scan inbox → analyse gaps → check deadlines."""
    console.print(Panel.fit("Running CareerSarthi pipeline...", style="cyan"))
    with console.status("[cyan]Agents working...", spinner="dots"):
        result = asyncio.run(
            _run_agent_query(
                "Check my applications — scan my inbox, analyse skill gaps, and check deadlines."
            )
        )
    console.print(Panel(result, title="CareerSarthi", border_style="green"))


@app.command()
def gaps(
    resume: str = typer.Option(..., "--resume", "-r", help="Path to resume PDF/DOCX."),
    company: str = typer.Option("", "--company", "-c", help="Limit to one company (optional)."),
):
    """Run skill gap analysis against tracked applications."""
    prompt = f"Analyse my skill gaps using the resume at {resume}."
    if company:
        prompt += f" Focus on the {company} application."
    with console.status("[cyan]Analysing gaps...", spinner="dots"):
        result = asyncio.run(_run_agent_query(prompt))
    console.print(Panel(result, title="Skill Gap Report", border_style="yellow"))


@app.command()
def prep(
    company: str = typer.Argument(..., help="Company name to prep for."),
    role: str = typer.Option("", "--role", "-R", help="Job title (optional)."),
):
    """Generate interview prep for a specific company."""
    prompt = f"Prep me for the interview at {company}."
    if role:
        prompt += f" The role is {role}."
    with console.status(f"[cyan]Preparing for {company}...", spinner="dots"):
        result = asyncio.run(_run_agent_query(prompt))
    console.print(Panel(result, title=f"Interview Prep — {company}", border_style="magenta"))


@app.command()
def deadlines():
    """List all upcoming application deadlines, sorted by urgency."""
    with console.status("[cyan]Checking deadlines...", spinner="dots"):
        result = asyncio.run(
            _run_agent_query("What deadlines are coming up across my applications?")
        )
    console.print(Panel(result, title="Deadlines", border_style="red"))


@app.command()
def audit():
    """Show the recent agent activity log and PII-safety status."""
    with console.status("[cyan]Pulling audit trail...", spinner="dots"):
        result = asyncio.run(
            _run_agent_query("Show me the audit log and confirm my data is being handled safely.")
        )
    console.print(Panel(result, title="Privacy & Audit", border_style="blue"))


@app.command(name="serve-mcp")
def serve_mcp(
    http: bool = typer.Option(False, "--http", help="Serve over HTTP/SSE instead of stdio."),
):
    """Start the Career MCP server (stdio by default; --http for Cloud Run)."""
    import subprocess

    args = [sys.executable, "-m", "mcp_server.server"]
    if http:
        args.append("--http")
    console.print(f"[cyan]Starting Career MCP server ({'http' if http else 'stdio'})...[/cyan]")
    subprocess.run(args)


@app.command()
def applications():
    """List all tracked applications in a table."""
    from careersarthi.utils.storage import get_all_applications

    apps = asyncio.run(get_all_applications())
    if not apps:
        console.print("[yellow]No applications tracked yet. Run `careersarthi track` first.[/yellow]")
        return

    table = Table(title="Tracked Applications")
    table.add_column("Company", style="cyan")
    table.add_column("Role")
    table.add_column("Portal")
    table.add_column("Status", style="green")
    table.add_column("Deadline", style="red")

    for a in apps:
        table.add_row(
            a.get("company", ""), a.get("role", ""), a.get("portal", ""),
            a.get("status", ""), a.get("deadline", "") or "—",
        )
    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
