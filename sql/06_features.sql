\set ON_ERROR_STOP on

DROP MATERIALIZED VIEW IF EXISTS features.model_snapshots;

CREATE TABLE IF NOT EXISTS features.availability_registry (
    feature_name text PRIMARY KEY,
    available_at text NOT NULL,
    sql_source text NOT NULL,
    leakage_control text NOT NULL
);

TRUNCATE features.availability_registry;
INSERT INTO features.availability_registry VALUES
    ('clicks_7d', 'end of snapshot week', 'analytics.weekly_engagement',
        'course_week equals snapshot week'),
    ('clicks_prior_7d', 'end of prior week', 'analytics.weekly_engagement',
        'LAG is ordered within the student attempt'),
    ('clicks_14d', 'end of snapshot week', 'analytics.weekly_engagement',
        'window frame includes current and previous week only'),
    ('clicks_to_date', 'end of snapshot week', 'analytics.weekly_engagement',
        'cumulative window ends at current row'),
    ('mean_score_to_date', 'submission date at or before snapshot', 'analytics.assessment_progress',
        'submission submitted_day must be no later than snapshot_day'),
    ('missing_due_to_date', 'assessment due day at or before snapshot', 'analytics.assessment_progress',
        'only assessments already due are counted'),
    ('target_next_assessment_event', 'after next assessment due day', 'analytics.assessment_progress',
        'label only; explicitly excluded from model features'),
    ('target_withdrawal_28d', 'up to 28 days after snapshot', 'core.student_attempts',
        'label only; unregistration date is never a model feature');

CREATE MATERIALIZED VIEW features.model_snapshots AS
WITH attempt_weeks AS (
    SELECT
        attempt.code_module,
        attempt.code_presentation,
        attempt.id_student,
        week.course_week,
        week.course_week * 7 + 6 AS snapshot_day
    FROM core.student_attempts AS attempt
    JOIN core.module_presentations AS presentation
        USING (code_module, code_presentation)
    CROSS JOIN LATERAL generate_series(
        0,
        LEAST(12, floor(presentation.presentation_length_days / 7.0)::integer)
    ) AS week(course_week)
    WHERE attempt.registration_day <= week.course_week * 7 + 6
      AND (
          attempt.unregistration_day IS NULL
          OR attempt.unregistration_day > week.course_week * 7 + 6
      )
),
padded_weeks AS (
    SELECT
        weeks.*,
        coalesce(current_week.click_count, 0) AS clicks_7d,
        coalesce(current_week.active_days, 0) AS active_days_7d,
        coalesce(current_week.distinct_sites, 0) AS distinct_sites_7d,
        current_week.latest_activity_day
    FROM attempt_weeks AS weeks
    LEFT JOIN analytics.weekly_engagement AS current_week
        ON current_week.code_module = weeks.code_module
       AND current_week.code_presentation = weeks.code_presentation
       AND current_week.id_student = weeks.id_student
       AND current_week.course_week = weeks.course_week
),
engagement AS (
    SELECT
        padded.*,
        lag(clicks_7d, 1, 0::bigint) OVER attempt_time AS clicks_prior_7d,
        sum(clicks_7d) OVER (
            PARTITION BY code_module, code_presentation, id_student
            ORDER BY course_week
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
        ) AS clicks_14d,
        sum(clicks_7d) OVER (
            PARTITION BY code_module, code_presentation, id_student
            ORDER BY course_week
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS clicks_to_date,
        sum(active_days_7d) OVER (
            PARTITION BY code_module, code_presentation, id_student
            ORDER BY course_week
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
        ) AS active_days_14d,
        sum(distinct_sites_7d) OVER (
            PARTITION BY code_module, code_presentation, id_student
            ORDER BY course_week
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
        ) AS distinct_sites_14d,
        max(latest_activity_day) OVER attempt_time AS latest_feature_day
    FROM padded_weeks AS padded
    WINDOW attempt_time AS (
        PARTITION BY code_module, code_presentation, id_student
        ORDER BY course_week
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )
),
assessment_history AS (
    SELECT
        engagement.*,
        progress_history.submissions_to_date,
        progress_history.mean_score_to_date,
        progress_history.missing_due_to_date,
        progress_history.weighted_score_to_date
    FROM engagement
    LEFT JOIN LATERAL (
        SELECT
            count(progress.id_assessment)
                FILTER (WHERE progress.submitted_day <= engagement.snapshot_day)
                AS submissions_to_date,
            avg(progress.score)
                FILTER (WHERE progress.submitted_day <= engagement.snapshot_day)
                AS mean_score_to_date,
            count(progress.id_assessment)
                FILTER (
                    WHERE progress.due_day <= engagement.snapshot_day
                      AND progress.missing_submission = 1
                ) AS missing_due_to_date,
            coalesce(sum(progress.score * progress.weight / 100.0)
                FILTER (WHERE progress.submitted_day <= engagement.snapshot_day), 0)
                AS weighted_score_to_date
        FROM analytics.assessment_progress AS progress
        WHERE progress.code_module = engagement.code_module
          AND progress.code_presentation = engagement.code_presentation
          AND progress.id_student = engagement.id_student
    ) AS progress_history ON true
)
SELECT
    history.code_module,
    history.code_presentation,
    history.id_student,
    attempt.gender,
    attempt.age_band,
    attempt.disability,
    attempt.imd_band,
    history.course_week,
    history.snapshot_day,
    history.clicks_7d,
    history.clicks_prior_7d,
    history.clicks_14d,
    history.clicks_to_date,
    history.active_days_14d,
    history.distinct_sites_14d,
    history.snapshot_day - history.latest_feature_day AS days_since_activity,
    history.clicks_7d - history.clicks_prior_7d AS engagement_change,
    history.submissions_to_date,
    round(history.mean_score_to_date, 3) AS mean_score_to_date,
    history.missing_due_to_date,
    round(history.weighted_score_to_date, 3) AS weighted_score_to_date,
    history.latest_feature_day,
    next_assessment.id_assessment AS next_assessment_id,
    next_assessment.due_day AS next_assessment_due_day,
    next_assessment.adverse_assessment_event AS target_next_assessment_event,
    CASE
        WHEN attempt.unregistration_day > history.snapshot_day
         AND attempt.unregistration_day <= history.snapshot_day + 28
        THEN 1
        ELSE 0
    END AS target_withdrawal_28d
FROM assessment_history AS history
JOIN core.student_attempts AS attempt
    USING (code_module, code_presentation, id_student)
JOIN LATERAL (
    SELECT
        progress.id_assessment,
        progress.due_day,
        progress.adverse_assessment_event
    FROM analytics.assessment_progress AS progress
    WHERE progress.code_module = history.code_module
      AND progress.code_presentation = history.code_presentation
      AND progress.id_student = history.id_student
      AND progress.due_day > history.snapshot_day
    ORDER BY progress.due_day, progress.id_assessment
    LIMIT 1
) AS next_assessment ON true;

CREATE UNIQUE INDEX model_snapshots_grain_idx
    ON features.model_snapshots
    (code_module, code_presentation, id_student, course_week);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM features.model_snapshots
        WHERE latest_feature_day > snapshot_day
    ) THEN
        RAISE EXCEPTION 'Temporal leakage: feature date exceeds snapshot date';
    END IF;
END
$$;
