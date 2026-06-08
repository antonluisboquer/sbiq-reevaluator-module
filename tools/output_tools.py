"""
output_tools.py — STEP_02: Generate the final output with satisfied_specifications populated.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import Annotated


def _as_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return [val]
    return [val] if val else []


@tool
def generate_final_output(
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
    state: Annotated[dict, InjectedState] = None,
) -> Command:
    """
    Assemble the final reevaluated output. The document_requests now have
    satisfied_specifications populated — specs that the manifest satisfies
    have been moved there from specifications.
    """
    s = state or {}
    document_requests = _as_list(s.get("document_requests", []))
    scenario_summary = s.get("scenario_summary", {})

    # Compute stats
    total = len(document_requests)
    by_status: dict[str, int] = {}
    total_satisfied_specs = 0
    total_remaining_specs = 0

    for dr in document_requests:
        st = dr.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        display = dr.get("display", {})
        total_satisfied_specs += len(_as_list(display.get("satisfied_requirements", [])))
        total_remaining_specs += len(_as_list(display.get("documentation_requirements", [])))

    final: dict[str, Any] = {
        "scenario_summary": scenario_summary,
        "document_requests": document_requests,
        "stats": {
            "total_document_requests": total,
            "by_status": by_status,
            "total_satisfied_specifications": total_satisfied_specs,
            "total_remaining_specifications": total_remaining_specs,
        },
    }

    msg = (
        f"Final output: {total} document requests. "
        f"Status: {by_status}. "
        f"{total_satisfied_specs} specs satisfied, {total_remaining_specs} remaining."
    )

    return Command(update={
        "final_output": final,
        "messages": [ToolMessage(msg, tool_call_id=tool_call_id)],
    })
