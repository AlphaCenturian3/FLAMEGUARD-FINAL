# CP1 workstream plan

**Status:** proposal. Nobody starts feature work until CP1 passes: Members 1, 2, 3 and 5 declare their GitHub usernames in spec §4 and approve the contract v0.2.0 PR, and it is merged. Until then, only the "Start now" items below are allowed.

**Team:** Members 1, 2, 3 and 5. There is no Member 4 (Command Center roster decision, option (b), 2026-11-14, recorded on PR #1; same wording as spec §4). Ownership, TARS, the interface matrix, the one-implementation rule and the independent-review matrix are in spec §4.1 to §4.4.

**Product priority, in order:**
1. NASA evidence explorer
2. Comparison
3. Transparent ranking
4. Traceable fire-safety interpretation and TARS
5. Illustrative simulation, which is optional, kept separate, and done last

Every item must keep the rules in spec §2.

**Acceptance rule for every item:** an item is done only when its check is merged on `main` with CI green, or recorded in `docs/verification/` with the date, the person and the result. A claim that cannot be checked is not done. Scientific artifacts also need the independent reviewer from spec §4.4.

**Item map.** Item IDs are unchanged from the earlier plan, so references stay valid. B4's criteria freeze is now R1, and B5 is now R2. The former `test/qa-demo` items Q1 to Q6 are assigned below.

| Item | Member | | Item | Member |
|---|---|---|---|---|
| D1–D5, T1 | 3 | | F1–F8, Q4 | 2 |
| B1–B4, B6–B8, Q1 | 1 | | R1–R4, Q2, Q3, Q5 narrative, Q6 | 5 |
| Q5 clean-clone run | 3 | | | |

---

## Member 1: `feat/backend-science` (backend, physics, APIs, integration, TARS backend)

**Owns:** `backend/` (except `backend/flameguard/evidence/`), `config/` (except ranking criteria), `pyproject.toml`, `.github/workflows/`, `tests/backend/`, `tests/integration/`.

**Start now:** loaders and endpoint code tested against `tests/fixtures/` only, on a branch, unmerged until CP1.

- **B1. Loader.** Reads only manifest entries that pass the provenance check and validate against their schema. It enforces S1 to S4 at load time. A bad file is skipped and reported, never loaded partially (fails closed).
- **B2. Explorer API.** `GET /api/investigations`, `/api/investigations/{id}` (404 returns `not_found`) and `/api/findings` with filters. An unknown filter value returns 400 `invalid_request`.
- **B3. Compare.** `GET /api/compare` uses measured findings only. It follows rule S5 in `contracts/README.md` and never converts units, interpolates or fills gaps.
- **B4. Ranking.** Implement `GET /api/rankings` **only after** R1's frozen criteria file is merged. Read it, never edit it.
- **B6. TARS backend.** `POST /api/assistant/ask`, citing only findings returned by Member 3's `retrieve()` (spec §4.2).
  - With a blank `FLAMEGUARD_AI_API_KEY`, it returns `fallback_quotes` or `no_evidence` from exact source quotes.
  - Generated text never says "according to NASA", and never presents an interpretation as a NASA conclusion.
  - Test AI mode with a mocked client only. Run a live test only when a person approves it, and record the result.
- **B7. Static frontend.** Mount `frontend/` at `/`.
- **B8 (optional, last). Simulations.** `/api/simulations/{id}` with the required label. Ranking, compare and assistant modules must not import simulation code.
- **Q1. Integration.** Every endpoint is called through TestClient on real curated data, and every response validates against its schema. Write each test as "if the response is 2xx it validates against the schema, otherwise it is the 501 `Error`", so the tests turn strict as endpoints go live without anyone editing them.

| Check | How it is verified |
|---|---|
| Every 2xx response validates against its schema | `tests/backend/` and `tests/integration/` with real curated data |
| Compare never fills gaps | test: a `not_reported` row gives `value: null`, `comparable: false` |
| Ranking scores are weighted sums | test: `score == Σ weight × criterion score` within 1e-9 for every item |
| Ranking inputs resolve | test: every input `finding_id` exists and is measured or interpretation |
| Excluded values never used, transitively (S9) | test: no ranking input, no comparable row, and no TARS numeric statement uses a `excluded` finding |
| Assistant works without a key | test runs with the key blank: `mode` is `fallback_quotes` or `no_evidence` |
| Assistant cites only retrieved evidence | test: every citation's `finding_id` was returned by `retrieve()` for that request |
| Simulation isolation | test: the ranking, compare and assistant modules do not import simulation code |
| Independent review | Member 5's `tests/research/` checks of S5, S6 and S8 pass (spec §4.4) |

## Member 2: `feat/frontend-dashboard` (frontend, dashboard, visualizations, UX, TARS UI)

**Owns:** `frontend/`, `tests/frontend/`, `tests/e2e/`.

**Start now:** layout and components against `contracts/examples/`, in fixture mode (`?fixtures=1`) with the permanent "FIXTURE DATA. NOT NASA DATA." banner.

- **F1. Explorer.** Investigation list and detail with findings. Every value shows an evidence-class badge, and every missing value shows "Not reported" or "Not applicable", never 0 or a blank. A `excluded` value shows "Excluded by FlameGuard-SI" with the exclusion note and a link to its source location. `curation_notes` are labelled as FlameGuard-SI assessments, and `uncertainty` as "reported by the source".
- **F2. Traceability.** Every finding shows its source title, link, locator and quote. Interpretations link to their `derived_from` findings.
- **F3. Compare.** A table or chart from `/api/compare`.
  - The page shows the backend's `comparable` decision and `non_comparable_reasons` exactly as returned. It never computes its own comparability (spec §4.2, §4.3).
  - Non-comparable reasons are shown in full.
  - Missing points are not drawn, and lines never join across a gap.
  - Conditions are shown next to each value.
- **F4. Ranking.** Shows the criteria, the weights, each criterion score and its input findings, plus the excluded investigations and why.
- **F5. TARS UI.** Shows "Generated by FlameGuard-SI" and the mode (AI or quotes only). Citations link to their findings. Interpretations are visibly marked as FlameGuard-SI interpretations, not NASA conclusions.
- **F6. Errors.** 501, 404, 400 and network failures each show a message and never crash the page.
- **F7. Simulation (only if B8 exists).** A separate section that always shows the label. It never appears on the same chart or table as measured data.
- **F8. Usability.** Works at 360 px width with no horizontal scroll, works in light and dark themes, and every control can be reached with the keyboard.
- **Q4. Browser tests.** End-to-end tests for F1 to F8 in a separate CI job, using a Playwright version Member 2 picks. Member 1 adds it through a dependency PR, and Member 1 also adds the CI job.

| Check | How it is verified |
|---|---|
| F1 to F8 behave as described | Q4 browser tests pass in CI |
| No fixture leak | test: without `?fixtures=1`, the page makes no request for `contracts/examples/` |
| No NASA misattribution | test: the string "according to NASA" appears nowhere in `frontend/` |
| Independent review | Member 1 approves the API use, Member 5 approves the scientific wording and labels |

**PR #2 alignment (held until CP1; then verified against v0.2.0):**
- Set `CONTRACT_VERSION` to `0.2.0` and update the JSDoc mirrors in `api/types.js` to the v0.2.0 schemas.
- Read list responses as `finding_list` / `investigation_list` (`items`, `total`).
- Use `quantity`, `unit`, `value_status` and the fixed `conditions` keys. Show `not_reported` and `not_applicable` with their exact wording.
- Replace the browser-side comparability decision in `model/compare.js` with the `/api/compare` response (F3). The page may still hide a chart, but its reasons come from the backend.
- Leave `tests/fixtures/frontend/records.json` where it is. Under spec §4 that folder now belongs to Member 2.
- Every contract example renders in fixture mode, and Member 1 confirms that no field from v0.1.0 alone is still read.

## Member 3: `feat/nasa-data-tars` (NASA datasets, provenance, TARS evidence)

**Owns:** `data/` (except Member 5's interpretations), `data/curated/interpretations/quality/`, `tools/`, `backend/flameguard/evidence/`, `tests/data/`, `docs/verification/data_candidates.md`.

**PR #4 alignment** (FLEX Table IX, FLEX-001 to FLEX-010). Member 3 makes these changes on their own branch:
- Keep the as-printed CSV as the registered `measured` source. It is the transcription of record.
- Move the flags CSV to `data/curated/interpretations/quality/`. This is the one v0.2.0 manifest rule PR #4 fails today: interpretation paths must start with `data/curated/interpretations/`. Member 5 reviews the flags.
- When deriving findings, map each flag onto the contract (convention 9):
  - `exclude` (e.g. the FLEX-010 burning rate) → `value_status: "excluded"`, `value: null`, an exclusion note with `flag_ref` pointing to the flag id;
  - `caution` → a caution note in `curation_notes`, **never** in `uncertainty`;
  - `not_available` → `not_reported`, with no note for that flag;
  - every note carries `flag_ref` and the flag row's `source` passage with its quote. The derivation tool and `tests/data/` enforce rule S10: references resolve, every `exclude` and `caution` row is covered, and each referenced flag quote is verified against the registered source text.
- Add a tool in `tools/` that derives contract `Finding` JSON (`data/curated/findings/flex.json`) from the CSV, because the B1 loader reads `Finding` JSON, not CSV. It needs the decisions below on units, flags and vocabulary.
- After PR #1 merges, rebase. `data/manifest.json` and `tools/check_data_provenance.py` conflict textually with PR #1. For the tool, take PR #1's version (it already reads UTF-8, through `load_strict_json`). Set `manifest_version` to `0.2.0`.
- Change the "Member 4 / QA" review requests to the members in the item map.

**Start now (before CP1):**
- List candidate investigations and their public NASA sources (PSI, NTRS) in `docs/verification/data_candidates.md`, giving the URL, the access route and the rights notes for each.
- Download through a normal browser only. Do not script around logins, 403 responses or bot protection. If access is blocked, record that and ask a person.

**After CP1:**
- **D1.** `data/curated/investigations.json`: at least 3 investigations, each with at least one real NASA source.
- **D2.** `data/curated/findings/<id>.json`: measured findings, each with a `locator` and an exact `quote` where the source has text. At least 2 investigations must share one vocabulary `quantity`, so that comparison can be tested. A value the source does not report is entered as `not_reported`, never estimated.
- **D3.** Every file is registered in `data/manifest.json` with its SHA-256 and `rights_status`. Raw downloads stay in `data/raw/`, which git ignores.
- **D4.** `tests/data/` checks the rules that schemas cannot express (S1 to S4 in `contracts/README.md`):
  - every curated file validates against its schema;
  - every `investigation_id`, `manifest_id` and `datasets` reference resolves;
  - each findings file is named after the `investigation_id` of every finding in it;
  - each measured finding's `manifest_id` points to a `measured` manifest entry whose file contains that finding;
  - **S3, independently:** every `derived_from` in Member 5's interpretations resolves, with no cycles.
- **D5.** Any new quantity or condition key goes through a contract PR first, never straight into the data. The five vocabulary quantities stay provisional until D2 confirms them against NASA sources.
- **T1. TARS evidence retrieval.** `retrieve()` in `backend/flameguard/evidence/`, following the interface in spec §4.2: deterministic, no network or AI calls, measured and interpretation findings only, never simulations.
- **Q5 (clean-clone run).** Follow `docs/DEMO.md` from a fresh clone without its authors' help, and record the date and result.

| Check | How it is verified |
|---|---|
| D1 to D4 pass | `pytest tests/data` and `python tools/check_data_provenance.py` exit 0 in CI |
| Values match the sources | Member 5's spot check (Q3) finds 0 mismatches |
| No raw files committed | `secrets-and-raw-data` CI job is green |
| `retrieve()` returns no simulation and is deterministic | test in `tests/data/`: the same input gives the same output, and every returned `evidence_class` is measured or interpretation |
| Independent review | Member 1 reviews T1; Member 5 performs Q3 |

## Member 5: `feat/research-safety-intelligence` (PR #3; research, ranking criteria, Moon/Mars recommendations)

**Branch status:** exists (PR #3, draft). It is kept under its current name. `test/qa-demo` is left unchanged until the team decides what happens to it.

**Owns:** `research/` (non-runtime), `data/curated/interpretations/`, `config/ranking_criteria_v*.json`, `docs/research/`, `docs/DEMO.md`, `docs/SUBMISSION_CHECKLIST.md`, `docs/verification/source_spotcheck.md`, `tests/research/`, `tests/fixtures/research/`.

**PR #3 alignment.** Member 5 makes these changes on their own branch; nobody else edits it. All research content is kept.

| PR #3 path | Aligned destination | Why |
|---|---|---|
| `backend/flameguard/research/ranking.py`, `comparability.py` | `research/` as the **independent reference implementation** used by `tests/research/` | One runtime implementation per rule (spec §4.3). Member 1's B3/B4 is the runtime, and Member 5's code checks it independently. |
| `backend/flameguard/research/evidence.py`, `common.py`, `insights.py` | `research/` (test and reference use only) | Runtime validation is the contract schemas plus the B1 loader. |
| `backend/flameguard/research/verify_sources.py` | `research/verify_sources.py` | Member 5's tool for Q3 |
| `config/research_relevance_criteria_v1.proposed.json` | stays as the proposal. On approval it is committed alone as `config/ranking_criteria_v1.json` (R1) | Already planned in PR #3 itself |
| `docs/research/member5/evidence_reported.json` (11 records) | Member 3 curates them into `data/curated/findings/` with manifest entries. Until then they stay as research notes the app never loads | 0 of 11 validate as contract v0.2.0 `Finding` (no `evidence_class`/`provenance`; extra keys). See "P0 contract additions" below |
| `docs/research/member5/insight_cards.json` (6 cards) | Interpretation findings in `data/curated/interpretations/` (R2/R3), with `derived_from` pointing to curated measured ids | Cards become traceable through S3 |
| `docs/research/member5/investigations.json` | Member 3 merges it into `data/curated/investigations.json` (D1), keeping the candidate PSI ids until they are confirmed | Single investigations file |
| `tests/research/` (98 tests passing on the branch) | stays | Member 5's test folder (replaces the earlier `tests/integrity/` proposal) |
| References to "Member 4 / QA" | the assigned member in the item map | There is no Member 4 |

Member 1 answers for each record in `evidence_reported.json` how it maps. This applies the existing contract and changes nothing:
- `stated_objective` → `Investigation.objectives`;
- `experimental_result` → a measured qualitative finding (`quantity`/`value`/`unit` all `null`, `value_status: not_applicable`, exact quote and locator);
- `source_statement` and `hypothesis_under_test` → kept as source quotes for context only, never scored and never presented as findings.

**Start now:** a draft of the ranking criteria and a research outline in `docs/research/`, both unmerged until CP1. No ranking output is produced before R1 is frozen.

- **R1. Ranking criteria freeze** (formerly the first half of B4).
  - Write `config/ranking_criteria_v1.json` (criteria, weights, scoring rules), each criterion tied to fire safety in crewed environments.
  - Commit it **in its own commit before any ranking output exists**, with Members 1 and 3 approving it.
  - After that it is never edited. Changes go in a new `_v2` file.
- **R2. Interpretations** (formerly B5). Fire-safety interpretation findings in `data/curated/interpretations/`. Each one has `derived_from` pointing to existing measured or interpretation ids, a `method` and a `method_version`, and states its uncertainty in the `statement`.
  - An interpretation that depends on an `excluded` finding at any depth may only explain the exclusion (S9, transitive): `value` and `quantity` are `null`, no `relevant_environments`, and limitations that say so.
- **R3. Moon/Mars fire-safety recommendations.**
  - Interpretation findings in `data/curated/interpretations/`, plus a readable summary in `docs/research/`.
  - Each recommendation:
    - is traced through `derived_from` to measured findings;
    - names the conditions it relies on;
    - says where lunar or Martian conditions (gravity, pressure, oxygen) differ from the tested ones;
    - never presents itself as a NASA conclusion.
  - No recommendation relies on simulation output.
- **R4. Independent scientific review.** Review Member 1's ranking, compare and assistant output against the rules, and Member 2's scientific wording.
- **Q2. Integrity tests** in `tests/research/`:
  - No `illustrative_simulation` appears in findings, compare, rankings or assistant output.
  - The ranking, compare and assistant modules do not import simulation code.
  - "according to NASA" appears in no output and in no file under `frontend/`.
  - Nothing marked `fixture: true` appears in `data/curated/`.
  - S9, independently and **transitively** (any `derived_from` depth; cycles rejected): `excluded` findings never reach ranking inputs or comparable comparisons, and TARS never states an excluded value.
  - S10, independently: every `flag_ref` resolves with the matching `ranking_use`, every flag row is covered, no note comes from a `not_available` row, and the flag quotes match the source.
  - Independent checks of S5, S6 and S8 against live responses.
- **Q3. Source spot check.** Draw a sample of max(5, 10%) of measured findings with a fixed recorded seed. Check each one against the source page and log it in `docs/verification/source_spotcheck.md`. The bar is 0 mismatches. A mismatch blocks CP3 until Member 3 fixes it and the finding is checked again. Member 2 is the second checker for any disputed entry.
- **Q5 (narrative).** `docs/DEMO.md`, the judge-demo walkthrough, written with Member 2 for the UI path. Member 3 performs the clean-clone run.
- **Q6. Submission checklist.** `docs/SUBMISSION_CHECKLIST.md`: SI use described, every source cited, license chosen, organizer ruling recorded, no "according to NASA". Member 1 verifies each item.

| Check | How it is verified |
|---|---|
| Criteria frozen before results | git log: the R1 commit is older than the first ranking code or output, and Members 1 and 3 approved it |
| R2 and R3 are traceable | S3 passes in Member 3's `tests/data/`; schema validation passes |
| R2 and R3 are scientifically reviewed | Member 1 approves the PR (spec §4.4) |
| Q2 | CI green on `main` |
| Q3, Q5, Q6 | Signed entries in `docs/verification/` by the named member |

---

## Dependencies and integration order

```
CP1  contract PR merged; Members 1, 2, 3, 5 confirmed and approved; TARS and
     interface matrix approved; P0 contract additions decided
 │
 ├── M3 D1–D4 ─────────────────┐            (parallel, disjoint folders)
 ├── M1 B1–B2 on fixtures, Q1 harness
 ├── M2 F1, F2, F6 on fixtures │
 └── M5 R1 draft, Q2 harness   │
                               ▼
CP2  first real data on main (D1–D4 green, M5 Q3 spot check done)
 │
 ├── M1 B1–B2 on real data ──► M2 F1/F2 wired to API
 ▼
CP3  explorer working end to end on main
 │
 ├── M1 B3 compare ──► M2 F3              (needs 2 investigations with a shared quantity)
 ├── M5 R1 freeze (M1 + M3 approve) ──► M1 B4 ranking ──► M2 F4
 ├── M3 T1 retrieve() ──► M1 B6 TARS backend ──► M2 F5
 ├── M5 R2/R3 interpretations and Moon/Mars recommendations (M3 + M1 review)
 └── M2 Q4 browser tests; M5 + M2 Q5 demo; M3 clean-clone run
 ▼
CP4  demo freeze: fixes only after this point
 │
 └── M1 B8 / M2 F7 simulation, only if time allows and never before CP4 items are green
 ▼
CP5  submission (M5 Q6 complete, M1 verified)
```

**Merge order on `main`:**
1. Contract PR.
2. Data, backend, research and integrity PRs in any order, since they touch disjoint folders.
3. R1 before any ranking code.
4. T1 before B6.
5. Frontend wiring after the backend endpoints it calls are merged.

Every PR merges only with CI green, a review from the owner of each area it touches, and the independent reviewer from spec §4.4 for scientific work.

## P0 contract additions: ACCEPTED (Option B, Command Center 2026-11-14)

They are part of this PR (from PR #5, fast-forwarded):
1. `Finding.relevant_environments`: an optional array of `environment`, allowed **only on interpretation findings**. A measured value records where the experiment ran (`conditions`, `platform`). Saying it is relevant to a lunar base is an interpretation.
2. `Finding.limitations`: an array of non-empty strings, **required on interpretation findings** (at least 1) and not allowed on measured findings. A measured finding keeps the source-reported `uncertainty`.
3. `AssistantAnswer.limitations`: a required array of non-empty strings, with at least 1 entry in `ai` and `fallback_quotes` modes, so TARS always states uncertainty.

They were added before CP1 because `Finding` and `AssistantAnswer` reject unknown fields. Adding them later would have broken any validator pinned to v0.2.0.

## Other CP1 decisions (Command Center, 2026-11-14)

| # | Decision | Status | Where it is recorded |
|---|---|---|---|
| C1 | TARS = **Traceable Analysis and Research Support** | decided | spec §4.1, §8 |
| C2 | Condition values may be converted by **exact defined factors only**, in Member 3's curation tool. The as-printed value stays in the registered source file. Quantity values are never converted | accepted | `contracts/README.md` convention 4 |
| C3 | **Corrected at CP1 (Command Center Option A).** A value flagged `exclude` becomes a measured finding with `value_status: "excluded"`, `value: null` and an attributed exclusion note with `flag_ref`. A `caution` goes into `curation_notes`, never `uncertainty`. A `not_available` cell is `not_reported` with no note. Every note has a `flag_ref`. Nothing is deleted from source files | accepted. The flag mapping, S10, `source` and `flag_ref` on every note, and the `excluded` name come from Member 2's PR #7. Member approvals are pending | `contracts/README.md` conventions 9 and 10, rules S9 and S10 |
| C4 | FLEX quantities (`burning_rate_constant`, `visible_flame_extinction_diameter`, `burn_time`, `initial_droplet_diameter`) | accepted. Implemented **after CP1** in a separate reviewed contract PR (Member 3, D5). Not in this PR | this table |
| C5 | `test/qa-demo` | open: keep it untouched (recommendation: delete at CP4) | this table |
| — | PRs #2, #3 and #4 | not merged before CP1 | spec §6 |
