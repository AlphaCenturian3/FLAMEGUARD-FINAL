# Questions for Members 1 and 2: G2, G5, G7

**From:** Member 3 workstream, 2026-11-14. **Background:** [`g2-g5-g7-resolution.md`](g2-g5-g7-resolution.md) and [`flex-flags-to-curation-notes.md`](flex-flags-to-curation-notes.md).

**How answers count.**
- Only an answer posted by the **owner from their own GitHub account** counts as a decision.
- A coordinator recommendation, or an executor's summary, is input, **not** approval.
- Nothing in PR #1's contract changes because of these answers. Any change needed goes through its own contract PR (spec §5.4).

**PR #1 state when these questions were written** (from git refs and the PR #3 coordination record, 21:10 UTC):
- PR #1 head is `eaae6d6`. It added transitive S9 on top of `a6876d1`.
- Formal approvals at `eaae6d6`: **none recorded**. Member 1's "APPROVE" was given at `a6876d1`.
- Members 2, 3 and 5 have no approval at either SHA.
- **Derived FLEX Findings are not started**, and won't be until PR #1 is approved and merged.

Please answer by number, for example "G2-Q1: yes", on PR #6.

## G2. Test outcome (Extinction / Disruption / Completion)

| # | Question | To |
|---|---|---|
| G2-Q1 | For P0, may each FLEX test's outcome be a **measured qualitative finding** (`quantity`, `value`, `unit` = null; `value_status: "not_applicable"`; statement quoting the printed outcome; locator = Table IX row and column)? The 5 outcome caution flags would attach to it as `curation_notes`. | Member 1 |
| G2-Q2 | Will the B1 loader accept a measured finding with `quantity: null` for FLEX, as the CP1 doc already does for `experimental_result` records? | Member 1 |
| G2-Q3 | Until a machine-readable outcome exists, how should `/api/compare` keep FLEX rows with different outcomes non-comparable? (a) Member 3 adds the outcome to each quantity finding's statement, and compare treats rows from different outcomes as non-comparable by locator row. (b) Member 3 emits a separate grouping file. (c) Defer FLEX compare until a D5 contract field exists. | Member 1 |
| G2-Q4 | Should the UI show the outcome finding next to each FLEX value, and label rows by outcome (never pooled)? Any wording preference? | Member 2 |
| G2-Q5 | Do you want a later D5 contract PR for a machine-readable outcome field? If yes: a condition-like enum, or a qualitative vocabulary quantity? | Members 1 + 2 |

## G5. Verifying source quotes (S10(d))

| # | Question | To |
|---|---|---|
| G5-Q1 | The FLEX PDF cannot be committed (spec §2.4), so CI cannot read "the registered source document's text". For P0, is S10(d) satisfied by (i) Member 3's local `tools/verify_flex_table_ix.py` run, with its output pasted in each PR touching the CSV, flags or quotes, **plus** (ii) Member 5's independent Q3 check? | Member 1 |
| G5-Q2 | If yes, should `contracts/README.md` S10(d) get a footnote saying so? That would be a contract-text change in its own PR. Or is a note in `docs/verification/` enough? | Members 1 + 2 |
| G5-Q3 | After submission, should we register a text extract of only the cited pages so CI can enforce S10(d)? NTRS marks the report "Public Use Permitted". This needs a rights decision and a manifest place for source text. | Members 1 + 2 |
| G5-Q4 | Which page convention should `Source.page` use? Printed page in `page`, with the PDF index in the locator when they differ? PR #4 uses printed pages; Member 5 uses PDF indices (the FLEX report differs by 6). | Members 1 + 2 |

## G7. Units, conversions, vocabulary

| # | Question | To |
|---|---|---|
| G7-Q1 | `pressure_kpa`: convert Table IX mmHg by the exact conventional factor **133.322387415 Pa per mmHg** (not the torr), storing the **unrounded** product (e.g. 757.7 mmHg → 101.0183729443455 kPa)? | Member 1 |
| G7-Q2 | Display: should the UI round `pressure_kpa` to the printed significant figures and also show the as-printed mmHg from the locator? | Member 2 |
| G7-Q3 | For the D5 vocabulary PR: are `initial_droplet_diameter` (mm), `visible_flame_extinction_diameter` (mm), `burning_rate_constant` and `burn_time` (s) acceptable keys? What exact unit string for the burning-rate constant: `mm2/s` or `mm^2/s`? | Members 1 + 2 |
| G7-Q4 | `flow_configuration` for free-floating droplets with residual drift: `null` (conservative) or `quiescent`? | Member 1 |
| G7-Q5 | `diluent` format for FLEX rows: `"N2"` and `"N2+CO2"`, or another convention? And `fuel_or_material`: `"heptane"` (Table IX) or `"n-heptane"` (report §6)? | Members 1 + 2 |
