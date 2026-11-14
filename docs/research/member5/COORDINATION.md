# Member 5 coordination notes and decision log

**Last updated:** 2026-11-14. PR #3 is a **draft** at the head recorded in its description. **Not merged, not rebased.** No shared API contract is changed by PR #3.

PR #3 adds only new files:

- `backend/flameguard/research/`
- `config/research_relevance_criteria_v1.proposed.json`
- `docs/research/member5/`
- `tests/research/` and `tests/fixtures/research/`

## 1. Team roster conflict (flagged for team confirmation)

| Source | Roster |
|---|---|
| Established project roster (coordinator, 2026-11-14) | **Five members:** 1 Backend and Science; 2 Frontend and Dashboard; 3 NASA Data and TARS; **4 QA, Testing and Judge Demo**; 5 Research Interpretation and Safety Intelligence |
| CP1 proposal, PR #1 at `b89604a` (not approved) | "The active team is Members 1, 2, 3 and 5. **There is no Member 4.**" QA items are spread across Members 1, 2, 3 and 5. |

**Status: unresolved.** PR #3 does not change the CP1 proposal. The team must confirm the roster in PR #1 before CP1 can be approved. If Member 4 exists, their GitHub identity, ownership (for example `tests/integration/`, `tests/e2e/`, `docs/DEMO.md`) and review duties must be added to spec §4 through PR #1.

## 2. GitHub identities and approvals

Identity counts only from GitHub-authenticated actions (PR authorship or text, review submissions), following the PR #1 checklist. Commit author names are not evidence, because commits are unsigned.

