# Ranking criteria for the environment-only interface (D-01, condition 1). Revision 2

**Status:** proposal, **not approved**. Revised after Member 1's owner answers on PR #3 ([comment 6883984161](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6883984161), 2026-11-14), which are owner proposals and not approvals. The eligibility gates are **pending Member 3's approval of the tag-provenance rule**. No weights are frozen, rankings stay disabled, and nothing here changes `config/`, a contract or any runtime code. Member 1 owns the production implementation (B4); Member 5's reference implementation is updated only after CP1 and the move to `research/`.

**What changed from revision 1:**

- `purpose_relevance` is **removed from the weighted score** and becomes eligibility gate E2.
- `condition_match` is **scored on gravity only**.
- O₂ and pressure are **descriptive, not scored**.
- The proposed O₂ and pressure tolerances are **inactive**.
- Contract question Q-1 no longer arises, because the gate needs no criterion inputs.

## Interface

Contract v0.2.0 (CP1 candidate `a6876d1`) ranks with one input: `GET /api/rankings?context=<environment>`, one of `spacecraft`, `space_station`, `lunar_base`, `martian_base`, `pressurized_rover`, `earth`. There are no user-supplied topics, quantities or conditions (D-06: v0.3).

The ranking has two stages: **eligibility gates**, then a **weighted score** for the investigations that pass.

## Stage 1: eligibility gates (Member 1 proposal; pending Member 3)

An investigation is scored for a context only if it passes **every** gate. Otherwise it goes in the ranking's `excluded` list, and the reason given is the **first** gate it fails, checked in the order E1, E2, E3. The contract supports this without change.

| Gate | Passes when | Fails when | Notes |
|---|---|---|---|
| **E1 Evidence** | The investigation has at least one eligible **measured** finding that is either `value_status: reported`, or a measured qualitative finding (quantity, value and unit `null`; `not_applicable`; exact quote and locator; D-05) | No such finding. A finding with `value_status: excluded` never counts (rule S9), and a `not_reported` finding alone does not count | Descriptive investigation text and quoted objectives are **not** measurements and never satisfy E1 |
| **E2 Source-stated relevance** | `Investigation.relevant_environments` contains the context **and** that tag is stated by one of the investigation's own sources, backed by a quote in `Investigation.sources`, with the tag-to-quote mapping recorded in Member 3's data documentation | The tag is absent, or no source states it. An unset tag fails E2 | **Pending Member 3** (tag-provenance rule). The contract has no per-tag provenance field, and none is added |
| **E3 Integrity** | No input is a fixture or a simulation, and rules S0 to S10 pass | Any input fails | S9: `excluded` findings are never inputs. S10: flag resolution and quote checks against the registered source |

Member 1 labelled these gates G1 to G3 (comment 6883984161). This document calls them **E1 to E3**, so they are not confused with the options G0 to G2 in Member 5's earlier decision form.

**What passing means.** Passing the gates means "relevant according to its own sources, and backed by measured evidence". It does **not** mean "applicable under the conditions of that environment". Applicability is what the condition score measures.

**Wider applicability is an interpretation.** A statement such as "an ISS microgravity result informs lunar habitats" is a FlameGuard-SI inference. It belongs in a Member 5 **interpretation finding** (with `relevant_environments`, the required `limitations` and `generated_by: "FlameGuard-SI"`), never in an Investigation tag. So the person who writes the criteria never sets the tags that decide eligibility.

**An empty ranking is a valid result.** If no investigation passes for a context (likely for `lunar_base` and `martian_base` at present), the ranking is reported as empty, with each investigation's failing gate.

## Stage 2: weighted score (weights not determined)

`score = w_C · C + w_T · T + w_D · D`, each criterion in [0, 1] (continuous, D-02). The weights must satisfy the applicability-dominance invariant (see `WEIGHT_SENSITIVITY.md`). **No weights are proposed or approved here.** The earlier proposal (40/25/20/15) cannot satisfy the invariant, and P no longer exists.

