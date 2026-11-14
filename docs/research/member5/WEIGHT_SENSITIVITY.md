# Weight-sensitivity assessment (D-01, condition 3)

**Status:** method proposal for Member 1 and Member 3 review. **No NASA data is used.** Every number below comes from a **synthetic software fixture** (`tests/fixtures/research/synthetic_criterion_scores.json`, marked `fixture: true`), with placeholder ids that correspond to no investigation. The results show how the method behaves; they are not findings, and they are not a ranking of NASA investigations. The ranking stays disabled.

**Revision 2:** records Member 1's applicability-dominance invariant ([PR #3 comment 6883984161](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883984161), an owner proposal, not an approval). The ±0.05 method is unchanged. The worked examples below still use the **superseded four-criterion structure** (with `purpose_relevance`). They demonstrate the method only, and are not redone until a weight set for C, T and D is proposed through the approval process. **This is not validation on NASA measurements.**

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

## Applicability-dominance invariant (Member 1 requirement; not yet approved)

### The rule

Member 1's proposal, after the eligibility gates (E1–E3 in `CRITERIA_ENVIRONMENT_CONTEXT.md`), weights only condition match C, source traceability T and data completeness D, and requires:

> **w_C · Δ_min > w_T + w_D**

**Why it works.** T and D each lie in [0, 1], so between any two eligible investigations the T and D terms together can differ by at most `w_T + w_D`. If every non-zero difference in C is worth more than that, then an investigation with a lower C can never outrank one with a higher C. In particular, an investigation with C = 0 can never outrank one with C > 0, whatever their documentation. The score stays a weighted sum, so ranking rule S6 is unchanged.

### Defining Δ_min

Δ_min is the **smallest non-zero difference that C can take** between two eligible investigations for one context. It follows from how C is defined, not from data:

| Definition of C | Possible C values | Δ_min | Invariant requires |
|---|---|---|---|
| Gravity only (P0 proposal) | {0, 1} | **1** | w_C > w_T + w_D, i.e. **w_C > 0.5** |
| k equally weighted assessable conditions | {0, 1/k, …, 1} | 1/k | w_C > k · (w_T + w_D); for k = 3, w_C > 0.75 |
| Continuous matching (for example a distance-based score) | any value in [0, 1] | no positive minimum | **cannot be satisfied**; C would first have to take a fixed set of values |

With the weights summing to 1, `w_C · Δ_min > 1 − w_C` gives **`w_C > 1 / (1 + Δ_min)`**.

### Can Δ_min be established from available evidence?

- **The value of Δ_min: yes, by definition.** Under the gravity-only proposal, Δ_min = 1 exactly. No measurement is needed.
- **Whether the invariant does anything for a context: no, not yet.** That depends on the curated data, which does not exist yet (CP2):
  - No provenance-checked measured finding exists, so no investigation currently passes E1.
  - Every investigation in Member 5's register (BASS-II, FLEX, SoFIE, Saffire) ran in microgravity, and FM² has no verified data. For `lunar_base` or `martian_base`, every eligible investigation would therefore have C = 0. The invariant would hold only **vacuously**, and the order would come from T and D alone. The UI must say so, or the ranking for that context should not be shown (open point 1 in `CRITERIA_ENVIRONMENT_CONTEXT.md`).
  - For `space_station` and `spacecraft`, eligible microgravity investigations would all have C = 1. C would then not separate them, and the order would again come from T and D.
  - So with gravity-only C, the invariant separates investigations only for a context where **some** eligible investigations match the gravity reference and others do not. Whether that happens is known only once real data exists, at CP2.
  - **Member 5 records the gravity-only model as insufficiently discriminating** for the current evidence, and has asked Member 1 for a methodological decision (options M-1 to M-4 in `CRITERIA_ENVIRONMENT_CONTEXT.md`) before any production ranking implementation.

### Why the original 40 / 25 / 20 / 15 weights fail

| Weight set | w_C | w_T + w_D | w_C · Δ_min with Δ_min = 1 | Invariant |
|---|---|---|---|---|
| Original proposal (P 0.40, C 0.25, T 0.20, D 0.15) | 0.25 | 0.35 | 0.25 | **fails** (0.25 < 0.35) |
| The same set with P removed and the rest rescaled (C 0.4167, T 0.3333, D 0.25) | 0.4167 | 0.5833 | 0.4167 | **fails** (0.4167 < 0.5833) |

For any Δ_min ≤ 1, `w_C · Δ_min ≤ w_C`, so a weight set fails whenever `w_C ≤ w_T + w_D`. In the original set w_C = 0.25 and w_T + w_D = 0.35, so it fails for **every** possible Δ_min. Removing P does not help, because rescaling keeps the ratio of C to T + D (0.25 : 0.35). The synthetic `documentation-trade-off` example above shows the failure: `synthetic-q` (C = 0) ranks above `synthetic-p` (C = 0.5).

**No replacement weight set is proposed here.** The invariant gives a lower bound on w_C (w_C > 0.5 under gravity-only C). Choosing actual values, and deciding whether T earns any weight (Member 1: once the loader enforces provenance it may barely vary), needs real criterion scores at CP2 and the approval of Members 1 and 3.

### How the gates and the weighted score interact

1. **Gates first.** E1 (measured evidence), E2 (source-stated environment tag) and E3 (integrity) decide eligibility. A failing investigation is listed in `excluded` with its first failing gate. It is never ranked low; it is not ranked at all.
2. **Purpose is no longer weighted.** E2 replaces the old 0.40 `purpose_relevance` criterion. That removes the binary 0.40 jump, and documentation can no longer lift an investigation its sources do not tie to the environment.
3. **Weighted score among eligible investigations only.** C, T and D order the eligible set, and the invariant guarantees that C dominates documentation.
4. **Sensitivity analysis afterwards.** The ±0.05 method is applied to w_C, w_T and w_D (three weights, six scenarios) and must check the invariant in **every** perturbed scenario, not only the baseline. A weight set within 0.05 of the bound `1 / (1 + Δ_min)` would break the invariant under some perturbation, so it is fragile and must be reported as such.
5. **Empty results are reported.** If the gates leave no investigation, or none with C > 0, the result says that rather than producing an order.

### What needs Member 1 and Member 3 approval

| Item | Needs |
|---|---|
| Gates E1–E3, especially the E2 tag-provenance rule | Member 1 (proposer) and **Member 3** (owner of the tags) |
| Gravity-only C and its Δ_min = 1 | Members 1 and 3 |
| The invariant itself, as a test in Member 5's reference implementation and in Member 1's B4 | Members 1 and 3 |
| Any weight set (w_C, w_T, w_D) | Members 1 and 3, **after** real criterion scores and a sensitivity rerun at CP2; then frozen alone in `config/ranking_criteria_v1.json` |
| Behaviour when a context has no scorable C (reference unknown, or C constant across eligible investigations) | Members 1 and 3 |
| Any later scoring of O₂ or pressure (changes Δ_min) | A cited equivalence tolerance, Members 1 and 3, and a rerun |

## Before the R1 freeze

1. Members 1 and 3 accept or change this method.
2. Once curated, provenance-checked measured findings exist (after CP2), Member 1's production ranking (B4) produces the real criterion scores for each environment, and the same assessment is run on them for all six contexts. The result is recorded here, replacing nothing above. If any context is weight-sensitive, that is stated in the UI.
3. Only then are the weights frozen in `config/ranking_criteria_v1.json`, in their own commit, with Member 1 and Member 3 approval.
