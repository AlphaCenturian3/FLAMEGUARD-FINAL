# CP1 workstream plan

**Status:** proposal. Nobody starts feature work until CP1 passes: owners are named in spec §4 and the contract v0.2.0 PR is approved and merged. Until then, only the "Start now" items below are allowed.

**Product priority, in order:**
1. NASA evidence explorer
2. Comparison
3. Transparent ranking
4. Traceable fire-safety interpretation and assistant
5. Illustrative simulation, which is optional, kept separate, and done last

Every item must keep the rules in spec §2.

**Acceptance rule for every item:** an item is done only when its check is merged on `main` with CI green, or recorded in `docs/verification/` with the date, the person and the result. A claim that cannot be checked is not done.

---

## 1. `feat/nasa-data-tars`: NASA data

**Owns:** `data/` (except `data/curated/interpretations/`), `tools/`, `tests/data/`.

**Start now (before CP1):**
- List candidate investigations and their public NASA sources (PSI, NTRS) in `docs/verification/data_candidates.md`, giving the URL, the access route and the rights notes for each.
- Download through a normal browser only. Do not script around logins, 403 responses or bot protection. If access is blocked, record that and ask a person.

**After CP1:**
- **D1.** `data/curated/investigations.json`: at least 3 investigations, each with at least one real NASA source.
- **D2.** `data/curated/findings/<id>.json`: measured findings, each with a `locator` and an exact `quote` where the source has text. At least 2 investigations must share one vocabulary `quantity`, so that comparison can be tested. A value the source does not report is entered as `not_reported`, never estimated.
- **D3.** Every file is registered in `data/manifest.json` with its SHA-256 and `rights_status`. Raw downloads stay in `data/raw/`, which git ignores.
- **D4.** `tests/data/`: every curated file validates against its schema. Every `investigation_id`, `manifest_id` and `datasets` reference resolves. Every numeric `quantity` and `unit` matches `contracts/vocabulary.json`.
- **D5.** Any new quantity or condition key goes through a contract PR first, never straight into the data.

| Check | How it is verified |
|---|---|
| D1 to D4 pass | `pytest tests/data` and `python tools/check_data_provenance.py` exit 0 in CI |
| Values match the sources | QA spot check (Q3) finds 0 mismatches |
| No raw files committed | `secrets-and-raw-data` CI job is green |

## 2. `feat/backend-science`: API and science

**Owns:** `backend/`, `config/`, `data/curated/interpretations/`, `tests/backend/`, `pyproject.toml`.

**Start now:** loaders and endpoint code tested against `tests/fixtures/` only, on a branch, unmerged until CP1.

- **B1. Loader.** Reads only manifest entries that pass the provenance check and validate against their schema. A bad file is skipped and reported, never loaded partially (fails closed).
- **B2. Explorer API.** `GET /api/investigations`, `/api/investigations/{id}` (404 returns `not_found`) and `/api/findings` with filters. An unknown filter value returns 400 `invalid_request`.
- **B3. Compare.** `GET /api/compare` uses measured findings only. It sets `comparable: false` with reasons when units, quantities or any reported condition differ, or when a value is missing. It never converts units, interpolates or fills gaps.
- **B4. Ranking.**
  - Commit `config/ranking_criteria_v1.json` (criteria, weights, scoring rules) **in its own commit before any ranking output exists**, and get it approved by QA and one other owner. After that it is never edited; changes go in a new `_v2` file.
  - Then implement `GET /api/rankings`.
- **B5. Interpretations.** Fire-safety interpretation findings in `data/curated/interpretations/`. Each one has `derived_from` pointing to existing measured or interpretation ids, and a `method` and `method_version`.
- **B6. Assistant.** `POST /api/assistant/ask`.
  - With a blank `FLAMEGUARD_AI_API_KEY`, it returns `fallback_quotes` or `no_evidence` from exact source quotes.
  - Generated text never says "according to NASA".
  - Test AI mode with a mocked client only. Run a live test only when a person approves it, and record the result.
- **B7. Static frontend.** Mount `frontend/` at `/`.
- **B8 (optional, last). Simulations.** `/api/simulations/{id}` with the required label. Ranking, compare and assistant modules must not import simulation code.

| Check | How it is verified |
|---|---|
| Every 2xx response validates against its schema | `tests/backend/` with real curated data |
| Compare never fills gaps | test: a `not_reported` row gives `value: null`, `comparable: false` |
| Ranking scores are weighted sums | test: `score == Σ weight × criterion score` within 1e-9 for every item |
| Ranking inputs resolve | test: every input `finding_id` exists and is measured or interpretation |
| Criteria frozen before results | the git log shows the criteria commit is older than the first ranking code or output |
| Assistant works without a key | test runs with the key blank: `mode` is `fallback_quotes` or `no_evidence` |
| Simulation isolation | test: the ranking, compare and assistant modules do not import simulation code |