### C: condition match, gravity only (P0)

**Reference (D-13 gravity: accepted with labels by Member 1, owner answer):**

| Context | Reference gravity category | Label shown |
|---|---|---|
| `space_station` | microgravity | physical (orbital free fall) |
| `spacecraft` | microgravity | **assumed: coast phase** (excludes launch, entry and landing) |
| `lunar_base` | partial_gravity | physical (1.62 m/s²) |
| `martian_base` | partial_gravity | physical (3.73 m/s²) |
| `pressurized_rover` | partial_gravity | **assumed: lunar rover** (NTRS 20220000245, p. 2) |
| Martian pressurized rover | — | **reference unknown** (the contract context cannot express it; see "Open points") |
| `earth` | normal_gravity | physical |

**Score.**

- C = 1 if at least one eligible measured finding reports a `gravity_environment` equal to the reference category.
- C = 0 if the findings report gravity but none match.
- If no eligible finding reports gravity, C = 0 and the gap is listed as "not reported". This follows D-03, and the methodology states that it penalizes less-documented investigations.
- With a gravity-only C, C takes only the values 0 and 1.

**Reference unknown.** When a context's gravity reference is unknown, the condition is left out of C and listed as "reference unknown". With gravity as the only scored condition, C then has **nothing to score** for that context. How the ranking should behave in that case is an **open decision** (see "Open points").

**Stated limits.**

- Lunar (0.165 g) and Martian (0.380 g) gravity are both `partial_gravity` in the contract, so C cannot distinguish them. A numeric gravity level is a v0.3 candidate.
- Matching a gravity category is not evidence that a test is applicable to a habitat: atmosphere, flow and scale may still differ.

### O₂ and pressure: descriptive, not scored

**D-13 tolerances: inactive (Command Center, recorded by Member 1).** The proposed O₂ ±0.02 and pressure ±10 % tolerances are inactive. No source supports them, and near a material's oxygen limit ±0.02 absolute can move a test across the flammability boundary.

For P0, the UI shows each eligible finding's **reported** O₂ and pressure next to the context's reference points from `environment_reference.json`, each labelled with its status (physical, operational, design assumption, historical recommendation, or reference unknown). These values do **not** enter any score.

Scoring them later requires all of:

1. a cited source that defines an **equivalence** tolerance for this purpose (a chamber's control tolerance is not one);
2. approval by Members 1 and 3;
3. a sensitivity rerun.

When matching becomes active, the result must say **which** reference point matched, because some contexts have two design points.

### T: source traceability

Unchanged and independent of the context. Per eligible finding, the share of four checks on its best source: http(s) URL; retrieval date; exact quote; locator, archive id or DOI. An interpretation takes the mean of the findings it is derived from. Member 1 notes that once the loader enforces provenance, T may barely vary between eligible findings. Whether T carries any information is **measured at CP2** before any weight is chosen.

### D: data completeness

Unchanged and independent of the context. Per eligible finding, the share reported among the eight condition keys and the test id, plus value and uncertainty for quantities.

## Disclaimer text (proposed)

> Research-relevance ranking for the selected environment. An investigation is listed only if its own sources state that it is relevant to the environment and it has measured evidence. The score combines a gravity-condition match with how completely the evidence is documented. It is not a fire-danger, fire-risk or hazard score, not a probability, and it does not show that a result applies under the environment's conditions. Oxygen and pressure are shown for comparison and are not scored.

## Decision status

| ID | Item | Status | Owner(s) |
|---|---|---|---|
| E1–E3 | Eligibility gates | **Owner proposal (Member 1); pending Member 3**; not approved | M1, M3 |
| E2 rule | Tags hold only source-stated environments, each backed by a quote | **Pending Member 3** | M3 (with M1) |
| C | Gravity-only condition match | Owner proposal (Member 1, "For P0, C is scored on gravity only"); not approved | M1, M3 |
| D-13 gravity | Categories and labels above | Accepted with labels (Member 1 owner answer) | M1 |
| D-13 O₂/pressure | Tolerances | **Inactive** (Command Center, via Member 1) | M1, M3 |
| D-13 unknowns | "Reference unknown", left out of the score | Accepted (Member 1 owner answer) | M1 |
| Weights | w_C, w_T, w_D | **Not proposed, not approved**; must satisfy the invariant; real data at CP2 | M1, M3 |
| Q-1 | Criterion inputs for a tag signal | Resolved by the gate (Member 1), pending Member 3 | M1, M3 |

## Scientific flag: the model does not discriminate on current evidence (2026-11-14)

Every investigation documented so far (BASS-II, FLEX, SoFIE, Saffire) ran in **microgravity**, and FM² has no verified data. With binary gravity-only C, **all eligible investigations within one selected context get the same C**: 1 for `space_station` and `spacecraft`, 0 for `lunar_base`, `martian_base`, `pressurized_rover` and `earth`. The applicability-dominance invariant then holds only vacuously, and the order comes from T and D alone. If T barely varies once provenance is enforced, the order is set by **data completeness alone**: documentation, not applicability.

**Member 5 therefore records this scoring model as insufficiently discriminating** for the current evidence. A methodological decision from Member 1 is requested **before any production ranking implementation** ([PR #3 comment 6884182608](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/3#issuecomment-6884182608)):

| Option | Content | Status |
|---|---|---|
| M-1 (Member 5 recommendation for P0) | No weighted order: an unordered eligible-evidence list of gate-passing investigations, with C, O₂ and pressure shown descriptively and the excluded investigations with their reasons. A weighted score only after real CP2 data shows a criterion that separates eligible investigations, with M1 and M3 approval | **AWAITING OWNER RESPONSE** |
| M-2 | Rank by C, T and D, labelled "documentation completeness only" whenever C is constant across the eligible set | **AWAITING OWNER RESPONSE** |
| M-3 | Add another scorable applicability criterion (for example flow configuration or fuel/material category), with a cited reference per environment and a sensitivity rerun | **AWAITING OWNER RESPONSE** |
| M-4 | Defer ranking to v0.3 (numeric gravity level, or O₂ and pressure with a sourced equivalence tolerance) | **AWAITING OWNER RESPONSE** |

## Open points (not decided; for Member 1 and Member 3)

1. **A context whose gravity reference is unknown.** If C has nothing to score, it would be 0 for every eligible investigation, and the order would fall to T and D alone, which is what the invariant is meant to prevent. Options: (a) report no ranking for that context ("reference unknown"); (b) rank by T and D with a visible warning. Member 5 recommends **(a)**.
2. **A Martian pressurized rover cannot be expressed.** `pressurized_rover` is a single context value. Member 1's labels assume a lunar rover; a Martian rover's reference is unknown. Separate contexts would be a v0.3 contract change.
3. **E1 versus D.** E1 can pass on a measured qualitative finding with no quantity, and D gives such a finding fewer checks (no value or uncertainty). Member 1 should confirm this is intended.
4. **Gate order.** The first failing gate is reported in the order E1, E2, E3. If integrity (E3) should be reported first, Member 1 should say so.
5. **Transitive exclusion (S9).** An interpretation derived, at any depth, from an `excluded` finding must never satisfy E1 or count toward any criterion. Member 5 adopted this rule **after CP1** ([PR #1 comment 6884177976](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/1#issuecomment-6884177976)). Member 1's decision is pending.

## Superseded (revision 1, kept for traceability)

Revision 1 defined `purpose_relevance` (weight 0.40) as a binary environment-tag match, and proposed O₂ ±0.02 and pressure ±10 % tolerances. Both are superseded by Member 1's answers above. Revision 1 is in this file's git history (commit `24f710e`).
