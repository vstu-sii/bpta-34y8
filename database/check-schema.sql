-- Run with psql -v ON_ERROR_STOP=1 against the initialized development DB.
-- No records survive this check.
BEGIN;
DO $$
DECLARE
    owner_id uuid := gen_random_uuid();
    doc_a uuid := gen_random_uuid();
    doc_b uuid := gen_random_uuid();
    chunk_id uuid := gen_random_uuid();
    job_id uuid := gen_random_uuid();
    card_id uuid := gen_random_uuid();
BEGIN
    INSERT INTO student(id, external_subject) VALUES (owner_id, 'schema-check-' || owner_id);
    INSERT INTO document(id, student_id, title, source_text)
        VALUES (doc_a, owner_id, 'A', 'Source A'), (doc_b, owner_id, 'B', 'Source B');
    INSERT INTO source_chunk(id, document_id, sequence_no, source_locator, start_offset, end_offset, content)
        VALUES (chunk_id, doc_a, 1, 'block-1', 0, 8, 'Source A');
    INSERT INTO generation_job(id, document_id, idempotency_key, status)
        VALUES (job_id, doc_a, 'job-1', 'partial');
    INSERT INTO card(id, document_id, source_chunk_id, question, reference_answer, source_quote)
        VALUES (gen_random_uuid(), doc_a, chunk_id, 'Q', 'A', 'Source A');
    BEGIN
        INSERT INTO card(id, document_id, source_chunk_id, question, reference_answer, source_quote)
            VALUES (gen_random_uuid(), doc_b, chunk_id, 'Q', 'A', 'Source A');
        RAISE EXCEPTION 'Cross-document source was incorrectly accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'PASS: cross-document card source rejected';
    END;
    BEGIN
        INSERT INTO generation_job(id, document_id, idempotency_key, status)
            VALUES (gen_random_uuid(), doc_a, 'invalid-status', 'unknown');
        RAISE EXCEPTION 'Unknown job status was incorrectly accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: unknown job status rejected';
    END;
    BEGIN
        INSERT INTO card(id, document_id, source_chunk_id, question, reference_answer, source_quote, card_type)
            VALUES (gen_random_uuid(), doc_a, chunk_id, 'Q', 'A', 'Source A', 'formula');
        RAISE EXCEPTION 'Formula without expression/variables was incorrectly accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: incomplete formula rejected';
    END;
    BEGIN
        INSERT INTO card(id, document_id, source_chunk_id, question, reference_answer, source_quote, formula)
            VALUES (gen_random_uuid(), doc_a, chunk_id, 'Q', 'A', 'Source A', 'I = U / R');
        RAISE EXCEPTION 'Formula on short_qa was incorrectly accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: formula on non-formula card rejected';
    END;
    BEGIN
        INSERT INTO card(id, document_id, source_chunk_id, question, reference_answer, source_quote, card_type, formula, variables)
            VALUES (gen_random_uuid(), doc_a, chunk_id, 'Q', 'A', 'Source A', 'formula', 'I = U / R', '{}');
        RAISE EXCEPTION 'Non-array variables were incorrectly accepted';
    EXCEPTION WHEN check_violation OR invalid_parameter_value THEN
        RAISE NOTICE 'PASS: non-array variables rejected';
    END;
    BEGIN
        INSERT INTO source_chunk(id, document_id, sequence_no, source_locator, start_offset, end_offset, content)
            VALUES (gen_random_uuid(), doc_a, 1, 'block-2', 8, 16, 'Source B');
        RAISE EXCEPTION 'Duplicate document chunk number was incorrectly accepted';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'PASS: duplicate document chunk number rejected';
    END;
    INSERT INTO card(id, document_id, source_chunk_id, generation_job_id, question, reference_answer,
                     source_quote, card_type, formula, variables)
        VALUES (card_id, doc_a, chunk_id, job_id, 'Q', 'A', 'Source A', 'formula', 'I = U / R', '["I", "U", "R"]');
    RAISE NOTICE 'PASS: valid formula and partial generation job accepted';
    INSERT INTO review(id, card_id, answer, result, assessed_by, model_result, model_confidence, requires_self_check)
        VALUES (gen_random_uuid(), card_id, 'Answer', 'partially_correct', 'student', 'partially_correct', 0.4, true);
    RAISE NOTICE 'PASS: API evaluation status and self-check metadata accepted';
    BEGIN
        INSERT INTO generation_job(id, document_id, idempotency_key) VALUES (gen_random_uuid(), doc_b, 'other-job');
        UPDATE card SET generation_job_id = (SELECT id FROM generation_job WHERE document_id = doc_b)
            WHERE id = card_id;
        RAISE EXCEPTION 'Cross-document job was incorrectly accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'PASS: cross-document generation job rejected';
    END;
    DELETE FROM student WHERE id = owner_id;
    IF EXISTS (SELECT 1 FROM card WHERE document_id IN (doc_a, doc_b)) THEN
        RAISE EXCEPTION 'Cascade deletion failed';
    END IF;
    RAISE NOTICE 'PASS: deleting owner removes dependent cards';
END $$;
ROLLBACK;
