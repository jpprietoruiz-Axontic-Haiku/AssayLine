from app.services.classifier import UNKNOWN_REPORT_TYPE, classify_report_type


def test_classifies_certificate_of_analysis() -> None:
    text = "CERTIFICADO DE ANALISIS\nLote: ABC123\npH: 7.2"

    assert classify_report_type(text) == "certificate_of_analysis"


def test_classifies_process_log() -> None:
    text = "REGISTRO DE PROCESO\nParametros de proceso: temperatura 80C"

    assert classify_report_type(text) == "process_log"


def test_unknown_when_no_keywords_match() -> None:
    text = "Documento sin palabras clave reconocibles."

    assert classify_report_type(text) == UNKNOWN_REPORT_TYPE


def test_is_case_insensitive() -> None:
    text = "certificate of analysis for batch 42"

    assert classify_report_type(text) == "certificate_of_analysis"
