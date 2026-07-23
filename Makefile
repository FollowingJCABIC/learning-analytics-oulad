PYTHON ?= python3
PSQL ?= psql
DATABASE_URL ?= postgresql://learning_analytics:learning_analytics@localhost:5432/learning_analytics

.PHONY: setup data audit db-up db-down db-init ingest validate sql features analyze model report test lint format dashboard clean-db

setup:
	$(PYTHON) -m pip install -e ".[dev]"

data:
	$(PYTHON) -m learning_analytics download
	$(PYTHON) -m learning_analytics audit

audit:
	$(PYTHON) -m learning_analytics audit

db-up:
	docker compose up -d

db-down:
	docker compose down

db-init:
	createdb learning_analytics || true

ingest:
	DATABASE_URL="$(DATABASE_URL)" bash scripts/load_raw.sh

validate:
	DATABASE_URL="$(DATABASE_URL)" bash scripts/run_quality.sh

sql:
	DATABASE_URL="$(DATABASE_URL)" bash scripts/run_pipeline.sh

features:
	$(PSQL) "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f sql/06_features.sql
	$(PSQL) "$(DATABASE_URL)" -c "\copy features.model_snapshots to 'data/processed/model_snapshots.csv' csv header"

analyze:
	$(PYTHON) -m learning_analytics analyze

model:
	$(PYTHON) -m learning_analytics model

report:
	$(PYTHON) -m learning_analytics report

dashboard:
	$(PYTHON) -m learning_analytics dashboard

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests

clean-db:
	dropdb --if-exists learning_analytics
