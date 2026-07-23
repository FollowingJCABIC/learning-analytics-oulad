\set ON_ERROR_STOP on

DROP TABLE IF EXISTS core.vle_interactions;
DROP TABLE IF EXISTS core.assessment_submissions;
DROP TABLE IF EXISTS core.student_attempts;
DROP TABLE IF EXISTS core.vle_resources;
DROP TABLE IF EXISTS core.assessments;
DROP TABLE IF EXISTS core.module_presentations;

CREATE TABLE core.module_presentations (
    code_module text NOT NULL,
    code_presentation text NOT NULL,
    presentation_length_days integer NOT NULL CHECK (presentation_length_days > 0),
    PRIMARY KEY (code_module, code_presentation)
);

INSERT INTO core.module_presentations
SELECT * FROM staging.courses;

CREATE TABLE core.assessments (
    id_assessment integer PRIMARY KEY,
    code_module text NOT NULL,
    code_presentation text NOT NULL,
    assessment_type text NOT NULL CHECK (assessment_type IN ('TMA', 'CMA', 'Exam')),
    due_day integer,
    weight numeric(6, 2) NOT NULL CHECK (weight BETWEEN 0 AND 100),
    FOREIGN KEY (code_module, code_presentation)
        REFERENCES core.module_presentations (code_module, code_presentation)
);

INSERT INTO core.assessments
SELECT
    id_assessment,
    code_module,
    code_presentation,
    assessment_type,
    due_day,
    weight
FROM staging.assessments;

CREATE TABLE core.vle_resources (
    id_site integer NOT NULL,
    code_module text NOT NULL,
    code_presentation text NOT NULL,
    activity_type text NOT NULL,
    week_from integer,
    week_to integer,
    PRIMARY KEY (id_site, code_module, code_presentation),
    FOREIGN KEY (code_module, code_presentation)
        REFERENCES core.module_presentations (code_module, code_presentation)
);

INSERT INTO core.vle_resources
SELECT * FROM staging.vle_resources;

CREATE TABLE core.student_attempts (
    code_module text NOT NULL,
    code_presentation text NOT NULL,
    id_student integer NOT NULL,
    gender text NOT NULL,
    region text NOT NULL,
    highest_education text NOT NULL,
    imd_band text,
    age_band text NOT NULL,
    previous_attempts integer NOT NULL CHECK (previous_attempts >= 0),
    studied_credits integer NOT NULL CHECK (studied_credits > 0),
    disability text NOT NULL CHECK (disability IN ('Y', 'N')),
    final_result text NOT NULL
        CHECK (final_result IN ('Distinction', 'Pass', 'Fail', 'Withdrawn')),
    registration_day integer,
    unregistration_day integer,
    PRIMARY KEY (code_module, code_presentation, id_student),
    FOREIGN KEY (code_module, code_presentation)
        REFERENCES core.module_presentations (code_module, code_presentation)
);

INSERT INTO core.student_attempts
SELECT
    info.code_module,
    info.code_presentation,
    info.id_student,
    info.gender,
    info.region,
    info.highest_education,
    info.imd_band,
    info.age_band,
    info.previous_attempts,
    info.studied_credits,
    info.disability,
    info.final_result,
    registration.registration_day,
    registration.unregistration_day
FROM staging.student_info AS info
LEFT JOIN staging.student_registration AS registration
    USING (code_module, code_presentation, id_student);

CREATE TABLE core.assessment_submissions (
    id_assessment integer NOT NULL REFERENCES core.assessments (id_assessment),
    id_student integer NOT NULL,
    submitted_day integer NOT NULL,
    is_banked boolean NOT NULL,
    score numeric(5, 2) CHECK (score BETWEEN 0 AND 100),
    PRIMARY KEY (id_assessment, id_student)
);

INSERT INTO core.assessment_submissions
SELECT * FROM staging.assessment_submissions;

CREATE UNLOGGED TABLE core.vle_interactions (
    code_module text NOT NULL,
    code_presentation text NOT NULL,
    id_student integer NOT NULL,
    id_site integer NOT NULL,
    activity_day integer NOT NULL,
    click_count integer NOT NULL CHECK (click_count >= 0)
);

INSERT INTO core.vle_interactions
SELECT * FROM staging.vle_interactions;

CREATE INDEX vle_interactions_attempt_day_idx
    ON core.vle_interactions
    (code_module, code_presentation, id_student, activity_day)
    INCLUDE (click_count, id_site);

CREATE INDEX vle_interactions_site_idx
    ON core.vle_interactions
    (code_module, code_presentation, id_site);

ANALYZE core.vle_interactions;

COMMENT ON TABLE core.student_attempts IS
    'One row per student-module-presentation attempt; students may appear in multiple attempts.';
COMMENT ON TABLE core.assessment_submissions IS
    'One row per submitted student-assessment pair; absent rows are not submissions.';
COMMENT ON TABLE core.vle_interactions IS
    'Source interaction grain: student, module-presentation, site, and relative day; duplicate keys can occur.';
