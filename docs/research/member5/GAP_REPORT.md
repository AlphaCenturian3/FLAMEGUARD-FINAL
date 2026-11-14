# Member 5 requirements-to-implementation gap report

**Date:** 2026-11-14. **Branch:** `feat/research-safety-intelligence` (draft PR #3). **Sources of requirements:** the Member 5 kickoff (`FLAMEGUARD_MEMBER5_RESEARCH_KICKOFF_2026-11-14.md`), the execution brief, the master spec, and the CP1 proposal (PR #1, head `29c7078`).

Status key: **Done** (implemented and tested in this PR), **Partial**, **Gap** (not done), **Blocked** (needs another member).

## Evidence and sources

| Requirement | Status | Where / note |
|---|---|---|
| Source registry with investigation id, NASA URL, DOI | Done | `investigations.json`. Dataset DOIs for BASS-II and FLEX were verified in DataCite. SoFIE, Saffire IV–VI and FM²: no DOI found, recorded as `null`. |
| Kickoff DOIs (BASS-II `10.60555/4qc4-de67`, FLEX `10.60555/mbq8-0451`) | Done | Both confirmed in DataCite: NASA PSI datasets PSI-25 and PSI-69, CC0-1.0 |
| Test id, fuel, gravity, O₂, pressure, flow, geometry fields | Done | `evidence.py`. The condition keys follow contract v0.2.0; `test_id` is explicit, `null` when unknown. |
| Measured / reported / interpreted labels | Done | `evidence_category`, plus `source_claim_strength` for quoted statements |
| NASA objectives never shown as measured outcomes | Done | Reported records cannot carry numbers. Cards cannot call a hypothesis or objective an `experimental_result` (tested). |
| Missing data marked missing | Done | `missing_fields()`; every condition key required, with `null` meaning missing |
| Measured values and units, when verified | **Blocked** | No test-level NASA data imported (kickoff R2). Needs Member 3. |
| Fuel phase, thickness and ignition/source conditions logged (kickoff C.2) | **Gap** | Not in contract v0.2.0 `conditions`. Needs a contract PR (decision D-07). |
| Every quote checked against the source | Done | 43 quote citations across three files: 29 matched automatically against live sources; 14 PDF quotes checked by hand (pages and SHA-256 in `SOURCE_AUDIT.md`); 0 failed |
| Dataset licences and credits | Done | README "Credits and licences" |

## Comparability and ranking

| Requirement | Status | Where / note |
|---|---|---|
| Block comparison across inconsistent units, fuel, pressure, O₂, gravity, flow | Done | `comparability.py`; parametrized test over every condition key and unit |
| Show "Not comparable" with reasons | Done | `ComparabilityResult.reasons`, `IncomparableEvidenceError` |
| Ranking by declared user purpose; re-rank when purpose changes | Done | Structured question; test shows the order changes with purpose |
| Weights 40 / 25 / 20 / 15, visible, marked unapproved | Done | `config/research_relevance_criteria_v1.proposed.json` (`status: proposed`) |
| **0–3 assessment rubric per criterion** (kickoff C.3) | **Gap** | Implemented as continuous 0–1 fractions. Member 1 picks one (decision D-02). |
| Unknown criteria marked Missing, never silently zero (kickoff C.4) | Partial | Each criterion now carries `status` (`complete`, `partially_missing`, `not_assessed`), and missing items are listed. The numeric score still treats missing as 0. Member 1 decides the policy (D-03). |
| "Insufficient evidence" bucket instead of forced ordering | Done | Investigations without verified evidence go to `excluded` with an "insufficient evidence" reason; `release_status: evidence_insufficient` |
| Ranking disabled until verified measurements exist | Done | Real measured records need a `manifest_id` in `verified_manifest_ids`. Ranking stays `disabled_criteria_not_frozen` until the criteria are approved. |
| Never a risk, probability or safety score | Done | Disclaimer on every output; banned-phrase checks |
| Explanations: query, criterion scores, origin, limitations | Done | `explanations`. Cohort labelling is partial (the gap above). |
| Criteria frozen before any ranking output (CP1 R1) | **Blocked** | Needs Members 1 and 3 to approve, then `config/ranking_criteria_v1.json` in its own commit |
| Member 1's D-01 conditions: environment-only criteria, cited reference table, ±0.05 sensitivity | Partial | Prepared for review: `CRITERIA_ENVIRONMENT_CONTEXT.md`, `ENVIRONMENT_REFERENCE.md`, `WEIGHT_SENSITIVITY.md` (synthetic only). Reference implementation not yet updated; real sensitivity run needs curated data |

## Interpretation and Moon/Mars insights

| Requirement | Status | Where / note |
|---|---|---|
| Six themes; Finding → source → interpretation → implication → limitation | Done | `insight_cards.json`, `insights.py` |
| Kickoff cards M5-I01 to I04 and D1 to D5 reconciled | Done | Each card has a `kickoff_ref`. I03 retitled "Suppression evidence requires fuel context"; I04 now cites the partial-gravity white paper. |
| Inference vs observation distinguished | Done | `claim_type`: `flameguard_interpretation` and `engineering_hypothesis` |
| Not presented as flight-qualified | Done | Fixed disclaimer on every card |
| R3: recommendations traced via `derived_from` to **measured** findings | **Blocked** | Cards cite quoted statements, since no measured findings exist yet. They stay in `docs/research/` as drafts until Member 3 imports data. |

## Integration and process

| Requirement | Status | Where / note |
|---|---|---|
| Judge path Find → Compare → Rank → Interpret → Moon/Mars (kickoff R4) | **Gap** | Not connected to the UI or TARS. Needs Members 1 and 2 after CP1. |
| TARS narrative separate from NASA statements | **Blocked** | TARS retrieval is Member 3, assistant Member 1 (CP1 §4.1) |
| Isolation from other members' work | Done | Only new files; `app.py`, `contracts/`, `frontend/` and `data/` untouched |
| Placement matches CP1 ownership | **Done after CP1** | Reference code is in non-runtime `research/`; tests remain in `tests/research/` and fixtures in `tests/fixtures/research/`, per `docs/CP1_WORKSTREAMS.md` and D-08 to D-10. |
| QA review (kickoff R5) | **Blocked** | The brief names Member 4; the CP1 proposal says there is no Member 4 (decision D-11) |
