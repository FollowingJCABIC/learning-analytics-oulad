\set ON_ERROR_STOP on

SET work_mem = '512MB';

CREATE TABLE IF NOT EXISTS quality.run_results (
    run_at timestamptz NOT NULL DEFAULT now(),
    check_name text NOT NULL,
    severity text NOT NULL CHECK (severity IN ('error', 'warning', 'informational')),
    failing_rows bigint NOT NULL,
    status text NOT NULL CHECK (status IN ('pass', 'fail', 'profile')),
    detail text NOT NULL
);

TRUNCATE quality.run_results;

INSERT INTO quality.run_results (check_name, severity, failing_rows, status, detail)
VALUES
    ('source_courses_row_count', 'error',
        ABS((SELECT count(*) FROM raw.courses) - 22),
        CASE WHEN (SELECT count(*) FROM raw.courses) = 22 THEN 'pass' ELSE 'fail' END,
        'Official archive should contain 22 module-presentation rows.'),
    ('source_student_info_row_count', 'error',
        ABS((SELECT count(*) FROM raw.student_info) - 32593),
        CASE WHEN (SELECT count(*) FROM raw.student_info) = 32593 THEN 'pass' ELSE 'fail' END,
        'Calculated from the downloaded 2015 UCI archive.'),
    ('source_activity_row_count', 'error',
        ABS((SELECT count(*) FROM raw.student_vle) - 10655280),
        CASE WHEN (SELECT count(*) FROM raw.student_vle) = 10655280 THEN 'pass' ELSE 'fail' END,
        'Calculated from the downloaded 2015 UCI archive.');

WITH checks AS (
    SELECT 'duplicate_student_attempts' AS name, 'error' AS severity, count(*) AS failures,
        'Natural key is module, presentation, student.' AS detail
    FROM (
        SELECT code_module, code_presentation, id_student
        FROM staging.student_info
        GROUP BY 1, 2, 3 HAVING count(*) > 1
    ) AS duplicated
    UNION ALL
    SELECT 'duplicate_assessment_submissions', 'error', count(*),
        'Submission key is assessment and student.'
    FROM (
        SELECT id_assessment, id_student
        FROM staging.assessment_submissions
        GROUP BY 1, 2 HAVING count(*) > 1
    ) AS duplicated
    UNION ALL
    SELECT 'orphan_assessments', 'error', count(*),
        'Every assessment must map to a module-presentation.'
    FROM staging.assessments AS assessment
    LEFT JOIN staging.courses AS course USING (code_module, code_presentation)
    WHERE course.code_module IS NULL
    UNION ALL
    SELECT 'orphan_submissions', 'error', count(*),
        'Every submission must map to an assessment.'
    FROM staging.assessment_submissions AS submission
    LEFT JOIN staging.assessments AS assessment USING (id_assessment)
    WHERE assessment.id_assessment IS NULL
    UNION ALL
    SELECT 'registrations_without_attempts', 'error', count(*),
        'Registration rows require a matching student attempt.'
    FROM staging.student_registration AS registration
    LEFT JOIN staging.student_info AS attempt
        USING (code_module, code_presentation, id_student)
    WHERE attempt.id_student IS NULL
    UNION ALL
    SELECT 'activity_without_resources', 'error', count(*),
        'Interaction site must exist in the same module-presentation.'
    FROM staging.vle_interactions AS activity
    WHERE NOT EXISTS (
        SELECT 1
        FROM staging.vle_resources AS resource
        WHERE resource.code_module = activity.code_module
          AND resource.code_presentation = activity.code_presentation
          AND resource.id_site = activity.id_site
    )
    UNION ALL
    SELECT 'activity_without_attempts', 'warning', count(*),
        'Early or retained activity may exist outside the studentInfo attempt set.'
    FROM staging.vle_interactions AS activity
    WHERE NOT EXISTS (
        SELECT 1
        FROM staging.student_info AS attempt
        WHERE attempt.code_module = activity.code_module
          AND attempt.code_presentation = activity.code_presentation
          AND attempt.id_student = activity.id_student
    )
    UNION ALL
    SELECT 'invalid_assessment_weights', 'error', count(*),
        'Assessment weights must be between zero and 100.'
    FROM staging.assessments WHERE weight NOT BETWEEN 0 AND 100
    UNION ALL
    SELECT 'invalid_score_ranges', 'error', count(*),
        'Recorded scores must be between zero and 100.'
    FROM staging.assessment_submissions WHERE score NOT BETWEEN 0 AND 100
    UNION ALL
    SELECT 'invalid_final_results', 'error', count(*),
        'Accepted final results are Distinction, Pass, Fail, and Withdrawn.'
    FROM staging.student_info
    WHERE final_result NOT IN ('Distinction', 'Pass', 'Fail', 'Withdrawn')
    UNION ALL
    SELECT 'negative_click_counts', 'error', count(*),
        'Click count cannot be negative.'
    FROM staging.vle_interactions WHERE click_count < 0
    UNION ALL
    SELECT 'registration_after_unregistration', 'error', count(*),
        'Unregistration cannot precede registration.'
    FROM staging.student_registration
    WHERE unregistration_day < registration_day
    UNION ALL
    SELECT 'unexpected_module_codes', 'warning', count(*),
        'Archive is documented as seven anonymized modules AAA through GGG.'
    FROM staging.courses
    WHERE code_module NOT IN ('AAA', 'BBB', 'CCC', 'DDD', 'EEE', 'FFF', 'GGG')
    UNION ALL
    SELECT 'unexpected_presentation_codes', 'warning', count(*),
        'Presentations should be 2013B, 2013J, 2014B, or 2014J.'
    FROM staging.courses
    WHERE code_presentation !~ '^201[34][BJ]$'
    UNION ALL
    SELECT 'missing_imd_band', 'informational', count(*),
        'Profile known missing area deprivation bands; do not impute without documentation.'
    FROM staging.student_info WHERE imd_band IS NULL
    UNION ALL
    SELECT 'missing_assessment_due_dates', 'informational', count(*),
        'Exam dates are often absent and are excluded from next-assessment targets.'
    FROM staging.assessments WHERE due_day IS NULL
    UNION ALL
    SELECT 'activity_before_course_start', 'informational', count(*),
        'Negative activity days are legitimate pre-course interactions and excluded from model weeks.'
    FROM staging.vle_interactions WHERE activity_day < 0
)
INSERT INTO quality.run_results (check_name, severity, failing_rows, status, detail)
SELECT
    name,
    severity,
    failures,
    CASE
        WHEN severity = 'informational' THEN 'profile'
        WHEN failures = 0 THEN 'pass'
        ELSE 'fail'
    END,
    detail
FROM checks;

CREATE OR REPLACE VIEW quality.latest_results AS
SELECT * FROM quality.run_results;
