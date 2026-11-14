# FlameGuard-SI

**A research dashboard that summarizes, ranks, and interprets NASA microgravity combustion investigations to surface fire-safety insights for crewed spacecraft and surface habitats.**

Built for the 2026 NASA Space Apps Challenge: *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data*.

> **Status: repository scaffold.** The only working pieces are a health endpoint (`GET /api/health`) and a data-provenance checker. The dashboard, data ingest, ranking, and assistant have not been built. See [`FLAMEGUARD_MASTER_SPEC.md`](FLAMEGUARD_MASTER_SPEC.md) §5.1 for each endpoint's status.

## Why

Without buoyancy, flames behave very differently, so Earth-based fire intuition does not transfer to a spacecraft. NASA has decades of low-gravity combustion experiments, but the results are hard to find, compare, and interpret. FlameGuard-SI aims to make them usable for fire-safety work.

## How we treat data

Every value carries an evidence class:

- **Measured**: taken directly from a NASA experimental record, with source, checksum, and rights status.
- **Interpretation**: our analysis of measured data, linked to the records it uses.
- **Illustrative simulation**: our model output. It is labelled and never mixed into measured data, rankings, or the assistant's evidence.

NASA data is never fabricated or gap-filled. Generated text is attributed to FlameGuard-SI, not NASA. Full rules are in the [master spec](FLAMEGUARD_MASTER_SPEC.md) §2.

## Repository layout

```
backend/flameguard/   FastAPI service (health endpoint only so far)
frontend/             Static dashboard (not started)
contracts/            JSON Schemas and examples: the API contract between teams
data/                 manifest.json, curated/ and simulated/ (raw/ is git-ignored)
docs/                 Design notes and decision records
tests/                pytest suite
tools/                Data provenance checker and, later, ingest scripts
```

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest
python tools/check_data_provenance.py
uvicorn flameguard.api.app:app --reload   # http://127.0.0.1:8000/api/health
```

Copy `.env.example` to `.env` for local settings. Never commit `.env`.

## Team

Four parallel workstreams, each on its own branch. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and spec §4.

| Branch | Workstream |
|---|---|
| `feat/backend-science` | API, analysis, ranking, assistant |
| `feat/frontend-dashboard` | Dashboard UI |
| `feat/nasa-data-tars` | NASA data acquisition and provenance |
| `test/qa-demo` | QA, integration tests, demo |

## License

Not chosen yet (spec §8). All rights reserved until the team decides.
