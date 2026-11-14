# Proposal: TARS data requirements

**Status:** proposal from `feat/nasa-data-tars`, for review by the backend owner (`feat/backend-science`). Not approved. Nothing here changes `contracts/` or `backend/`.
**Date:** 2026-11-14

## Definition

**TARS = Traceable Analysis and Research Support.** This is the name decided by the Command Center (decision C1, recorded in the contract v0.2.0 proposal, PR #1); this document follows it. An earlier draft here proposed "Traceable Aerospace Research System", which is withdrawn. TARS is an evidence-grounded research assistant. It explains NASA combustion investigations, compares compatible experimental findings, and communicates source-backed fire-safety relevance with explicit uncertainty.

In the current contract TARS is the assistant behind `POST /api/assistant/ask` (planned, returns 501 today). The backend owns its implementation. The data workstream owns the evidence it may draw on.

## Requirements on TARS (proposed)

1. **Evidence scope.** TARS answers only from `data/manifest.json` entries that pass `tools/check_data_provenance.py`, and from the cited source passages in those entries. Entries with `evidence_class: illustrative_simulation` are never used as evidence (spec §2.3).
2. **Evidence class is visible.** Every value TARS states carries its evidence class. A `measured` value is quoted as printed, with its unit and its manifest id. Anything TARS computes or infers is an `interpretation` attributed to FlameGuard-SI, never to NASA. Do not write "according to NASA" (spec §2.4).
3. **Citations.** Every answer returns `citations` as `Source` objects, taken from the manifest entry's `sources`: title, url, page, exact quote, retrieved date, archive_id. TARS never invents a page or a quote.
4. **Missing stays missing.** An empty cell listed in `source_dash_fields` is reported as "not reported in the source", never as 0 and never estimated.
5. **Respect usage flags.** TARS reads the flags file (`...flags.csv`, manifest `...flex-001-010.flags`). It never uses a value flagged `exclude` (currently the FLEX-010 burning rate) or `not_available` (printed dashes). It shows the reason for any value flagged `caution` alongside the value.
6. **Limitations travel with values.** When TARS uses a dataset, it surfaces the dataset's limitations from the manifest `description` and `data/docs/`. For the first dataset these are needle contamination, early-test imaging, calibration runs, possibly extrapolated extinction diameters, and the FLEX-010 burning-rate conflict.
7. **Compatible comparisons only.** TARS compares findings only when fuel, ambient composition, pressure and outcome type are compatible, and it states the conditions next to the comparison. Extinction, disruption and completion outcomes are never pooled.
8. **No out-of-scope outputs.** No risk scores, alarms, extinction predictions, warning times or safety guarantees (spec §1, out of scope).
9. **Works without an AI key.** With `FLAMEGUARD_AI_API_KEY` empty, TARS falls back to returning the matching source quotes and table rows verbatim (spec §3).

## What the data workstream provides now

- `data/curated/flex_tp2015216046_table_ix_001_010.csv`: 10 FLEX tests, `measured`, all cells verified against the PDF.
- Manifest entry `nasa-tp-2015-216046.table-ix.flex-001-010`, with 7 verbatim quotes (table title, A.1 dash definition, contamination, shutter speed, two figure captions).
- `data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv`: 43 source-cited usage flags (`interpretation`).
- `data/docs/flex_table_ix.md`: data dictionary and caveats.

## Open questions for the backend owner

1. **Limitations field.** `data_manifest.schema.json` has no limitations field, so limitations live in `description` for now. A structured `limitations: [string]` field (and maybe `known_conflicts`) would let TARS show them reliably. That is a contract change (spec §5.4: backend and frontend approval, version bump). Do you want it?
2. **Row-level findings.** Should the backend turn CSV rows into `Finding` objects (one per cell, with `provenance.manifest_id`), or should the data workstream publish a Findings JSON alongside the CSV?
3. **Answer shape.** Is `{answer, citations, generated_by}` enough? Or should the response also carry `evidence_class` per statement and a `limitations` list (another contract change)?
