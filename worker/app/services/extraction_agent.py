import json
import logging
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services import tools

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 8

SYSTEM_PROMPT = (
    "You are a data extractor for industrial/laboratory technical reports "
    "(certificates of analysis, process logs). You are given the report type and "
    "the transcribed text of its pages. Identify every measurable field (e.g. pH, "
    "purity, temperature, batch, date) and its value.\n\n"
    "Use the tools whenever they help your reasoning: lookup_spec_profile to know "
    "which unit is expected and whether a value looks out of range, convert_units "
    "to normalize units, calculate for arithmetic (averages, differences). Do not "
    "invent values that are not in the text. When you are done, CALL "
    "submit_extraction exactly once with every field you found. Assign low "
    "confidence (< 0.5) to any field you had to infer or that is ambiguous in the "
    "source text."
)

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "convert_units",
        "description": (
            "Converts a numeric value between units "
            "(mass, volume, concentration, pressure, temperature)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "from_unit": {"type": "string"},
                "to_unit": {"type": "string"},
            },
            "required": ["value", "from_unit", "to_unit"],
        },
    },
    {
        "name": "lookup_spec_profile",
        "description": (
            "Looks up the specification range (min, max, unit) "
            "for a field of a given report type."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {"type": "string"},
                "field": {"type": "string"},
            },
            "required": ["report_type", "field"],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluates an arithmetic expression (+ - * / ** parentheses).",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "submit_extraction",
        "description": (
            "Records the final extraction result. "
            "Call exactly once, when finished."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": ["number", "string", "null"]},
                            "unit": {"type": ["string", "null"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["name", "value", "confidence"],
                    },
                }
            },
            "required": ["fields"],
        },
    },
]

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    return _client


def _build_user_prompt(report_type: str, transcripts: list[str]) -> str:
    pages = "\n\n".join(f"--- page {i} ---\n{text}" for i, text in enumerate(transcripts))
    return f"Report type: {report_type}\n\n{pages}"


def _execute_tool(db: Session, report_type: str, name: str, tool_input: dict[str, Any]) -> Any:
    try:
        if name == "convert_units":
            return {
                "result": tools.convert_units(
                    tool_input["value"], tool_input["from_unit"], tool_input["to_unit"]
                )
            }
        if name == "lookup_spec_profile":
            return {
                "result": tools.lookup_spec_profile(
                    db, tool_input.get("report_type", report_type), tool_input["field"]
                )
            }
        if name == "calculate":
            return {"result": tools.calculate(tool_input["expression"])}
        return {"error": f"unknown tool: {name}"}
    except Exception as exc:  # deterministic tools must never crash the agent loop
        return {"error": str(exc)}


def run_extraction_agent(
    db: Session,
    report_type: str,
    transcripts: list[str],
    client: anthropic.Anthropic | None = None,
) -> dict[str, Any] | None:
    """Runs the tool-calling agent loop; returns the raw `submit_extraction` payload
    (untrusted - caller must validate with Pydantic) or None if the agent never
    submitted within MAX_TOOL_ITERATIONS."""
    client = client or _get_client()
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": _build_user_prompt(report_type, transcripts)}
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=get_settings().anthropic_agent_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "submit_extraction":
                return block.input
            result = _execute_tool(db, report_type, block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
            )

        if not tool_results:
            logger.warning("extraction agent stopped without submitting (no tool calls)")
            return None

        messages.append({"role": "user", "content": tool_results})

    logger.warning(
        "extraction agent exhausted %d iterations without submitting", MAX_TOOL_ITERATIONS
    )
    return None
