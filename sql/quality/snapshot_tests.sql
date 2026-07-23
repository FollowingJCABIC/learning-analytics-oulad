\set ON_ERROR_STOP on

DELETE FROM quality.run_results
WHERE check_name IN (
    'duplicate_model_snapshots',
    'invalid_snapshot_dates',
    'future_information_in_snapshots',
    'invalid_model_targets'
);

WITH checks AS (
    SELECT 'duplicate_model_snapshots' AS name, 'error' AS severity, count(*) AS failures,
        'Snapshot grain is module, presentation, student, and course week.' AS detail
    FROM (
        SELECT code_module, code_presentation, id_student, course_week
        FROM features.model_snapshots
        GROUP BY 1, 2, 3, 4 HAVING count(*) > 1
    ) AS duplicates
    UNION ALL
    SELECT 'invalid_snapshot_dates', 'error', count(*),
        'Model snapshots cover nonnegative course weeks zero through twelve.'
    FROM features.model_snapshots
    WHERE course_week NOT BETWEEN 0 AND 12 OR snapshot_day <> course_week * 7 + 6
    UNION ALL
    SELECT 'future_information_in_snapshots', 'error', count(*),
        'Latest source activity used by a feature must be at or before the snapshot.'
    FROM features.model_snapshots
    WHERE latest_feature_day > snapshot_day
    UNION ALL
    SELECT 'invalid_model_targets', 'error', count(*),
        'The next-assessment event is binary and must refer to a later due day.'
    FROM features.model_snapshots
    WHERE target_next_assessment_event NOT IN (0, 1)
       OR target_withdrawal_28d NOT IN (0, 1)
       OR next_assessment_due_day <= snapshot_day
)
INSERT INTO quality.run_results (check_name, severity, failing_rows, status, detail)
SELECT
    name,
    severity,
    failures,
    CASE WHEN failures = 0 THEN 'pass' ELSE 'fail' END,
    detail
FROM checks;
