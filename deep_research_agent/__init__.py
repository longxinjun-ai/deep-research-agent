"""deep-research-agent: document-driven deep & wide research agent system.

Synthesizes the ideas of grapeot/deep_research_agent (planner-executor +
scratchpad memory), grapeot/codex_wide_research (wide-research playbook),
and grapeot/context-infrastructure (incentive-aware source tiers, claim
verification, AGENTS.md routing), plus provider-agnostic LLM access.
"""
__version__ = "0.1.0"

from .config import load_config  # noqa: F401
from .orchestrator import Orchestrator  # noqa: F401
from .session import Session  # noqa: F401
from .usage import TokenTracker  # noqa: F401
