\set ON_ERROR_STOP on

CREATE OR REPLACE VIEW staging.courses AS
SELECT
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    module_presentation_length::integer AS presentation_length_days
FROM raw.courses;

CREATE OR REPLACE VIEW staging.assessments AS
SELECT
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    id_assessment::integer AS id_assessment,
    trim(assessment_type) AS assessment_type,
    NULLIF(date, '?')::integer AS due_day,
    weight::numeric(6, 2) AS weight
FROM raw.assessments;

CREATE OR REPLACE VIEW staging.vle_resources AS
SELECT
    id_site::integer AS id_site,
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    trim(activity_type) AS activity_type,
    NULLIF(week_from, '?')::integer AS week_from,
    NULLIF(week_to, '?')::integer AS week_to
FROM raw.vle;

CREATE OR REPLACE VIEW staging.student_info AS
SELECT
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    id_student::integer AS id_student,
    trim(gender) AS gender,
    trim(region) AS region,
    trim(highest_education) AS highest_education,
    NULLIF(imd_band, '?') AS imd_band,
    trim(age_band) AS age_band,
    num_of_prev_attempts::integer AS previous_attempts,
    studied_credits::integer AS studied_credits,
    trim(disability) AS disability,
    trim(final_result) AS final_result
FROM raw.student_info;

CREATE OR REPLACE VIEW staging.student_registration AS
SELECT
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    id_student::integer AS id_student,
    NULLIF(date_registration, '?')::integer AS registration_day,
    NULLIF(date_unregistration, '?')::integer AS unregistration_day
FROM raw.student_registration;

CREATE OR REPLACE VIEW staging.assessment_submissions AS
SELECT
    id_assessment::integer AS id_assessment,
    id_student::integer AS id_student,
    date_submitted::integer AS submitted_day,
    is_banked::integer::boolean AS is_banked,
    NULLIF(score, '?')::numeric(5, 2) AS score
FROM raw.student_assessment;

CREATE OR REPLACE VIEW staging.vle_interactions AS
SELECT
    trim(code_module) AS code_module,
    trim(code_presentation) AS code_presentation,
    id_student,
    id_site,
    date AS activity_day,
    sum_click AS click_count
FROM raw.student_vle;
