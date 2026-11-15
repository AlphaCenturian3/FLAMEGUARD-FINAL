# Deploying the FlameGuard-SI development preview

One Python service serves the dashboard at `/` and the API at `/api/*`, on one origin, behind the
host's HTTPS. There is no build step, no database and no secret.

**Status: development preview.** Every page shows a permanent "Development preview" notice.
Scientific validation is not finished. Compare, rankings, the assistant and simulations
answer HTTP 501. Only evidence registered in `data/manifest.json` and accepted by the loader is
served; nothing unapproved is registered. `?fixtures=1` shows labelled contract examples under the
banner **FIXTURE DATA. NOT NASA DATA.**, and the API never returns fixture data.

## Run it locally (any OS, Python 3.11+)

```bash
python -m venv .venv
.venv/bin/pip install -r deploy/requirements.lock      # Windows: .venv\Scripts\pip
PYTHONPATH=backend .venv/bin/python -m flameguard serve --fixtures --auto-port --open
```

(Or `pip install -e .` and then `python -m flameguard serve --fixtures --open`.) Open the
address it prints, for example `http://127.0.0.1:8000/`.

## Run the container

```bash
docker build -t flameguard-si .
docker run --rm -p 8000:8000 flameguard-si          # set -e PORT=... to change the port
```

- Listens on `0.0.0.0:$PORT` (default 8000), which is how cloud hosts route traffic.
- Health check: `GET /api/investigations`. It returns 200 only when the registered evidence
  loaded, and 503 when the loader fails closed. `GET /api/health` is liveness only: it says 200
  even when no evidence can be served. A build missing `tools/check_data_provenance.py` once
  passed `/api/health` while serving nothing. The image's `HEALTHCHECK` and `render.yaml`
  use `/api/investigations`.
- Runs as an unprivileged user. Dependencies are pinned in `deploy/requirements.lock`, and the
  base image is pinned to `python:3.12.10-slim`.

## Public staging on Render (recommended)

Render's free web service builds this Dockerfile, gives one HTTPS URL, health-checks
`/api/investigations` and restarts the service on failure. `render.yaml` describes it.

1. A repository owner signs in at render.com with GitHub and grants access to this repository.
2. Choose **New > Blueprint** and select the repository. Render reads `render.yaml`.
3. Deploy. Render prints the URL, such as `https://flameguard-si-preview.onrender.com`.
4. Check it: `/api/health` and `/api/investigations` return 200, every page shows the preview notice, and `/?fixtures=1`
   shows the fixture banner.

Free instances sleep after inactivity, so the first request can take about a minute.
Alternatives that run the same Dockerfile unchanged: Fly.io, Google Cloud Run, Railway.

## What must not change when deploying

- Do not add an AI key. No feature uses one yet.
- Do not register evidence for deployment's sake. Registration needs its own approvals.
- Do not remove the preview notice or the fixture banner.
- Keep `autoDeploy: false` until the branch being deployed has been reviewed.
