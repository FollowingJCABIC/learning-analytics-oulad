\set ON_ERROR_STOP on

CREATE OR REPLACE VIEW analytics.portfolio_overview AS
SELECT
    (SELECT count(DISTINCT code_module) FROM core.module_presentations) AS modules,
    (SELECT count(*) FROM core.module_presentations) AS module_presentations,
    (SELECT count(DISTINCT id_student) FROM core.student_attempts) AS unique_students,
    (SELECT count(*) FROM core.student_attempts) AS student_attempts,
    (SELECT count(*) FROM core.assessments) AS assessments,
    (SELECT count(*) FROM core.vle_interactions) AS activity_records;

CREATE OR REPLACE VIEW analytics.weekly_engagement_summary AS
SELECT
    code_module,
    code_presentation,
    course_week,
    count(*) AS active_student_attempts,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY click_count) AS median_clicks,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY click_count) AS p75_clicks,
    avg(active_days)::numeric(10, 2) AS mean_active_days
FROM analytics.weekly_engagement
WHERE course_week BETWEEN 0 AND 12
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW analytics.assessment_summary AS
SELECT
    code_module,
    code_presentation,
    assessment_type,
    count(*) AS eligible_student_assessments,
    avg(missing_submission)::numeric(10, 4) AS missing_rate,
    avg(score)::numeric(10, 2) AS mean_recorded_score,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY submission_delay_days)
        AS median_submission_delay_days
FROM analytics.assessment_progress
GROUP BY 1, 2, 3;
