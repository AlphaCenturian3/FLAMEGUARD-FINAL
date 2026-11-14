# FlameGuard-SI Master Specification

**Spec version:** 0.1.0 (initialization)
**Status:** Scaffold only. Nothing beyond `GET /api/health` and the data-provenance checker exists yet.
**Rule:** This file is the single source of truth. If code, a README, or a PR description disagrees with it, this file wins until someone changes it through a reviewed PR.

---

## 1. Mission

FlameGuard-SI is a web dashboard for the NASA Space Apps 2026 challenge *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data*. It **summarizes, ranks, and interprets** NASA microgravity combustion investigations so that researchers and engineers can find fire-safety insights for crewed environments: spacecraft, stations, lunar and Martian bases, and pressurized rovers.

The audience is professors, students, aerospace researchers, and aerospace engineers. Fire safety is the mission. Every tool in the dashboard has to support an insight we can defend.

### Out of scope (decided)

- No alarm, stability score, extinction prediction, or automatic shutdown logic.
- No precursor, warning-time, or false-alarm claims unless measured data supports them.
- No decorative machine learning, meaning models that add nothing the evidence supports.

## 2. Scientific integrity rules (non-negotiable)

These rules come from the team's existing project requirements. A PR that breaks one of them is not merged.

### 2.1 Evidence classes

Every scientific value shown, stored, or sent between components carries exactly one `evidence_class`:

| Class | Meaning | Required provenance |
|---|---|---|
| `measured` | A value taken directly from a NASA experimental record. | Source title, URL or archive identifier, retrieval date, file SHA-256, rights status. |
| `interpretation` | A FlameGuard-SI analysis derived from measured data. | IDs of the `measured` records it uses, plus the method or code version. |
| `illustrative_simulation` | Output of a FlameGuard-SI model. It is never experimental data. | Model name and version, and the required label (§2.3). |

### 2.2 No fabrication

1. **NASA experimental data is never fabricated, estimated, interpolated into gaps, or "filled in."** A missing value stays missing and is shown as missing.
2. Placeholder or mock data used during development lives only in `tests/fixtures/`, is marked `"fixture": true`, and never ships in `data/curated/`.
3. No test result, benchmark, accuracy, or CI status is reported unless it was actually run. Report the command and its output.
4. Do not claim functionality that is not implemented. README status lines must match the code.

### 2.3 Simulations

- Every simulation output and view shows the label **"Fluid and thermal transport model. No combustion chemistry."**, or a stricter label if the model differs.
- Simulated values never feed the ranking, the assistant's evidence, or any `measured` field.
- Ranking and assistant modules must not import simulation modules. A test will enforce this once those modules exist.

### 2.4 Attribution and rights

- NASA documents are cited by title, page, URL, and exact quote. Quotes are checked against the source text.
- Generated text is attributed to FlameGuard-SI and never to NASA. Do not write "according to NASA" in generated output, because NASA's media guidelines prohibit it.
- Raw NASA files (images, video, PDFs, archives) are **not committed** until their provenance and rights are reviewed. `data/raw/` is git-ignored.
- Spatial frequency is reported in cycles/pixel unless a verified spatial calibration exists.
- Spatial and temporal Fourier analyses are kept separate.

### 2.5 Pre-event material

This repository starts with fresh history. Nothing from earlier private development repositories is copied here. Reusing earlier material requires (a) a ruling from the Space Apps organizers on pre-event work and (b) a content and license audit. Record both in `docs/decisions/`.

## 3. Architecture

```
┌────────────────────┐   HTTP/JSON (contracts/)   ┌──────────────────────────┐
│ frontend/          │ ─────────────────────────▶ │ backend/flameguard/api   │
│ static HTML/CSS/JS │ ◀───────────────────────── │ FastAPI                  │
└────────────────────┘                            └────────────┬─────────────┘
                                                               │ reads only curated,
                                                               │ provenance-checked data
                                                  ┌────────────▼─────────────┐
                                                  │ data/manifest.json       │
                                                  │ data/curated/            │
                                                  │ data/simulated/ (label)  │
                                                  └────────────▲─────────────┘
                                                               │ ingest + checksum
                                                  ┌────────────┴─────────────┐
                                                  │ data/raw/ (git-ignored)  │
                                                  │ NASA PSI / NTRS sources  │
                                                  └──────────────────────────┘
```

| Layer | Technology | Location |
|---|---|---|
| Backend API | Python 3.11 / 3.12, FastAPI, Uvicorn | `backend/flameguard/` |
| Frontend | Static HTML, CSS, and vanilla JS (no build step), served by the backend at `/` once it exists | `frontend/` |
| Data | JSON manifest plus curated files with SHA-256 | `data/` |
| Contracts | JSON Schema (draft 2020-12) | `contracts/` |
| Checks | ruff, pytest, `tools/check_data_provenance.py` | `tests/`, `tools/` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

