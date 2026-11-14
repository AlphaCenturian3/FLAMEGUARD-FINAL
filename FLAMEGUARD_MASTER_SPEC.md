# FlameGuard-SI Master Specification

**Spec version:** 0.2.0 (CP1 final candidate: Command Center decisions of 2026-11-14 recorded; **member approvals pending**)
**Status:** Scaffold only. Nothing beyond `GET /api/health` and the data-provenance checker exists yet. Workstream tasks and acceptance criteria are in [`docs/CP1_WORKSTREAMS.md`](docs/CP1_WORKSTREAMS.md).
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
- Simulations are never `Finding` objects. They are served only as `SimulationResult` from `/api/simulations/*`. The `Finding`, `Comparison`, `Ranking` and `AssistantAnswer` schemas reject `illustrative_simulation` (contract v0.2.0).

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

**Proposed for CP1, not approved.** The active team is Members 1, 2, 3 and 5. There is no Member 4 (Command Center roster decision, option (b), 2026-11-14, recorded on PR #1); no account is identified as Member 4. A GitHub username counts only once that member confirms it in their CP1 approval. The evidence for each one is recorded on PR #1.

| Member | GitHub (status) | Branch | Responsibility | Owns (writes) |
|---|---|---|---|---|
| 1 | `AlphaCenturian3` (designated by coordination; confirm) | `feat/backend-science` | Backend, physics, APIs, scientific implementation and integration; all runtime ranking, comparison and TARS execution | `backend/` (except `backend/flameguard/evidence/`), `config/` (except ranking criteria), `pyproject.toml`, `.github/workflows/`, `tests/backend/`, `tests/integration/` |
| 2 | _not declared_ | `feat/frontend-dashboard` | Frontend, dashboard, visualizations and UX; TARS UI | `frontend/`, `tests/frontend/`, `tests/e2e/`, `tests/fixtures/frontend/` |
| 3 | `huyenthoai272008` (self-identified in PR #4; confirm) | `feat/nasa-data-tars` | NASA datasets, provenance, data-quality flags, TARS evidence integration and retrieval | `data/` (except `data/curated/interpretations/` outside `quality/`), `data/curated/interpretations/quality/`, `tools/`, `backend/flameguard/evidence/`, `tests/data/`, `docs/verification/data_candidates.md` |
| 5 | `16trtuoiloz-ducdo` (self-identified in PR #3; confirm) | `feat/research-safety-intelligence` (exists, PR #3) | Research interpretation, ranking criteria, Moon/Mars fire-safety recommendations, judge-demo narrative, independent scientific review | `research/` (non-runtime), `data/curated/interpretations/` (except `quality/`), `config/ranking_criteria_v*.json`, `docs/research/`, `docs/DEMO.md`, `docs/SUBMISSION_CHECKLIST.md`, `docs/verification/source_spotcheck.md`, `tests/research/`, `tests/fixtures/research/` |
| all | | | Contract and spec | `contracts/`, `FLAMEGUARD_MASTER_SPEC.md`, root `tests/test_*.py`, `docs/verification/` (shared log) |

`test/qa-demo` stays on the remote unchanged until the team decides what happens to it. It has no owner, and nobody commits to it in the meantime. Its QA and demo duties are spread across the four members in the plan (`docs/CP1_WORKSTREAMS.md`, item map).

### 4.1 TARS

**Definition (Command Center decision, 2026-11-14):** *TARS (Traceable Analysis and Research Support)* is a source-grounded research assistant that cites evidence, identifies uncertainty, and never presents generated interpretations as NASA conclusions.

| Part | Member | Location |
|---|---|---|
| Evidence retrieval | 3 | `backend/flameguard/evidence/` |
| Assistant backend: endpoint, AI call, quotes-only fallback, reply checks | 1 | `backend/flameguard/assistant/` |
| Assistant UI | 2 | `frontend/` |

### 4.2 Interface matrix

Each interface has one producer and one consumer. The producer may not change an interface without the consumer's approval.

| Interface | Producer | Consumer | Form | Rule |
|---|---|---|---|---|
| Curated measured data | 3 | 1 | `data/curated/investigations.json`, `data/curated/findings/<id>.json` + manifest | contract `investigation`/`finding`; S0–S4 |
| Interpretations and Moon/Mars recommendations | 5 | 1 | `data/curated/interpretations/<name>.json` + manifest | contract `finding` (interpretation); S3 |
| Data-quality flags (exclude / caution / not available) | 3 | 1, 5 | `data/curated/interpretations/quality/` + manifest (`interpretation`) | Member 5 reviews independently; the loader and ranking respect `exclude` (see the CP1 decisions in `docs/CP1_WORKSTREAMS.md`) |
| Ranking criteria | 5 | 1 | `config/ranking_criteria_v1.json`, frozen in its own commit before any ranking output | Members 1 and 3 approve; never edited after the freeze |
| Evidence retrieval | 3 | 1 | `retrieve(question: str, investigation_ids: list[str] \| None, limit: int) -> list[Finding]` | deterministic, no network or AI calls; returns only `measured`/`interpretation` findings that passed the loader, never a `SimulationResult` |
| HTTP API | 1 | 2 | the endpoints in §5.1 | the response schemas in `contracts/schemas/` |
| Comparability decision | 1 | 2 | `GET /api/compare` → `comparable`, `non_comparable_reasons` | **The frontend displays this decision and never computes its own** |
| Independent reference checks | 5 | tests only | `research/` (reference scoring and comparability, quote verifier) | imported only by `tests/research/`; never by `backend/` (a test enforces this once `research/` exists) |

### 4.3 One runtime implementation per rule

Ranking, comparability and evidence logic each run in exactly one place in the shipped app:

| Logic | Runtime owner and location | What other members contribute |
|---|---|---|
| Ranking (B4) | Member 1, `backend/flameguard/ranking/` | Member 5: criteria and scoring rules (R1); an independent reference implementation in `research/` that `tests/research/` compares against Member 1's output |
| Comparability, S5 (B3) | Member 1, `backend/flameguard/compare/` | Member 5: stricter-mode proposal (a v0.3 candidate, §8); Member 2: rendering only |
| Evidence validation | Contract schemas + Member 1's loader (B1) | Member 3: cross-file checks in `tests/data/` |
| Evidence retrieval (T1) | Member 3, `backend/flameguard/evidence/` | none |

`backend/flameguard/research/` is not an allowed package.

**Frontend display checks (Member 2).** `frontend/` may run fail-closed checks before it displays a result. For example, `traceSupport()` and `reviewRankings()` withhold a ranking item or interpretation whose inputs do not resolve, fail provenance, trace back to a simulation, or cite a `excluded` value, and say why. These checks are not a second implementation: they never compute, re-weight or re-order scores, never decide comparability, and never show anything the backend did not return. The display follows the backend's `rank` order and `comparable` decision.

### 4.4 Independent review

No member reviews their own scientific work. Each artifact needs approval from someone other than its author:

| Artifact | Author | Independent reviewer |
|---|---|---|
| Curated measured data (D1 to D3) | 3 | 5 (source spot check Q3) |
| Data-quality flags | 3 | 5 |
| Interpretations, Moon/Mars recommendations (R2, R3) | 5 | 3 (traceability: `derived_from`, quotes) **and** 1 (scientific soundness) |
| Ranking criteria freeze (R1) | 5 | 1 and 3, approved before any ranking output exists |
| Ranking, compare and TARS code (B3, B4, B6) | 1 | 5 (independent checks of S5, S6, S8 in `tests/research/`) |
| Evidence retrieval (T1) | 3 | 1 |
| Dashboard (F1 to F8) | 2 | 1 (API use) and 5 (scientific wording, labels) |
| Demo walkthrough (Q5) | 5 (narrative), 2 (UI path) | 3 runs it from a clean clone |
| Submission checklist (Q6) | 5 | 1 verifies each item |

Rules that keep the branches from conflicting:

- Change files outside your own area only through a PR that requests review from that area's owner.
- Dependency changes go in `pyproject.toml` through a small PR of their own (Member 1). Never bundle them with feature work.
- Only Member 1 edits `backend/flameguard/api/app.py`. Member 1 also mounts `frontend/` at `/`.
- Only Member 1 edits `.github/workflows/`. Anyone who needs a CI step asks Member 1, and a second member reviews the change.
- All text file I/O names `encoding="utf-8"`, because the team works on both Windows and Linux. `tests/test_portability.py` enforces it.

## 5. Integration contract (v0.2.0, proposed)

Full details are in [`contracts/README.md`](contracts/README.md). The schemas are in `contracts/schemas/`, the quantity vocabulary is in `contracts/vocabulary.json`, and CI validates the examples in `contracts/examples/` against the schemas.

### 5.1 Endpoints

All planned endpoints return HTTP 501 with an `Error` body today (`backend/flameguard/api/app.py`).

| Method and path | Status | Response schema |
|---|---|---|
| `GET /api/health` | **implemented** | `health` |
| `GET /api/investigations` | planned | `investigation_list` |
| `GET /api/investigations/{id}` | planned | `investigation`; `error` (`not_found`) with 404 |
| `GET /api/findings?investigation_id=&evidence_class=&quantity=` | planned | `finding_list` |
| `GET /api/compare?quantity=&investigation_ids=a,b` | planned | `comparison` (measured findings only) |
| `GET /api/rankings?context=<environment>` | planned | `ranking` |
| `POST /api/assistant/ask` | planned | request `assistant_request`, response `assistant_answer` |
| `GET /api/simulations/{id}` | planned, lowest priority | `simulation_result` |

Every query parameter is optional except `quantity` on `/api/compare` and `context` on `/api/rankings`. An unknown parameter value returns 400 with an `invalid_request` error. Lists are not paginated in v0.2.

### 5.2 Shared objects

- `Source`: a citation (title, URL, page, exact quote, retrieval date). Dates are ISO `YYYY-MM-DD`, checked by tests.
- `Investigation`: a NASA investigation, with `datasets` pointing to manifest ids.
- `Finding`: one `measured` value or one `interpretation`.
  - **A measured finding** needs a `locator` (where in the source) and a manifest id.
  - **`value_status`** is `reported`, `not_reported`, `not_applicable` or `excluded`. A missing value is `null` and can never be filled in.
    - `excluded` means the source reports a value, but FlameGuard-SI excludes it after a reviewed quality flag. Its value is `null`, it needs an attributed exclusion note that references the flag, and it keeps full measured provenance. **Exclusion is transitive:** an interpretation that depends on an excluded finding at any depth of `derived_from` may only explain the exclusion. It never supports a ranking, a comparison, a TARS conclusion or a Moon/Mars recommendation, and never carries the excluded number (rule S9).
  - **`uncertainty`** holds only uncertainty the source reports. FlameGuard-SI cautions and exclusions go in **`curation_notes`** (measured findings only, always `generated_by: "FlameGuard-SI"`). See `contracts/README.md` conventions 9 and 10. Flags map exactly: `caution` → caution note, `exclude` → `excluded` plus an exclusion note, `not_available` → `not_reported` with no note. Every note has a `flag_ref` and a `source` with a recorded quote. The schema checks only shapes: a recorded quote is not an authenticated one. Member 3 verifies flag references, coverage and NASA quotes against the registered source, and Member 5 checks this independently (rule S10).
  - **A numeric value** needs a `quantity` from `contracts/vocabulary.json`, exactly that unit, and must fall within that quantity's physical bounds. A string value is allowed only for a qualitative statement, with `quantity` and `unit` both `null`.
  - `quantity`, `value` and `unit` are always present. `null` is written out explicitly, never left out.
  - **Interpretation findings** must list `limitations` (at least 1) and may list `relevant_environments`. Measured findings may have neither, because environment relevance is an interpretation.
  - **`conditions`** is required on measured findings. Every key is present (`null` = not reported). Key names carry the units, and unknown keys are rejected.
- `Comparison`: rows for one quantity. Every row must carry `evidence_class: "measured"`. `comparable: true` needs at least 2 rows, all `reported`, and no reasons. `comparable: false` needs at least one reason. The backend never converts units, interpolates or fills gaps.
- `Ranking`: frozen criteria with weights. Each score is the weighted sum of its criterion scores, and each criterion score lists its input findings, which are measured or interpretation only. Investigations left out of the ranking appear in `excluded` with a reason.
- `AssistantAnswer`: `mode` is `ai`, `fallback_quotes` or `no_evidence`. Every mode except `no_evidence` needs at least one citation. `limitations` is required: at least one entry in `ai` and `fallback_quotes` modes, so TARS always states uncertainty. Citations are findings only.
- `SimulationResult`: `illustrative_simulation` with the required label. `verification_status` is `unverified` or `numerically_verified` only.
- `DataManifest`: the registry of every data file in `data/`.
- `Error`: `{"error": {"code", "message"}}`, where `code` is `not_implemented`, `not_found`, `invalid_request` or `unavailable`.

### 5.2a Data layout

| File | Contents | Owner | Manifest `evidence_class` |
|---|---|---|---|
| `data/curated/investigations.json` | JSON array of `Investigation` | Member 3 | `measured` |
| `data/curated/findings/<investigation_id>.json` | JSON array of measured `Finding` | Member 3 | `measured` |
| `data/curated/interpretations/<name>.json` | JSON array of interpretation `Finding` (including Moon/Mars recommendations) | Member 5 | `interpretation` |
| `data/curated/interpretations/quality/<name>.csv` | Data-quality flags on measured values (FlameGuard-SI curation judgments) | Member 3 | `interpretation` |
| `data/curated/<source>.csv` | As-printed transcription of a NASA table, the registered measured source for the findings files | Member 3 | `measured` |
| `data/simulated/<name>.json` | `SimulationResult` | Member 1 | `illustrative_simulation` |
| `config/ranking_criteria_v<N>.json` | Ranking criteria and weights, frozen in its own commit before any ranking output exists | Member 5 (Members 1 and 3 approve) | not data, so it is not in the manifest |

The backend loads only manifest entries that pass `tools/check_data_provenance.py` and whose contents validate against the schemas. If a file fails, the backend fails closed: it skips the file and reports it, and never loads it partially.

### 5.3 Independent development

- Frontend: build against `contracts/examples/*.json` until the backend serves real data. Example files are fixtures. Fixture mode must be switched on explicitly (`?fixtures=1`). While it is on, every page shows a permanent "FIXTURE DATA. NOT NASA DATA." banner. Never display fixtures as NASA data in the demo.
- Backend: build against the schemas and use `tests/fixtures/` for test data.
- Data: register each file in `data/manifest.json`. The backend reads only manifest entries that pass `tools/check_data_provenance.py`.

### 5.4 Changing the contract

1. Open a PR that changes `contracts/` only and bumps `CONTRACT_VERSION` (in `backend/flameguard/__init__.py`) and the spec version here.
2. Members 1 and 2 both approve. Members 3 and 5 also approve when a data, interpretation or ranking rule changes.
3. Breaking changes bump the minor version while we are below 1.0.

## 6. Checkpoints

All times are **proposed**. The team confirms them. Submission closes Sunday, November 15, 2026, at 11:59 PM local time.

| ID | Checkpoint | Exit criteria | Status |
|---|---|---|---|
| CP0 | Repository initialized | main, 4 branches, CI green on main | done: `3dc56ff`, CI run 43627519740 |
| CP1 | Contract frozen | Members 1, 2, 3 and 5 each confirm their GitHub username and explicitly approve the same PR head; TARS definition (§4.1) and the §4.2 interface matrix approved; P0 contract additions decided (accepted or deferred); PR merged with CI green | open |
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
3. ~~TARS definition~~: decided by Command Center ("Traceable Analysis and Research Support", §4.1). Other expansions, such as "Traceable Aerospace Research System" in PR #4, are not used.
4. Member GitHub usernames (§4); what happens to `test/qa-demo`.
5. Hosting and deployment target for the demo.
6. Which GitHub account belongs to which member. Five accounts have access or a pending invitation, for four active members.
7. Whether the AI assistant uses a live key at the demo, and who holds that key.
8. Branch protection: GitHub blocks it on a private free-plan repo, so `main` stays green by team convention only.
9. v0.3 candidates raised by Member 5 (PR #3), none needed for P0:
   - a claim-strength or "reported statement" evidence class;
   - a structured research-question ranking context;
   - a stricter comparability mode that blocks comparisons when a core condition is unreported for every row.
