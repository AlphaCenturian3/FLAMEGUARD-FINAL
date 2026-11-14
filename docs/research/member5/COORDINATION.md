# Member 5 coordination notes and decision log

**Last updated:** 2026-11-14, 21:35 UTC (CP1 head `e44ec26`, 0 of 4 approvals; Member 5 independent S9 oracle review posted; second FLEX verification completed). PR #3 is a **draft**. **Not merged, not rebased.** No shared API contract is changed by PR #3. Rankings are **disabled**.

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
| A′ (update, 2026-11-14) | Treat Members 1, 2, 3 and 5 as the **provisional** four-active-member roster (Command Center clarification). Member 5 may confirm role and identity personally, with the account holder's authorization. Members 2 and 3 confirm individually. C5 is non-blocking, and its QA owner is unresolved until assigned. Member 5's CP1 approval is **still withheld**. Reviews must name the final SHA if CP1 changes | Instruction to Member 5 | Member 5's confirmation posted with the account holder's explicit authorization ([PR #1 comment 6884177976](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884177976)). CP1 approval not submitted |
| A‴ | Record M-1 (unordered eligible-evidence list) as the coordinator's **preferred interim fallback**, pending Member 1; begin a read-only Q3 spot-check of Member 3's FLEX material | Instruction | M-1 recorded in `CRITERIA_ENVIRONMENT_CONTEXT.md`; Q3 record in `Q3_FLEX_SPOTCHECK.md`; findings sent to Member 3 on PR #4 |
| A″ | Flag gravity-only scoring as insufficiently discriminating; request Member 1's methodological decision before any production ranking | Instruction | Requested ([PR #3 comment 6884182608](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6884182608)) |
| A.1 | Coordinator guidance is not a Member 5 approval; nobody may impersonate a reviewer | Instruction | Followed |
| A.2 | The established roster includes Member 4 (QA, Testing and Judge Demo); keep unresolved until the team confirms | Coordinator position | Recorded in §2 as unresolved |
| B | Apply Member 1's six-card review now on the Member 5 branch | Instruction | Applied in `2754d91` and `a6b85f9` |
| C | Prepare Member 1's three D-01 conditions; verify the FLEX pre-dilution against the NASA report | Instruction | Done in `24f710e` and `a6b85f9` (prepared, not approved) |
| D | Request explicit decisions from Members 1 and 3; record each individually; silence is not approval | Instruction | Decision form posted on PR #3 ([comment 6883945480](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883945480)) |
| — | Ownership boundary: Member 1 production ranking and compare; Member 5 interpretation, criteria and independent research-integrity tests; Member 3 provenance and measured-data import; Member 4 integration QA (pending identity) | Recommendation | Matches the CP1 candidate except for Member 4 |

## 1. CP1 status (PR #1)

| Item | State on 2026-11-14 at 21:35 UTC |
|---|---|
| Current head | **`e44ec26e31f58d8a63d40cac0872d0b393de3a6f`** (draft), "CP1: correct the three S9 test-oracle defects (Command Center Option 1)". CI run 43642851847 passed. Approval request: [6884465691](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884465691) |
| What changed since `eaae6d6` | `tests/test_exclusion_dependency.py` and its documentation only; rule text and schemas unchanged. Adds the S9 runtime-gate rows for B6 and T1 (Member 5 tests them independently) |
| **Formal approvals at `e44ec26`** | **0 of 4.** All earlier approvals are superseded. Member 2 will approve after reviewing the final head; Member 5's approval is withheld |
| **Member 5 independent S9 review** ([6884478474](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884478474)) | Defects 1–3 fixed; direct and multi-step chains, per-citation note-text checks and positive controls verified; **mutation evidence reproduced independently** (baseline 29 passed; reinstating defect 1, 2 or 3 fails 5, 2 or 2 tests; cycle short-circuit fails 1; non-transitive ancestors fails 11). **Open finding:** the number regex misses a value with its unit attached (`0.37mm2/s` → only `0` is extracted). Tested fix: lookahead `(?!\d|\.\d)` (13 cases, existing assertions kept). Minor: decimal comma not detected. Suggestion: test an answer citation at depth ≥ 2. **Decision needed (Members 1 and 5):** fix in CP1, or record as a B6/T1 runtime acceptance criterion. AWAITING OWNER RESPONSE |
| Earlier heads (superseded) | `ca128d0`, `2ce0d53`, `a6876d1`, `eaae6d6` |
| C5 (`test/qa-demo`) | Non-blocking; **QA owner unresolved** |
| Member 5 trial merges into PR #3 | `a6876d1`: 299 passed; `eaae6d6`: 325 passed; **`e44ec26`: no conflicts, 338 passed**. Temporary worktrees only |

## 2. Roster and identities

**Roster: provisional four-active-member roster (coordinator instruction A′). Individual confirmations:**

| Member | Account | Roster confirmation on PR #1 | Evidence |
|---|---|---|---|
| 1 | `AlphaCenturian3` | Covered by the CP1 approval ("the four-active-member ownership model") | [6884018748](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884018748) |
| 2 | `buihhlong-a11y` | **Confirmed**: "I am Member 2 (buihhlong-a11y). I confirm the four-active-member CP1 roster"; stated as "not my approval of PR #1" | [6884379301](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884379301) |
| 3 | `huyenthoai272008` | **AWAITING** explicit confirmation on PR #1. On PR #4 Member 3 wrote "My earlier review request mentioning Member 4 is superseded" | [PR #4 6884037095](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884037095) |
| 5 | `16trtuoiloz-ducdo` | **Confirmed**: "Member 5 (16trtuoiloz-ducdo) confirms the four-active-member roster." Posted with the account holder's authorization | [6884177976](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884177976) |

C5 (`test/qa-demo`): non-blocking for CP1; **QA owner unresolved** until explicitly assigned.

Earlier context: Command Center's "final roster clarification" ([comment 6884060166](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884060166), 20:54 UTC) states: "The active FlameGuard-SI engineering team consists of Members 1, 2, 3 and 5. There is no currently assigned Member 4." It asks each member to post `Member <N> (<username>) confirms the four-active-member roster.` or a dispute with evidence, and adds: "Silence is not taken as consent." Member 1's CP1 approval covers "the four-active-member ownership model". Member 3 wrote on PR #4 ([6884037095](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884037095)): "My earlier review request mentioning Member 4 is superseded." Members 2, 3 and 5 have **not** posted the requested confirmation on PR #1. Member 5's confirmation or dispute is Member 5's own decision; the executor does not post it. Earlier statements:

| Source | Statement | Kind |
|---|---|---|
| Command Center, relayed by Member 1 on PR #1 ([6883551034](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883551034)) | "The active engineering team for CP1 is Members 1, 2, 3 and 5. There is no active Member 4." | Coordinator decision |
| Member 5's coordinator | The established roster includes Member 4 (QA); keep unresolved until the team confirms | Coordinator position |
| `buihhlong-a11y` on PR #1 ([6883703493](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883703493)) | Asks the team to reply "Confirmed: there is no Member 4…" or name Member 4 | Request |
| Member 3 on PR #4 ([6883924995](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6883924995)) | Addresses "**Member 4 (QA):** Please inspect the data tests and verifier…" | Implies Member 4 exists |

No member has confirmed the roster from their own account, and no account has claimed Member 4. No role is assigned to the pending invitee.

| Member | Account | Identity evidence | Formal CP1 approval at `a6876d1` |
|---|---|---|---|
| 1 | `AlphaCenturian3` | Designated by coordination | approved `a6876d1` (comment 6884018748); **superseded by head `eaae6d6`** |
| 2 | `buihhlong-a11y` (confirmed 21:21 UTC) | Self-identified on PR #1 ([6884379301](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884379301)) | none |
| 3 | `huyenthoai272008` | Self-identified in PR #4 | none |
| 4 | not established | — | not in the approval table |
| 5 | `16trtuoiloz-ducdo` | Author of PR #3 | none (withheld per instruction A) |

## 3. Member 1 decision records

Requests: [PR #3 comment 6883945480](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883945480) (decision form, head `22bbd3f`). **Member 1 answered at 20:48 UTC: [comment 6883984161](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883984161)**, reviewing `22bbd3f`, with contract references to CP1 at `a6876d1`. Member 1 states: "These are Member 1's owner answers and proposals, not approvals. Nothing here freezes weights, activates rankings or approves a card." Earlier answers: [comment 6883406826](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883406826) (head `9b6348c`). Quotes are exact, with markdown emphasis removed.

| ID | Owner | PR / SHA | Evidence | Exact owner response | Decision status | Implementation consequence | Remaining blocker |
|---|---|---|---|---|---|---|---|
| M1-C1 … C6 (six cards) | M1 | #3 / `22bbd3f` | 6883984161 | "The wording matches my review on all six" … "This is not scientific approval of any card" | **Wording ACCEPTED; evidence not approved** | `review_status: wording_confirmed_by_member1` (status name requested by M1) | M3 independent quote check; M3 curation (C1, C2); FLEX data (C3); C4–C6 stay context only |
| D-01 weights | M1 and M3 | #3 / `22bbd3f` | 6883984161 | "Yes, as proposed." (documentation can outweigh applicability) … "No weights are frozen until then" | **REVISIONS REQUESTED** (M1). M3: AWAITING OWNER RESPONSE | No freeze. Proposed: after gating, weight only C, T and D under the invariant `w_C · Δ_min > w_T + w_D`, tested in the reference implementation and in B4 | Real criterion scores after CP2; sensitivity rerun; M1 and M3 approval |
| D-01.1 criteria | M1 | #3 / `24f710e` | 6883984161 | "With G2 as a gate, purpose_relevance stops being a 0.40 weighted criterion." | **REVISIONS REQUESTED** | Criteria to be redrafted: gate plus C, T, D | M5 redraft; M1 and M3 review |
| D-01.2 reference table | M1 | #3 / `24f710e` | 6883984161 | Gravity rows accepted with labels; unknown rule: "Accept your rule"; quotes "are recorded, not authenticated" until Member 3 checks them | **ACCEPTED in part; REVISIONS REQUESTED** (label `spacecraft` gravity "assumed: coast phase"; Martian rover "reference unknown") | Table stays a draft; labels to update | M3 authentication of the 19 quotes |
| D-01.3 sensitivity method | M1 | #3 / `24f710e` | 6883984161 | "Run the sensitivity method again on real criterion scores after CP2, as you already planned." | **Method used; real run DEFERRED to CP2** | Synthetic demonstration stands | Real data (CP2) |
| D-13 gravity | M1 | #3 / `22bbd3f` | 6883984161 | `space_station`: "Accept"; `spacecraft`: "Accept as a labelled editorial assumption"; `pressurized_rover`: "Accept as a labelled assumption"; lunar = Martian category: "Accept as a stated limit" | **ACCEPTED (labelled)** | UI labels: "assumed: coast phase"; lunar rover assumption | none for P0 |
| D-13 O₂ / pressure tolerances | M1 (Command Center) | #3 / `22bbd3f` | 6883984161 | "INACTIVE (Command Center)." … "For P0, C is scored on gravity only" | **REJECTED for P0 (inactive)** | O₂ and pressure shown, not scored; C ∈ (0, 1) | A cited equivalence tolerance; M1 and M3 approval; sensitivity rerun |
| D-13 unknown conditions | M1 | #3 / `22bbd3f` | 6883984161 | "Accept your rule: not in the denominator, and listed as \"reference unknown\"." | **ACCEPTED** | as drafted | none |
| G-1 applicability gate | M1 | #3 / `22bbd3f` | 6883984161 | "An investigation is scored for ?context=<env> only if it passes every gate." Gates: G1 evidence, G2 source-stated relevance, G3 integrity | **Owner proposal (recommended); not approved**. Note: Member 1's G1–G3 differ from the G0–G2 options in Member 5's form | Gate replaces the P criterion; an empty ranking is reported as empty | M3 view; CP1; then redraft and approval |
| M-1 … M-4 scoring discrimination | M1 | #3 / `a0fa130` | [6884182608](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6884182608) | — | **AWAITING OWNER RESPONSE** | Member 5 records gravity-only scoring as **insufficiently discriminating** on current evidence (all documented investigations are microgravity, so C is constant within each context). No production ranking until Member 1 decides | M1 decision |
| Q-1 contract fit | M1 with M3 | #3 / `22bbd3f` | 6883984161 | "Q-1 goes away under the gate" … tags hold "only environments the investigation's own sources state" | **Resolved by proposal, pending M3** | Wider applicability goes in Member 5's interpretation findings, never in tags | M3 tag-provenance rule |
| D-02 scale | M1 | #3 / `9b6348c` | 6883406826 | "Use the continuous 0–1 formulas you implemented." | Owner response | Keep 0–1 | none |
| D-03 missing inputs | M1 | #3 / `9b6348c` | 6883406826 | "Use both mechanisms, matching the contract" | Owner response | Align the reference implementation after CP1 | CP1 merge |
| D-04 strict comparability | M1 | #3 / `9b6348c` | 6883406826 | "Not for v0.2.0. Command Center kept S5 as written." | Owner response | Strict mode non-default (v0.3) | CP1 merge |
| D-05 quoted statements | M1 | #3 / `9b6348c` | 6883406826 | "No new class for P0" | Owner response | Applied to the BASS-II quote | M3 curation |
| D-06 question input | M1 | #3 / `9b6348c` | 6883406826 | "v0.3 (spec §8). P0 ranks by environment only." | Owner response | Environment-only | none for P0 |
| D-08 reference code location | M1, M5 | #3 / `9b6348c` | 6883406826 | "Agreed, and now decided by Command Center" | Owner response plus coordinator decision | Move to `research/` after CP1 | CP1 merge; M1's `pythonpath` PR |
| D-09 test folder | M5 (M1 review) | #3 / `9b6348c` | 6883406826 | "The folder is tests/research/, not tests/integrity/." | Owner response | Keep `tests/research/` | none |
| D-10 branch name | Team | #3 / `9b6348c` | 6883406826 | "The branch keeps its name, feat/research-safety-intelligence." | Owner response | none | CP1 approvals |
| D-11 QA reviewer | Team | #3 / `9b6348c` | 6883406826 | "There is no Member 4." | Owner response; **conflicts with the roster record (§2)** | Tests reviewed by M1 and M3 per M1 | Roster confirmation |

**Owner requests to Member 5** (Member 1 on PR #1, [6883818321](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883818321) and [6883970652](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6883970652)): "Your reference ranking must treat withheld as unusable evidence" (the value status is now `excluded`); "you independently check S9 and S10 in tests/research/, and the quotes in Q3"; review quality flags in `data/curated/interpretations/quality/`. **Status:** accepted by Member 5 as tasks, to be implemented after the CP1 contract is merged, because the branch is still on contract v0.1.0.

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

**Member 3 comment on PR #3** ([6884145867](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6884145867), 21:01 UTC). Member 3 labels it: "These are coordinator recommendations only, not Member 3's formal signature, ranking-weight co-approval or an independent quotation audit." It asks: "Please keep these items awaiting named owner responses rather than recording this comment as approval." Recorded accordingly: **no Member 3 item changes status.** Status information it gives:
- M3-S2: "contract-v0.2 provenance-validated, row-level Finding JSON is not yet available on main" (only a transcribed CSV on the PR #4 branch). This confirms that rankings cannot be activated.
- M3-A1: "A '0 failed' report from the author is not a reviewer sign-off." Consistent with `SOURCE_AUDIT.md`.
- M3-T1/Q-1, D-01-M3 and D-12 restate the recommendations, pending Member 3's own explicit confirmation.

**Member 3 activity on other PRs (earlier):**

- PR #4 ([6884037095](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884037095), head `e9c89aa`): "Member 5 is requested for independent scientific source spot-check and quality-flag review"; "Do not merge before reviewers approve and CP1 alignment is reconciled."
- PR #6 ([6884037456](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/6#issuecomment-6884037456), head `2b18563`): "Do not create a redundant Finding.flags field"; tracks gaps G1–G7, including "G5 source-quote authentication"; "Member 5: independent source audit".

These are requests **to** Member 5 about Member 3's data (Q3, spec §4.2). They are not answers to the PR #3 form. Every Member 3 item in the table above remains **AWAITING OWNER RESPONSE**. No further notification was sent at 21:05 UTC, because one was posted at 20:51 UTC ([PR #3 comment 6884018291](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6884018291)).

**Reciprocal audits (not a contradiction):** Member 3 authenticates Member 5's 43 citations (Member 1's assignment), and Member 5 spot-checks Member 3's FLEX transcription and quality flags (Q3). Neither may authenticate their own work.

**Member 3's PR #6 material affecting Member 5** (head `e4d3892`, read-only review):
- `docs/verification/m3_citation_audit_of_member5.md`: a machine check by Member 3's executor, independent of Member 5's tool. **43 of 43 quotes found; all 6 PDF hashes match. Status "NOT SIGNED OFF".** The human checks and the signature remain Member 3's. M3-A1 stays **AWAITING OWNER RESPONSE** (signature).
- Findings for Member 5: **F1** page convention (Member 5 cites the FLEX report by PDF index; PR #4 uses printed pages); **F2** "impelements" is verbatim; **F3** NSSDC quotes are to be used only as environment context. **Member 5 decision (account holder, 2026-11-14; posted on PR #6, [6884357973](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/6#issuecomment-6884357973)):** F1 **adopted**: all 14 PDF citations now read "printed p. X (PDF p. Y)"; OCHMO PDF p. 2 is recorded as having no printed page number. F2 kept verbatim. F3 confirmed.
- `docs/verification/environment_tag_mapping.md` proposes **removing tags not stated by the investigations' own sources** from Member 5's `investigations.json`: BASS-II `lunar_base` and `pressurized_rover`; FLEX `lunar_base`; SoFIE `martian_base` (`lunar_base` borderline); Saffire `lunar_base`, `martian_base` and `pressurized_rover`. Wider applicability would go into interpretation findings with limitations. **Member 5 decision (account holder): accepted and applied** in `investigations.json`. SoFIE `lunar_base` is left out pending evidence, and the synthesis `martian_base` stays pending team confirmation. Each investigation has a `tag_provenance` note citing Member 3's mapping (quotes not yet human-checked).

**Q3 spot-check by Member 5's executor** (`Q3_FLEX_SPOTCHECK.md`): PR #4 transcription **140 of 140 cells match**; **43 of 43 flag quotes verbatim on the cited pages**; dash coverage 9 of 9; manifest hashes match; same source PDF hash. Source findings S-2 (FLEX-010 initial diameter: saturated image; no caution flag) and S-3 (FLEX-010 burn time basis unclear) are recommendations for Member 3. Contract questions C-1 to C-8 are listed separately. **Blocker:** PSI electronic data not accessed.

Note for Member 3 (information only): DataCite lists the FLEX PSI dataset (PSI-69, DOI 10.60555/mbq8-0451) as CC0-1.0. PR #4 registers its transcription of the NASA/TP report as `permitted_with_citation`. That rights decision belongs to Member 3.

## 5. Ranking status

**Disabled.** `rank_investigations` returns `disabled_criteria_not_frozen` until D-01 is fully approved (Member 1's revisions applied and accepted, Member 3's co-approval, real criterion scores and a sensitivity rerun after CP2) and `config/ranking_criteria_v1.json` is committed alone. After that it returns `evidence_insufficient` until provenance-checked measured findings exist (and S9: never `withheld` ones).

## 6. Source verification

`SOURCE_AUDIT.md`: 43 quote citations across `evidence_reported.json` (17), `investigations.json` (7) and `environment_reference.json` (19). **29 automated, 14 manual** (PDFs, pages and SHA-256 recorded), 0 failed. The original 21 entries are unchanged in it. This is an executor check only; the independent review (M3-A1) is **awaiting owner response**.

## 7. Authorized and pending work

| Task | Authorized by | Status |
|---|---|---|
| Card corrections, FLEX verification, D-01 preparation documents | Coordinator instructions B and C | Done (prepared; not approved) |
| Keep `tests/research/` (D-09) | Member 1 owner response | In place |
| S9 and S10 independent tests, `excluded` handling in the reference ranking, Q3 quote checks of curation notes | Member 1 requests | **Authorized, deferred until the CP1 contract is merged** |
| Move the reference code to `research/` (D-08) | Member 1 plus Command Center | **Authorized, after CP1** |
| D-03 and D-04 reference-implementation alignment | Member 1 owner responses | **Authorized, after CP1** |
| Card status `wording_confirmed_by_member1` | Member 1 request (6883984161) | Done |
| Redraft criteria to gates (E1–E3) plus C, T, D with gravity-only C; record the dominance invariant; reference-table labels | Member 1 revision request; coordinator authorization (documentation only) | **Done as proposals** (revision 2: `CRITERIA_ENVIRONMENT_CONTEXT.md`, `ENVIRONMENT_REFERENCE.md`, `environment_reference.json`, `WEIGHT_SENSITIVITY.md`); not approved; E2 pending M3 |
| Q3 spot-check of Member 3's FLEX transcription (PR #4) and quality-flag review | Member 3 request (PR #4, #6); spec §4.2; coordinator A‴ | **Done (executor record)**: `Q3_FLEX_SPOTCHECK.md`; Member 5's personal confirmation optional |
| Respond to Member 3's F1–F3 and the tag-removal proposal | Member 3 (PR #6) | **Done**: decided by the account holder and applied; posted on PR #6 ([6884357973](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/6#issuecomment-6884357973)) |
| Send the Q3 findings to Member 3 | Coordinator A‴ | **Done**: PR #4 ([6884315288](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884315288)) |
| Environment-only reference ranking with gate and invariant test | Member 1 revision request | **Deferred until after CP1** (move to `research/` first) and the redraft is reviewed |
| Weight freeze (`config/ranking_criteria_v1.json`) | — | **Not authorized** (needs M1 and M3) |
| Ranking activation | — | **Not authorized** (needs the freeze plus measured data) |

## 8. After CP1 merges (not before)

1. Re-check against `main`, then rebase PR #3 (no force-push to anyone else's branch).
2. Apply the alignment: `backend/flameguard/research/` → `research/`, keep `tests/research/`, and wait for Member 1's `pythonpath` PR.
3. Add the S9 and S10 tests and `excluded` handling; apply D-03 and D-04.
4. Rerun ruff, pytest, the provenance check and `verify_sources`; request a fresh review.

CP1 rebase readiness (trial merges only, nothing pushed): `29c7078` 191 passed; `b89604a` 209 passed; `ca128d0` 220 passed; `2ce0d53` 279 passed; **`a6876d1` (current) no conflicts, 299 passed**.
