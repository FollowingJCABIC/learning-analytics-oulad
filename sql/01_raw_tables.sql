\set ON_ERROR_STOP on

DROP TABLE IF EXISTS raw.student_vle;
DROP TABLE IF EXISTS raw.student_assessment;
DROP TABLE IF EXISTS raw.student_registration;
DROP TABLE IF EXISTS raw.student_info;
DROP TABLE IF EXISTS raw.vle;
DROP TABLE IF EXISTS raw.assessments;
DROP TABLE IF EXISTS raw.courses;

CREATE TABLE raw.courses (
    code_module text,
    code_presentation text,
    module_presentation_length text
);

CREATE TABLE raw.assessments (
    code_module text,
    code_presentation text,
    id_assessment text,
    assessment_type text,
    date text,
    weight text
);

CREATE TABLE raw.vle (
    id_site text,
    code_module text,
    code_presentation text,
    activity_type text,
    week_from text,
    week_to text
);

CREATE TABLE raw.student_info (
    code_module text,
    code_presentation text,
    id_student text,
    gender text,
    region text,
    highest_education text,
    imd_band text,
    age_band text,
    num_of_prev_attempts text,
    studied_credits text,
    disability text,
    final_result text
);

CREATE TABLE raw.student_registration (
    code_module text,
    code_presentation text,
    id_student text,
    date_registration text,
    date_unregistration text
);

CREATE TABLE raw.student_assessment (
    id_assessment text,
    id_student text,
    date_submitted text,
    is_banked text,
    score text
);

CREATE UNLOGGED TABLE raw.student_vle (
    code_module text,
    code_presentation text,
    id_student integer,
    id_site integer,
    date integer,
    sum_click integer
);
