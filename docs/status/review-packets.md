# Review packets (SHA-specific), 2026-11-15

For reviewers, when available. Nobody has been contacted. Each packet names the exact head to review, what changed, what was verified, and the **decisions that need an independent approval** (separate from "the tests pass"). Integration evidence: a disposable tree built from `main` at **`db916a1`** plus #32, #29, #30 (which carry #10, #11, #12, #17, #18, #26, #23, #25, #24 and #2, #21) and #28's wording: **697 passed, 0 failed** in a UTF-8 and in a C locale; lint clean; provenance passes; PDF verifier and S10 tool pass; 89/89 browser tests. The same tree plus #31 passes everything except the deliberate registration-gate test.

**Defect found in that run (fixed on isolated branches; reviewed heads unchanged):** child-process output (Chrome, Node, pip) was decoded with the locale's encoding, so the browser tests and preview smoke crashed under a C locale and would compare mojibake on Windows (cp1252). Fix branches, to be folded into the affected PRs only with authorization:
| Affected PR(s) | Fix branch | Head |
|---|---|---|
| #32 (B7 browser tests) | `fix/b7-utf8-subprocess` | `dcb5f48` |
| #8 / #19 / #33 (preview smoke, since #8) | `fix/preview-utf8-subprocess` | `7385084` |
| #16 (CI browser runner) | `fix/ci-runner-utf8` | `e3957bf` |
Not changed (ASCII-only output, low risk, noted): `tools/check_data_provenance.py` on `main` (git file list) and three calls in #17's tests (Python scripts printing ASCII).

## Backend and contract chain
| PR @ head | Scope | Verified | Independent decision needed |
|---|---|---|---|
| **#10** @ `849fb8a` | `jsonschema` moves to runtime deps; 1 test | CI green; merges onto `db916a1`, 265 passed | Member 3: runtime dependency and `>=4.23` floor acceptable |
| **#11** @ `e6f51f8` | B1 strict, fail-closed loader (6 files) | mutation-checked; 3.11 and 3.12 | Members 3 and 5: the fail-closed rules (whole-file rejection, cascade, S9 transitive) match the contract; Member 5: independent S9 test |
| **#12** @ `1f52b57` (Member 3's) + **#28** @ `23cd7ad` | FLEX vocabulary v0.2.1; #28 = Member 5's two wording corrections, text only | #28: 279 passed; merges into v0.2.2 cleanly | Member 3 adopts #28; **Member 5 re-reviews the corrected text**; Members 1+2 re-approve on the new head |
| **#17** @ `c289e74` | v0.2.2 test identity and outcome, S11, confirmed outcome list | contract tests | Members 2, 3, 5 (contract rule); outcome list stays Member 5's confirmed P1 decision |
| **#18** @ `5e579f3` | B2 evidence explorer API | 18 mutations caught | independent API review |
| **#26** @ `b13ab40` | S11 in the loader; staging-isolation tests | loader agrees with the oracle on 64 patterns; real staged output never served | Member 5: independent S11 test |
| **#32** @ `aa50837` | B7: dashboard served on one origin; `python -m flameguard serve` | 15 mechanics tests, module crawl, 7 browser tests; 24/24 in both full-app trees; clean venv | independent review; fold in `fix/b7-utf8-subprocess` first |

## Source registration and derivation
| PR @ head | Scope | Verified | Independent decision needed |
|---|---|---|---|
| **#23** @ `99cdb2c` | S10 validation tool | 44 tests with the PDF; 15 mutations | **Member 3** (provenance/code); then squash |
| **#25** @ `8bbafad` | 14 Sources, one per (page, exact quote); 17/17 passages | PDF-verified; manifest additions only | Member 3 (manifest owner); **Member 5 Q3 quote audit**; owner-assigned section titles for p.16/p.17 |
| **#24** @ `d149d1c` | staging-only derivation, F042 curated note, G7, audit, docs | 40 staged; audit 0 failures, 96/96 quotes | Members 3 and 5; the three G7 condition decisions need **independent** approval (today `owner_provisional`) |
| **#30** @ `654da28` | registration-independent tests; registered-state integrity tests | 526 passed; 8 tamper cases caught | Member 3 |
| **#31** @ `740b901` | registration candidate: 2 data files + 2 manifest entries | everything passes except the gate test, **by design** | **Member 5: Q3 review of the 40 Findings; written F042-NOTE approval with the exact note and reviewed SHA**; Members 3, 5, 1 |

## Frontend, CI, preview, illustrations
| PR @ head | Scope | Verified | Independent decision needed |
|---|---|---|---|
| **#2** @ `c48eaf6` (Member 2's) | dashboard | approved by Member 1 | **Member 5 scientific review** |
| **#21** @ `3c9ce44` | rejected-files warning; footer version | 71/71 | Member 2; Member 5 wording |
| **#29** @ `9655a57` | v0.2.2 compatibility; group by `test_id`; printed outcome | 89/89; 12 mutations | Member 2; Member 5 wording of "Test end as printed" |
| **#16** @ `ed4ccaf` | CI browser runner | 20 tests | Member 2; fold in `fix/ci-runner-utf8` first |
| **#8** @ `993fdc4`, **#19** @ `3ed4aed`, **#33** @ `0dcf110` | dev preview; registration-aware smoke | empty 60/60, registered 72/72 | review; fold in `fix/preview-utf8-subprocess` first |
| **#20** @ `cdf4b94` | Blender illustrations | captions enforced in the script | Member 5 communication review |
