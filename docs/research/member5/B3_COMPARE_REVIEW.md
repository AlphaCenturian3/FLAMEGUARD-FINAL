# B3 comparability (PR #37) and test selection (PR #38): Member 5 scientific QA

**Status:** review record only. This is **not an approval** of PR #37 or PR #38. It closes no gate. Q3, G7, S10(d), the F042 note regression and the TARS B6/T1 runtime gate all remain open (section 5).

Date: 2026-11-15. Executor: Member 5's Claude Code session, operated by Member 5.

## 1. Heads reviewed

| PR | Head | Role |
| --- | --- | --- |
| #37 B3 engine (draft) | `17dab2dec3220c8b6d769b53ac7a5f8ec159d5f3` | Member 1; stacked on #26 `b13ab40` |
| #38 test-selection proposal (draft) | `cb9c4b8ab9c20bf74633eb60455b5ce1afb966cd` | Member 1; contract v0.3 candidate |
| #31 FLEX registration candidate (draft) | `740b90137ee7d45832a7148b6e0ca131cec065c5` | Used read-only for a local dry run; nothing registered |

Review comments (not approvals):
- PR #37: <https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/37#issuecomment-6898944205>
- PR #38: <https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/38#issuecomment-6898950711>

**Contract status note:** B3 implements contract **v0.2.2**, but v0.2.2 (PR #17) is still an open draft with no reviews. The merged contract is v0.2.0 (`f7cef55`). The Member 5 reference therefore keeps the v0.2.2 outcome rules opt-in (section 4).

## 2. Confirmed defects in PR #37 (reproduced at `17dab2d`)

| Id | Severity | Defect | Reproduction (synthetic) | Proposed fix |
| --- | --- | --- | --- | --- |
| D2 | Medium | Reasons format numbers with `:g` and leave strings unquoted, so distinct values print identically, and rows are not named | pressures `101.32501443539999` vs `101.3250144354` give "differs across rows: 101.325, 101.325"; `0.21` vs `0.2100001` give "0.21, 0.21"; `"Methanol"` vs `"Methanol "` | Print exact values (`repr` / JSON), grouped with their row ids |
| D3 | Medium | A rejected investigation is described as having "no measured finding". An unfiltered request can return `comparable: true` while the rejection appears only in a header | `tamper["ds-b"]` with `investigation_ids=inv-a,inv-b`; three investigations with inv-c rejected and no filter | Add a reason naming the rejection (fails closed; no schema change) |
| D5 | Low | Direct engine calls accept NaN/±inf as reported values | `value=nan`, `value=inf` give `comparable: True` | `math.isfinite` in `_is_number` |
| D4 | Low–Medium (coordinated decision) | Two findings of the same (investigation, test_id, quantity) are compared as independent tests. PR #38 treats this case as an error | same `T-1`, both `Extinction`, give `comparable: True` | Loader uniqueness rule (preferred), or a B3 reason as an interim |
| D10 | Low (tooling) | `tests/backend/conftest.py` writes fixtures with `write_text` (CRLF on Windows) but hashes LF text. Origin `5e579f3` (PR #18), inherited by #26 and #37 | Windows: 67 failed / 466 passed; with `write_bytes`: 533 passed | Fix in #18 or #26 |

Verified as passing: S9 (no excluded or missing value in rows, reasons or logs, including the FLEX-010 excluded burning rate in the #31 dry run); S11 (mixed identity across investigations refused; within an investigation it is enforced by #26's loader); S5 decisions (section 4).

## 3. Scientific limitations (contract level, not B3 defects)

1. **Null on every row.** Under v0.2.2, a condition null on every row gives no reason. In the FLEX 004/005/006 subset, `flow_velocity_mm_s`, `flow_configuration` and `sample_geometry` are null on every row, and the response does not disclose this.
2. **Unmodelled covariates.** S5 cannot see initial droplet diameter (a quantity), extinction diameter, ignition, facility, residual gravity or test duration. The same outcome is necessary but not sufficient. FLEX "Extinction" burn times end at flame extinction, not at burnout.
3. **Exact equality** is kept on purpose (Member 5 sets no tolerance). The cost: FLEX-001/002/003/007/008 (757.7–764.2 mmHg) can never be paired.
4. **The test selector (#38) makes `comparable: true` reachable on real data for the first time.** The only FLEX like-for-like set is FLEX-004/005/006, with initial diameters 2.06 / 1.92 / 2.54 mm.

Recommendations sent to PR #38 (proposals that need owner approval): `eligible_not_selected` and `not_selected_ids` (E1); `unchecked_conditions` and a fixed `scope` statement in the API response (E2); rejection and duplicate handling consistent with B3 (E3/E4); exact equality kept; strict core defined per experiment class (droplet: gravity, fuel, O₂, pressure, diluent), not requiring `flow_configuration` for FLEX droplets.

## 4. Member 5 reference correction (D11) and differential check

`research/comparability.py` compared condition values by `repr`, so `760` and `760.0` (and `0` and `-0.0`) "differed". B3 was right. Changes:

- Numbers are compared by numeric value. Equality stays exact (no tolerance), text is compared exactly, a number never equals text, and a non-finite number equals nothing.
- A reported value must be a finite number.
- Reasons print each distinct value with `repr`.
- The v0.2.2 test identity and outcome rules (plus S11 "an outcome needs a test") are available as `outcome_rules=True`. The default stays the merged v0.2.0 S5 until PR #17 is approved.
- Strict mode is unchanged and still labelled a proposal. Its core set is flagged as under revision (experiment class).

Tests: `tests/research/test_research_comparability_v022.py` (760 vs 760.0, 0 vs -0.0, no-tolerance cases, outcome mismatch, missing outcome, outcome without test, excluded/not_reported/not_applicable, non-finite values, null conditions in S5 vs strict).

Differential results, recorded seed `20261115`:

| Check | Cases | Comparable | Disagreements |
| --- | --- | --- | --- |
| Reference (`outcome_rules=True`) vs independent brute-force S5 (runs in CI) | 5,000 | 445 | 0 |
| Reference (`outcome_rules=True`) vs B3 at `17dab2d` (runs where `flameguard.compare` is importable; skipped otherwise) | 20,000 | 1,822 | **0** |
| *Previous* reference (repr) vs B3, conditions only, same seed | 20,000 | — | 332 |

## 5. Evidence gates: still open (not claimed complete)

| Gate | What remains | Owner(s) |
| --- | --- | --- |
| **Q3** source spot check | The executor's 100 % check covers the CSV transcription and the 45 flags, not the derived **Findings**. Still needed: a spot check of the final registered FLEX Findings (values, exact kPa products, `test_id`/`test_outcome`, `value_status`, notes, quotes) pinned to the registration SHA; a recorded seed and a sample of at least max(5, 10 %); a signed entry in `docs/verification/source_spotcheck.md` (path absent on main `db916a1`); **Member 2 as second checker**. S-1 and S-3 remain blocked on PSI data (open, not mismatches). | M5 (check), M2 (second checker), M3 (fixes) |
| **G7** vocabulary and units | Canonical exact-decimal mmHg→kPa conversion pinned by tests on all stored values; storage and display rule; `flow_configuration` null; fuel naming (`Heptane` vs `n-heptane`); frozen diluent string format (`N2 0.79`, `CO2 0.7; N2 0.09`). Under exact equality these strings *are* the comparability key. Member 2's written confirmation is pending. | M1 + M2 decision; M3 data |
| **F042** exclusion note | At #31 `740b901` the note is value-free and correctly attributed. Still needed: registration approval; a regression test that the excluded finding's `statement`, notes, locator and `uncertainty` never contain the printed value (`.37`, `0.37`, with or without a unit). The F042 flag row's own reason text contains `.37`. | M3 (derivation), M5 (independent test) |
| **S10(d)** quote verification | Verification of each referenced flag quote and page against the registered source, logged for the **registered** Findings (PRs #23/#25 tooling). | M3 / M5 |
| **TARS B6/T1** runtime S9 | Exclusion-dependent findings must never reach the answer generator as evidence. Untested at runtime; mandatory before any B6 or T1 merge. | M1 (build), M5 (independent test) |

Not done in this review: no measured data registered, no ranking weights approved, no ranking activated, no PR approved or merged, no gate modified.
