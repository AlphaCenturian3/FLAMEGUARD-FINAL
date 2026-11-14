# Member 5 coordination notes and decision log

PR #3 adds only new files, so nobody's work is overwritten:

- `backend/flameguard/research/`
- `config/research_relevance_criteria_v1.proposed.json`
- `docs/research/member5/`
- `tests/research/` and `tests/fixtures/research/`

It does not touch `contracts/`, `frontend/`, `data/`, `tools/`, `.github/`, `app.py` or existing tests. **No shared API contract is changed.** Anything below that needs a contract change goes through a contract PR approved by its owners (spec §5.4).

## Ownership: CP1 proposal vs PR #3

The CP1 proposal (PR #1, head `29c7078`, **proposed, not approved**) changes ownership in ways that affect this PR:

| Topic | CP1 proposal | PR #3 today |
|---|---|---|
| Team | Members 1, 2, 3 and 5; **no Member 4** | The brief asks for Member 4 QA review |
| Member 5 branch | `feat/research-fire-safety` (proposed, not created) | `feat/research-safety-intelligence` (requested by the brief) |
| Member 5 owns | `data/curated/interpretations/`, `config/ranking_criteria_v*.json`, `docs/research/`, `docs/DEMO.md`, `docs/SUBMISSION_CHECKLIST.md`, `docs/verification/source_spotcheck.md`, `tests/integrity/` | `docs/research/member5/` and the criteria proposal are in scope |
| Ranking and compare code (B3, B4) | Member 1, implemented **after** R1 is frozen; Member 5 tests it independently | `backend/flameguard/research/` contains ranking and comparability code (Member 1's area) |
| Tests | Member 5 owns `tests/integrity/`; Member 1 owns `tests/backend/` | `tests/research/` (no owner) |

## Decision log

Status: **open** until the named members decide. Record the decision, who made it, and the date.

| ID | Decision | Owner | Options / Member 5 recommendation | Status |
|---|---|---|---|---|
| D-01 | Ranking weights 40 / 25 / 20 / 15 | M1 and M3 approve (CP1 R1) | Approve as `config/ranking_criteria_v1.json` in its own commit, or change | open |
| D-02 | Criterion scale: kickoff 0–3 rubric, or continuous 0–1 (implemented) | M1 | 0–3 is easier to review; 0–1 is already implemented and tested. Either way, document the rubric in the frozen file. | open |
| D-03 | Missing inputs: count as 0 with a `partially_missing` status (implemented), or move the item to "insufficient evidence" | M1 | Recommend: insufficient evidence when a core criterion is `not_assessed` | open |
| D-04 | Strict comparability: block when a core condition is unknown for every row (stricter than S5) | M1 | Recommend strict | open |
| D-05 | Evidence class for quoted NASA statements (v0.2.0 has none) | M1, M3 (contract PR) | (a) new `reported` class; (b) `measured` with `quantity: null` and a `claim_strength`; (c) keep outside `Finding`. Recommend (a) or (b). | open |
| D-06 | Research-question ranking input (v0.2.0 takes only `?context=<environment>`) | M1, M2 (contract PR) | New `POST /api/rankings/query` or extra query parameters | open |
| D-07 | Add fuel phase, thickness and ignition conditions to `conditions` (kickoff C.2) | M1, M3 (contract PR) | Needed for the kickoff's cohort grouping | open |
| D-08 | Who owns `backend/flameguard/research/` after CP1 | M1 | (a) Member 1 adopts the ranking and comparability code as B3/B4; (b) it stays a Member 5 reference implementation; Member 1 writes B3/B4 and Member 5 tests it from `tests/integrity/`. Recommend (b), so Member 5 stays an independent reviewer. | open |
| D-09 | Move `tests/research/` to `tests/integrity/` (Member 5) and/or `tests/backend/` (Member 1) | M1, M5 | Follows D-08 | open |
| D-10 | Branch name: keep `feat/research-safety-intelligence` or rename to `feat/research-fire-safety` | Team (CP1) | Rename after CP1 if the team approves it; no force-push | open |
| D-11 | Who does QA review, given no Member 4 | Team | Under CP1 §4.2: Member 1 reviews scientific soundness and Member 3 reviews traceability | open |
| D-12 | `investigations.json` → `data/curated/investigations.json` | M3 | Member 3 imports it with a manifest entry and rights status (BASS-II and FLEX datasets are CC0) | open |

## Requests by member

### Member 1: science, backend, ranking methodology
1. Decide D-01 to D-08, and review the 6 insight cards for scientific soundness (spec §4.2).
2. Confirm that `rank_investigations(..., verified_manifest_ids=...)` fits the B1 loader; the loader should pass the ids that passed the provenance check.

### Member 3: NASA data, provenance, TARS evidence
1. **First authentic test-level measurements** (kickoff R2): FLEX (PSI-69, NTRS 20150023456 reports 284 tests) and BASS-II (PSI-25) first, each with test id, conditions, units, locator, rights.
2. **PSI IDs and DOIs:** PSI-25 and PSI-69 were verified in DataCite. Confirm whether SoFIE, Saffire IV–VI or FM² have PSI datasets. A DataCite title search found none, but that does not prove none exists.
3. Confirm FM² flight status and whether any lunar data is public.
4. Review traceability of the 6 cards (spec §4.2) and decide D-12.

### QA review (Member 4 in the brief; see D-11)
1. Review the 80 tests in `tests/research/`.
2. Source integrity: spot-check the quotes with `python -m flameguard.research.verify_sources docs/research/member5/evidence_reported.json docs/research/member5/investigations.json`, and check the PDF quote by hand.
3. **Windows UTF-8 failure (existing, not from this PR):** `tests/test_contracts.py:76` calls `read_text()` without `encoding="utf-8"` and fails on Windows (cp1252). It passes on Linux CI and with `PYTHONUTF8=1`. The fix is one line in a root test file (shared ownership under CP1).

### Member 2: frontend
Render `release_status`, `disclaimer`, per-criterion `status`, the `excluded` reasons, and the card chain with `claim_type`, `strength` and `extrapolation_warning`. Check the shape against `frontend/static/js/model/ranking.js` (PR #2).

## CP1 rebase readiness (checked 2026-11-14)

A trial merge of `origin/contract/cp1-v0.2-proposal` (`29c7078`) into this branch, done in a temporary worktree and not pushed:

- **No textual conflicts.**
- `ruff check`, `ruff format --check` and the provenance check pass.
- `pytest`: 191 passed (CP1's tests plus this PR's tests at that point).

The remaining blockers are ownership and process (D-08 to D-11), not code. After CP1 merges, redo this check on the merged `main`, then rebase. No force-push to a shared branch, and no merge without explicit approval.
