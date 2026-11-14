# Member 5 coordination notes and decision log

**Last updated:** 2026-11-14 (after coordinator decisions A and B). PR #3 is a **draft**. **Not merged, not rebased.** No shared API contract is changed by PR #3.

PR #3 adds only new files:

- `backend/flameguard/research/`
- `config/research_relevance_criteria_v1.proposed.json`
- `docs/research/member5/`
- `tests/research/` and `tests/fixtures/research/`

**How decisions are recorded here.** These three things are kept apart:

| Kind | What it is | Counts as a CP1 approval? |
|---|---|---|
| **Formal approval** | A member's own **Approve** review, or the approval comment text, on PR #1 at the final SHA, from their own GitHub account | **Yes**, and only this |
| **Owner answer** | A comment by the authorized owner on GitHub (for example Member 1's answers on PR #3) | No. It is the owner's stated position, binding once CP1 is approved |
| **Coordinator decision / recommendation** | "Command Center" (ChatGPT coordination) or Member 5 proposals, including the decisions written into PR #1 | No. It is not an approval by any member |

## 0. Coordinator positions (instructions and recommendations, NOT team approvals)

These come from Member 5's coordinator (ChatGPT) and were relayed to the executor on 2026-11-14. They direct Member 5's own actions. They are **not** formal GitHub approvals by any member, and they do not override a member's own decision.

| Ref | Coordinator position | Kind | Effect on PR #3 / CP1 |
|---|---|---|---|
| A | **Do not submit Member 5's approval of PR #1 at `ca128d0`.** Member 4's existence and GitHub identity must be confirmed by the team first. Then C5 and Member 2's identity are resolved, the candidate SHA is updated if needed, and each authorized member submits their own Approve review. | Instruction to Member 5 | No Member 5 approval has been or will be submitted on Member 5's behalf by the executor. |
| A.1 | The coordinator's guidance is not a Member 5 approval; nobody may impersonate a reviewer | Instruction | Recorded; followed |
| A.2 | The established roster includes Member 4 (QA, Testing and Judge Demo) | Coordinator position | Conflicts with `ca128d0` ("There is no Member 4"); team confirmation needed (§2) |
| B | **Apply Member 1's six-card review now** on the Member 5 branch; keep the FLEX card pending; present three cards as research context; preserve sources, uncertainty and extrapolation warnings; commit separately; keep rankings disabled; no contract change, merge or rebase | Instruction to Member 5 | Applied in commit `2754d91` (§3, card table) |
| — | Ownership boundary: Member 1 production ranking and compare; Member 5 interpretation, criteria and independent research-integrity tests; Member 3 provenance and measured-data import; Member 4 independent integration QA (pending identity) | Recommendation | Matches the `ca128d0` candidate except for Member 4 |

## 1. CP1 decision matrix (final candidate: PR #1 at `ca128d0149659fd4ee7dee9e6322297d685c7597`)

| Item | Content at `ca128d0` | Source | Status |
|---|---|---|---|
| Roster | Members 1, 2, 3 and 5. "There is no Member 4." | Coordinator decision in PR #1 | **Disputed.** The established project roster (coordinator message to Member 5, 2026-11-14) lists Member 4 (QA, Testing and Judge Demo). Needs explicit team confirmation (§2). |
| P0 | **Option B**: `relevant_environments` and `limitations` on interpretation findings; `limitations` on assistant answers (PR #5 merged into PR #1) | Coordinator decision | In the candidate; awaiting member approvals |
| C1 | TARS = *Traceable Analysis and Research Support* | Coordinator decision | In the candidate; awaiting member approvals |
| C2 | Condition values converted only by exact defined factors, in Member 3's tool; quantity values never converted (`contracts/README.md` convention 4) | Coordinator decision | In the candidate; awaiting member approvals |
| C3 | `exclude` values not emitted as numeric findings; `caution` reasons go in `uncertainty` (convention 9) | Coordinator decision | In the candidate; awaiting member approvals |
| C4 | FLEX quantities accepted; added after CP1 in a separate reviewed contract PR (Member 3) | Coordinator decision | In the candidate; vocabulary PR not yet opened |
| C5 | `test/qa-demo`: keep untouched (recommendation: delete at CP4) | Recommendation | **Open.** Depends on the roster: if Member 4 owns QA/demo, that member decides. |
| Ownership | One runtime per rule. Member 1 runs ranking and compare; Member 5's reference implementation moves to top-level `research/`; Member 5 keeps `feat/research-safety-intelligence` | Coordinator decision; Member 1 answer on PR #3 | In the candidate; awaiting member approvals |

## 2. Roster and reviewers

**Roster conflict: unresolved.** If the team confirms Member 4:
- spec §4 and the approval table in PR #1 need a fifth approver. That edit creates a new SHA, so **every member approves again**;
- C5 and the QA items (Q1, Q4, demo) move to Member 4;
- Member 4's GitHub identity is recorded only when they confirm it themselves.

| Member | GitHub account | Identity evidence | Formal CP1 approval at `ca128d0` |
|---|---|---|---|
| 1 Backend and Science | `AlphaCenturian3` | Designated by coordination; author of PRs #1 and #5 | **none yet** (expected as a comment, since GitHub blocks self-review) |
| 2 Frontend and Dashboard | **not established** | `buihhlong-a11y` authored PR #2 and has been asked to reply "I am Member 2" or "I am not Member 2" | **none yet** |
| 3 NASA Data and TARS | `huyenthoai272008` | Self-identified in PR #4 | **none yet** |
| 4 QA, Testing and Judge Demo | **not established** | No account has claimed the role. `jrromero54123-lab` has a pending invitation and no activity; **no role is assigned to it** | not in the approval table (roster conflict) |
| 5 Research and Safety Intelligence | `16trtuoiloz-ducdo` | Author of PR #3 | **none yet**. Member 5 submits this personally. |

Checked at 2026-11-14 20:03 UTC: **0 reviews on PR #1, 0 on PR #3.** No formal approval exists on any SHA.

## 3. Scientific decisions D-01 to D-12

Member 1's answers were posted on PR #3 by `AlphaCenturian3` at 20:01 UTC, reviewing head `9b6348c` (comment `6883406826`). They are **owner answers, not CP1 approvals**.

| ID | Decision | Authorized owner(s) | Owner answer on GitHub | Still needed |
|---|---|---|---|---|
| D-01 | Weights 40 / 25 / 20 / 15 | M1 **and** M3 | **M1: conditionally approved.** Conditions: (1) define each criterion for `?context=<environment>`, with the environment signal from the investigation's `relevant_environments` (curated by M3); (2) a cited target-condition table per environment (gravity, O₂ fraction, pressure); (3) a ±0.05 weight-sensitivity check recorded in `docs/research/`, with a UI warning if the top 3 changes; state that traceability and completeness (35%) measure documentation, not fire-safety relevance | M5 meets conditions 1–3; **M3's approval**; then `config/ranking_criteria_v1.json` committed alone |
| D-02 | Criterion scale | M1 | **Continuous 0–1** (as implemented). A 0–3 rubric only as interpretation findings mapped to {0, 1/3, 2/3, 1} | Record in the methodology |
| D-03 | Missing inputs | M1 | **Both:** a criterion with no evidence scores 0 with empty `inputs` and a rationale; an investigation with no measured evidence goes in `excluded` as "insufficient evidence". Document that 0 penalizes less-documented investigations. | Align `ranking.py` (the inputs-empty-at-0 rule) and the methodology |
| D-04 | Strict comparability | M1 | **Not for v0.2.0.** S5 as written; strict mode is a v0.3 candidate (needs `caveats`) | Make strict mode non-default in the reference implementation, or label it v0.3 |
| D-05 | Quoted statements | M1 (with M3 for curation) | **No new class.** `stated_objective` → `Investigation.objectives`; `experimental_result` → measured qualitative finding, **observational clauses only**; `source_statement` and `hypothesis_under_test` → context only, never scored | M3 curates; M5 trims evaluative clauses (e.g. BASS-II "not particularly dangerous…") |
| D-06 | Research-question input | M1, M2 | **v0.3.** P0 ranks by environment only | none for P0 |
| D-07 | Cohort fields (fuel phase, thickness, ignition) | M1, M3 | Listed as a v0.3 candidate (spec §8 at `ca128d0`) | none for P0 |
| D-08 | Location of the reference code | M1, M5 | **Agreed:** move to top-level `research/`; nothing under `backend/` imports it; M1 adds `pythonpath = ["."]` to pytest config after CP1 | **M5's own confirmation**; apply after CP1 |
| D-09 | Test folder | M5 (M1 review) | **`tests/research/`** compares the reference with M1's runtime output | M5 confirmation |
| D-10 | Branch name | Team | Keep `feat/research-safety-intelligence` | Covered by the CP1 approvals |
| D-11 | QA reviewer | Team | M1: no Member 4. The 80 tests are reviewed by M1 (runtime overlap) and M3 (quotes and sources) | **Depends on the roster** (§2) |
| D-12 | Register → `data/curated/investigations.json` | M3 | no answer yet | M3 |

### Member 1's scientific review of the 6 cards (owner answer), applied in `2754d91`

| Card | Member 1 verdict | `presentation` | What was changed |
|---|---|---|---|
| `card-ventilation-flow` | accept as R3 once Member 3 curates `m5-bass2-flow-flareup` | `accepted_pending_curation` | Evidence quote trimmed to "they can flare up quickly with a sudden increase in air flow speed." The authors' evaluation ("not particularly dangerous…") and the unquoted "dim and stable" detail were removed |
| `card-detection-monitoring` | accept with change | `accepted_pending_curation` | "Larger signal" (a cross-unit comparison) replaced by the Saffire authors' framing; title reworded; limitation added: large uncrewed Cygnus vehicle, not a crewed habitat atmosphere |
| `card-fuel-extinction-suppression` | accept with change, later | `pending_measured_data` | States that FLEX tested extinction in inert-gas pre-diluted atmospheres, not discharged suppressants (attributed to Member 1, **not yet checked by Member 5 against the FLEX report**); `pending_on` = PR #4 data plus the C4 vocabulary PR |
| `card-material-selection` | research context, not R3 | `research_context` | Retitled as an open question; `open_question` added; interpretation draws no conclusion |
| `card-lunar-partial-gravity` | research context, not R3 | `research_context` | Title begins "Hypothesis under test"; `open_question` added; white-paper authors named |
| `card-martian-extrapolation` | research context, not R3 | `research_context` | White paper attributed to Liao, Carmignani, Niehaus and Gollner (hosted on a NASA website, not NASA-authored); `open_question` added |

All six cards keep their verified sources, limitations and extrapolation warnings. `review_status` is now `member1_changes_applied`. It becomes `reviewed_by_member1` only when Member 1 confirms the new wording. The validator (`insights.py`) enforces the presentation rules: research-context cards need an open question and cannot present an experimental result; pending cards must name what they wait for.

## 4. Ranking status

**Disabled.** `rank_investigations` returns `disabled_criteria_not_frozen` until D-01 is fully approved (M1 conditions met **and** M3 approval) and `config/ranking_criteria_v1.json` is committed alone. After that it returns `evidence_insufficient` until measured records come from verified, provenance-checked manifest entries. PR #4's FLEX data is not merged, and its quantities wait on the C4 vocabulary PR.

## 5. Source verification

`SOURCE_AUDIT.md`: 21 quote citations, **19 automated, 2 manual** (one PDF quote, page 4, SHA-256 recorded), 0 failed. Executor check only. **Independent review pending:** Member 1 assigned quote and source checks to **Member 3** (or Member 4, if the roster confirms that role).

## 6. After CP1 merges (not before)

1. Re-check against `main`, then rebase PR #3 (no force-push to anyone else's branch).
2. Apply the alignment: `backend/flameguard/research/` → `research/`, keep `tests/research/`, and wait for Member 1's `pythonpath` PR.
3. Apply the D-03, D-04 and D-05 adjustments to the reference implementation (the card changes are already applied in `2754d91`); meet the D-01 conditions; get M1 and M3 approval of `config/ranking_criteria_v1.json`.
4. Rerun ruff, pytest, the provenance check and `verify_sources`; request a fresh review.

CP1 rebase readiness so far (trial merges only, nothing pushed): `29c7078` had no conflicts and 191 tests passed; `b89604a` had no conflicts and 209 tests passed; **`ca128d0` (final candidate) had no conflicts, 220 tests passed and ruff was clean**.
