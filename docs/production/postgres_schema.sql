
-- ============================================================================
-- MAHARASHTRA SCHEME NAVIGATOR — POSTGRESQL 16+ CANONICAL SCHEMA DDL
-- Generated for production migration with JSONB, TIMESTAMPTZ, and cascade rules
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Migration History
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64) NOT NULL
);

-- 2. Interview Sessions
CREATE TABLE IF NOT EXISTS interview_sessions (
    thread_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_expiry ON interview_sessions(expires_at);

-- 3. Document Reviews and Events
CREATE TABLE IF NOT EXISTS document_reviews (
    review_id VARCHAR(255) PRIMARY KEY,
    status VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_pdf BOOLEAN NOT NULL DEFAULT FALSE,
    source_file_sha256 VARCHAR(64) NOT NULL,
    target_financial_year VARCHAR(32) NOT NULL,
    original_documents_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_documents_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    original_page_extractions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_page_extractions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    original_document_groups_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_document_groups_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    original_audit_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    current_audit_json JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_document_reviews_expiry ON document_reviews(expires_at);
CREATE INDEX IF NOT EXISTS idx_document_reviews_status ON document_reviews(status);
CREATE INDEX IF NOT EXISTS idx_document_reviews_sha ON document_reviews(source_file_sha256);

CREATE TABLE IF NOT EXISTS document_review_events (
    event_id BIGSERIAL PRIMARY KEY,
    review_id VARCHAR(255) NOT NULL REFERENCES document_reviews(review_id) ON DELETE CASCADE,
    action VARCHAR(64) NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255),
    field_name VARCHAR(128),
    original_value_json JSONB,
    previous_value_json JSONB,
    new_value_json JSONB,
    note TEXT NOT NULL DEFAULT '',
    page_numbers_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_events_review ON document_review_events(review_id, event_id);

-- 4. Ingestion Snapshots and Changes
CREATE TABLE IF NOT EXISTS ingested_snapshots (
    snapshot_id VARCHAR(255) PRIMARY KEY,
    source_url TEXT NOT NULL,
    final_url TEXT NOT NULL,
    source_kind VARCHAR(64) NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    byte_size BIGINT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    publication_date VARCHAR(64),
    official_reference VARCHAR(255),
    title TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    file_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_snapshots_url ON ingested_snapshots(source_url);
CREATE INDEX IF NOT EXISTS idx_snapshots_sha256 ON ingested_snapshots(sha256);

CREATE TABLE IF NOT EXISTS document_change_events (
    change_id VARCHAR(255) PRIMARY KEY,
    source_url TEXT NOT NULL,
    change_type VARCHAR(64) NOT NULL,
    previous_sha256 VARCHAR(64),
    new_sha256 VARCHAR(64) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    summary TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_changes_url ON document_change_events(source_url);

CREATE TABLE IF NOT EXISTS ingestion_review_queue (
    item_id VARCHAR(255) PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    source_kind VARCHAR(64) NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    review_status VARCHAR(64) NOT NULL,
    reviewer_id VARCHAR(255),
    review_notes TEXT,
    extracted_scheme_data_json JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_queue_status ON ingestion_review_queue(review_status);

-- 5. Citizen Profiles and Interview Runs
CREATE TABLE IF NOT EXISTS citizen_profiles (
    session_id VARCHAR(255) PRIMARY KEY,
    profile_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    local_government_type VARCHAR(64),
    municipal_corporation VARCHAR(128),
    municipal_council VARCHAR(128),
    nagar_panchayat VARCHAR(128),
    gram_panchayat VARCHAR(128),
    ward VARCHAR(64),
    locality VARCHAR(255),
    residence_years INTEGER,
    pin_code VARCHAR(16)
);

CREATE TABLE IF NOT EXISTS interview_runs (
    thread_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    scheme_id VARCHAR(255),
    status VARCHAR(64) NOT NULL,
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    mode VARCHAR(64) NOT NULL DEFAULT 'DISCOVERY',
    target_scheme_id VARCHAR(255),
    catalogue_version VARCHAR(32) NOT NULL DEFAULT '2026.11',
    rule_version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    language VARCHAR(16) NOT NULL DEFAULT 'en',
    completed_at TIMESTAMPTZ,
    results_json JSONB,
    target_jurisdiction_id VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS idx_interview_runs_session ON interview_runs(session_id);

CREATE TABLE IF NOT EXISTS citizen_progress (
    session_id VARCHAR(255) PRIMARY KEY,
    active_scheme_id VARCHAR(255),
    active_scheme_version VARCHAR(32),
    paused_schemes_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    dismissed_schemes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL
);
