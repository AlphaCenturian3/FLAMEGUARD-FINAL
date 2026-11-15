# FlameGuard-SI development preview: one container, API and dashboard on one origin.
# No secrets are baked in; the application calls no AI service.
FROM python:3.12.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONPATH=/app/backend \
    PORT=8000

WORKDIR /app
COPY deploy/requirements.lock deploy/requirements.lock
RUN pip install --no-cache-dir -r deploy/requirements.lock

# Only what the service reads: code, contracts (schemas, vocabulary, labelled fixtures),
# registered data (manifest-checked by sha256 at load) and the static dashboard.
COPY backend/ backend/
COPY contracts/ contracts/
COPY data/ data/
COPY frontend/ frontend/
# The B1 loader runs the one provenance implementation from tools/; without it nothing is served.
COPY tools/check_data_provenance.py tools/check_data_provenance.py

RUN useradd --uid 10001 --no-create-home app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/investigations', timeout=4)"

# The host binds 0.0.0.0 inside the container and reads the platform's $PORT.
# --fixtures only allows the labelled ?fixtures=1 page; the API never returns fixture data.
CMD ["sh", "-c", "exec python -m flameguard serve --host 0.0.0.0 --port \"${PORT}\" --fixtures --data-root /app --frontend-dir /app/frontend"]
