from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.services.tools import convert_units, lookup_spec_profile

# How far outside the spec range (relative to the range width) turns a
# borderline "warning" into a "critical" anomaly. 15% is a pragmatic default
# for a demo-grade engine, not a regulatory threshold.
CRITICAL_RELATIVE_DEVIATION = 0.15


@dataclass(frozen=True)
class AnomalyFlag:
    field: str
    value: str
    expected_range: str
    severity: str


def detect_anomalies(
    db: Session, report_type: str, extracted_data: dict[str, dict[str, Any]]
) -> list[AnomalyFlag]:
    flags: list[AnomalyFlag] = []
    for field, payload in extracted_data.items():
        value = payload.get("value")
        if not isinstance(value, int | float):
            continue  # anomaly detection only applies to numeric measurements

        spec = lookup_spec_profile(db, report_type, field)
        if spec is None:
            continue  # no spec on file for this field: nothing to compare against

        comparable_value = _normalize_unit(value, payload.get("unit"), spec)
        if comparable_value is None:
            continue

        flag = _check_bounds(field, comparable_value, spec)
        if flag is not None:
            flags.append(flag)
    return flags


def _normalize_unit(value: float, unit: str | None, spec: dict[str, Any]) -> float | None:
    spec_unit = spec["unit"]
    if not unit or not spec_unit or unit.lower() == spec_unit.lower():
        return value
    try:
        return convert_units(value, unit, spec_unit)
    except ValueError:
        # incompatible units: we cannot honestly compare, so we skip rather
        # than silently mis-flag (or mis-clear) an anomaly.
        return None


def _check_bounds(field: str, value: float, spec: dict[str, Any]) -> AnomalyFlag | None:
    min_value, max_value, unit = spec["min"], spec["max"], spec["unit"]

    if min_value is not None and value < min_value:
        bound = min_value
    elif max_value is not None and value > max_value:
        bound = max_value
    else:
        return None

    width = (max_value - min_value) if (min_value is not None and max_value is not None) else None
    deviation = abs(value - bound)
    relative = deviation / width if width else deviation / max(abs(bound), 1e-9)
    severity = "critical" if relative > CRITICAL_RELATIVE_DEVIATION else "warning"

    range_label = f"[{min_value}, {max_value}]" + (f" {unit}" if unit else "")
    return AnomalyFlag(field=field, value=str(value), expected_range=range_label, severity=severity)
