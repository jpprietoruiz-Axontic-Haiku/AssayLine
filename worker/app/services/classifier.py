import re

UNKNOWN_REPORT_TYPE = "unknown"

_KEYWORD_PATTERNS: dict[str, list[str]] = {
    "certificate_of_analysis": [
        r"certificado\s+de\s+an[aá]lisis",
        r"certificate\s+of\s+analysis",
        r"\bcoa\b",
    ],
    "process_log": [
        r"log\s+de\s+proceso",
        r"process\s+log",
        r"registro\s+de\s+proceso",
        r"par[aá]metros\s+de\s+proceso",
    ],
}


def classify_report_type(text: str) -> str:
    normalized = text.lower()
    scores = {
        report_type: sum(1 for pattern in patterns if re.search(pattern, normalized))
        for report_type, patterns in _KEYWORD_PATTERNS.items()
    }
    best_type, best_score = max(scores.items(), key=lambda item: item[1])
    return best_type if best_score > 0 else UNKNOWN_REPORT_TYPE
