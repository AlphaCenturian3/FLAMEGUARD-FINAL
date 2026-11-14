# Weight-sensitivity assessment (D-01, condition 3)

**Status:** method proposal for Member 1 and Member 3 review. **No NASA data is used.** Every number below comes from a **synthetic software fixture** (`tests/fixtures/research/synthetic_criterion_scores.json`, marked `fixture: true`), with placeholder ids that correspond to no investigation. The results show how the method behaves; they are not findings, and they are not a ranking of NASA investigations. The ranking stays disabled.

## Method

Proposed weights: `w = (P 0.40, C 0.25, T 0.20, D 0.15)` (purpose relevance, condition match, source traceability, data completeness).

1. **Perturbation.** For each criterion `c` and each shift `δ ∈ {+0.05, −0.05}` (8 scenarios), set `w_c' = w_c + δ` and leave the other weights unchanged.
2. **Normalization.** Divide every weight by the new total `1 + δ`, so the weights again sum to 1. The other three weights are scaled by the same factor, so their ratios to each other are preserved. Example: `C +0.05` gives `(0.40, 0.30, 0.20, 0.15) / 1.05 = (0.3810, 0.2857, 0.1905, 0.1429)`.
3. **Re-scoring.** Each investigation's score is recomputed as `Σ w_i'' · s_i` from its unchanged criterion scores `s_i`. The criterion contributions `w_i'' · s_i` are listed for the baseline so a reviewer can see which criterion drives each total.
4. **Re-ranking.** Descending score, ties broken by investigation id (the same rule as the ranking). Near-ties (gap < 1e-9) are reported.
5. **Stability rule (Member 1).** The ranking is **weight-sensitive** if the **ordered top 3** differs from the baseline in any of the 8 scenarios. The largest rank change of any investigation is reported for each scenario. If a real ranking is weight-sensitive, the UI must say so next to the ranking.

The computation is in `tests/research/research_sensitivity.py` (pure functions over a criterion-score matrix). `tests/research/test_research_sensitivity.py` checks the arithmetic and checks that the tables below are exactly what the code produces. Regenerate them with `python tests/research/research_sensitivity.py`.

## Worked examples (synthetic)

Two synthetic scenarios show both outcomes:

- `well-separated`: investigations whose evidence differs clearly. Expected stable.
- `documentation-trade-off`: one investigation that matches the environment's conditions but is poorly documented (`synthetic-p`), against one that matches no condition but is fully documented (`synthetic-q`) and one that is not tagged for the environment but matches every condition (`synthetic-r`). Expected weight-sensitive.

#### Scenario `well-separated` (synthetic)

Baseline criterion scores (synthetic inputs) and weighted contributions:

| Investigation | purpose_relevance (score → contribution) | condition_match (score → contribution) | source_traceability (score → contribution) | data_completeness (score → contribution) | Total |
|---|---|---|---|---|---|
| `synthetic-a` | 1.0000 → 0.4000 | 0.8000 → 0.2000 | 0.9000 → 0.1800 | 0.8000 → 0.1200 | 0.9000 |
| `synthetic-b` | 1.0000 → 0.4000 | 0.5000 → 0.1250 | 0.7000 → 0.1400 | 0.6000 → 0.0900 | 0.7550 |
| `synthetic-c` | 1.0000 → 0.4000 | 0.2000 → 0.0500 | 0.6000 → 0.1200 | 0.5000 → 0.0750 | 0.6450 |
| `synthetic-d` | 0.0000 → 0.0000 | 0.4000 → 0.1000 | 0.9000 → 0.1800 | 0.9000 → 0.1350 | 0.4150 |
| `synthetic-e` | 0.0000 → 0.0000 | 0.1000 → 0.0250 | 0.5000 → 0.1000 | 0.4000 → 0.0600 | 0.1850 |

Baseline order: `synthetic-a`, `synthetic-b`, `synthetic-c`, `synthetic-d`, `synthetic-e`

| Shift | Effective weights (P / C / T / D) | Order | Top 3 changed | Max rank shift |
|---|---|---|---|---|
| purpose_relevance +0.05 | 0.4286 / 0.2381 / 0.1905 / 0.1429 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| purpose_relevance -0.05 | 0.3684 / 0.2632 / 0.2105 / 0.1579 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| condition_match +0.05 | 0.3810 / 0.2857 / 0.1905 / 0.1429 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| condition_match -0.05 | 0.4211 / 0.2105 / 0.2105 / 0.1579 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| source_traceability +0.05 | 0.3810 / 0.2381 / 0.2381 / 0.1429 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| source_traceability -0.05 | 0.4211 / 0.2632 / 0.1579 / 0.1579 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| data_completeness +0.05 | 0.3810 / 0.2381 / 0.1905 / 0.1905 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |
| data_completeness -0.05 | 0.4211 / 0.2632 / 0.2105 / 0.1053 | synthetic-a, synthetic-b, synthetic-c, synthetic-d, synthetic-e | no | 0 |

