# Ranking criteria for the environment-only interface (D-01, condition 1)

**Status:** proposal by Member 5 for Member 1 and Member 3 review. **Not approved.** The ranking stays disabled. This document defines the criteria; it does not change `config/research_relevance_criteria_v1.proposed.json`, the reference implementation, or any contract. Member 1 owns the production implementation (B4).

## Interface

Contract v0.2.0 (CP1 candidate `ca128d0`) ranks with one input: `GET /api/rankings?context=<environment>`, where the environment is one of `spacecraft`, `space_station`, `lunar_base`, `martian_base`, `pressurized_rover` or `earth`. There are no user-supplied topics, quantities or conditions (a research-question input is a v0.3 candidate, D-06). Every criterion below therefore depends only on the context and the curated data.

**Eligible evidence:** curated measured findings (and interpretation findings derived from them) that passed the provenance check and the loader. An investigation with no measured evidence goes in `excluded` with the reason "insufficient evidence" (D-03).

**Score:** `score = 0.40·P + 0.25·C + 0.20·T + 0.15·D`, each criterion in [0, 1] (continuous, D-02). The weights are proposed, not approved.

## 1. `purpose_relevance` (P, weight 0.40)

**Proposed definition (P1, recommended for P0):** P = 1 if the investigation's curated `Investigation.relevant_environments` contains the context, otherwise 0.

- The tag comes from the **Investigation** object, which **Member 3** curates with sources. It does not come from interpretation tags written by Member 5, so the author of the criteria does not also set the tags that drive the score (Member 1's condition).
- P is binary, so it moves an investigation by 0.40 at once. The sensitivity assessment shows the effect (`WEIGHT_SENSITIVITY.md`).

**Alternative (P2, not recommended for P0):** P = ½·(environment tag) + ½·(share of fire-safety topics covered by the investigation's measured findings). It needs per-environment topic priorities, which would be an editorial choice with no source. Listed for completeness.

**Contract question Q-1 (Member 1):** for a non-zero criterion score the ranking schema requires at least one input `finding_id`, but P's signal is on the Investigation, not a finding. Proposal: cite the investigation's eligible measured findings as inputs and name the `relevant_environments` tag and its source in the rationale. Member 1 decides whether that satisfies the schema's intent or needs a v0.3 change.

## 2. `condition_match` (C, weight 0.25)

**Reference conditions** come from `environment_reference.json` (D-01, condition 2). Each condition is either **assessable** (a cited reference exists) or **reference unknown**.

| Context | Gravity (contract category) | O₂ mole fraction reference | Pressure reference (kPa) | Assessable conditions |
|---|---|---|---|---|
| `space_station` | microgravity (physical) | 0.21 (ISS, operational) | 101.3 (ISS, operational) | 3 |
| `spacecraft` | microgravity (**editorial classification**, Member 1 to confirm) | 0.265 (Gateway nominal, design assumption) | 70.3 (Gateway, design assumption); 101.4 (Mars transit, design assumption) | 3 |
| `lunar_base` | partial_gravity (physical: 1.62 m/s²) | 0.265 or 0.34 (Surface Habitat nominal or capability, design assumption) | 70.3 or 56.5 (Surface Habitat, design assumption) | 3 |
| `martian_base` | partial_gravity (physical: 3.73 m/s²) | **unknown** (no habitat atmosphere found) | **unknown** | 1 (gravity only) |
| `pressurized_rover` | partial_gravity (**location-dependent**; lunar rover assumed) | **unknown** | **unknown** | 1 (gravity only) |
| `earth` | normal_gravity (physical) | 0.2095 (physical) | 101.4 (physical) | 3 |

**Proposed matching rule:** a condition is matched if at least one eligible measured finding of the investigation reports a value that matches any listed reference point:

- gravity: exact category match;
- oxygen mole fraction: within **±0.02** (absolute) of a reference point;
- pressure: within **±10 %** (relative) of a reference point.

The tolerances are **editorial proposals with no source**. Member 1 decides them (new decision D-13).

**Score:** C = matched / assessable.

- A condition whose reference is unknown is **not** in the denominator and is listed as "reference unknown".
- A condition the findings do not report counts as unmatched and is listed as "not reported" (D-03: this penalizes less-documented investigations, which the methodology states).
- If no condition is assessable, C = 0 with empty inputs and status `not_assessed` (cannot happen with the table above, because gravity is always assessable).

**Limits to state in the UI:**

- The contract's `gravity_environment` is a category, so lunar (0.165 g) and Martian (0.380 g) gravity both map to `partial_gravity` and cannot be told apart. A numeric gravity level is a v0.3 candidate.
- Matching a habitat **design** atmosphere does not make a microgravity test lunar or Martian evidence; the gravity condition still differs.
- `martian_base` and `pressurized_rover` are assessed on gravity alone, so their C scores are not comparable with the other contexts.

**Illustration (hypothetical conditions, not NASA data):** a test reported as microgravity, O₂ 0.21, 101.3 kPa, ranked for `lunar_base`: gravity unmatched (microgravity ≠ partial_gravity); O₂ unmatched (0.21 is 0.055 from 0.265); pressure unmatched (101.3 is 44 % above 70.3). C = 0/3. For `space_station` the same test gives C = 3/3.

## 3. `source_traceability` (T, weight 0.20)

Independent of the context. Per eligible finding: the share of four checks on its best source (http(s) URL; retrieval date; exact quote; locator, archive id or DOI). An interpretation takes the mean of the findings it is derived from, and unresolved inputs count as 0. T is the mean over eligible findings.

## 4. `data_completeness` (D, weight 0.15)

Independent of the context. Per eligible finding: the share reported among the eight condition keys and the test id, plus value and uncertainty for quantities. D is the mean over eligible findings.

## Disclaimer text (proposed)

> Research-relevance score: how well the curated evidence matches the selected environment. It is not a fire-danger, fire-risk or hazard score, and not a probability. 35 % of the score (traceability 20 %, completeness 15 %) measures how well the evidence is documented, not how relevant it is to fire safety in the selected environment.

## Status of the reference implementation

`backend/flameguard/research/ranking.py` (Member 5's reference, moving to `research/` after CP1) still implements the earlier structured-question form. It is **not** updated in this change, so that Member 1 and Member 3 can review these definitions first and Member 1's B4 remains the only runtime. After approval, Member 5 updates the reference implementation to these definitions and `tests/research/` compares it with Member 1's output.

## Decisions requested

| ID | Question | Owner |
|---|---|---|
| D-01 (conditions 1–3) | Accept these definitions, the reference table and the sensitivity method; then co-approve the weights | M1 and M3 |
| D-13 | O₂ and pressure tolerances (±0.02, ±10 % proposed); gravity class for `spacecraft` and `pressurized_rover` | M1 |
| Q-1 | Inputs for P when the signal is investigation-level | M1 |
| — | Curate `Investigation.relevant_environments` with sources for each investigation | M3 |
