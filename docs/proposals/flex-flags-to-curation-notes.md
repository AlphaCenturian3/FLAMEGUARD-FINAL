# Prepared, not implemented: mapping FLEX flags onto PR #1 `curation_notes`

**Status:** preparation from `feat/nasa-data-tars`, 2026-11-14. **Nothing here is implemented**, and `contracts/` is unchanged. It assumes the contract v0.2.0 proposal (PR #1, head `a6876d1`) merges as written; if PR #1 changes, this changes with it.

**Why there is no `Finding.flags` extension.** PR #1 already covers flags:
- `curation_note`: `kind` caution or exclusion, `note`, `generated_by`, `flag_ref` {`manifest_id`, `flag_id`}, and `source` with a quote.
- `value_status` adds `excluded`.
- Rules S9 and S10 govern how they are used.

A separate `flags` field would duplicate this and break the "one implementation" rule, so the data workstream is not proposing one.

## Mapping of the 43 flags in `flex_tp2015216046_table_ix_001_010.flags.csv`

| `ranking_use` | Count | Becomes (PR #1 convention 9) |
|---|---|---|
| `exclude` | 1 | FLEX-010 `burning_rate_constant` finding: `value_status: "excluded"`, `value: null`, `curation_notes: [{kind: "exclusion", flag_ref: {manifest_id: "nasa-tp-2015-216046.table-ix.flex-001-010.flags", flag_id: "<id>"}, …}]`. The printed `0.37` stays in the CSV. |
| `not_available` | 9 | `value_status: "not_reported"`, `value: null`, no note. Cells: FLEX-004 and FLEX-010 extinction diameter; FLEX-007 and FLEX-008 extinction diameter; FLEX-009 initial diameter, extinction diameter, burning rate, burn time and test time. |
| `caution` | 33 | `curation_notes` entries with `kind: "caution"` (never `uncertainty`). |

How the 33 cautions break down:
- Row-level (`field = "*"`): 15. That's 10 contamination, one per row, plus 5 calibration (FLEX-002 to 006).
- `initial_droplet_diameter`: 10. Imaging cautions for FLEX-001 to 008 (FLEX-001 has two) plus FLEX-008 soot.
- `burning_rate_constant`: 2 (FLEX-007, FLEX-008).
- `visible_flame_extinction_diameter`: 1 (FLEX-006, possibly extrapolated).
- `test_end`: 5. See G2.

Each note's `source` would be built from the flag row (`source_printed_page`, `source_quote`) plus the measured manifest entry's report citation (title, url, retrieved, archive_id). `note` would be the flag row's `reason`.

## Gaps found while mapping (for the PR #1 owners)

- **G1. Row-level flags. Resolved by PR #1, no proposal needed.** S10(a) accepts a flag whose field is the finding's field or `*`, and convention 9 allows a whole-row caution note on a `not_reported` finding. Our `*` flags (contamination, calibration) give a caution note on every finding from that row.
- **G2. `test_end` has no home.** The C4 quantities are `burning_rate_constant`, `visible_flame_extinction_diameter`, `burn_time` and `initial_droplet_diameter`. Test outcome is none of these, and it is not among the condition keys I could find. Five caution flags sit on it (FLEX-001 outcome ambiguity, and contaminant-related disruption for 001, 007, 008, 009). S10 requires every caution row to be covered, so the outcome needs a finding. Options:
  - (a) a measured qualitative finding: `quantity: null`, `value_status: "not_applicable"`, a statement quoting the printed outcome;
  - (b) a new vocabulary quantity or condition key through D5.
  - The data workstream leans to (a), because it needs no new key. That is the contract owners' call.
- **G3. Non-quantity dashes.** FLEX-009 test time is flagged `not_available`, but time is not a quantity, so no finding exists to mark `not_reported`. Proposal: S10 treats `not_available` flags on non-quantity fields as documentary only.
- **G4. Source fields on notes.** `curation_note.source` requires title, url and retrieved, but the flags CSV stores only page and quote. Proposal: the derivation tool fills them from the measured manifest entry. The alternative is adding columns to the flags CSV, which would change its SHA-256 and need re-review.
- **G5. S10(d) in CI.** S10(d) wants each flag quote checked "against the registered source text". The FLEX PDF is not committed (spec §2.4), so CI cannot do this. Today `tools/verify_flex_table_ix.py` checks all 43 flag quotes and 7 manifest quotes against the PDF **locally**, and the output is pasted into the PR. Options:
  - (a) accept the local check plus Member 5's independent Q3 check;
  - (b) register a text extract of the cited pages. This needs a rights decision, although NTRS marks the report "Public Use Permitted".
  - Needs a decision.
- **G6. Dash meaning.** With no note on `not_reported`, the A.1 caveat (a dash is not a confirmed no-extinction event) lives only in the finding's `statement`. No contract change is needed. The derivation tool would write that sentence, and the UI would show it.

- **G7. Pressure units and C4 quantities.**
  - PR #1's condition key is `pressure_kpa`, while Table IX prints mmHg. Under C2, Member 3's tool may convert by an exact defined factor (1 mmHg = 133.322387415 Pa, so ÷ 7.50061683… for kPa). The as-printed mmHg stays in the CSV.
  - The four C4 FLEX quantities are accepted but not yet in `contracts/vocabulary.json` (checked on PR #1 head `a6876d1`). They need the separate D5 contract PR before any FLEX finding can validate.

## Not done, on purpose

- No change to `contracts/`, `backend/` or `frontend/`.
- No `data/curated/findings/flex.json`. It needs PR #1 merged, plus decisions G2 and G5.
- PR #4 is aligned only where PR #1's workstream doc asks Member 3 to act now: flags path and TARS name. The manifest version bump and the rebase wait for PR #1 to merge.