Verdict: **stable** under ±0.05 shifts.

#### Scenario `documentation-trade-off` (synthetic)

Baseline criterion scores (synthetic inputs) and weighted contributions:

| Investigation | purpose_relevance (score → contribution) | condition_match (score → contribution) | source_traceability (score → contribution) | data_completeness (score → contribution) | Total |
|---|---|---|---|---|---|
| `synthetic-q` | 1.0000 → 0.4000 | 0.0000 → 0.0000 | 1.0000 → 0.2000 | 1.0000 → 0.1500 | 0.7500 |
| `synthetic-p` | 1.0000 → 0.4000 | 0.5000 → 0.1250 | 0.2500 → 0.0500 | 0.2000 → 0.0300 | 0.6050 |
| `synthetic-r` | 0.0000 → 0.0000 | 1.0000 → 0.2500 | 1.0000 → 0.2000 | 0.9000 → 0.1350 | 0.5850 |
| `synthetic-s` | 0.0000 → 0.0000 | 0.5000 → 0.1250 | 0.7500 → 0.1500 | 0.7000 → 0.1050 | 0.3800 |

Baseline order: `synthetic-q`, `synthetic-p`, `synthetic-r`, `synthetic-s`

| Shift | Effective weights (P / C / T / D) | Order | Top 3 changed | Max rank shift |
|---|---|---|---|---|
| purpose_relevance +0.05 | 0.4286 / 0.2381 / 0.1905 / 0.1429 | synthetic-q, synthetic-p, synthetic-r, synthetic-s | no | 0 |
| purpose_relevance -0.05 | 0.3684 / 0.2632 / 0.2105 / 0.1579 | synthetic-q, synthetic-r, synthetic-p, synthetic-s | **yes** | 1 |
| condition_match +0.05 | 0.3810 / 0.2857 / 0.1905 / 0.1429 | synthetic-q, synthetic-r, synthetic-p, synthetic-s | **yes** | 1 |
| condition_match -0.05 | 0.4211 / 0.2105 / 0.2105 / 0.1579 | synthetic-q, synthetic-p, synthetic-r, synthetic-s | no | 0 |
| source_traceability +0.05 | 0.3810 / 0.2381 / 0.2381 / 0.1429 | synthetic-q, synthetic-r, synthetic-p, synthetic-s | **yes** | 1 |
| source_traceability -0.05 | 0.4211 / 0.2632 / 0.1579 / 0.1579 | synthetic-q, synthetic-p, synthetic-r, synthetic-s | no | 0 |
| data_completeness +0.05 | 0.3810 / 0.2381 / 0.1905 / 0.1905 | synthetic-q, synthetic-r, synthetic-p, synthetic-s | **yes** | 1 |
| data_completeness -0.05 | 0.4211 / 0.2632 / 0.2105 / 0.1053 | synthetic-q, synthetic-p, synthetic-r, synthetic-s | no | 0 |

Verdict: **weight-sensitive** under ±0.05 shifts.

## What the examples show

- In `well-separated`, no ±0.05 shift changes any position. A ranking like this can be shown without a sensitivity warning.
- In `documentation-trade-off`, positions 2 and 3 swap in 4 of 8 scenarios: lowering purpose relevance, or raising condition match, traceability or completeness, moves `synthetic-r` ahead of `synthetic-p`. The ranking would need the weight-sensitive warning.
- The same example illustrates Member 1's caution: `synthetic-q` ranks first with a condition-match score of 0, because 35 % of the weight (traceability and completeness) rewards documentation rather than fire-safety relevance. The proposed disclaimer states this (`CRITERIA_ENVIRONMENT_CONTEXT.md`).

## Before the R1 freeze

1. Members 1 and 3 accept or change this method.
2. Once curated, provenance-checked measured findings exist (after CP2), Member 1's production ranking (B4) produces the real criterion scores for each environment, and the same assessment is run on them for all six contexts. The result is recorded here, replacing nothing above. If any context is weight-sensitive, that is stated in the UI.
3. Only then are the weights frozen in `config/ranking_criteria_v1.json`, in their own commit, with Member 1 and Member 3 approval.
