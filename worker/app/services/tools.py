import ast
import operator
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.models import SpecProfile

# Multiplicative unit conversions, grouped by dimension, expressed relative to
# an arbitrary base unit per dimension. Temperature is handled separately
# because C/F/K conversions are affine, not multiplicative.
_LINEAR_UNIT_GROUPS: dict[str, dict[str, float]] = {
    "mass": {"mg": 0.001, "g": 1.0, "kg": 1000.0},
    "volume": {"ml": 1.0, "l": 1000.0},
    "concentration": {"mg/l": 1.0, "ppm": 1.0, "g/l": 1000.0, "%": 10000.0},
    "pressure": {"kpa": 1.0, "bar": 100.0, "psi": 6.894757},
}
_TEMPERATURE_UNITS = {"c", "f", "k"}


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    from_u = from_unit.strip().lower()
    to_u = to_unit.strip().lower()
    if from_u == to_u:
        return value
    if from_u in _TEMPERATURE_UNITS and to_u in _TEMPERATURE_UNITS:
        return _convert_temperature(value, from_u, to_u)
    for units in _LINEAR_UNIT_GROUPS.values():
        if from_u in units and to_u in units:
            base_value = value * units[from_u]
            return base_value / units[to_u]
    raise ValueError(f"no conversion path from {from_unit!r} to {to_unit!r}")


def _convert_temperature(value: float, from_u: str, to_u: str) -> float:
    if from_u == "f":
        celsius = (value - 32) * 5 / 9
    elif from_u == "k":
        celsius = value - 273.15
    else:
        celsius = value

    if to_u == "f":
        return celsius * 9 / 5 + 32
    if to_u == "k":
        return celsius + 273.15
    return celsius


def lookup_spec_profile(db: Session, report_type: str, field: str) -> dict[str, Any] | None:
    profile = (
        db.query(SpecProfile)
        .filter(SpecProfile.report_type == report_type, SpecProfile.field == field)
        .first()
    )
    if profile is None:
        return None
    return {
        "min": float(profile.min_value) if profile.min_value is not None else None,
        "max": float(profile.max_value) if profile.max_value is not None else None,
        "unit": profile.unit,
    }


_ALLOWED_BINOPS: dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS: dict[type, Callable[[float], float]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression: str) -> float:
    """Safely evaluate a numeric expression (+ - * / ** parentheses only)."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid expression: {expression!r}") from exc
    return _eval_node(tree.body)


def _eval_node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"unsupported expression element: {ast.dump(node)}")
