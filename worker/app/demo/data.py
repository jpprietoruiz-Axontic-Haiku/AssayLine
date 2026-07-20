"""100% synthetic demo data: spec ranges + seed reports with pre-computed
extractions, so the demo dataset never needs a live Anthropic API call
(deterministic, free, reproducible - see DECISIONS.md)."""

DEMO_SPEC_PROFILES: list[dict] = [
    {"report_type": "certificate_of_analysis", "field": "ph", "min": 6.5, "max": 7.5, "unit": None},
    {
        "report_type": "certificate_of_analysis",
        "field": "pureza_pct",
        "min": 98.0,
        "max": 100.0,
        "unit": "%",
    },
    {
        "report_type": "certificate_of_analysis",
        "field": "humedad_pct",
        "min": 0.0,
        "max": 2.0,
        "unit": "%",
    },
    {
        "report_type": "process_log",
        "field": "temperatura_c",
        "min": 70.0,
        "max": 90.0,
        "unit": "c",
    },
    {"report_type": "process_log", "field": "presion_bar", "min": 1.0, "max": 3.0, "unit": "bar"},
    {"report_type": "process_log", "field": "caudal_lpm", "min": 10.0, "max": 20.0, "unit": None},
]

DEMO_REPORTS: list[dict] = [
    {
        "filename": "certificado_lote_CB-2026-014.pdf",
        "report_type": "certificate_of_analysis",
        "text": (
            "CERTIFICADO DE ANALISIS\n"
            "Producto: Buffer Fosfato PB-7\n"
            "Lote: CB-2026-014\n"
            "Fecha de analisis: 2026-01-10\n"
            "Analista: L. Fernandez\n\n"
            "Resultados:\n"
            "pH: 7.1\n"
            "Pureza: 99.2 %\n"
            "Humedad: 0.8 %\n\n"
            "Conclusion: Producto conforme a especificacion."
        ),
        "fields": [
            {"name": "ph", "value": 7.1, "unit": None, "confidence": 0.97},
            {"name": "pureza_pct", "value": 99.2, "unit": "%", "confidence": 0.96},
            {"name": "humedad_pct", "value": 0.8, "unit": "%", "confidence": 0.94},
        ],
    },
    {
        "filename": "certificado_lote_CB-2026-021.pdf",
        "report_type": "certificate_of_analysis",
        "text": (
            "CERTIFICADO DE ANALISIS\n"
            "Producto: Solvente Etanolico ET-100\n"
            "Lote: CB-2026-021\n"
            "Fecha de analisis: 2026-01-15\n"
            "Analista: R. Gomez\n\n"
            "Resultados:\n"
            "pH: 5.8\n"
            "Pureza: 97.85 %\n"
            "Humedad: 1.2 %\n\n"
            "Conclusion: Revisar lote - valores fuera de rango esperado."
        ),
        "fields": [
            {"name": "ph", "value": 5.8, "unit": None, "confidence": 0.95},
            {"name": "pureza_pct", "value": 97.85, "unit": "%", "confidence": 0.9},
            {"name": "humedad_pct", "value": 1.2, "unit": "%", "confidence": 0.93},
        ],
    },
    {
        "filename": "log_proceso_L3_manana.pdf",
        "report_type": "process_log",
        "text": (
            "REGISTRO DE PROCESO\n"
            "Linea: Envasado L3\n"
            "Turno: Manana\n"
            "Fecha: 2026-01-12\n"
            "Operario: J. Torres\n\n"
            "Parametros de proceso:\n"
            "Temperatura: 82.4 C\n"
            "Presion: 2.1 bar\n"
            "Caudal: 15.2 L/min\n\n"
            "Observaciones: Operacion normal, sin incidencias."
        ),
        "fields": [
            {"name": "temperatura_c", "value": 82.4, "unit": "c", "confidence": 0.96},
            {"name": "presion_bar", "value": 2.1, "unit": "bar", "confidence": 0.95},
            {"name": "caudal_lpm", "value": 15.2, "unit": None, "confidence": 0.94},
        ],
    },
    {
        "filename": "log_proceso_L1_noche.pdf",
        "report_type": "process_log",
        "text": (
            "REGISTRO DE PROCESO\n"
            "Linea: Esterilizacion L1\n"
            "Turno: Noche\n"
            "Fecha: 2026-01-18\n"
            "Operario: M. Duarte\n\n"
            "Parametros de proceso:\n"
            "Temperatura: 96.7 C\n"
            "Presion: 3.25 bar\n"
            "Caudal: 14.0 L/min\n\n"
            "Observaciones: Alarma de temperatura alta activada durante 12 minutos."
        ),
        "fields": [
            {"name": "temperatura_c", "value": 96.7, "unit": "c", "confidence": 0.97},
            {"name": "presion_bar", "value": 3.25, "unit": "bar", "confidence": 0.9},
            {"name": "caudal_lpm", "value": 14.0, "unit": None, "confidence": 0.95},
        ],
    },
]
