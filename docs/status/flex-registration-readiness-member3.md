# FLEX registration readiness: Member 3 independent audit

**Date:** 2026-11-15. **Author:** Member 3's engineering session (data, provenance, TARS evidence).
**Status:** documentation only. **Not an approval, not a merge request.** It changes no Finding, contract schema, registration gate or comparison engine.

## 1. State checked (git refs fetched 2026-11-15)

| PR | Head | What | Merged | Contains |
|---|---|---|---|---|
| #12 | `1f52b57` | D5 FLEX vocabulary (v0.2.1) | no | — |
| #13 | `51d891f` | S10 page-coverage proposal (docs) | no | — |
| #17 | `c289e74` | Contract v0.2.2: test identity and outcome, S11 | no | #12 |
| #26 | `b13ab40` | S11 in the B1 loader, staging isolation | no | #11, #12, #17 |
| #31 | `740b901` | FLEX registration candidate (staged Findings, gates) | no | #12, #17, #25 |
| #37 | `17dab2d` | B3 comparability engine | no | #12, #17, #26 |
| #38 | `cb9c4b8` | v0.3 test-selection proposal (docs) | no | — |
| #39 | `c05b429` | R1/R4 identity-invariant tests (proposal) | no | #12, #17, #26, #37 |

`main` is `db916a1` (contract v0.2.0 + PR #4 + #9). Gate-related PRs outside this list: #11 `e6f51f8` (B1 loader), #23 (S10 tool), #25 `8bbafad` (S10 registration), #24 `5813f26` (derivation), #28 `23cd7ad` (wording corrections for #12). None are merged.

PR #31's `docs/status/merge-readiness.md` is a snapshot. Some heads in it are older than the refs above (it lists #26 `72a7204` and #24 `c827890`). Its dependency picture still holds:

```
#10 -> #11 -> #18 -> #26 (S11 loader)            \
#12 (+ #28 corrections) -> #17 -------------------+--> #24 (derivation, includes #25) --> registration PR (not written)
#23 -> #25 (S10 registration) --------------------/
```

## 2. Registration gates (PR #31, `tools/flex_derivation_gates.json`)

`registrable` is true only when every gate is closed **and** every condition decision is `approved`.

| Gate | Status | Kind | Owners (file) | What closes it |
|---|---|---|---|---|
| PR12 | **open** | missing approvals + scientific wording | 3, 5, 1, 2 | Member 3 adopts #28 on PR #12; Member 5 re-review; Members 1 and 2 re-approve on the new SHA; merge |
| PR17 | **open** | missing approvals (contract) | 2, 3, 5 | Contract approvals at the final SHA (Members 1 and 2, plus 3 and 5), after #12 |
| S10-REGISTRATION | **open** | technical (unmerged) + review | 1, 3, 5 | #23 then #25 merged; Member 3 reviews the manifest change; Member 5 Q3 quote audit |
| S10-TITLES | closed | owner decision | 3, 5 | — |
| G7 | closed | owner decision (not scientific verification) | 1, 2 | — |
| Q3 | **open** | scientific review | 5 | Member 5's written review of the staged Findings and quote audit |
| B1-S11 | **open** | technical (unmerged) | 1 | #10 → #11 → #18 → #26 merged |
| F042-NOTE | **open** | scientific review | 5 | Member 5's written approval of the exact F042 note, naming the reviewed SHA |

Condition decisions: `diluent`, `fuel_or_material` and `sample_geometry` are all **`owner_provisional`**, explicitly "not an independent scientific approval". All three must become `approved`, which needs Member 5's independent scientific review. The pressure rule (exact 0.133322387415 kPa/mmHg, unrounded) is also an owner decision.

**Open: 6 gates and 3 condition decisions.** PR #31's own gate test fails by design until they close (re-run below).

## 3. Blockers by type

**Technical (code not merged)**
- T1: B1 chain #10 → #11 → #18 → #26 (gate B1-S11). Member 1 authors; Member 3 and Member 5 reviews requested in the matrix.
- T2: S10 chain #23 → #25 (gate S10-REGISTRATION). Member 1 authors; Member 3 owns the manifest; Member 5 Q3.
- T3: Derivation #24 merges after #17 and #25.
- T4: The registration PR itself is not written yet.
- T5 (not a gate): Windows-only test defects in #37 (`tests/backend/conftest.py` hashes LF but writes CRLF) and #31 (path separator in one assertion). Already reported; Linux CI is unaffected.

**Scientific decisions (Member 5)**
- S1: Q3 review of the staged Findings (gate).
- S2: F042 exclusion-note wording, written approval with the SHA (gate).
- S3: The three condition decisions, from `owner_provisional` to `approved`.
- S4: PR #12 wording. Member 5 requested changes; #28 prepares them (see §5).

**Missing approvals**
- PR #12 (after #28 is adopted): Member 5 re-review; Members 1 and 2 re-approve on the new SHA.
- PR #17: contract approvals, Members 1 and 2 plus 3 and 5.
- #10, #11, #23, #25: reviews, with Member 3 named in the matrix for each.
- #26: Member 5's independent S11 test.

**Not registration gates, but open before compare selection (PR #38):** R1–R3 from the PR #38 audit, R1/R4 tests in PR #39, and `outcomes.json` condition 5 enforcement in B3.

## 4. Staged FLEX Findings: integrity re-verified (2026-11-15)

All checks ran in temporary worktrees; nothing was committed or registered.

| Check | Result |
|---|---|
| Regenerate with PR #31's `tools/derive_flex_findings.py` | Byte-identical to PR #31's `data/curated/findings/flex.json`, SHA-256 `1d3cf89827015e72…`; `registrable: false` |
| Regenerate with PR #24's (newer) derivation | Byte-identical, same SHA-256; `registrable: false` |
| PR #31 manifest SHA-256 for `flex.json` | Matches the file (`1d3cf89827015e72…`) |
| `tools/audit_flex_findings.py` against the checksum-verified PDF (SHA-256 `b4f6ca98…`), both heads | **passed**: 40 findings (31 reported, 8 not_reported, 1 excluded), 96 notes, **96/96 quotes verified**, 0 failures |
| Exclusion | `flex.flex-010.burning_rate_constant`: `value_status: excluded`, `value: null`, exclusion note referencing F042. The printed value appears in no note or statement |
| Cautions | 95 caution notes; every note has a `flag_ref` and a quoted source |
| Provenance | Every finding has ≥ 1 source; note source pages are printed 16, 17, 29–36 and 38. The p. 37 flags are FLEX-009 `not_available` and correctly produce no note |
| Loader acceptance (PR #37 loader, earlier today, same data) | 40 accepted, 0 rejected; only FLEX-010's burning rate is exclusion-dependent |
| PR #31 suite (excluding `tests/backend`) | 531 passed, 9 skipped, 2 failed: the Windows path assertion (T5) and the registration-gate test (fails by design) |

The audit tool's JSON report contains the printed excluded number for internal checking. It was kept in a scratch folder and is **not** committed (S9 handling note in the report).

## 5. Work Member 3 can do independently (own branches, or reviews that the account holder submits)

| Priority | Task | Why | Touches others' branches? |
|---|---|---|---|
| **1** | **Adopt PR #28's corrections on PR #12** (`contract/d5-flex-vocabulary`, Member 3's branch); run the tests; ask Member 5 to re-review and Members 1 and 2 to re-approve on the new SHA | First link of the contract chain (gate PR12). #28 keeps the required F1 sentence ("does not imply the test's recorded outcome"), adds "an absent value does not imply that extinction did not occur", and states K's sign and averaging as Appendix A.1 does. Text and tests only | No (own branch; #28 itself is not merged) |
| 2 | Technical reviews requested of Member 3: #25 (manifest change, 14 Sources, 17/17 passages; compare with draft #13), #23 (S10 tool), #11 and #10 (loader and runtime dependency) | Unblocks gates S10-REGISTRATION and B1-S11 | No (review comments only; approval is the account holder's act) |
| 3 | Member 3's contract review of #17 at its final SHA | Gate PR17 | No |
| 4 | Revise PR #39 (R1/R4 tests) on owner feedback | Prerequisite for PR #38's `tests=` mode | No |
| 5 | After #25 merges and 17/17 is verified: close #13 as superseded, linking #25 | Housekeeping (matrix) | No |
| 6 | Draft the registration-PR checklist (files, manifest entries, re-run audit, gates JSON update by its owner) without registering anything | Prepares T4 | No |

## 6. Prioritized checklist

| # | Item | Responsible | Blocks |
|---|---|---|---|
| 1 | Adopt #28 on PR #12, re-run tests | **Member 3** | PR12 |
| 2 | Re-review PR #12 wording | **Member 5** | PR12 |
| 3 | Re-approve PR #12 on the new SHA | **Members 1, 2** | PR12 |
| 4 | Contract approvals on #17 at its final SHA (after #12) | **Members 1, 2, 3, 5** | PR17 |
| 5 | Review and merge #10 → #11 → #18 → #26 | **Member 1** (author); reviews **3, 5** | B1-S11 |
| 6 | Review and merge #23 → #25 | **Member 1** (author); reviews **3** (manifest), **5** (Q3) | S10-REGISTRATION |
| 7 | Q3 written review of the 40 staged Findings | **Member 5** | Q3 |
| 8 | F042 note written approval with the SHA | **Member 5** | F042-NOTE |
| 9 | Condition decisions → `approved` (or changes requested) | **Member 5** (scientific); **Command Center** records | `registrable` |
| 10 | Merge #24 after #17 and #25 | **Member 1**; reviews **3, 5** | T3 |
| 11 | Write the registration PR; update the gates file only when each gate is truly closed | **Member 3** (data) with **Member 1** (gates owner) | T4 |
| 12 | Fix the Windows test portability defects (#37, #31) | **Member 1** | none (Windows dev only) |

## 7. Recommendation: next safe implementation task

**Adopt PR #28's two wording corrections onto PR #12** (`contract/d5-flex-vocabulary`), as a regular commit on Member 3's own branch:
- **Why it's safe:** text and tests only; no schema shape, version, unit or data change; `mm2/s` and 0.2.1 are preserved; the F1 sentence and the O2 sentence stay.
- **How:** run the full suite, schema and example validation, and the provenance check, then push.
- **After:** request Member 5's re-review and Members 1 and 2's fresh approvals on the new SHA.

It is the first link of the PR12 → PR17 → #24 → registration chain, and the only critical-path item Member 3 can finish alone.
