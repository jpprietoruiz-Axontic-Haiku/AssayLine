import pytest

from app.models import SpecProfile
from app.services.tools import calculate, convert_units, lookup_spec_profile


def test_convert_units_same_unit_is_noop() -> None:
    assert convert_units(5.0, "g", "g") == 5.0


def test_convert_units_mass() -> None:
    assert convert_units(1000, "mg", "g") == pytest.approx(1.0)
    assert convert_units(2, "kg", "g") == pytest.approx(2000.0)


def test_convert_units_temperature() -> None:
    assert convert_units(0, "c", "f") == pytest.approx(32.0)
    assert convert_units(100, "c", "k") == pytest.approx(373.15)
    assert convert_units(32, "f", "c") == pytest.approx(0.0)


def test_convert_units_unknown_path_raises() -> None:
    with pytest.raises(ValueError):
        convert_units(1.0, "g", "celsius")


def test_calculate_basic_arithmetic() -> None:
    assert calculate("(2 + 3) * 4") == 20.0
    assert calculate("10 / 4") == 2.5
    assert calculate("-2 ** 2") == -4.0


@pytest.mark.parametrize(
    "expression",
    ["__import__('os').system('echo pwned')", "open('x')", "1; 2", "a + 1"],
)
def test_calculate_rejects_unsafe_expressions(expression: str) -> None:
    with pytest.raises(ValueError):
        calculate(expression)


def test_lookup_spec_profile_returns_none_when_missing(db_session_factory) -> None:
    db = db_session_factory()
    try:
        assert lookup_spec_profile(db, "certificate_of_analysis", "ph") is None
    finally:
        db.close()


def test_lookup_spec_profile_returns_range(db_session_factory) -> None:
    db = db_session_factory()
    try:
        db.add(
            SpecProfile(
                report_type="certificate_of_analysis",
                field="ph",
                min_value=6.5,
                max_value=7.5,
                unit=None,
            )
        )
        db.commit()

        result = lookup_spec_profile(db, "certificate_of_analysis", "ph")

        assert result == {"min": 6.5, "max": 7.5, "unit": None}
    finally:
        db.close()
