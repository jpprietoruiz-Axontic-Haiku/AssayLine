"""100% synthetic demo data: spec ranges + seed reports with pre-computed
extractions, so the demo dataset never needs a live Anthropic API call
(deterministic, free, reproducible - see DECISIONS.md)."""

DEMO_SPEC_PROFILES: list[dict] = [
    {"report_type": "certificate_of_analysis", "field": "ph", "min": 6.5, "max": 7.5, "unit": None},
    {
        "report_type": "certificate_of_analysis",
        "field": "purity_pct",
        "min": 98.0,
        "max": 100.0,
        "unit": "%",
    },
    {
        "report_type": "certificate_of_analysis",
        "field": "moisture_pct",
        "min": 0.0,
        "max": 2.0,
        "unit": "%",
    },
    {
        "report_type": "process_log",
        "field": "temperature_c",
        "min": 70.0,
        "max": 90.0,
        "unit": "c",
    },
    {"report_type": "process_log", "field": "pressure_bar", "min": 1.0, "max": 3.0, "unit": "bar"},
    {
        "report_type": "process_log",
        "field": "flow_rate_lpm",
        "min": 10.0,
        "max": 20.0,
        "unit": None,
    },
]

DEMO_REPORTS: list[dict] = [
    {
        "filename": "certificate_batch_CB-2026-014.pdf",
        "report_type": "certificate_of_analysis",
        "text": (
            "CERTIFICATE OF ANALYSIS\n"
            "Product: Phosphate Buffer PB-7\n"
            "Batch: CB-2026-014\n"
            "Analysis date: 2026-01-10\n"
            "Analyst: L. Fernandez\n\n"
            "Results:\n"
            "pH: 7.1\n"
            "Purity: 99.2 %\n"
            "Moisture: 0.8 %\n\n"
            "Conclusion: Product conforms to specification."
        ),
        "fields": [
            {"name": "ph", "value": 7.1, "unit": None, "confidence": 0.97},
            {"name": "purity_pct", "value": 99.2, "unit": "%", "confidence": 0.96},
            {"name": "moisture_pct", "value": 0.8, "unit": "%", "confidence": 0.94},
        ],
    },
    {
        "filename": "certificate_batch_CB-2026-021.pdf",
        "report_type": "certificate_of_analysis",
        "text": (
            "CERTIFICATE OF ANALYSIS\n"
            "Product: Ethanolic Solvent ET-100\n"
            "Batch: CB-2026-021\n"
            "Analysis date: 2026-01-15\n"
            "Analyst: R. Gomez\n\n"
            "Results:\n"
            "pH: 5.8\n"
            "Purity: 97.85 %\n"
            "Moisture: 1.2 %\n\n"
            "Conclusion: Review batch - values outside expected range."
        ),
        "fields": [
            {"name": "ph", "value": 5.8, "unit": None, "confidence": 0.95},
            {"name": "purity_pct", "value": 97.85, "unit": "%", "confidence": 0.9},
            {"name": "moisture_pct", "value": 1.2, "unit": "%", "confidence": 0.93},
        ],
    },
    {
        "filename": "process_log_L3_morning.pdf",
        "report_type": "process_log",
        "text": (
            "PROCESS LOG\n"
            "Line: Packaging L3\n"
            "Shift: Morning\n"
            "Date: 2026-01-12\n"
            "Operator: J. Torres\n\n"
            "Process parameters:\n"
            "Temperature: 82.4 C\n"
            "Pressure: 2.1 bar\n"
            "Flow rate: 15.2 L/min\n\n"
            "Notes: Normal operation, no incidents."
        ),
        "fields": [
            {"name": "temperature_c", "value": 82.4, "unit": "c", "confidence": 0.96},
            {"name": "pressure_bar", "value": 2.1, "unit": "bar", "confidence": 0.95},
            {"name": "flow_rate_lpm", "value": 15.2, "unit": None, "confidence": 0.94},
        ],
    },
    {
        "filename": "process_log_L1_night.pdf",
        "report_type": "process_log",
        "text": (
            "PROCESS LOG\n"
            "Line: Sterilization L1\n"
            "Shift: Night\n"
            "Date: 2026-01-18\n"
            "Operator: M. Duarte\n\n"
            "Process parameters:\n"
            "Temperature: 96.7 C\n"
            "Pressure: 3.25 bar\n"
            "Flow rate: 14.0 L/min\n\n"
            "Notes: High temperature alarm activated for 12 minutes."
        ),
        "fields": [
            {"name": "temperature_c", "value": 96.7, "unit": "c", "confidence": 0.97},
            {"name": "pressure_bar", "value": 3.25, "unit": "bar", "confidence": 0.9},
            {"name": "flow_rate_lpm", "value": 14.0, "unit": None, "confidence": 0.95},
        ],
    },
]
