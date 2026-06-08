"""
general.py — General-purpose tools available at every step.
"""

from __future__ import annotations

import datetime

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import Annotated


_STEP_SEQUENCE = ["STEP_00", "STEP_01", "STEP_02"]


@tool
def save_step_report(
    step_id: str,
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
    state: Annotated[dict, InjectedState] = None,
) -> Command:
    """
    Persist findings for a completed step and advance to the next step.
    Call this after completing each step.

    Args:
        step_id: The step identifier (e.g. "STEP_00").
        summary: A brief summary of what this step accomplished.
    """
    report = {
        "step_id": step_id,
        "summary": summary,
        "completed_at": datetime.datetime.utcnow().isoformat(),
    }

    idx = _STEP_SEQUENCE.index(step_id) if step_id in _STEP_SEQUENCE else -1
    if idx >= 0 and idx + 1 < len(_STEP_SEQUENCE):
        next_step = _STEP_SEQUENCE[idx + 1]
        msg = f"Step report saved for {step_id}. Advancing to {next_step}."
    else:
        next_step = step_id
        msg = f"Step report saved for {step_id}. This is the final step."

    return Command(update={
        "step_reports": {step_id: report},
        "current_step": next_step,
        "messages": [ToolMessage(msg, tool_call_id=tool_call_id)],
    })


@tool
def get_workflow_status(
    state: Annotated[dict, InjectedState] = None,
) -> dict:
    """Return current workflow progress."""
    s = state or {}
    return {
        "current_step": s.get("current_step"),
        "completed_steps": list(s.get("step_reports", {}).keys()),
    }
