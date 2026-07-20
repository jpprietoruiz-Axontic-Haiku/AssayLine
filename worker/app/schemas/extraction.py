from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ExtractedField(BaseModel):
    name: str
    value: float | str | None
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)


def validate_fields(
    raw_fields: list[dict[str, Any]],
) -> tuple[dict[str, ExtractedField], list[dict[str, Any]]]:
    """Validate each extracted field independently.

    A single malformed field (bad type, out-of-range confidence, ...) is
    reported and dropped without discarding the rest of the extraction -
    the LLM output is never trusted wholesale.
    """
    valid: dict[str, ExtractedField] = {}
    errors: list[dict[str, Any]] = []
    for raw in raw_fields:
        name = raw.get("name") if isinstance(raw, dict) else None
        try:
            field = ExtractedField.model_validate(raw)
        except ValidationError as exc:
            errors.append({"field": name or "<unknown>", "errors": exc.errors(include_url=False)})
            continue
        valid[field.name] = field
    return valid, errors
