# Member 5 coordination notes

The master spec (§4) defines four workstreams. "Member 5" is not one of them yet. This work overlaps backend B4 (ranking) and B5 (interpretations), and frontend F4 (ranking UI). It is kept in its own folders so nobody's files are overwritten:

- `backend/flameguard/research/` (new package; `app.py` not touched)
- `config/research_relevance_criteria_v1.proposed.json`
- `docs/research/member5/`
- `tests/research/` and `tests/fixtures/research/`

Not touched: `contracts/`, `frontend/`, `data/`, `tools/`, `.github/`, existing tests.

## Decisions needed

### Member 1: scientific schema and methodology

1. **Ranking weights** 0.40 / 0.25 / 0.20 / 0.15: approve, change, or reject. On approval, commit them alone as `config/ranking_criteria_v1.json` (CP1 plan B4) before any ranking output.
2. **Strict comparability**: should a core condition (gravity, O₂, pressure, flow configuration, fuel) that no record reports block comparison? S5 alone allows it.
3. **Evidence class for quoted statements**: contract v0.2.0 has no class for a NASA-quoted qualitative statement (objective, stated result, hypothesis). Options: (a) a new `reported` class, (b) a `measured` finding with `quantity: null` plus a `claim_strength` field, (c) keep these outside `Finding`. Member 5 recommends (a) or (b) with `claim_strength`. Calling them `measured` without that field would overstate them.
4. **Ranking context**: the v0.2.0 `/api/rankings?context=` takes only an environment. A research-purpose ranking needs a structured question (topics, quantities, conditions). This would need a new parameter or endpoint, through a contract PR.
5. Review all 6 insight cards and set `review_status` to `reviewed_by_member1` or `withdrawn`.

### Member 3: NASA data and provenance

1. Import test-level measured findings (D2) for BASS-II, FLEX and Saffire first. The FLEX report (NTRS 20150023456) presents results from 284 tests. Without measured data, the ranking stays empty by design.
2. Confirm or reject the candidate PSI IDs in `investigations.json` (PSI-25, PSI-69, PSI-98).
3. Confirm FM² flight status and whether any lunar data is public.
4. Decide whether `investigations.json` should become `data/curated/investigations.json` (with manifest entry and rights status).
5. Define "TARS" (spec §8, item 3) so scientific explanations can be attributed correctly.

### Member 2: frontend

The UI can render, without changing anything here:

- `explanations[inv].criteria[*]`: weight, score, weighted contribution, matched, unmatched and missing items
- `release_status`, shown as a banner when it isn't `released`
- `disclaimer`, always visible
- the card chain (finding → sources → interpretation → implication → limitations), with `claim_type` and `strength` badges and the `extrapolation_warning`

Member 2's existing `frontend/static/js/model/ranking.js` is untouched. Please check its shape against `rank_investigations()` output.

### Member 4: QA

1. `tests/research/` adds 64 tests. Please review them, and decide whether they belong in `tests/backend/` under the CP1 layout.
2. Spot-check the 17 quotes (Q3) using `python -m flameguard.research.verify_sources ...`.
3. There is an existing issue, not caused by this PR: `tests/test_contracts.py:76` calls `read_text()` without `encoding="utf-8"`, so it fails on Windows (cp1252) and passes on Linux CI. `PYTHONUTF8=1` works around it.
