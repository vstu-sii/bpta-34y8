-- PostgreSQL 16. Initial migration; a new empty database is required.
BEGIN;
CREATE TABLE student (
    id uuid PRIMARY KEY,
    external_subject text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE document (
    id uuid PRIMARY KEY,
    student_id uuid NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    title text NOT NULL CHECK (length(trim(title)) > 0),
    source_text text NOT NULL CHECK (length(trim(source_text)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE exam_question (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    question text NOT NULL CHECK (length(trim(question)) > 0)
);
CREATE TABLE source_chunk (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    sequence_no integer NOT NULL CHECK (sequence_no > 0),
    source_locator text NOT NULL CHECK (length(trim(source_locator)) > 0),
    page_number integer CHECK (page_number > 0),
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    content text NOT NULL CHECK (length(content) BETWEEN 1 AND 5000),
    UNIQUE (document_id, sequence_no),
    UNIQUE (document_id, source_locator),
    UNIQUE (document_id, start_offset, end_offset),
    UNIQUE (id, document_id)
);
CREATE TABLE generation_job (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    idempotency_key text NOT NULL,
    status text NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'partial', 'failed')),
    error_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, idempotency_key),
    UNIQUE (id, document_id)
);
CREATE TABLE card (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    source_chunk_id uuid NOT NULL,
    generation_job_id uuid,
    card_type text NOT NULL DEFAULT 'short_qa'
        CHECK (card_type IN ('short_qa', 'summary', 'formula')),
    formula text,
    variables jsonb NOT NULL DEFAULT '[]'::jsonb,
    question text NOT NULL CHECK (length(trim(question)) > 0),
    reference_answer text NOT NULL CHECK (length(trim(reference_answer)) > 0),
    source_quote text NOT NULL CHECK (length(trim(source_quote)) > 0),
    status text NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'accepted', 'deleted')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (jsonb_typeof(variables) = 'array'),
    CHECK (
        (card_type = 'formula' AND formula IS NOT NULL AND length(trim(formula)) > 0
            AND jsonb_array_length(variables) > 0)
        OR (card_type <> 'formula' AND formula IS NULL AND variables = '[]'::jsonb)
    ),
    FOREIGN KEY (source_chunk_id, document_id)
        REFERENCES source_chunk(id, document_id) ON DELETE CASCADE,
    FOREIGN KEY (generation_job_id, document_id)
        REFERENCES generation_job(id, document_id) ON DELETE CASCADE
);
CREATE TABLE review_schedule (
    card_id uuid PRIMARY KEY REFERENCES card(id) ON DELETE CASCADE,
    next_due_at timestamptz NOT NULL,
    interval_days integer NOT NULL DEFAULT 0 CHECK (interval_days >= 0),
    repetitions integer NOT NULL DEFAULT 0 CHECK (repetitions >= 0)
);
CREATE TABLE review (
    id uuid PRIMARY KEY,
    card_id uuid NOT NULL REFERENCES card(id) ON DELETE CASCADE,
    answer text NOT NULL,
    result text NOT NULL CHECK (result IN ('correct', 'partially_correct', 'incorrect', 'skipped')),
    assessed_by text NOT NULL CHECK (assessed_by IN ('model', 'student')),
    model_result text CHECK (model_result IN ('correct', 'partially_correct', 'incorrect')),
    model_confidence double precision CHECK (model_confidence BETWEEN 0 AND 1),
    requires_self_check boolean NOT NULL DEFAULT false,
    disputed boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE quality_event (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX document_owner_idx ON document(student_id);
CREATE INDEX job_queued_idx ON generation_job(created_at) WHERE status = 'queued';
CREATE INDEX card_document_idx ON card(document_id, status);
CREATE INDEX review_due_idx ON review_schedule(next_due_at);
CREATE INDEX review_card_idx ON review(card_id, created_at);
COMMIT;
