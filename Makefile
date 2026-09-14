.PHONY: test lint run ingest-real frontend-test

test:
	pytest

lint:
	ruff check src tests scripts

ingest-real:
	python scripts/ingest_osm.py --place "Mitte, Berlin, Germany" --output data/generated

run:
	uvicorn urban_resilience_twin.api.app:app --app-dir src --reload --host 0.0.0.0 --port 8000

frontend-test:
	cd frontend && npm test -- --run
