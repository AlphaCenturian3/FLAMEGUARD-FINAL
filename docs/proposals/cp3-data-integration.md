# Proposal: CP3 integration of curated NASA data

**Status:** proposal from `feat/nasa-data-tars`. **Not an accepted contract.**
**Date:** 2026-11-14 (revised the same day)
**Depends on:** PR #4 (FLEX Table IX + flags) and the contract v0.2.0 proposal in PR #1, which is not merged.

**Revision note.** The first version of this file proposed its own flag field on `Finding` (old decision D1) and its own Finding mapping. PR #1 already defines both, through decisions C1–C4, conventions 9–10 and rules S9–S10, so those parts are **withdrawn**. This file now only describes how the FLEX data would follow PR #1, and lists the gaps. Interface changes still need the backend and frontend owners (spec §5.4).

## Data available after PR #4

| Manifest id | Class | File |
|---|---|---|
| `nasa-tp-2015-216046.table-ix.flex-001-010` | measured | `data/curated/flex_tp2015216046_table_ix_001_010.csv` (as-printed transcription of record) |
| `nasa-tp-2015-216046.table-ix.flex-001-010.flags` | interpretation | `data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv` |

## How FLEX would follow PR #1 (once it merges)

- Member 3 adds a tool in `tools/` that derives `data/curated/findings/flex.json` (contract `Finding` JSON) from the CSV. The backend loader (B1) reads that JSON, not the CSV.
- Flags map onto findings as PR #1 decision C3 and convention 9 require. The details, with every flag counted, are in [`flex-flags-to-curation-notes.md`](flex-flags-to-curation-notes.md):
  - `exclude` (FLEX-010 burning rate) → `value_status: "excluded"`, `value: null`, an exclusion note with `flag_ref`
  - `caution` → `curation_notes`
  - `not_available` → `not_reported`
- `retrieve()` for TARS (T1) is Member 3's, and is deterministic. The TARS backend (B6) is Member 1's; the TARS UI (F5) is Member 2's.

## For Member 1 (backend)

- Load only manifest entries that pass `tools/check_data_provenance.py`.
- Excluded findings never reach ranking inputs, comparisons or TARS numeric statements (rule S9).
- Never pool different test outcomes (Extinction, Disruption, Completion).
- Only compare rows whose fuel, pressure and composition are compatible.

## For Member 2 (frontend), as already specified in PR #1 F1 and F5

- Missing values show "Not reported", never 0 and never blank.
- Excluded values show "Excluded by FlameGuard-SI", with the exclusion note and a link to the source location.
- `curation_notes` are labelled as FlameGuard-SI assessments; `uncertainty` as "reported by the source".
- Add-on suggestion from the data side: for FLEX extinction diameters printed as a dash, show the A.1 note that a dash can mean "no extinction" or "not listed". It must never read as a confirmed no-extinction event.
- Limitations panel per dataset: contamination, early-test imaging, calibration runs, possible extrapolation, and the FLEX-010 conflict.

## Open decisions

| # | Decision | Owner |
|---|---|---|
| D1 | ~~Flag field on `Finding`~~. **Withdrawn**: use PR #1 `curation_notes` and `value_status` | n/a |
| D2 | How Table IX test outcome (`test_end`) and its 5 caution flags are represented (gap G2 in the mapping doc) | Member 1 + Member 2 (contract, via D5) |
| D3 | `relevant_environments` for FLEX (interpretation findings only, per PR #1) | Member 5 / team |
| D4 | The quote-verification route for S10(d) when the source PDF cannot be committed (gap G5) | Member 1, Member 5, Member 3 |
