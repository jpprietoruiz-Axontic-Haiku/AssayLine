-- AssayLine initial schema
-- Milestone 1: core tables for reports, extractions, anomalies, reviews, spec_profiles.

CREATE TABLE IF NOT EXISTS reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        TEXT NOT NULL,
    report_type     TEXT,
    status          TEXT NOT NULL DEFAULT 'uploaded',
    storage_path    TEXT NOT NULL,
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS extractions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id           UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    schema_version       TEXT NOT NULL,
    data                JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence          JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_errors   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS anomalies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    field           TEXT NOT NULL,
    value           TEXT,
    expected_range  TEXT,
    severity        TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    reviewer_edits  JSONB NOT NULL DEFAULT '{}'::jsonb,
    approved_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS spec_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type     TEXT NOT NULL,
    field           TEXT NOT NULL,
    min_value       NUMERIC,
    max_value       NUMERIC,
    unit            TEXT,
    UNIQUE (report_type, field)
);

CREATE INDEX IF NOT EXISTS idx_extractions_report_id ON extractions(report_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_report_id ON anomalies(report_id);
CREATE INDEX IF NOT EXISTS idx_reviews_report_id ON reviews(report_id);
CREATE INDEX IF NOT EXISTS idx_spec_profiles_report_type ON spec_profiles(report_type);
