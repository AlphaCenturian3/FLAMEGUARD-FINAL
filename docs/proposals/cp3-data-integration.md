# Proposal: CP3 integration of curated NASA data

**Status:** proposal from `feat/nasa-data-tars`. Nothing here is decided. Backend items need the backend owner (Member 1); UI items need the frontend owner (Member 2); anything touching `contracts/` follows spec §5.4.
**Date:** 2026-11-14
**Depends on:** PR #4 (FLEX Table IX dataset + flags)

## Inputs available after PR #4

| Manifest id | Class | File | Key |
|---|---|---|---|
| `nasa-tp-2015-216046.table-ix.flex-001-010` | measured | `data/curated/flex_tp2015216046_table_ix_001_010.csv` | `flex_test` |
| `nasa-tp-2015-216046.table-ix.flex-001-010.flags` | interpretation | `data/curated/flex_tp2015216046_table_ix_001_010.flags.csv` | (`flex_test`, `field`); `field = "*"` applies to the whole row |

## Part A: backend (Member 1)

1. **Load only checked data.** Read `data/manifest.json` and load an entry only if `check_manifest()` in `tools/check_data_provenance.py` returns no errors for it. Never load `data/raw/` or `tests/fixtures/`.
2. **Parse without inventing.**
   - An empty measured cell becomes `None`, never `0`. Its column is listed in that row's `source_dash_fields`.
   - Keep the printed string next to any parsed number, so precision is not invented (`0.6` is not `0.60`).
3. **Join the flags** on (`flex_test`, `field`), plus all `field = "*"` flags for the row.
4. **Quantitative operations** (rankings, comparisons, any statistic):
   - Drop cells flagged `exclude` (currently the FLEX-010 burning rate) or `not_available` (every printed dash).
   - Cells flagged `caution` may be used, but their flag reasons must travel with the result.
   - Never pool rows with different `test_end` values (Extinction, Disruption, Completion).
   - Only compare rows with compatible fuel, pressure and composition.
5. **Map to existing schemas, with no contract change needed:**
   - `Investigation`: `id: "flex"`, `name: "Flame Extinguishment Experiment"`, `acronym: "FLEX"`, `platform: "ISS"`, `sources` taken from the manifest entry. `relevant_environments` is a FlameGuard-SI judgment and needs a team decision before it is filled.
   - `Finding` (measured), one per cell:
     - `id: "flex.FLEX-004.burning_rate_constant_mm2_per_s"`
     - `investigation_id: "flex"`
     - `value`: the printed number
     - `unit`: from the data dictionary
     - `uncertainty: null`. Table IX reports none, so none may be added.
     - `provenance: {manifest_id, sources: [the Table IX source]}`
   - Missing cells: emit a Finding with `value: null` and a statement saying the source printed a dash. This lets the UI show "not reported" instead of dropping the cell silently.
6. **Where flags go (decision needed).**
   - Option 1: put them in `Finding.provenance.flags`. `provenance` allows extra keys, so the schema doesn't change, but clients come to depend on an undocumented field.
   - Option 2: add a documented `flags` field to `Finding` through a contract PR (spec §5.4, version bump).
   - The data workstream recommends option 2.
7. **TARS** (`POST /api/assistant/ask`): see `docs/proposals/tars-data-requirements.md`.
   - Answers only from loaded entries.
   - `citations` copied from manifest sources.
   - Never uses `exclude` or `not_available` values.
   - States caution reasons and dataset limitations.
   - With no AI key, returns the matching rows and verbatim source quotes.

## Part B: frontend (Member 2)

1. **Missing values.** Show "Not reported (source printed –)". Never show 0 and never leave the cell blank. On hover, show the A.1 note that a dash can mean "no extinction" or "not listed".
2. **Indicators.**
   - A visible **Excluded** badge on FLEX-010's burning rate, with its reason.
   - A **Caution** marker with the reason text on cautioned cells.
   - An evidence-class badge on every value: measured, interpretation, or simulation (with the required simulation label).
3. **Citations.** For every value, show title, printed page, exact quote, and a link to the NTRS record. Generated text is attributed to FlameGuard-SI, never to NASA.
4. **Limitations panel** per dataset, built from the manifest `description` and `data/docs/flex_table_ix.md`: contamination, early-test imaging, calibration runs, possible extrapolation, and the FLEX-010 conflict.
5. **Views.**
   - Investigation view: the Table IX rows with flags inline.
   - Comparison view: groups by fuel, pressure and composition, keeps outcomes separate, and leaves excluded and missing cells out of any chart while still listing them.
6. Until the backend serves data, build against `contracts/examples/*.json`. Those are fixtures and must never be shown as NASA data.

## Decisions requested

| # | Decision | Owner |
|---|---|---|
| D1 | Where flags go on a `Finding` (option 1 or 2 above) | Member 1 + Member 2 (contract) |
| D2 | One measured Finding per cell, and Findings with `value: null` for missing cells | Member 1 |
| D3 | `relevant_environments` for FLEX | Team |
| D4 | UI wording for missing, excluded and caution states | Member 2 |
