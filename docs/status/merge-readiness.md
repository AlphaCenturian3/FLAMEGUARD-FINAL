# Merge-readiness matrix (snapshot 2026-11-15, updated after the frontend-compat, test-fix and registration-candidate drafts; written by Member 1 for Command Center)

Nothing here authorizes a merge. Rules used: CONTRIBUTING.md (at least one approving review; scientific work also needs the independent reviewer of spec section 4.4; contract changes need Members 1 and 2, plus 3 and 5 when a data, interpretation or ranking rule changes; nobody approves their own scientific work; a changed head SHA needs renewed review and CI). GitHub branch protection could not be read on this plan, so the documented rules above are the checkable requirement. All heads below are drafts unless noted.

## Critical path to registering the FLEX Findings

```
#9 --------------------------------------------\
#10 -> #11 -> #18 -> #26 (S11 loader, isolation) \
#12 (+ fix/pr12-wording-corrections) -> #17 ------+--> #24 (derivation, includes #25) --> registration PR (not yet written)
#23 -> #25 (S10 registration) ---------------------/            ^ needs Q3 + F042-NOTE written approval
```

## Matrix

| PR | What | Base (depends on) | Head | CI | Approvals now | Still required before merge | Blocker |
|---|---|---|---|---|---|---|---|
| #9 | pytest pythonpath | main | bf3c1e4 | green | Member 5 | Command Center authorization | none technical |
| #10 | jsonschema runtime dep | main | 849fb8a | green | none | Member 3 review; CC authorization | review |
| #11 | B1 strict loader | #10 | e6f51f8 | green | none | Members 3 and 5; #10 merged first | review, #10 |
| #12 | D5 FLEX vocabulary (v0.2.1) | main | 1f52b57 | green | Members 1, 2 | Member 3 adopts Member 5's two corrections (prepared in draft **#28**, commit 23cd7ad, text only, 279 tests; cherry-pick instructions in its description), then Member 5 re-review and Members 1 and 2 re-approve on the new SHA | Member 5 changes requested |
| #17 | contract v0.2.2 test identity and outcome | #12 | c289e74 | green | none | Members 2, 3, 5 (contract rule: 1 and 2, plus 3 and 5); rebase on corrected #12 | #12, reviews |
| #18 | B2 evidence explorer | #11 | 5e579f3 | green | none | B1 chain merged; independent review of the API | #11 |
| #26 | S11 in loader + staging isolation | #18 (+ #17 merged in) | 72a7204 | green | none | #11, #12, #17, #18 merged first; Member 5 independent S11 test | whole chain |
| #23 | S10 source-passage validation tool | main | 99cdb2c | green | none | one independent approving review, preferably Member 3 (provenance/code); then **squash merge** per CONTRIBUTING; no self-approval. Verified: head, CI (2 runs), 44 tests with the PDF, scope 2 files. Not merged: no approving review | review |
| #25 | S10 registration (14 Sources, 17/17) | #23 | 8bbafad | green | none | #23 merged; Member 3 (owns the manifest) and Member 5 (Q3 quote audit) | #23, reviews |
| #24 | FLEX derivation scaffold, G7, F042 curated note, audit | #17 (includes #25) | c827890 | green | none | #17 and #25 merged; Member 5 review of staged output (Q3) and of the F042 note (written, with the reviewed SHA); Member 3 | #17, #25, Q3, F042-NOTE |
| #13 | S10 proposal (docs) | main | 51d891f | n/a | none | stays open. Close as superseded **only after #25 merges and 17/17 registration is verified**, with a link to #25 for audit history | #25 |
| #15 | derivation design (docs) | main | b6b55d3 | n/a | none | Members 1, 2, 3, 5 review; partly superseded by #24 | review |
| #14 | TARS requirements (docs) | main | 67edf2f | n/a | Member 1 | Members 2/3/5 as the doc owner requires | review |
| #2 | frontend dashboard | main | c48eaf6 | n/a | Member 1 | Member 5 scientific review | review |
| #28 | PR #12 wording corrections (draft, text only) | #12 | 23cd7ad | green | none | Member 3 cherry-picks (or adopts the wording); Member 5 re-review; Members 1+2 re-approve on the new #12 head. Not to be merged itself | Member 3 |
| #29 | frontend: contract v0.2.2 compatibility, group by `test_id`, printed test outcome | #21 | a5cc826 / 9655a57 | green (backend jobs only); browser 89/89 locally | none | Member 2 review; Member 5 wording review; #2 and #21 merged first | #2, #21, reviews |
| #30 | tests: registration-independent derivation tests + registered-state integrity tests (deliberate gate red light) | #24 | see PR | pending | none | #24 merged first; Member 3 review | #24 |
| #31 | **REGISTRATION CANDIDATE** (3 files: 2 derived files + 2 manifest entries) | #30 | see PR | **red by design** until every gate closes | none | all of steps 1-5 of the integration plan, Members 3 and 5 (and 1) | **gates**, #30 |
| #21 | frontend: rejected-files warning, footer | #2 | 3c9ce44 | green (backend jobs only) | none | Member 2 review, Member 5 wording review; #2 merged | #2, reviews |
| #16 | CI frontend browser tests | main | ed4ccaf | green | none | Member 2 approval | review |
| #8 / #19 | dev preview / B2 preview | main / #8 | 993fdc4 / 2c82959 | green | none | reviews; #19 serves unmerged #18 and #21 (pinned) | not for production |
| #20 | Blender illustrations | main | cdf4b94 | green | none | Member 5 communication review | review |
| #3, #6 | research / CP3 evidence (Members 5 and 3) | main / feat/nasa-data-tars | 5a5a699 / a6f62af | n/a | none | not assessed in this pass | owner |

## Gates that block registering any FLEX Finding (tools/flex_derivation_gates.json)
Open: PR12, PR17, S10-REGISTRATION, Q3 (Member 5 review of the staged Findings), B1-S11, F042-NOTE (explicit written scientific approval recording the exact note and the reviewed SHA). Closed: S10-TITLES (owner-assigned descriptive titles), G7 (representation criteria A1-A7 satisfied as an owner decision: docs/decisions/g7-flex-conditions.md). `registrable` additionally requires every condition decision to be `approved`, which no one has granted.

## Test status of the staged output
40 Findings staged (31 reported, 8 not_reported, 1 excluded), 96 notes. Audit against the checksum-verified PDF: 0 failures, 96/96 quotes verbatim. Live API serves none of them (tests in #26). Staging stays staging-only.

## Future review assignments (recorded only; nobody has been contacted, no review requested, no approval implied)
| Item | Reviewer | What they are asked to do, later |
|---|---|---|
| PR #23 (S10 validation tool) | **Member 3** | Independent provenance and code review. Then squash merge per CONTRIBUTING, by whoever is authorized. |
| PR #28 (prepared #12 wording corrections) | **Member 3** | Adopt the prepared corrections into PR #12 (cherry-pick `23cd7ad`) or the equivalent wording. Member 5 then re-reviews and Members 1 and 2 re-approve on the new head. |
| **Q3** (derived Findings) | **Member 5** | Independent scientific review of the 40 derived Findings, using `~/flameguard-audit/flex_acceptance_report.json` (regenerate with `tools/audit_flex_findings.py`) and the PDF. |
| **F042-NOTE** | **Member 5** | An explicit **written** approval that records the exact curated note text and the reviewed commit SHA. Until it exists the gate stays open. |
| G7 condition decisions | an independent scientist (Member 5 or a delegate named by the owner) | Move diluent, fuel and sample-geometry representations from `owner_provisional` to `approved`. Nobody has done this. |
