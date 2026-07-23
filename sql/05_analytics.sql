\set ON_ERROR_STOP on

DROP MATERIALIZED VIEW IF EXISTS analytics.withdrawal_aligned_engagement;
DROP MATERIALIZED VIEW IF EXISTS analytics.assessment_progress;
DROP MATERIALIZED VIEW IF EXISTS analytics.weekly_engagement;

CREATE MATERIALIZED VIEW analytics.weekly_engagement AS
SELECT
    interaction.code_module,
    interaction.code_presentation,
    interaction.id_student,
    floor(interaction.activity_day / 7.0)::integer AS course_week,
    sum(interaction.click_count)::bigint AS click_count,
    count(DISTINCT interaction.activity_day)::integer AS active_days,
    count(DISTINCT interaction.id_site)::integer AS distinct_sites,
    max(interaction.activity_day)::integer AS latest_activity_day,
    count(*)::bigint AS source_rows
FROM core.vle_interactions AS interaction
GROUP BY 1, 2, 3, 4;

CREATE UNIQUE INDEX weekly_engagement_grain_idx
    ON analytics.weekly_engagement
    (code_module, code_presentation, id_student, course_week);

CREATE MATERIALIZED VIEW analytics.assessment_progress AS
SELECT
    attempt.code_module,
    attempt.code_presentation,
    attempt.id_student,
    assessment.id_assessment,
    assessment.assessment_type,
    assessment.due_day,
    assessment.weight,
    submission.submitted_day,
    submission.score,
    submission.is_banked,
    submission.submitted_day - assessment.due_day AS submission_delay_days,
    CASE WHEN submission.id_student IS NULL THEN 1 ELSE 0 END AS missing_submission,
    CASE
        WHEN submission.score < 40 THEN 1
        WHEN submission.id_student IS NULL THEN 1
        ELSE 0
    END AS adverse_assessment_event
FROM core.student_attempts AS attempt
JOIN core.assessments AS assessment
    USING (code_module, code_presentation)
LEFT JOIN core.assessment_submissions AS submission
    ON submission.id_assessment = assessment.id_assessment
   AND submission.id_student = attempt.id_student
WHERE assessment.assessment_type <> 'Exam'
  AND assessment.due_day IS NOT NULL;

CREATE UNIQUE INDEX assessment_progress_grain_idx
    ON analytics.assessment_progress (id_assessment, id_student);

CREATE INDEX assessment_progress_attempt_due_idx
    ON analytics.assessment_progress
    (code_module, code_presentation, id_student, due_day)
    INCLUDE (submitted_day, score, weight, missing_submission, adverse_assessment_event);

CREATE MATERIALIZED VIEW analytics.withdrawal_aligned_engagement AS
SELECT
    attempt.code_module,
    attempt.code_presentation,
    attempt.id_student,
    attempt.final_result,
    attempt.unregistration_day,
    engagement.course_week,
    engagement.course_week * 7 - attempt.unregistration_day AS days_relative_to_unregistration,
    engagement.click_count,
    engagement.active_days
FROM core.student_attempts AS attempt
JOIN analytics.weekly_engagement AS engagement
    USING (code_module, code_presentation, id_student)
WHERE attempt.final_result = 'Withdrawn'
  AND attempt.unregistration_day IS NOT NULL;

CREATE OR REPLACE VIEW analytics.course_outcome_summary AS
SELECT
    code_module,
    code_presentation,
    count(*) AS student_attempts,
    count(DISTINCT id_student) AS unique_students_within_presentation,
    count(*) FILTER (WHERE final_result = 'Distinction') AS distinctions,
    count(*) FILTER (WHERE final_result = 'Pass') AS passes,
    count(*) FILTER (WHERE final_result = 'Fail') AS fails,
    count(*) FILTER (WHERE final_result = 'Withdrawn') AS withdrawals,
    round(avg((final_result = 'Withdrawn')::integer)::numeric, 4) AS withdrawal_rate
FROM core.student_attempts
GROUP BY 1, 2;

CREATE OR REPLACE VIEW analytics.resource_type_usage AS
SELECT
    interaction.code_module,
    interaction.code_presentation,
    resource.activity_type,
    sum(interaction.click_count)::bigint AS clicks,
    count(DISTINCT interaction.id_student)::bigint AS active_students
FROM core.vle_interactions AS interaction
JOIN core.vle_resources AS resource
    USING (code_module, code_presentation, id_site)
GROUP BY 1, 2, 3;
