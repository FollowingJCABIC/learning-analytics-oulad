\set ON_ERROR_STOP on

CREATE TABLE IF NOT EXISTS analytics.performance_runs (
    captured_at timestamptz NOT NULL DEFAULT now(),
    case_name text NOT NULL,
    variant text NOT NULL,
    plan jsonb NOT NULL
);

TRUNCATE analytics.performance_runs;

CREATE OR REPLACE FUNCTION analytics.capture_plan(sql_text text)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
    captured jsonb;
BEGIN
    EXECUTE 'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' || sql_text INTO captured;
    RETURN captured;
END
$$;

INSERT INTO analytics.performance_runs (case_name, variant, plan)
VALUES (
    'weekly_engagement',
    'raw_fact_aggregation',
    analytics.capture_plan(
        'SELECT code_module, code_presentation, id_student,
            floor(activity_day / 7.0)::integer AS course_week,
            sum(click_count)
         FROM core.vle_interactions
         WHERE activity_day BETWEEN 0 AND 84
         GROUP BY 1, 2, 3, 4'
    )
);

INSERT INTO analytics.performance_runs (case_name, variant, plan)
VALUES (
    'weekly_engagement',
    'materialized_weekly_mart',
    analytics.capture_plan(
        'SELECT code_module, code_presentation, course_week, sum(click_count)
         FROM analytics.weekly_engagement
         WHERE course_week BETWEEN 0 AND 12
         GROUP BY 1, 2, 3'
    )
);

INSERT INTO analytics.performance_runs (case_name, variant, plan)
VALUES (
    'model_snapshots',
    'generated_range_join_aaa',
    analytics.capture_plan(
        'SELECT attempt.code_module, attempt.code_presentation, attempt.id_student,
            week.course_week, coalesce(sum(history.click_count), 0)
         FROM core.student_attempts AS attempt
         JOIN core.module_presentations AS presentation
           USING (code_module, code_presentation)
         CROSS JOIN LATERAL generate_series(
           0, LEAST(12, floor(presentation.presentation_length_days / 7.0)::integer)
         ) AS week(course_week)
         LEFT JOIN analytics.weekly_engagement AS history
           ON history.code_module = attempt.code_module
          AND history.code_presentation = attempt.code_presentation
          AND history.id_student = attempt.id_student
          AND history.course_week <= week.course_week
         WHERE attempt.code_module = ''AAA''
           AND attempt.registration_day <= week.course_week * 7 + 6
           AND (
             attempt.unregistration_day IS NULL
             OR attempt.unregistration_day > week.course_week * 7 + 6
           )
         GROUP BY 1, 2, 3, 4'
    )
);

INSERT INTO analytics.performance_runs (case_name, variant, plan)
VALUES (
    'model_snapshots',
    'materialized_snapshot_scan_aaa',
    analytics.capture_plan(
        'SELECT code_module, code_presentation, id_student, course_week, clicks_to_date
         FROM features.model_snapshots
         WHERE code_module = ''AAA'''
    )
);