| Member | GitHub account | Evidence | Confirmed by the member in a CP1 approval? |
|---|---|---|---|
| 1 Backend and Science | `AlphaCenturian3` | Designated by coordination; repo admin; author of PRs #1 and #5 | no |
| 2 Frontend and Dashboard | not established | `buihhlong-a11y` authored PR #2 but has not stated a member number | no |
| 3 NASA Data and TARS | `huyenthoai272008` | Self-identified in PR #4 ("Data / Member 3") | no |
| 4 QA, Testing and Judge Demo | **not established** | No account has claimed this role. `jrromero54123-lab` has a pending invitation and no activity (per PR #1). **No role is assigned to that account.** | no |
| 5 Research and Safety Intelligence | `16trtuoiloz-ducdo` | Author of PR #3 | no |

**Approvals recorded so far:** none. On 2026-11-14 at 20:00 UTC there were 0 reviews on PR #1 (`b89604a`) and 0 reviews on PR #3.

## 3. Ownership boundary

| Area | Coordinator's provisional recommendation (2026-11-14) | CP1 proposal (`b89604a`) | Approved? |
|---|---|---|---|
| Production ranking and comparison | Member 1 | Member 1 (B3, B4); "one runtime implementation per rule" | no |
| Scientific interpretation, review criteria, independent research-integrity tests | Member 5 | Member 5: R1 to R4, `tests/research/`, the non-runtime `research/` reference implementation | no |
| NASA provenance and measured-data import | Member 3 | Member 3 (D1 to D5; PR #4 adds the first FLEX data) | no |
| Independent integration QA | Member 4, once their GitHub identity is confirmed | No Member 4; QA items assigned to Members 1, 2, 3 and 5 | no (roster conflict, §1) |

**PR #3 alignment in the CP1 proposal** (not yet applied, pending CP1): move `ranking.py`, `comparability.py`, `evidence.py`, `common.py`, `insights.py` and `verify_sources.py` from `backend/flameguard/research/` to a non-runtime `research/` folder; keep `tests/research/`; keep the branch name. This fits the coordinator's boundary. Member 5 applies it on this branch only after CP1 is approved.

## 4. Decision log

Neither the "provisional recommendation" nor the "CP1 proposal" column is a decision. A decision is recorded only when the named owners approve it on GitHub.

| ID | Decision | Owners | Provisional recommendation (Member 5 / coordinator) | CP1 proposal position | Approved decision |
|---|---|---|---|---|---|
| D-01 | Ranking weights 40 / 25 / 20 / 15 | M1 and M3 (R1) | Adopt as `config/ranking_criteria_v1.json` in its own commit after approval | R1: Member 5 authors; Members 1 and 3 approve | **none** |
| D-02 | Criterion scale: kickoff 0–3 rubric or continuous 0–1 (implemented) | M1 | Pick one and document the rubric in the frozen file | not addressed | **none** |
| D-03 | Missing inputs: 0 with a visible `partially_missing` status (implemented), or an "insufficient evidence" bucket | M1 | Insufficient evidence when a core criterion is `not_assessed` | not addressed | **none** |
| D-04 | Strict comparability (core condition unknown for every row blocks comparison) | M1 | Strict | S5 only; C2 allows exact defined conversions of condition units in Member 3's tool | **none** |
| D-05 | Classification of quoted NASA statements | M1, M3 | New class, or `claim_strength` on qualitative findings | Map without contract change: `stated_objective` → objectives; `experimental_result` → measured qualitative finding; `source_statement` and `hypothesis_under_test` → context only | **none** |
| D-06 | Research-question input for rankings | M1, M2 | New query endpoint or parameters, through a contract PR | not addressed (v0.2.0 takes `?context=<environment>`) | **none** |
| D-07 | Cohort fields: fuel phase, thickness, ignition conditions | M1, M3 | Contract PR after CP1 | not addressed (PR #5 adds only `relevant_environments` and `limitations`) | **none** |
| D-08 | Location of `backend/flameguard/research/` | M1, M5 | **Coordinator:** Member 1 owns production ranking and compare; Member 5 keeps a reference implementation | Move to non-runtime `research/` | **none** |
| D-09 | Test folder | M5 | **Coordinator:** Member 5 owns independent research-integrity tests | Keep `tests/research/` as Member 5's folder | **none** |
| D-10 | Branch name | Team | Keep `feat/research-safety-intelligence` | Keep the current name | **none** (both agree, not approved) |
| D-11 | Who performs integration QA | Team | **Coordinator:** Member 4, once their identity is confirmed | No Member 4; QA spread across members | **none** (conflict, §1) |
| D-12 | `investigations.json` → `data/curated/investigations.json` | M3 | Member 3 imports it with a manifest entry and rights status | Member 3 merges it into D1 | **none** |

Related CP1 decisions that need Member 5's own approval on PR #1: **P0** (option A at `b89604a`, or option B at `915675b` adding `relevant_environments` and `limitations`; PR #3 already uses both concepts) and **C1 to C5**. Member 5 states a choice only in their own approval review.

## 5. Ranking status

Ranking is **disabled**. `rank_investigations` returns `disabled_criteria_not_frozen` until D-01 is approved. After that it returns `evidence_insufficient` until measured records come from verified, provenance-checked manifest entries.

PR #4 (Member 3, open) proposes the first FLEX measurements. They are not merged, their quantities are not yet in the contract vocabulary (CP1 C4), and the ranking does not use them.

## 6. Source verification

See `SOURCE_AUDIT.md`: 21 quote citations, **19 verified automatically, 2 verified manually** (one PDF quote, page 4, file SHA-256 recorded), 0 failed. An independent spot check by another member is still pending.

## 7. CP1 rebase readiness (checked 2026-11-14, nothing pushed)

| CP1 head | Conflicts | Tests |
|---|---|---|
| `29c7078` | none | 191 passed |
| `b89604a` (current) | none | 209 passed, without `PYTHONUTF8`. CP1's UTF-8 change fixes the Windows failure in `tests/test_contracts.py`. |

Both were trial merges in a temporary worktree, which was deleted afterwards. **Do not rebase** until CP1 is approved and merged. Then redo this check on `main`, apply the alignment in §3, and get the PR reviewed. No force-push, and no merge without explicit approval.