Secrets such as AI API keys come only from environment variables (see `.env.example`). The app must work without a key, falling back to quoting source passages directly.

## 4. Team ownership

| Branch | Workstream | Owns (writes) | Reads |
|---|---|---|---|
| `feat/backend-science` | Backend API, analysis, ranking, assistant | `backend/`, `contracts/` (shared, see §5.4) | `data/` |
| `feat/frontend-dashboard` | Dashboard UI | `frontend/` | `contracts/` |
| `feat/nasa-data-tars` | NASA data acquisition, curation, provenance | `data/`, `tools/` ingest scripts | `contracts/schemas/data_manifest.schema.json` |
| `test/qa-demo` | QA, integration tests, demo script, submission checklist | `tests/`, `docs/DEMO.md` | everything |

**Names:** _team to fill in the GitHub handle for each row._ Current collaborators: `AlphaCenturian3`, `buihhlong-a11y`.
**Open question:** "TARS" in `feat/nasa-data-tars` is not defined anywhere yet. Define it here.

Changing a file outside your own area is allowed, but the PR must request review from that area's owner.

## 5. Integration contract (v0)

Full details are in [`contracts/README.md`](contracts/README.md). The schemas are in `contracts/schemas/`, and CI validates the examples in `contracts/examples/` against them.

### 5.1 Endpoints

| Method and path | Status | Owner | Response |
|---|---|---|---|
| `GET /api/health` | **implemented** | backend | `{"status":"ok","service":"flameguard-si","contract_version":"0.1.0"}` |
| `GET /api/investigations` | planned | backend | `{"items":[Investigation], "contract_version"}` |
| `GET /api/investigations/{id}` | planned | backend | `Investigation` |
| `GET /api/findings?investigation_id=` | planned | backend | `{"items":[Finding]}` |
| `GET /api/rankings?context=` | planned | backend | `{"items":[{investigation_id, score, rationale, inputs:[Finding.id]}]}`. Inputs must be `measured` or `interpretation` only. |
| `POST /api/assistant/ask` | planned | backend | `{"answer", "citations":[Source], "generated_by":"FlameGuard-SI"}` |
| `GET /api/simulations/{id}` | planned | backend | `SimulationResult` (carries `label`) |

Planned endpoints should return HTTP 501 with an `Error` body until they are implemented. The frontend must handle 501.

### 5.2 Shared objects

- `Source`: a citation (title, URL, page, quote, retrieval date).
- `Investigation`: a NASA investigation (id, name, platform, objectives, sources).
- `Finding`: one value or statement, with its `evidence_class` and provenance.
- `SimulationResult`: an `illustrative_simulation` payload with a required label.
- `DataManifest`: the registry of every data file in `data/`.
- `Error`: `{"error": {"code", "message"}}`.

### 5.3 Independent development

- Frontend: build against `contracts/examples/*.json` until the backend serves real data. Example files are fixtures. Never display them as NASA data in the demo.
- Backend: build against the schemas and use `tests/fixtures/` for test data.
- Data: register each file in `data/manifest.json`. The backend reads only manifest entries that pass `tools/check_data_provenance.py`.

### 5.4 Changing the contract

1. Open a PR that changes `contracts/` only and bumps `CONTRACT_VERSION` (in `backend/flameguard/__init__.py`) and the spec version here.
2. Backend and frontend owners both approve.
3. Breaking changes bump the minor version while we are below 1.0.

## 6. Checkpoints

All times are **proposed**. The team confirms them. Submission closes Sunday, November 15, 2026, at 11:59 PM local time.

| ID | Checkpoint | Exit criteria | Status |
|---|---|---|---|
| CP0 | Repository initialized | main, 4 branches, CI green on main | see completion report |
| CP1 | Contract v0 frozen | All owners approve `contracts/`; owner names filled in §4 | open |
| CP2 | First real data | ≥1 `measured` manifest entry passes provenance check; rights status recorded | open |
| CP3 | First integration | Frontend renders backend data from CP2 on `main`; CI green | open |
| CP4 | Demo freeze | `docs/DEMO.md` walkthrough passes on a clean clone; only fixes after this | open |
| CP5 | Submission | Submission form done; SI use described; every source cited; license decided | open |

## 7. Workflow

- `main` is always green. Merge only through a PR with CI passing and at least one review. Never merge incomplete or failing work.
- Feature branches merge into `main` through squash merges. Put the reviewed head SHA in the PR body.
- Freeze evaluation criteria in their own commit before producing results, and do not loosen frozen criteria afterwards. Write a new version instead.
- Never commit `.env`, API keys, or raw NASA files.

## 8. Open decisions

1. Organizer ruling on pre-event work (§2.5).
2. License for the submission: the Space Apps terms expect original content to be free or open source (Apache 2.0 is the default). No LICENSE file is added yet, so this is the team's call.
3. Definition of "TARS" (§4).
4. Owner names (§4).
5. Hosting and deployment target for the demo.
