# Research-relevance ranking: methodology (proposed)

**Status:** proposal for Member 1 and QA review. The weights are editorial. They are not NASA-certified and not approved by the team.

## What it answers, and what it does not

It answers: *which investigations hold evidence that best fits the research question the user stated?*

It does **not** rank fire danger, hazard or risk. No score is a probability. Every output carries this disclaimer:

> Research-relevance score: how well the evidence matches the stated research question. It is not a fire-danger, fire-risk or hazard score, and not a probability.

## Input: a structured research question

Relevance is computed from structured fields, not guessed from free text:

```json
{
  "text": "Which investigations inform solid-material flammability for a lunar habitat?",
  "target_environment": "lunar_base",
  "topics": ["material_flammability"],
  "quantities": ["flame_spread_rate"],
  "conditions": {"gravity_environment": "microgravity", "oxygen_mole_fraction": {"min": 0.19, "max": 0.30}}
}
```

## Score

`score = Σ weight × criterion score`, with each criterion scored from 0 to 1.

| Criterion | Weight (proposed) | Rule |
|---|---|---|
| `purpose_relevance` | 0.40 | Mean of the parts the question specifies: topics covered ÷ topics asked; quantities with a reported value ÷ quantities asked; 1 if any record is tagged for the target environment, else 0. |
| `condition_match` | 0.25 | Conditions matched by at least one record ÷ conditions specified. Exact match for categories, inclusive range for numbers. An unreported condition counts as unmatched and is listed as **missing**. If the question gives no conditions, the criterion scores 0 for everyone and is marked *not assessed*. |
| `source_traceability` | 0.20 | Per record, the best source's share of 4 checks: http(s) URL, retrieval date, exact quote, and locator, archive id or DOI. An interpretation takes the mean of the records it is derived from. Unresolved inputs count as 0. |
| `data_completeness` | 0.15 | Per record, the share reported among the 8 condition keys and the test id, plus the value and uncertainty for quantities. |

## Safeguards

| Safeguard | Where it is enforced |
|---|---|
| Ranks relevance, not danger | Disclaimer on every output; rationale ends "Research relevance only, not fire risk." |
| Only measured or interpreted evidence is scored (contract §5.1) | `ranking.SCORED_CATEGORIES`. Quoted statements are listed as context. |
| Comparability before numerical comparison | `comparability.require_comparable` (contract rule S5, plus a strict rule for core conditions) |
| Score components explained | `explanations[investigation].criteria`, with weight, score, weighted contribution, and matched, unmatched and missing items |
| Missing or incomparable evidence shown | `missing_evidence`, `excluded`, `excluded_records` |
| No ranking from fabricated data | Fixtures are refused unless `allow_fixtures=True` (tests only). Fixture output is `fixture_demo_only`. Fixture and real records cannot be mixed. |
| Simulations never feed the ranking | `RankingInputError` on any simulation record. The package does not import simulation code (tested). |
| Missing inputs visible, not hidden in a zero | Each criterion has a `status`: `complete`, `partially_missing` or `not_assessed` |

## Gates (`release_status`)

| Status | When | Items scored? |
|---|---|---|
| `disabled_criteria_not_frozen` | Real records, but the criteria file is not `approved` with named reviewers (CP1: no ranking output before R1) | No |
| `evidence_insufficient` | Criteria approved, but no investigation has verified measured or interpreted evidence | No |
| `fixture_demo_only` | Fixture records (tests only) | Yes, never released |
| `released` | Approved criteria and at least one scored investigation | Yes |

A real `measured` record counts only if its `manifest_id` is in `verified_manifest_ids`, the set of manifest entries that passed the provenance check and the loader (Member 3 data, Member 1's B1 loader). Interpretations built on unverified records lose their traceability score.

## Output

`rank_investigations()` returns a `ranking` object shaped like `ranking.schema.json` in the v0.2.0 proposal (rule S6 is tested), plus `disclaimer`, `release_status`, `explanations` and `excluded_records`.

## Current result on real data

No measured or interpreted NASA records have been imported, and the criteria are only proposed. A ranking over the real register therefore returns **no items** with `release_status: disabled_criteria_not_frozen`. With approved criteria it would still return no items, with status `evidence_insufficient`. All 5 investigations are listed in `excluded` with an "insufficient evidence" reason. This is intended: the method is ready, and no ranking result is fabricated.

## Open methodology decisions (see COORDINATION.md)

- **D-02:** the kickoff specifies a 0–3 rubric per criterion; this implementation uses continuous 0–1 fractions.
- **D-03:** missing inputs currently count as 0, with a visible `partially_missing` status. The alternative is moving the item to "insufficient evidence".
- **D-04:** the strict comparability rule.
- **D-07:** fuel phase, thickness and ignition conditions are not in the contract's `conditions` yet.

## Known limitations of the method

- Topic, environment and condition tags on records are assigned by people, so tagging quality limits the score.
- Equal treatment of conditions inside `condition_match` is a simplification. Member 1 may want per-condition weights.
- The strict comparability rule (core conditions must be known) is stricter than S5. It is proposed, not agreed.
