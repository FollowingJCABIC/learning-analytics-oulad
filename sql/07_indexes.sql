\set ON_ERROR_STOP on

CREATE INDEX IF NOT EXISTS vle_interactions_attempt_day_idx
    ON core.vle_interactions
    (code_module, code_presentation, id_student, activity_day)
    INCLUDE (click_count, id_site);

CREATE INDEX IF NOT EXISTS vle_interactions_site_idx
    ON core.vle_interactions
    (code_module, code_presentation, id_site);

CREATE INDEX IF NOT EXISTS student_attempts_result_idx
    ON core.student_attempts
    (code_module, code_presentation, final_result);

CREATE INDEX IF NOT EXISTS assessments_presentation_due_idx
    ON core.assessments
    (code_module, code_presentation, due_day);

CREATE INDEX IF NOT EXISTS submissions_student_day_idx
    ON core.assessment_submissions
    (id_student, submitted_day);

ANALYZE core.vle_interactions;
ANALYZE core.student_attempts;
ANALYZE analytics.weekly_engagement;
ANALYZE features.model_snapshots;
