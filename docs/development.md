# Development

## Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests scripts
uvicorn urban_resilience_twin.api.app:app --app-dir src --reload
```

## Frontend

```bash
cd frontend
npm install
npm audit --audit-level=high
npm test
npm run build
npm run dev
```

## Real Berlin snapshot

```bash
pip install -e ".[ingestion]"
python scripts/ingest_osm.py --place "Mitte, Berlin, Germany" --output data/generated
docker compose -f docker-compose.yml -f docker-compose.real.yml up --build
```

## TDD

For meaningful behaviour, add or change the deterministic test first, observe failure, implement the smallest behaviour, rerun the relevant test, then refactor under protection. Toy network tests are intentionally retained even when real data ingestion exists because external data is unsuitable as the sole oracle for algorithmic correctness.