## 3. `feat/frontend-dashboard`: dashboard

**Owns:** `frontend/`, `tests/frontend/`.

**Start now:** layout and components against `contracts/examples/`, in fixture mode (`?fixtures=1`) with the permanent "FIXTURE DATA. NOT NASA DATA." banner.

- **F1. Explorer.** Investigation list and detail with findings. Every value shows an evidence-class badge, and every missing value shows "Not reported" or "Not applicable", never 0 or a blank.
- **F2. Traceability.** Every finding shows its source title, link, locator and quote. Interpretations link to their `derived_from` findings.
- **F3. Compare.** A table or chart from `/api/compare`.
  - Non-comparable reasons are shown in full.
  - Missing points are not drawn, and lines never join across a gap.
  - Conditions are shown next to each value.
- **F4. Ranking.** Shows the criteria, the weights, each criterion score and its input findings, plus the excluded investigations and why.
- **F5. Assistant.** Shows "Generated by FlameGuard-SI" and the mode (AI or quotes only). Citations link to their findings.
- **F6. Errors.** 501, 404, 400 and network failures each show a message and never crash the page.
- **F7. Simulation (only if B8 exists).** A separate section that always shows the label. It never appears on the same chart or table as measured data.
- **F8. Usability.** Works at 360 px width with no horizontal scroll, works in light and dark themes, and every control can be reached with the keyboard.

| Check | How it is verified |
|---|---|
| F1 to F8 behave as described | QA browser tests (Q4) pass in CI |
| No fixture leak | test: without `?fixtures=1`, the page makes no request for `contracts/examples/` |
| No NASA misattribution | test: the string "according to NASA" appears nowhere in `frontend/` |

## 4. `test/qa-demo`: QA and demo

**Owns:** `tests/integration/`, `tests/e2e/`, `.github/`, `docs/DEMO.md`, `docs/SUBMISSION_CHECKLIST.md`, `docs/verification/`.

**Start now:** the integration harness and the integrity tests. Write each endpoint test as "if the response is 2xx it validates against the schema, otherwise it is the 501 `Error`". Tests then turn strict as endpoints go live, without anyone editing them.

- **Q1. Integration.** Every endpoint is called through TestClient on real curated data, and every response validates against its schema.
- **Q2. Integrity.**
  - No `illustrative_simulation` appears in findings, compare, rankings or assistant output.
  - The ranking, compare and assistant modules do not import simulation code.
  - "according to NASA" appears in no output and in no file under `frontend/`.
  - Nothing marked `fixture: true` appears in `data/curated/`.
- **Q3. Source spot check.** Draw a sample of max(5, 10%) of measured findings with a fixed recorded seed. A person checks each one against the source page and logs it in `docs/verification/source_spotcheck.md`. The bar is 0 mismatches. A mismatch blocks CP3 until it is fixed and the finding is checked again.
- **Q4. Browser tests.** End-to-end tests for F1 to F8 in a separate CI job, using the Playwright version QA chooses (added through a dependency PR).
- **Q5. Demo.** `docs/DEMO.md`: someone other than its author follows it from a clean clone and records the date and result.
- **Q6. Submission checklist.** `docs/SUBMISSION_CHECKLIST.md`: SI use described, every source cited, license chosen, organizer ruling recorded, no "according to NASA".

| Check | How it is verified |
|---|---|
| Q1, Q2, Q4 | CI green on `main` |
| Q3, Q5 | Signed entries in `docs/verification/` |

---

## Dependencies and integration order

```
CP1  contract v0.2.0 PR merged, owners named, TARS defined
 │
 ├── data D1–D4 ───────────────┐          (parallel, disjoint folders)
 ├── backend B1–B2 on fixtures │
 ├── frontend F1, F2, F6 on fixtures
 └── QA Q1, Q2 harness         │
                               ▼
CP2  first real data on main (D1–D4 green, Q3 spot check done)
 │
 ├── backend B1–B2 on real data ──► frontend F1/F2 wired to API
 ▼
CP3  explorer working end to end on main
 │
 ├── B3 compare ──► F3              (needs 2 investigations with a shared quantity)
 ├── B4 criteria freeze commit ──► B4 ranking ──► F4
 ├── B5 interpretations ──► B6 assistant ──► F5
 └── Q4 browser tests, Q5 demo dry run
 ▼
CP4  demo freeze: fixes only after this point
 │
 └── B8/F7 simulation, only if time allows and never before CP4 items are green
 ▼
CP5  submission (Q6 complete)
```

**Merge order on `main`:**
1. Contract PR.
2. Data, backend and QA PRs in any order, since they touch disjoint folders.
3. Frontend wiring after the backend endpoints it calls are merged.

Every PR merges only with CI green and a review from the owner of each area it touches.
