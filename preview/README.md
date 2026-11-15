# Development preview (not production)

A local, one-command preview of the FlameGuard-SI dashboard while CP1 is still in review. It **merges nothing and changes no branch**. It exports two git refs into `.preview/` (git-ignored) and serves them together:

| Part | Default ref | Exported paths |
|---|---|---|
| Backend and contract | `origin/contract/cp1-v0.2-proposal` (PR #1) | `backend/`, `contracts/`, `pyproject.toml`, `README.md` |
| Frontend | `origin/feat/frontend-dashboard` (PR #2) | `frontend/` only |

## Run

```bash
python preview/run.py              # then open http://127.0.0.1:8790/
python preview/run.py --smoke      # start, run the smoke checks, stop (exit code 1 on any failure)
```

Requirements: Git, Python 3.11+, and network access the first time (pip installs FastAPI and Uvicorn into `.preview/venv`). The browser checks also need Chrome or Chromium (set `CHROME` to override the path), and the judge-demo check needs Node 22+. A check that cannot run is reported as **SKIPPED (not verified)**, never as passed.

Options: `--backend-ref`, `--frontend-ref`, `--port` (default 8790), `--no-fetch`.

## What you will see

| URL | Data | Behaviour |
|---|---|---|
| `http://127.0.0.1:8790/` | live API | `GET /api/health` works; every other endpoint returns **HTTP 501 not implemented**, and the pages say so. No data, ranking or answer is shown. |
| `http://127.0.0.1:8790/?source=fixtures` | contract fixtures | Every page shows **"Fixture mode … This is not NASA data."** and every record is badged as a fixture. Rankings and the assistant still show 501. |

## Safety rules (enforced by `tests/test_preview_isolation.py`)

- `preview/server.py` only dispatches `/api/*` to the **unmodified production app** and serves static files. It adds no routes, scores, data or fallbacks. Nothing in `backend/` imports it. This is not B7: B7 (mounting `frontend/` in the production app) is Member 1's work after CP1.
- The AI key is forced blank, and the server binds to `127.0.0.1` only.
- No second ranking or comparability implementation exists here. The ranking page shows the backend's 501 response.

## Known limits

- The frontend at PR #2 still declares contract v0.1.0. Against the v0.2.0 contract, one of PR #2's own 46 browser tests fails, and only on the version string. The footer says "Contract v0.1.0" while the health badge says 0.2.0. Member 2's v0.2.0 alignment fixes this.
- Fixture mode loads only the examples PR #2 knows about. The v0.2.0 caution, excluded and missing examples are not shown yet.
- There is no real NASA data until CP2 (PR #4 plus the B1 loader), so no real ranking, comparison, interpretation or TARS answer exists.
