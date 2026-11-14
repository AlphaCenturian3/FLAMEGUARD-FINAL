# Member 5 coordination notes and decision log

**Last updated:** 2026-11-14, 20:50 UTC (scientific review gate). PR #3 is a **draft**. **Not merged, not rebased.** No shared API contract is changed by PR #3. Rankings are **disabled**.

PR #3 adds only new files:

- `backend/flameguard/research/`
- `config/research_relevance_criteria_v1.proposed.json`
- `docs/research/member5/`
- `tests/research/` and `tests/fixtures/research/`

**How decisions are recorded here.** These three things are kept apart:

| Kind | What it is | Counts as approval? |
|---|---|---|
| **Formal approval** | A member's own **Approve** review, or the exact approval comment text, at the named SHA, from their own GitHub account | **Yes**, and only this |
| **Owner response** | A comment by the authorized owner on GitHub | No. It is the owner's stated position. It is recorded word for word with a link. |
| **Coordinator instruction or decision** | Member 5's coordinator (ChatGPT), or "Command Center" decisions relayed in PR #1 | No. It is not an approval by any member. |

A request that has been posted but not answered is recorded as **AWAITING OWNER RESPONSE**. Silence is never recorded as approval.

## 0. Coordinator positions (instructions and recommendations, NOT team approvals)

| Ref | Coordinator position | Kind | Effect |
|---|---|---|---|
| A | Do not submit Member 5's CP1 approval until the roster (Member 4), C5 and Member 2's identity are resolved; each member approves personally | Instruction to Member 5 | No Member 5 approval has been submitted |
| A.1 | Coordinator guidance is not a Member 5 approval; nobody may impersonate a reviewer | Instruction | Followed |
| A.2 | The established roster includes Member 4 (QA, Testing and Judge Demo); keep unresolved until the team confirms | Coordinator position | Recorded in §2 as unresolved |
| B | Apply Member 1's six-card review now on the Member 5 branch | Instruction | Applied in `2754d91` and `a6b85f9` |
| C | Prepare Member 1's three D-01 conditions; verify the FLEX pre-dilution against the NASA report | Instruction | Done in `24f710e` and `a6b85f9` (prepared, not approved) |
| D | Request explicit decisions from Members 1 and 3; record each individually; silence is not approval | Instruction | Decision form posted on PR #3 ([comment 6883945480](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883945480)) |
| — | Ownership boundary: Member 1 production ranking and compare; Member 5 interpretation, criteria and independent research-integrity tests; Member 3 provenance and measured-data import; Member 4 integration QA (pending identity) | Recommendation | Matches the CP1 candidate except for Member 4 |

## 1. CP1 status (PR #1)

| Item | State on 2026-11-14 at 20:43 UTC |
|---|---|
| Current head | **`2ce0d53756921ba31e272c4833d6d89792e447a6`** (draft). CI green: backend 3.11, 3.12, secrets-and-raw-data. |
| Alternative head | PR #7 (Member 2's side) proposes the delta `a1e8a89` on top of `2ce0d53`. Member 1 has escalated it to Command Center; not decided. |
| What changed since `ca128d0` | `value_status: withheld`, `curation_notes`, rule **S9** (withheld findings are never ranking inputs or numeric TARS evidence). Option B, the TARS name and C2–C4 stay as before. |
| Formal approvals at `2ce0d53` | **none** (0 reviews; no approval comments). Member 1's approval comment at `ca128d0` ([6883450234](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883450234)) is **superseded**, as Member 1 states. |
| C5 (`test/qa-demo`) | Open; Member 1 states it does not block CP1 |
| Member 5 trial merge of `2ce0d53` into PR #3 | No conflicts; 279 tests passed (temporary worktree, nothing pushed) |

## 2. Roster and identities

**Roster: UNRESOLVED.** The statements differ:

| Source | Statement | Kind |
|---|---|---|
| Command Center, relayed by Member 1 on PR #1 ([6883551034](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883551034)) | "The active engineering team for CP1 is Members 1, 2, 3 and 5. There is no active Member 4." | Coordinator decision |
| Member 5's coordinator | The established roster includes Member 4 (QA); keep unresolved until the team confirms | Coordinator position |
| `buihhlong-a11y` on PR #1 ([6883703493](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883703493)) | Asks the team to reply "Confirmed: there is no Member 4…" or name Member 4 | Request |
| Member 3 on PR #4 ([6883924995](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6883924995)) | Addresses "**Member 4 (QA):** Please inspect the data tests and verifier…" | Implies Member 4 exists |

No member has confirmed the roster from their own account, and no account has claimed Member 4. No role is assigned to the pending invitee.

| Member | Account | Identity evidence | Formal CP1 approval at `2ce0d53` |
|---|---|---|---|
| 1 | `AlphaCenturian3` | Designated by coordination | none (re-approval pending) |
| 2 | not confirmed | `buihhlong-a11y` says approval "will come from the Member 2 account holder personally" | none |
| 3 | `huyenthoai272008` | Self-identified in PR #4 | none |
| 4 | not established | — | not in the approval table |
| 5 | `16trtuoiloz-ducdo` | Author of PR #3 | none (withheld per instruction A) |

