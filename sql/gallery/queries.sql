\set ON_ERROR_STOP on
\pset pager off

-- 01. What is the verified row count and grain of each source table?
SELECT 'courses' AS source_table, count(*) AS rows, 'module-presentation' AS grain FROM raw.courses
UNION ALL SELECT 'assessments', count(*), 'assessment' FROM raw.assessments
UNION ALL SELECT 'vle', count(*), 'module-presentation-site' FROM raw.vle
UNION ALL SELECT 'student_info', count(*), 'student-module-presentation' FROM raw.student_info
UNION ALL SELECT 'student_registration', count(*), 'student-module-presentation'
    FROM raw.student_registration
UNION ALL SELECT 'student_assessment', count(*), 'student-assessment'
    FROM raw.student_assessment
UNION ALL SELECT 'student_vle', count(*), 'student-site-relative-day' FROM raw.student_vle
ORDER BY source_table;

-- 02. Why must student-attempt rows not be described as unique students?
SELECT
    count(*) AS student_module_attempts,
    count(DISTINCT id_student) AS unique_students,
    count(*) - count(DISTINCT id_student) AS additional_attempt_records
FROM core.student_attempts;

-- 03. How do final outcomes vary across module-presentations?
SELECT * FROM analytics.course_outcome_summary
ORDER BY withdrawal_rate DESC, code_module, code_presentation;

-- 04. Which course-attempt fields connect registration, engagement, and outcomes?
SELECT
    attempt.code_module,
    attempt.code_presentation,
    attempt.id_student,
    attempt.registration_day,
    attempt.unregistration_day,
    attempt.final_result,
    coalesce(sum(engagement.click_count), 0) AS total_clicks,
    count(engagement.course_week) AS active_weeks
FROM core.student_attempts AS attempt
LEFT JOIN analytics.weekly_engagement AS engagement
    USING (code_module, code_presentation, id_student)
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY total_clicks DESC
LIMIT 100;

-- 05. Which executable quality checks fail or profile known missingness?
SELECT severity, check_name, failing_rows, status, detail
FROM quality.latest_results
ORDER BY severity, check_name;

-- 06. What assessment progress is available before the course ends?
SELECT
    code_module,
    code_presentation,
    id_student,
    count(*) FILTER (WHERE missing_submission = 0) AS submitted_assessments,
    count(*) FILTER (WHERE missing_submission = 1) AS missing_assessments,
    round(avg(score), 2) AS mean_score,
    round(sum(coalesce(score, 0) * weight / 100.0), 2) AS weighted_progress
FROM analytics.assessment_progress
GROUP BY 1, 2, 3
ORDER BY code_module, code_presentation, id_student
LIMIT 100;

-- 07. What is the weekly engagement grain?
SELECT *
FROM analytics.weekly_engagement
WHERE course_week BETWEEN 0 AND 12
ORDER BY code_module, code_presentation, id_student, course_week
LIMIT 100;

-- 08. How did engagement change from the previous observed week?
SELECT
    code_module,
    code_presentation,
    id_student,
    course_week,
    click_count,
    lag(click_count) OVER (
        PARTITION BY code_module, code_presentation, id_student
        ORDER BY course_week
    ) AS previous_observed_week_clicks
FROM analytics.weekly_engagement
WHERE course_week BETWEEN 0 AND 12
ORDER BY 1, 2, 3, 4
LIMIT 100;

-- 09. What was rolling fourteen-day activity at each weekly snapshot?
SELECT
    code_module,
    code_presentation,
    id_student,
    course_week,
    sum(click_count) OVER (
        PARTITION BY code_module, code_presentation, id_student
        ORDER BY course_week
        ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
    ) AS rolling_14_day_clicks
FROM analytics.weekly_engagement
WHERE course_week BETWEEN 0 AND 12
ORDER BY 1, 2, 3, 4
LIMIT 100;

-- 10. Where did each attempt rank relative to its weekly cohort?
SELECT
    code_module,
    code_presentation,
    id_student,
    course_week,
    click_count,
    percent_rank() OVER (
        PARTITION BY code_module, code_presentation, course_week
        ORDER BY click_count
    ) AS cohort_activity_percentile
FROM analytics.weekly_engagement
WHERE course_week BETWEEN 0 AND 12
ORDER BY 1, 2, 4, 6 DESC
LIMIT 100;

-- 11. What was the longest inactivity gap between observed activity days?
WITH active_days AS (
    SELECT DISTINCT code_module, code_presentation, id_student, activity_day
    FROM core.vle_interactions
),
gaps AS (
    SELECT
        *,
        activity_day - lag(activity_day) OVER (
            PARTITION BY code_module, code_presentation, id_student
            ORDER BY activity_day
        ) AS inactivity_days
    FROM active_days
)
SELECT
    code_module,
    code_presentation,
    id_student,
    max(inactivity_days) AS longest_observed_gap_days
FROM gaps
GROUP BY 1, 2, 3
ORDER BY longest_observed_gap_days DESC NULLS LAST
LIMIT 100;

-- 12. How does activity align with known withdrawal timing?
SELECT
    floor(days_relative_to_unregistration / 7.0)::integer AS weeks_from_unregistration,
    count(DISTINCT (code_module, code_presentation, id_student)) AS withdrawing_attempts,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY click_count) AS median_clicks
FROM analytics.withdrawal_aligned_engagement
WHERE days_relative_to_unregistration BETWEEN -84 AND 28
GROUP BY 1
ORDER BY 1;

-- 13. How did cumulative weighted assessment progress evolve by due date?
SELECT
    code_module,
    code_presentation,
    id_student,
    due_day,
    sum(coalesce(score, 0) * weight / 100.0) OVER (
        PARTITION BY code_module, code_presentation, id_student
        ORDER BY due_day, id_assessment
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_weighted_progress
FROM analytics.assessment_progress
ORDER BY 1, 2, 3, 4
LIMIT 100;

-- 14. Which point-in-time fields and next-event labels enter the model export?
SELECT *
FROM features.model_snapshots
ORDER BY code_module, code_presentation, id_student, course_week
LIMIT 100;

-- 15. What execution plans were captured for the optimization case studies?
SELECT
    case_name,
    variant,
    captured_at,
    plan #>> '{0,Execution Time}' AS execution_time_ms,
    plan #>> '{0,Plan,Node Type}' AS top_plan_node
FROM analytics.performance_runs
ORDER BY case_name, variant;
