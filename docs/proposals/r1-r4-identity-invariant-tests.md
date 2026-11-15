# Proposal: regression tests for identity invariants R1 and R4 (discussion only)

**Status:** test-only draft from Member 3, 2026-11-15. **The invariants are NOT enforced.** These tests document the gap found in the PR #38 audit (`docs/verification/pr38_member3_audit.md` on branch `review/pr38-member3-audit`). Nothing here changes the loader, the contract, any data or any registration gate.

- **R1** (audit: required; **subject to owner approval**): within one investigation, at most one measured finding per (`test_id`, `quantity`).
- **R4** (audit: **recommendation**): all measured findings of one test share one `test_outcome` and one `conditions` object.

**Base:** PR #37 head `17dab2d`. That's the latest B1 loader (including PR #26's S11 checks) and contract v0.2.2. File: `tests/data/test_identity_invariants_r1_r4.py` (`tests/data/` is Member 3's test area).

## How the tests are built

- **Synthetic repositories at test time.** Each test builds a minimal valid repository in `tmp_path`:
  - the branch's own `contracts/` and `tools/check_data_provenance.py`;
  - one findings file per investigation, an investigations file, and a manifest with byte-exact SHA-256 (written with `write_bytes`, so it is portable to Windows).

  Records are labelled SYNTHETIC and never touch the repository's `data/`, and a test checks this. They carry no `fixture: true`, because the loader rejects fixtures by design; they exist only in the temporary directory.
- **An independent oracle**, `identity_invariant_violations()`, written only for these tests (not production code), states R1 and R4 precisely. Each proposed-behaviour test first asserts that the oracle sees the violation, so a pass or fail is never down to a harness mistake.
- **Proposed-behaviour tests** are `xfail(strict=True)`. They fail today, which is the documented gap. If the loader enforces a rule, strict xfail turns the unexpected pass into a failure, so the marker must be removed in the same change.

## Expected versus actual (B1 loader at `17dab2d`)

| Test | Expected under R1/R4 | Actual today |
|---|---|---|
| `test_r1_duplicate_test_quantity_rejects_the_file` ×3 (second finding reported / `not_reported` / `excluded`) | File **rejected** whole; 0 findings loaded; the reason names both finding ids and `T-1` | **Accepted**, `reasons=()`, `loaded=5` (xfail) |
| `test_r4_conflicting_outcomes_within_a_test_reject_the_file` | Rejected; the reason names `T-1` | **Accepted**, `reasons=()`, `loaded=4` (xfail) |
| `test_r4_conflicting_conditions_within_a_test_reject_the_file` ×3 (value differs / text differs / null vs reported) | Rejected; the reason names `T-1` | **Accepted**, `reasons=()`, `loaded=4` (xfail) |
| `test_r1_rejection_is_isolated_and_reported` | Only the bad file rejected; the other investigation loads; the report names the entry, "R1" and the duplicate id; the investigations file warns | **Nothing rejected**: `rejected == []` (xfail) |
| `test_harness_baseline_is_accepted` | Consistent data loads (4 findings) | Passes |
| `test_findings_without_test_identity_are_outside_r1` | Findings with no `test_id` are out of R1's scope and load | Passes |
| `test_oracle_detects_r1_duplicates` ×2 | The oracle flags duplicates | Passes |
| `test_a_valid_investigation_loads_next_to_any_other` | Two valid investigations load (8 findings) | Passes |
| `test_staged_flex_findings_satisfy_r1_r4_and_still_load` | The 40 staged FLEX Findings satisfy R1 and R4 and all load; FLEX-010 burning rate stays exclusion-dependent | **Skipped on this branch** (the data is in PR #31). **Passes** in a checkout with PR #31's data overlaid (see below) |
| `test_synthetic_records_never_touch_repository_data` | No synthetic file under `data/` | Passes |

## Open points for the owners

1. **R1 scope:** identified tests only (proposed), so findings without `test_id` stay valid, as today.
2. **R1 includes `not_reported` and `excluded` duplicates.** A test may not hold two findings of one quantity whatever their status; otherwise an excluded row could shadow a reported one. Confirm.
3. **R4 strictness for conditions:** exact equality of the whole `conditions` object, including `null` versus reported. Confirm, or limit R4 to selected keys.
4. **Where the rule lives:** loader `_identity_reasons` (Member 1, B1) plus the derivation acceptance tests (Member 3), with a contract-text addition to S11 (Members 1, 2). The expected reason text in these tests is deliberately loose (ids and test id only), so the implementer can choose the wording.