## 3. Member 1 decision records

Request posted: [PR #3 comment 6883945480](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883945480) at head `22bbd3f`. Earlier owner responses come from [comment 6883406826](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883406826) (reviewing head `9b6348c`). Quotes below are exact, with markdown emphasis removed.

| ID | Owner | PR / SHA | Evidence | Exact owner response | Approval status | Implementation consequence | Remaining blocker |
|---|---|---|---|---|---|---|---|
| M1-C1 ventilation-flow | M1 | #3 / `2754d91` | 6883406826 | "accept as R3, once Member 3 curates m5-bass2-flow-flareup as a measured qualitative finding" (on the earlier wording) | Revised wording: **AWAITING OWNER RESPONSE** | `review_status: member1_changes_applied` | M1 confirmation; M3 curation |
| M1-C2 detection-monitoring | M1 | #3 / `2754d91` | 6883406826 | "accept with change" | Revised wording: **AWAITING OWNER RESPONSE** | as above | M1 confirmation; M3 curation |
| M1-C3 fuel-extinction-suppression | M1 | #3 / `a6b85f9` | 6883406826 | "accept with change, later" | Revised wording: **AWAITING OWNER RESPONSE** | Pre-dilution now verified against NASA/TP-2015-216046; card stays `pending_measured_data` | M1 confirmation; FLEX data plus the C4 vocabulary PR |
| M1-C4 material-selection | M1 | #3 / `2754d91` | 6883406826 | "research context, not R3" | Revised wording: **AWAITING OWNER RESPONSE** | Shown as an open question only | M1 confirmation |
| M1-C5 lunar-partial-gravity | M1 | #3 / `2754d91` | 6883406826 | "research context, not R3" | Revised wording: **AWAITING OWNER RESPONSE** | Labelled a hypothesis under test | M1 confirmation |
| M1-C6 martian-extrapolation | M1 | #3 / `2754d91` | 6883406826 | "research context, not R3" | Revised wording: **AWAITING OWNER RESPONSE** | White-paper authors named | M1 confirmation |
| D-01 (weights) | M1 and M3 | #3 / `22bbd3f` | 6883406826 | "Conditionally approved, on three conditions before the R1 freeze" | **Conditional (M1 only); not approved** | No freeze; ranking disabled | D-01.1–3 decisions; M3 co-approval |
| D-01.1 criteria | M1 | #3 / `24f710e` | 6883945480 | — | **AWAITING OWNER RESPONSE** | `CRITERIA_ENVIRONMENT_CONTEXT.md` remains a proposal | M1 decision |
| D-01.2 reference table | M1 | #3 / `24f710e` | 6883945480 | — | **AWAITING OWNER RESPONSE** | `environment_reference.json` remains a draft | M1 decision |
| D-01.3 sensitivity method | M1 | #3 / `24f710e` | 6883945480 | — | **AWAITING OWNER RESPONSE** | Real run only after curated data | M1 decision |
| D-02 scale | M1 | #3 / `9b6348c` | 6883406826 | "Use the continuous 0–1 formulas you implemented." | Owner response (not a CP1 approval) | Keep 0–1 | none |
| D-03 missing inputs | M1 | #3 / `9b6348c` | 6883406826 | "Use both mechanisms, matching the contract" | Owner response | Align the reference implementation after CP1 | CP1 merge |
| D-04 strict comparability | M1 | #3 / `9b6348c` | 6883406826 | "Not for v0.2.0. Command Center kept S5 as written." | Owner response | Strict mode becomes non-default (v0.3 candidate) | CP1 merge |
| D-05 quoted statements | M1 | #3 / `9b6348c` | 6883406826 | "No new class for P0" | Owner response | Applied to the BASS-II quote (`2754d91`); M3 curates | M3 curation |
| D-06 question input | M1 | #3 / `9b6348c` | 6883406826 | "v0.3 (spec §8). P0 ranks by environment only." | Owner response | Environment-only criteria drafted | none for P0 |
| D-08 reference code location | M1, M5 | #3 / `9b6348c` | 6883406826 | "Agreed, and now decided by Command Center" | Owner response plus coordinator decision | Move to `research/` after CP1 | CP1 merge; M1's `pythonpath` PR |
| D-09 test folder | M5 (M1 review) | #3 / `9b6348c` | 6883406826 | "The folder is tests/research/, not tests/integrity/." | Owner response | Keep `tests/research/` | none |
| D-10 branch name | Team | #3 / `9b6348c` | 6883406826 | "The branch keeps its name, feat/research-safety-intelligence." | Owner response | none | CP1 approvals |
| D-11 QA reviewer | Team | #3 / `9b6348c` | 6883406826 | "There is no Member 4." | Owner response; **conflicts with the roster record (§2)** | Tests reviewed by M1 and M3 per M1 | Roster confirmation |
| D-13 matching rules | M1 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | Tolerances stay proposals | M1 decision |
| G-1 applicability gate | M1 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | If G1 is chosen, the weights and sensitivity check are redone | M1 decision |
| Q-1 contract fit | M1 with M3 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | none until decided | M1 and M3 decision |

**Owner requests to Member 5** (Member 1 on PR #1, [6883818321](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883818321)): "Independently check S9 in tests/research/"; "Your reference ranking must treat withheld as unusable evidence"; review quality flags in `data/curated/interpretations/quality/`. **Status:** accepted by Member 5 as tasks, to be implemented after the CP1 contract is merged, because the branch is still on contract v0.1.0.

## 4. Member 3 decision records

Request posted: [PR #3 comment 6883945480](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883945480). Member 3 has posted nothing on PR #3. Member 3's latest comments (PR #4 [6883924995](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6883924995), PR #6 [6883925314](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/6#issuecomment-6883925314)) concern their own PRs and are recorded where relevant.

| ID | Owner | PR / SHA | Evidence | Exact owner response | Approval status | Implementation consequence | Remaining blocker |
|---|---|---|---|---|---|---|---|
| M3-A1 citation audit (43 entries; 21 original and 14 manual PDFs first) | M3 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | Audit stays executor-only | M3 review and signature |
| D-01-M3 weight co-approval | M3 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | No freeze | M3 decision |
| M3-T1 environment tags | M3 | #3 / `22bbd3f`; #6 / `d8a6fb3` | 6883925314 | On PR #6, D3: "Agree on evidence-backed relevant_environments for FLEX; keep unset until decided." | Owner proposal on their own PR; **AWAITING OWNER RESPONSE** on PR #3 | Under the draft criteria, an unset tag gives P = 0 (or exclusion under G1) | Team decision (D3); M3 provenance |
| Q-1-M3 | M3 with M1 | #3 / `22bbd3f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | none until decided | M1 and M3 |
| M3-S1 PR #4, vocabulary, `withheld` derivation | M3 | #4 / `f62330f` | 6883924995 | "No formal reviews are currently recorded. This is not approval to merge." | PR #4 open, CI green, **0 reviews** | No measured findings loaded | PR #4 review; C4 vocabulary PR (not opened); CP1 merge |
| M3-S2 test-level measurements available | M3 | #4 / `f62330f` | 6883945480 | — | **AWAITING OWNER RESPONSE** | **Ranking cannot be activated**; descriptive quotes are not measurements | Provenance-validated measured findings on `main` |
| D-12 register → curated | M3 | #3 | — | — | **AWAITING OWNER RESPONSE** | Register stays a research note | M3 decision |

Note for Member 3 (information only): DataCite lists the FLEX PSI dataset (PSI-69, DOI 10.60555/mbq8-0451) as CC0-1.0. PR #4 registers its transcription of the NASA/TP report as `permitted_with_citation`. That rights decision belongs to Member 3.

## 5. Ranking status

**Disabled.** `rank_investigations` returns `disabled_criteria_not_frozen` until D-01 is fully approved (Member 1's conditions accepted, Member 3's co-approval, G-1 and D-13 decided) and `config/ranking_criteria_v1.json` is committed alone. After that it returns `evidence_insufficient` until provenance-checked measured findings exist (and S9: never `withheld` ones).

## 6. Source verification

`SOURCE_AUDIT.md`: 43 quote citations across `evidence_reported.json` (17), `investigations.json` (7) and `environment_reference.json` (19). **29 automated, 14 manual** (PDFs, pages and SHA-256 recorded), 0 failed. The original 21 entries are unchanged in it. This is an executor check only; the independent review (M3-A1) is **awaiting owner response**.

## 7. Authorized and pending work

| Task | Authorized by | Status |
|---|---|---|
| Card corrections, FLEX verification, D-01 preparation documents | Coordinator instructions B and C | Done (prepared; not approved) |
| Keep `tests/research/` (D-09) | Member 1 owner response | In place |
| S9 independent tests and `withheld` handling in the reference ranking | Member 1 request | **Authorized, deferred until the CP1 contract is merged** |
| Move the reference code to `research/` (D-08) | Member 1 plus Command Center | **Authorized, after CP1** |
| D-03 and D-04 reference-implementation alignment | Member 1 owner responses | **Authorized, after CP1** |
| Environment-only reference ranking | — | **Not authorized** until D-01.1, D-13, G-1 and Q-1 are decided |
| Weight freeze (`config/ranking_criteria_v1.json`) | — | **Not authorized** (needs M1 and M3) |
| Ranking activation | — | **Not authorized** (needs the freeze plus measured data) |

## 8. After CP1 merges (not before)

1. Re-check against `main`, then rebase PR #3 (no force-push to anyone else's branch).
2. Apply the alignment: `backend/flameguard/research/` → `research/`, keep `tests/research/`, and wait for Member 1's `pythonpath` PR.
3. Add the S9 tests and `withheld` handling; apply D-03 and D-04.
4. Rerun ruff, pytest, the provenance check and `verify_sources`; request a fresh review.

CP1 rebase readiness (trial merges only, nothing pushed): `29c7078` 191 passed; `b89604a` 209 passed; `ca128d0` 220 passed; **`2ce0d53` (current) no conflicts, 279 passed**.
