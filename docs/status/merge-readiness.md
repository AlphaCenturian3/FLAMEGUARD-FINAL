# Merge-readiness matrix (snapshot 2026-11-15, updated after the Flame Lab, Signal Analysis preparation and B3 drafts; written by Member 1 for Command Center)

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
| #9 | pytest pythonpath | main | bf3c1e4 | green | Member 5 (on bf3c1e4) | — | **MERGED** (squash) as `db916a1` on 2026-11-15; post-merge CI on main green (3.11, 3.12, secrets-and-raw-data) |
| #10 | jsonschema runtime dep | main | 849fb8a | green | none (Member 3 review requested earlier, pending) | Member 3 approval on 849fb8a; CC authorization | **review only**: merges cleanly onto `db916a1`, 265 passed, ruff clean |
| #11 | B1 strict loader | #10 | e6f51f8 | green | none | Members 3 and 5; #10 merged first | review, #10 |
| #12 | D5 FLEX vocabulary (v0.2.1) | main | 1f52b57 | green | Members 1, 2 | Member 3 adopts Member 5's two corrections (prepared in draft **#28**, commit 23cd7ad, text only, 279 tests; cherry-pick instructions in its description), then Member 5 re-review and Members 1 and 2 re-approve on the new SHA | Member 5 changes requested |
| #17 | contract v0.2.2 test identity and outcome | #12 | c289e74 | green | none | Members 2, 3, 5 (contract rule: 1 and 2, plus 3 and 5); rebase on corrected #12 | #12, reviews |
| #18 | B2 evidence explorer | #11 | 5e579f3 | green | none | B1 chain merged; independent review of the API | #11 |
| #26 | S11 in loader + staging isolation | #18 (+ #17 merged in) | b13ab40 | green | none | #11, #12, #17, #18 merged first; Member 5 independent S11 test | whole chain |
| #23 | S10 source-passage validation tool | main | 99cdb2c | green | none | one independent approving review, preferably Member 3 (provenance/code); then **squash merge** per CONTRIBUTING; no self-approval. Verified: head, CI (2 runs), 44 tests with the PDF, scope 2 files. Not merged: no approving review | review |
| #25 | S10 registration (14 Sources, 17/17) | #23 | 8bbafad | green | none | #23 merged; Member 3 (owns the manifest) and Member 5 (Q3 quote audit) | #23, reviews |
| #24 | FLEX derivation scaffold, G7, F042 curated note, audit | #17 (includes #25) | see PR (this file lives on this branch) | green | none | #17 and #25 merged; Member 5 review of staged output (Q3) and of the F042 note (written, with the reviewed SHA); Member 3 | #17, #25, Q3, F042-NOTE |
| #13 | S10 proposal (docs) | main | 51d891f | n/a | none | stays open. Close as superseded **only after #25 merges and 17/17 registration is verified**, with a link to #25 for audit history | #25 |
| #15 | derivation design (docs) | main | b6b55d3 | n/a | none | Members 1, 2, 3, 5 review; partly superseded by #24 | review |
| #14 | TARS requirements (docs) | main | 67edf2f | n/a | Member 1 | Members 2/3/5 as the doc owner requires | review |
| #2 | frontend dashboard | main | c48eaf6 | n/a | Member 1 | Member 5 scientific review | review |
| #28 | PR #12 wording corrections (draft, text only) | #12 | 23cd7ad | green | none | Member 3 cherry-picks (or adopts the wording); Member 5 re-review; Members 1+2 re-approve on the new #12 head. Not to be merged itself | Member 3 |
| #29 | frontend: contract v0.2.2 compatibility, group by `test_id`, printed test outcome | #21 | a5cc826 / 9655a57 | green (backend jobs only); browser 89/89 locally | none | Member 2 review; Member 5 wording review; #2 and #21 merged first | #2, #21, reviews |
| #30 | tests: registration-independent derivation tests + registered-state integrity tests (deliberate gate red light) | #24 | see PR | pending | none | #24 merged first; Member 3 review | #24 |
| #31 | **REGISTRATION CANDIDATE** (3 files: 2 derived files + 2 manifest entries) | #30 | see PR | **red by design** until every gate closes | none | all of steps 1-5 of the integration plan, Members 3 and 5 (and 1) | **gates**, #30 |
| #32 | **B7**: dashboard served by the backend on one origin; `python -m flameguard serve` | #26 | dcb5f48 | green | none | independent review (backend, plus Member 2 for the frontend side); #26 chain merged first | #26 chain, review |
| #33 | preview: registration-aware smoke (empty and registered scenarios) | #19 | 57fb86f | green | none | review; #19 first | #19 |
| #21 | frontend: rejected-files warning, footer | #2 | 3c9ce44 | green (backend jobs only) | none | Member 2 review, Member 5 wording review; #2 merged | #2, reviews |
| #16 | CI frontend browser tests | main | e3957bf | green | none | Member 2 approval | review |
| #8 / #19 | dev preview / B2 preview | main / #8 | d0133e7 / f478d9c | green | none | reviews; #19 serves unmerged #18 and #21 (pinned) | not for production |
| #20 | Blender illustrations | main | cdf4b94 | green | none | Member 5 communication review | review |
| #34 | **Flame Lab**: standalone illustrative 3D flame at `#/flame` (vendored three.js 0.170.0, MIT) | #29 | 307a22d | green (backend jobs only); browser 102/102 locally | none | Member 2 (frontend) review; Member 5 review of the disclaimer and every explanatory sentence; team agreement to vendor three.js; #2, #21, #29 merged first | #29 chain, reviews |
| #36 | Flame Lab fix: idle under reduced motion (real-GPU acceptance finding) | #34 | 13bc16d | green (backend jobs only); browser 103/103 locally | none | reviewed together with #34 | #34 |
| #35 | Signal Analysis preparation: decision record (PENDING), proposal, pre-event gate test. **No analysis code or data** | main | 80c20d9 | green | none | docs review; see the open gates below | gates |
| #37 | **B3** comparability engine and unmounted `/api/compare` handler. **Served endpoint stays 501** | #26 | 17dab2d | see PR | none | Member 5 independent scientific validation (S5, S6 scope, wording); code review; #26 chain merged first; then a separate reviewed change to mount it | #26 chain, validation |
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

