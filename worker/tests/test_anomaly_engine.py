from app.models import SpecProfile
from app.services.anomaly_engine import detect_anomalies


def _seed_spec(db, report_type, field, min_value, max_value, unit=None):
    db.add(
        SpecProfile(
            report_type=report_type,
            field=field,
            min_value=min_value,
            max_value=max_value,
            unit=unit,
        )
    )
    db.commit()


def test_value_within_range_is_not_flagged(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "process_log", "temperatura_c", 10, 20)

    flags = detect_anomalies(db, "process_log", {"temperatura_c": {"value": 15, "unit": None}})

    assert flags == []
    db.close()


def test_slightly_out_of_range_is_a_warning(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "process_log", "temperatura_c", 10, 20)

    # 21 is 1 above max, range width 10 -> relative deviation 0.1 (< 0.15)
    flags = detect_anomalies(db, "process_log", {"temperatura_c": {"value": 21, "unit": None}})

    assert len(flags) == 1
    assert flags[0].severity == "warning"
    assert flags[0].field == "temperatura_c"


def test_far_out_of_range_is_critical(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "process_log", "temperatura_c", 10, 20)

    # 25 is 5 above max, range width 10 -> relative deviation 0.5 (> 0.15)
    flags = detect_anomalies(db, "process_log", {"temperatura_c": {"value": 25, "unit": None}})

    assert len(flags) == 1
    assert flags[0].severity == "critical"


def test_below_min_is_flagged(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "certificate_of_analysis", "ph", 6.5, 7.5)

    flags = detect_anomalies(db, "certificate_of_analysis", {"ph": {"value": 5.8, "unit": None}})

    assert len(flags) == 1
    assert flags[0].severity == "critical"
    assert flags[0].expected_range == "[6.5, 7.5]"


def test_missing_spec_profile_is_skipped(db_session_factory) -> None:
    db = db_session_factory()

    flags = detect_anomalies(
        db, "certificate_of_analysis", {"unknown_field": {"value": 1, "unit": None}}
    )

    assert flags == []


def test_non_numeric_value_is_skipped(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "certificate_of_analysis", "lote", 0, 1)

    flags = detect_anomalies(
        db, "certificate_of_analysis", {"lote": {"value": "CB-2026-014", "unit": None}}
    )

    assert flags == []


def test_unit_mismatch_is_converted_before_comparing(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "certificate_of_analysis", "masa", 1, 5, unit="g")

    # 6000 mg == 6 g, which is above the 5 g max -> should be flagged
    flags = detect_anomalies(db, "certificate_of_analysis", {"masa": {"value": 6000, "unit": "mg"}})

    assert len(flags) == 1
    assert flags[0].field == "masa"


def test_incompatible_units_are_skipped_rather_than_guessed(db_session_factory) -> None:
    db = db_session_factory()
    _seed_spec(db, "certificate_of_analysis", "temp", 10, 20, unit="c")

    flags = detect_anomalies(db, "certificate_of_analysis", {"temp": {"value": 100, "unit": "g"}})

    assert flags == []
