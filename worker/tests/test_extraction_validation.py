from app.schemas.extraction import validate_fields


def test_valid_fields_pass_through() -> None:
    raw = [{"name": "ph", "value": 7.2, "unit": None, "confidence": 0.9}]

    valid, errors = validate_fields(raw)

    assert errors == []
    assert valid["ph"].value == 7.2
    assert valid["ph"].confidence == 0.9


def test_invalid_field_is_reported_without_dropping_valid_siblings() -> None:
    raw = [
        {"name": "ph", "value": 7.2, "unit": None, "confidence": 0.9},
        {"name": "pureza", "value": 99.5, "unit": "%", "confidence": 1.5},
    ]

    valid, errors = validate_fields(raw)

    assert "ph" in valid
    assert "pureza" not in valid
    assert len(errors) == 1
    assert errors[0]["field"] == "pureza"


def test_missing_required_key_is_reported() -> None:
    raw = [{"value": 7.2, "confidence": 0.9}]  # missing "name"

    valid, errors = validate_fields(raw)

    assert valid == {}
    assert errors[0]["field"] == "<unknown>"