## Shortest dependency-safe merge sequence (2026-11-15)
Each step needs its listed review and an explicit Command Center authorization; nothing here is approved. Squash merges per CONTRIBUTING.

| Order | PRs | Technically passing today | Independent approval still needed |
|---|---|---|---|
| 1 | #9 | **merged** `db916a1`, main CI green | — |
| 2 | #10 then #11 | yes | Member 3 (#10); Members 3 and 5 (#11) |
| 3 | #12 (with #28's wording) then #17 | yes (#28: 279 tests) | Member 3 adopts #28; Member 5 re-review; Members 1+2 re-approve; #17: Members 2, 3, 5 |
| 4 | #18 then #26 | yes | independent backend review; Member 5 S11 test |
| 5 | #23 then #25 | yes (PDF-verified) | Member 3 (#23 provenance/code); Members 3 and 5 (#25) |
| 6 | #2, #21, #29, #16 | yes (89/89 browser) | Member 5 scientific review of #2; Member 2 for #21/#29/#16 |
| 7 | #32 (B7) | yes (15 mechanics + 7 browser + module crawl; both full-app trees 24/24) | independent review |
| 8 | #24 then #30 | yes | Members 3 and 5 |
| 9 | **Science gates** | the audit passes (0 failures, 96/96 quotes) | **Member 5: Q3 review; written F042-NOTE approval with the exact note and reviewed SHA; G7 condition decisions approved by an independent scientist** |
| 10 | #31 (registration) | **red by design** until step 9 closes every gate | Members 3, 5 and 1 |
| 11 | #8/#19/#33 re-pinned to merged commits; owner demo docs updated for live evidence | #33: empty 60/60, registered 72/72 | review |

Not on the critical path: #13 (close as superseded after #25 is verified), #14, #15, #20 (Blender), #3, #6.

