# Member 3 technical audit of PR #38 (test-level selection in `/api/compare`)

**Audited:** PR #38 head `cb9c4b8`, `docs/proposals/compare-test-selection.md`.
**Against:**
- contract v0.2.2 (PR #17 `c289e74`);
- the B3 engine and B1 loader (PR #37 `17dab2d`);
- the 40 staged FLEX Findings (PR #31 `740b901`, `data/curated/findings/flex.json`).

**By:** Member 3's engineering session (data, provenance, TARS evidence). 2026-11-15.

**This is a review record, not a formal approval.** It changes no contract, registers nothing, and implements nothing. All checks ran in temporary worktrees outside the repository with nothing committed. The harness lives outside the repository and simulates the proposal by handing PR #37's unchanged engine a store that holds only the selected findings ("S5 applied to the selected rows", proposal §2).

## Verdict

The direction is sound. The identity rules, error-first handling and S9 behaviour hold on real data. **Three corrections are required before the contract PR**, and four more are recommended. Decisions 4 and 5 interact with the FLEX data in a way the proposal does not state.

## Evidence

| # | Check | Result |
|---|---|---|
| C1 | PR #37 B1 loader on PR #31's data | Manifest ok; 0 rejected; **40 findings accepted**; `exclusion_dependent` = `flex.flex-010.burning_rate_constant` only |
| C2 | Identity | Every `test_id` matches `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`. No finding id contains `:` or `,`. **(investigation, test_id, quantity) unique for all 40** |
| C3 | Whole-investigation compare (v0.2.2) | `comparable: false` for all 4 quantities (5, 9, 6 and 5 reasons). Confirms proposal §1 |
| C3 | Every subset of the 10 tests, per quantity | Comparable selections: initial diameter, burning-rate constant and burn time **only {FLEX-004, -005, -006}** (3 of 45 pairs each). Extinction diameter **only {FLEX-005, -006}** (1 of 45; FLEX-004 is `not_reported`) |
| C4 | Selection containing the excluded FLEX-010 burning rate (as a pair and alone) | Row value `null`, `comparable: false`, printed `0.37` **absent** from the whole response |
| C5 | Comparison row keys | `conditions, evidence_class, finding_id, investigation_id, test_id, test_outcome, value, value_status`: **no `curation_notes` and no caution signal**. 31 of 31 reported FLEX values carry ≥ 1 caution |
| C6 | `not_selected` for a 2-test selection | 8 for every quantity, but the 8 mix statuses (e.g. burning-rate constant: 8 reported, 1 not reported, 1 excluded) |
| C10 | Row order | The engine's `_select` sorts by (investigation, id): request `[FLEX-002, FLEX-001]` returns `[FLEX-001, FLEX-002]`. The proposal requires request order |
| C11 | Two **Disruption** rows of `visible_flame_extinction_diameter` (synthetic twin of FLEX-001) | **`comparable: true`**, contrary to `contracts/outcomes.json` condition 5 (Member 5, confirmed) |
| C12 | Outcome flags (F004, F005, F026, F032, F038) attached to every Finding of their test (condition 6) | Holds for all 40 |
| C13 | S10(b) caution/exclude coverage; S10(c) no note from `not_available` | No gaps; none |
| C14 | `tools/derive_flex_findings.py` (PR #31) regenerating the Findings | **Byte-identical** to the staged file, SHA-256 `1d3cf89827015e720e700d29d4c250bcdbb887f5225576de9631805fa66afc65` |
| C15 | Within-test consistency | Each test's 4 Findings share one `test_outcome` and one `conditions` object, but **no rule enforces it** |
| C16 | Uniqueness enforcement | The loader's S11 check (`_identity_reasons`) covers all-or-nothing identity only. **Nothing enforces one measured finding per (investigation, test_id, quantity)** |

Test runs (Windows, Python 3.11.9; `PYTHONUTF8=1`):
- PR #31 targeted suites (derivation, outcome, identity, S10, FLEX dataset, vocabulary): 230 passed, 3 skipped (no local PDF in that worktree), 1 failed. The failure is Windows-only (`findings\flex.json` vs `findings/flex.json` in a path assertion).
- PR #31 full suite excluding `tests/backend`: 531 passed, 9 skipped, 2 failed.
  - One is the Windows path assertion above.
  - The other is `test_registration_requires_every_gate_closed_and_every_condition_approved`, which **fails by design**: gates PR12, PR17, S10-REGISTRATION, Q3, B1-S11 and F042-NOTE are open, and the diluent, fuel_or_material and sample_geometry decisions are unapproved. Registration is correctly blocked.
- PR #37 full suite: 466 passed, 67 failed, all in `tests/backend`. Cause: `tests/backend/conftest.py` writes fixtures with `write_text()`, which emits CRLF on Windows, and hashes the LF text, so every fixture SHA-256 mismatches. **Windows-only test-portability bug in PR #37, not a PR #38 issue**; Linux CI is unaffected. Fix: `write_bytes(text.encode("utf-8"))`.

## Findings by audit area

### 1. FLEX `test_id` and investigation identity

- **Sound.** `investigation:test` qualification, first-`:` split and exact case-sensitive matching all work with the v0.2.2 patterns. Neither pattern admits `:` or `,`.
- **Case.** FLEX finding ids are lowercase (`flex.flex-001.burn_time`), while `test_id` is the printed form (`FLEX-001`). So `tests=flex:FLEX-001` resolves, and `tests=flex:flex-001` is a 400 under rule 3. That is correct, but the frontend should send `finding_ids` (as §9 already says) to avoid user-typed case errors.
- **R1 (required). Make uniqueness a contract invariant, not only a request-time error** (C16). §6 answers an ambiguous test with 400, which is right as a backstop. But the property `tests=` relies on is that, within an investigation, each (test_id, quantity) has at most one measured finding, and nothing enforces it. Add it to S11 (or a new rule) and enforce it in the loader (reject the file) and the derivation tests, so ambiguity fails closed at load rather than surfacing per request. The staged 40 already satisfy it (C2).
- **R4 (recommended).** In the same rule, require that all measured findings of one test carry the same `test_outcome` and the same `conditions` (C15). Today a selection could mix two findings of "one" test that disagree, and nothing would notice.

### 2. Exact finding selection and ambiguous identities

- §6's table is complete for the cases the data can produce. Mutual exclusivity, the duplicate rule, the single-row rule and the limit of 50 are all reasonable.
- **R5 (recommended).** "Exactly these findings, in this order" conflicts with the engine's ordering (C10). The implementation must bypass `_select`'s sort when `finding_ids` or `tests` is used, so §9's claim that "the decision functions are untouched" needs that qualifier. N12 already tests order; keep it.

### 3. S9, S10 and S11 compatibility

- **S9:** compatible (C4). Exclusion-dependent findings can only appear as `excluded` measured rows (interpretations are a 400), with value `null` and no printed number. Transitive S9 is unaffected because interpretations never become rows.
- **S10:** the staged data is complete (C12, C13), and selection does not touch notes. **But see R2:** compare rows hide the notes.
- **S11:** compatible. `tests` requires identity, and legacy investigations get a 400 with a pointer to `finding_ids`.

### 4. Excluded, missing and rejected evidence

- The handling matches the engine:
  - `excluded`, `not_reported` and `not_applicable` rows are accepted with a null value and make the selection non-comparable;
  - rejected files give a 400 with the rejected-entries header (N10, N11).
- `not_selected` (see 5) should say which of the unselected rows were excluded or missing (C6).

### 5. Protection against cherry-picking

`selection.not_selected` as a single integer is **not adequate**:
- **Scope.** It counts only within the investigations of the selected rows. A user who selects two rows from investigation A never learns that investigation B holds the same quantity.
- **Content.** It does not say what was left out. With C6's mix, "8 not selected" can hide an excluded value and a missing one.
- **R2 (required) belongs here as well.** The only selections that can ever be comparable on the staged data (C3) are FLEX-004, -005 and -006. Those are **calibration runs** (Figure 8–10 captions) carrying contamination, early-imaging and calibration cautions (2–3 per finding). A `comparable: true` response would show none of them (C5). Selection must not turn caution-laden rows into an unqualified "comparable".

**R2 (required):** for every selection response, either
- (a) add to each row a read-only list of its caution and exclusion flag ids (or a `has_curation_notes` flag) in `comparison.schema.json`, or
- (b) require in the contract that the client fetch and display each selected finding's `curation_notes` before showing a comparable result. Then add an oracle that a comparable selection response is never rendered without them.

Option (a) is the safer one, because it is checkable server-side.

**Recommended answer to decision 2:** list the unselected finding ids with their `value_status`, and count across **all** loaded investigations that hold the quantity. For example, "2 of 10 in `flex` selected; 8 not selected (6 reported, 1 not reported, 1 excluded); 0 in other investigations".

### 6. Outcome condition 5 (visible-flame extinction diameter)

- **R3 (required).** `contracts/outcomes.json` condition 5 (Member 5, confirmed): "compare it only between Extinction rows, or require a caution on such Findings (recommendation for B3)". The engine does neither. Two Disruption rows of `visible_flame_extinction_diameter` come out comparable (C11).
- On the 40 staged Findings this is unreachable, because FLEX-001 is the only Disruption test with a reported diameter. Selection, and FLEX rows beyond FLEX-010, make it reachable.
- PR #38 must say how selection honours condition 5. Recommended: **fail closed**, with an S5 reason whenever the quantity is `visible_flame_extinction_diameter` and any row's `test_outcome` is not `Extinction`. That is an S5 extension and needs Members 1, 2 and 5. The same gap exists today in whole-investigation compare (PR #37).

### 7. Compatibility with the 40 staged FLEX Findings

- **Compatible.** The data loads cleanly (C1), identities are unique (C2), S10 is complete (C12, C13), and the derivation is reproducible byte for byte (C14). Whole-investigation compare stays non-comparable for all 4 quantities, exactly as §1 states (C3).
- **Practical yield:** under exact equality, selection can only ever make the FLEX-004/005/006 methanol calibration runs comparable (C3). That is a small and caution-heavy surface, which is why R2 matters.
- **Decisions 4 and 5 interact with this data.** FLEX-004, -005 and -006 have `flow_velocity_mm_s`, `flow_configuration` and `sample_geometry` null on every row. Under the stricter "null on every row" mode (decision 5), **no FLEX selection would ever be comparable**. Exact pressure equality (decision 4) is also what separates FLEX-002 and FLEX-003 (762 and 764.2 mmHg) from the 760 mmHg group. Decide 4 and 5 together with this proposal, with Member 5, since they determine whether the feature yields anything for FLEX.
- **Registration stays blocked** by PR #31's own gate test (open gates and unapproved condition decisions listed above). Nothing here changes that.

## Required corrections (before the v0.3 contract PR)

| # | Correction | Owner |
|---|---|---|
| R1 | Contract invariant: at most one measured finding per (investigation, test_id, quantity), enforced by the loader and derivation tests; the request-time 400 stays as a backstop | Members 1 (B1), 3 (derivation tests); contract: 1, 2 |
| R2 | Caution visibility in selection responses (row-level flag ids, or a mandatory client display rule plus an oracle) | Members 1, 2; Member 5 on wording |
| R3 | State and enforce `outcomes.json` condition 5 for `visible_flame_extinction_diameter` (fail closed when any row is not Extinction) | Members 1, 2, 5 |

## Recommended

| # | Recommendation |
|---|---|
| R4 | Same `test_outcome` and `conditions` across all measured findings of one test (load-time invariant) |
| R5 | Qualify §9: `_select`'s ordering must be bypassed for selections; keep N12 |
| R6 | Decision 2: list unselected finding ids with `value_status`, counted across all investigations holding the quantity |
| R7 | Decide 4 and 5 together with this proposal; record that the stricter mode makes every FLEX selection non-comparable |

Also report separately to Member 1: PR #37's Windows-only fixture hashing bug (`tests/backend/conftest.py`), and PR #31's Windows path assertion.

## Recommended answers to §11 (for the owners; not decisions)

1. Adopt `finding_ids` (normative) and `tests` (convenience), but `tests` only once R1 is enforced at load.
2. No; adopt R6.
3. An error, as proposed.
4. Exact equality for v0.3; a tolerance only from Member 5, with a citation. Decide with 5 (R7).
5. Together with this change (R7).
6. 50 is fine.

## Blockers

- PR #38 is a draft proposal; v0.2.2 (PR #17), B1 (PR #11/#26) and B3 (PR #37) are not merged into `main` (`db916a1`).
- R1–R3 need owner decisions, and R3 needs Member 5.
- FLEX registration (PR #31) is gated: PR12, PR17, S10-REGISTRATION, Q3, B1-S11, F042-NOTE, plus three condition decisions.
- Nothing here is a formal approval. Member 3's formal review of the v0.3 contract PR is a separate act by the account holder.
