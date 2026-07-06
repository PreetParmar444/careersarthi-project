"""
careersarthi.sub_agents
─────────────────────────
Re-exports each specialist agent so the root orchestrator
(careersarthi/agent.py) can do:

    from careersarthi.sub_agents import (
        inbox_tracker_agent,
        skill_gap_agent,
        deadline_guardian_agent,
        interview_prep_agent,
        privacy_guardian_agent,
    )

without needing to know the internal module layout of each sub-agent
package. Each sub-agent lives in its own folder (one agent.py per
specialist) so they stay independently testable and independently
swappable.
"""

from careersarthi.sub_agents.inbox_tracker.agent import inbox_tracker_agent
from careersarthi.sub_agents.skill_gap.agent import skill_gap_agent
from careersarthi.sub_agents.deadline_guardian.agent import deadline_guardian_agent
from careersarthi.sub_agents.interview_prep.agent import interview_prep_agent
from careersarthi.sub_agents.privacy_guardian.agent import privacy_guardian_agent

__all__ = [
    "inbox_tracker_agent",
    "skill_gap_agent",
    "deadline_guardian_agent",
    "interview_prep_agent",
    "privacy_guardian_agent",
]
