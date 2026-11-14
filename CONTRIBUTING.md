# Contributing to FlameGuard-SI

Read [`FLAMEGUARD_MASTER_SPEC.md`](FLAMEGUARD_MASTER_SPEC.md) first, especially §2 (scientific integrity) and §5 (integration contract).

## Branches

- `main` is protected by convention. It must always pass CI. Nobody pushes to it directly.
- Each workstream has a long-lived branch: `feat/backend-science`, `feat/frontend-dashboard`, `feat/nasa-data-tars`, `test/qa-demo`.
- For each piece of work, branch off your workstream branch or `main` (e.g. `feat/backend-science-rankings`), then open a PR.
- Rebase on or merge `main` often, so integration problems show up early.

## Pull requests

1. Keep PRs small and focused on one area.
2. CI must pass: ruff lint, ruff format, pytest, and the provenance check.
3. You need at least one approving review. Contract changes need both the backend and frontend owners.
4. Fill in the PR template honestly. State what you ran and what it output. If you did not run something, say so.
5. Do not merge incomplete or failing work. Mark drafts as Draft.
6. Squash merge, and record the reviewed head SHA in the PR body.

## Data rules (short version)

- Never fabricate, estimate, or gap-fill NASA data.
- Register every data file in `data/manifest.json` with its `evidence_class`. Run `python tools/check_data_provenance.py`.
- Raw NASA files go in `data/raw/`, which is git-ignored. Do not commit them until rights are reviewed.
- Simulations carry the label "Fluid and thermal transport model. No combustion chemistry." and never feed rankings or the assistant.
- Mock data lives only in `tests/fixtures/` and is marked `"fixture": true`.

## Secrets

Use `.env` (copied from `.env.example`). Never commit keys. The app must run with the AI key left blank.

## Local checks

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest && python tools/check_data_provenance.py
```
