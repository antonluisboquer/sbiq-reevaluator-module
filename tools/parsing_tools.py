"""
parsing_tools.py — STEP_00 tools: parse predicted-conditions output and manifest.
"""

from __future__ import annotations

import json
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


# Keys in manifest metadata that are system/internal, not useful extracted data
_SYSTEM_KEYS = {
    "category", "confidence", "exceptions", "group_name",
    "group_index", "object_name", "total_pages", "vision_check",
}


@tool
def parse_predicted_conditions(
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
    state: Annotated[dict, InjectedState] = None,
) -> Command:
    """
    Parse the predicted-conditions output (or final_state) to extract document_requests.
    """
    s = state or {}
    raw = s.get("predicted_conditions_json", "")

    if not raw:
        return Command(update={
            "messages": [ToolMessage("ERROR: No predicted_conditions_json in input.", tool_call_id=tool_call_id)],
        })

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as e:
        return Command(update={
            "messages": [ToolMessage(f"ERROR: Invalid JSON: {e}", tool_call_id=tool_call_id)],
        })

    # Handle final_state format (extract final_output)
    if "final_output" in data and "document_requests" not in data:
        data = data["final_output"]

    document_requests = _as_list(data.get("document_requests", []))
    scenario_summary = data.get("scenario_summary", {})

    msg = f"Parsed {len(document_requests)} document requests from predicted-conditions output."

    return Command(update={
        "document_requests": document_requests,
        "scenario_summary": scenario_summary,
        "messages": [ToolMessage(msg, tool_call_id=tool_call_id)],
    })


@tool
def parse_manifest(
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
    state: Annotated[dict, InjectedState] = None,
) -> Command:
    """
    Parse the manifest JSON into a normalized list of documents with
    detected_document_type and extracted_fields.
    """
    s = state or {}
    raw = s.get("updated_manifest_json", "")

    if not raw:
        return Command(update={
            "messages": [ToolMessage("ERROR: No updated_manifest_json in input.", tool_call_id=tool_call_id)],
        })

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as e:
        return Command(update={
            "messages": [ToolMessage(f"ERROR: Invalid JSON: {e}", tool_call_id=tool_call_id)],
        })

    # Extract documents array from various formats
    if isinstance(data, list):
        raw_docs = data
    elif isinstance(data, dict):
        raw_docs = _as_list(data.get("documents") or data.get("manifest") or data.get("items") or [])
    else:
        raw_docs = []

    # Normalize: resolve doc type from category, flatten metadata into extracted_fields
    manifest_docs: list[dict] = []
    for doc in raw_docs:
        norm: dict[str, Any] = {"_raw": doc}
        meta = doc.get("metadata", {})
        category = doc.get("category", {})

        # Resolve document type
        if isinstance(category, dict) and category.get("category_name"):
            norm["detected_document_type"] = category["category_name"]
        elif isinstance(category, str):
            norm["detected_document_type"] = category
        else:
            for key in ("detected_document_type", "document_type", "doc_type", "name"):
                val = (doc.get(key) or meta.get(key) or "").strip()
                if val:
                    norm["detected_document_type"] = val
                    break

        # Build extracted_fields from metadata (excluding system keys)
        extracted = {}
        for k, v in meta.items():
            if k not in _SYSTEM_KEYS and v is not None:
                extracted[k] = v
        norm["extracted_fields"] = extracted

        manifest_docs.append(norm)

    # Summary of what's in the manifest
    from collections import Counter
    type_counts = Counter(d.get("detected_document_type", "unknown") for d in manifest_docs)
    types_str = ", ".join(f"{t}: {c}" for t, c in type_counts.most_common(10))

    msg = f"Parsed manifest: {len(manifest_docs)} documents. Types: {types_str}."

    return Command(update={
        "manifest_docs": manifest_docs,
        "messages": [ToolMessage(msg, tool_call_id=tool_call_id)],
    })