## State after the #9 merge (2026-11-15)
- `main` = `db916a1` (#9 squash). Post-merge CI green.
- Every branch based on `main` still merges cleanly onto it (checked with `git merge-tree`, nothing modified): #10, #23, #20, #16, #8, #12, #2, #13, #15, #14.
- **#10 review summary (for Member 3, when available):** two files. `pyproject.toml` moves `jsonschema>=4.23` from the `dev` extra to the runtime `dependencies` (the B1 loader in #11 validates every evidence file against the contract schemas at runtime, so a production install without it would fail). `tests/test_dependencies.py` pins that it is a runtime dependency and declared only once. No code change, no data change. Verified: CI green on 3.11 and 3.12; merged onto `db916a1` locally 265 passed, ruff clean. Reviewer to confirm: the dependency belongs at runtime, and the version floor `>=4.23` (Draft 2020-12 + `referencing`) is acceptable.

## State after the visual and B3 phase (2026-11-15)

Nothing merged, deployed or registered. `main` is still `db916a1`.

### Flame Lab (#34, fix in #36)
- Accepted on the owner's Mac in Chrome 157 on the real GPU (ANGLE Metal, Apple M1 Pro), desktop 1440x900 and mobile 390x844: 120 frames per second in a visible window and 60 headless, no frame over 33 ms, 31 draw calls, about 13,000 triangles. Cold load of the page with the scene: 46 requests, 944 kB (three.js 740 kB, fetched only on this route), scene ready in 0.3 to 0.4 s warm and 1.2 to 2.3 s on first launch. The WebGL fallback loads 182 kB and no three.js.
- One defect found and fixed in #36: under reduced motion the still picture was redrawn every frame. No other visual change was needed.
- Not tested: Windows, Safari, Firefox, a real phone, low-end GPUs.
- Review needs: Member 2 (frontend), Member 5 (wording and disclaimers), team agreement on vendoring three.js.

### Signal Analysis (#35): open gates
The FFT/STFT code and BASS-II outputs exist only in an earlier private repository. Master spec 2.5 forbids copying them until all of these are recorded in `docs/decisions/pre-event-signal-analysis.md`:
1. Organizer ruling on pre-event work.
2. The owner's written license for the listed files.
3. An independent check of the content and license audit.
4. Team agreement to add NumPy and SciPy.
5. A rights decision on the series reconstructed from NASA video.
6. Member 5's view on showing a result that did not replicate.

`tests/test_pre_event_gate.py` fails any branch that adds the feature before the record is approved.

### UTF-8 fixes: adopted at the owning layer
Defect: `subprocess(..., text=True)` without an encoding crashed under the C locale and garbled text on Windows. Fixed, with regression tests, in #32 (`dcb5f48`), #16 (`e3957bf`), #8 (`d0133e7`), then carried up to #19 (`f478d9c`) and #33 (`57fb86f`). The three temporary fix branches are superseded and kept, not deleted.

### B3 (#37)
- Implemented against contract v0.2.2 on top of #26: S5 (values, conditions, outcomes), S9 (excluded and missing values always null, measured rows only), S11 through the loader. Outcomes are copied from `test_outcome`, never inferred.
- 533 tests pass on Python 3.12, 3.11 and under the C locale. The decision agrees with the contract's outcome oracle and an independent S5 oracle on 3,804 combinations; 17 of 17 engine mutations are caught.
- **Not served.** `app.py` is unchanged and `/api/compare` answers 501. Mounting it is a separate reviewed change after Member 5's validation.
- Open scientific points for Member 5: the contract has no way to select individual tests, so one investigation with heterogeneous tests (the FLEX candidate) is never comparable as a whole; conditions that are null for every row are compared (v0.2.2); condition equality is exact.

### Latest confirmed integration tests
| What | Result |
| --- | --- |
| Full stack on `db916a1`, empty tree (disposable local branch) | 697 passed |
| Full stack on `db916a1`, candidate tree (disposable local branch) | only the deliberate registration gate test fails |
| Preview smoke, empty scenario (#33) | 60/60, UTF-8 and C locale |
| Preview smoke, registered scenario (#33, candidate tree, local only) | 72/72, UTF-8 and C locale |
| Preview smoke with the Flame Lab frontend | 60/60 |
| Frontend browser tests with the Flame Lab and its fix | 103/103, UTF-8 and C locale |
| B3 branch | 533 passed (3.12, 3.11, C locale) |

