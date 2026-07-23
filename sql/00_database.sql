\set ON_ERROR_STOP on

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS quality;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS features;

COMMENT ON SCHEMA raw IS 'Source-faithful OULAD text tables loaded from official CSV files.';
COMMENT ON SCHEMA staging IS 'Typed, nullable views that normalize OULAD question-mark missing values.';
COMMENT ON SCHEMA core IS 'Constrained relational model with documented analytical grains.';
COMMENT ON SCHEMA quality IS 'Executable source, relationship, and temporal data checks.';
COMMENT ON SCHEMA analytics IS 'Stable SQL metric definitions and reusable analytical marts.';
COMMENT ON SCHEMA features IS 'Point-in-time weekly model snapshots and availability metadata.';
