# Integration contract v0.2.0 (proposed for CP1)

This is the agreement between Members 1 (backend), 2 (frontend), 3 (data and TARS evidence) and 5 (research), so each can develop independently. The summary is in master spec §5. The change log from v0.1.0 is at the bottom.

## Files

| Schema | Used by |
|---|---|
| `schemas/common.schema.json` | Shared definitions: ids, environments, value status, curation notes, dates, URLs |
| `schemas/quantity_rules.schema.json` | Quantity → unit and physical bounds, kept identical to `vocabulary.json` by a test |
| `schemas/source.schema.json` | Citation embedded in every scientific object |
| `schemas/conditions.schema.json` | Experimental conditions on findings and comparison rows |
| `schemas/finding.schema.json` | Curated findings files and ranking and assistant inputs |
| `schemas/finding_list.schema.json` | `GET /api/findings` |
| `schemas/investigation.schema.json` | `GET /api/investigations/{id}`, `data/curated/investigations.json` (an array of these) |
| `schemas/investigation_list.schema.json` | `GET /api/investigations` |
| `schemas/comparison.schema.json` | `GET /api/compare` |
| `schemas/ranking.schema.json` | `GET /api/rankings` |
| `schemas/assistant_request.schema.json`, `assistant_answer.schema.json` | `POST /api/assistant/ask` |
| `schemas/simulation_result.schema.json` | `GET /api/simulations/{id}` |
| `schemas/data_manifest.schema.json` | `data/manifest.json` |
| `schemas/health.schema.json`, `error.schema.json` | Health check and every non-2xx response |
| `vocabulary.json` | Allowed `quantity` keys, units and bounds |

`examples/*.json` are **fixtures**: every scientific example, and every item in a list example, has `"fixture": true` and placeholder content. None of it is NASA data. CI validates every example (`tests/test_contracts.py`) and checks that 33 rule-breaking mutations, plus a bad date under a validator without format checking, are rejected (`tests/test_contract_loopholes.py`).

## Conventions every workstream must share

1. **Absent and null.** Required keys are always present. `null` means not reported. Do not leave a key out to mean "unknown". Every key in `conditions` is required for this reason.
2. **Dates** are `YYYY-MM-DD`, enforced by a pattern. Never rely on JSON Schema `format`, because many validators skip it (Ajv does by default). A test confirms that a validator without format checking still rejects bad dates.
3. **Numbers.** Plain JSON numbers only. `NaN` and `Infinity` are forbidden (rule S0). Python's `json` accepts them by default and `NaN` passes schema bounds, so parse with `tools/check_data_provenance.load_strict_json` or the same `parse_constant` rule. When writing, use `json.dump(..., allow_nan=False)`.
4. **Units** are exactly the strings in `vocabulary.json`. `"1"` means dimensionless.
   - **Quantity values are never converted.** If a source reports a quantity in a different unit, raise a contract PR before you enter it.
   - **Condition values** (the `conditions` keys) may be converted only by an exact defined factor, in Member 3's curation tool. The as-printed value and unit stay in the registered source file that the finding's `locator` points to (decision C2).
   - The only factor allowed so far is **mmHg → kPa: 1 mmHg = 0.133322387415 kPa**. This is the conventional millimetre of mercury, defined as 13.5951 g/cm³ × 9.80665 m/s² × 1 mm; NIST SP 811 lists it rounded to 1.333224 × 10² Pa. Do not use the torr (101.325/760 kPa), which differs in the 7th significant digit. Any new factor needs a contract PR.
5. **Strings vs. numbers.** A quantity's value is a number, or `null` when missing. A string `value` is allowed only for a qualitative statement, and then `quantity` and `unit` are `null`.
6. **IDs** use one pattern (`^[a-z0-9][a-z0-9_.-]*$`, at most 128 characters) in three separate spaces: manifest ids, investigation ids and finding ids. Each id is unique within its own space. `Finding.provenance.derived_from` uses finding ids. `manifest.derived_from` uses manifest ids.
7. **Simulations** exist only as `SimulationResult`. The `Finding`, `Comparison`, `Ranking` and `AssistantAnswer` schemas reject `illustrative_simulation`, and no extra keys are allowed that could carry simulated values.
8. **Planned endpoints** return `501` with an `Error` body until they are implemented.
9. **Data-quality flags** (decision C3, corrected at CP1). Four cases stay distinct, and the schema enforces it:

   | Case | `value_status` | `value` | Explanation goes in |
   |---|---|---|---|
   | Source-reported uncertainty | `reported` | the number | `uncertainty`: **only** text the source itself reports |
   | Curator caution (flag `caution`) | `reported` | the number | `curation_notes[]` with `kind: "caution"`, `generated_by: "FlameGuard-SI"` |
   | Excluded measurement (flag `exclude`) | `excluded` | `null` | `curation_notes[]` with `kind: "exclusion"`, a reason, a `flag_ref` (`manifest_id` + `flag_id`) to the reviewed quality-flag record, and the `source` passage the flag rests on, with a recorded quote. The printed value stays in the registered source file that the `locator` points to |
   | Missing in the source (dash, `not_available`) | `not_reported` | `null` | nothing; an exclusion note is not allowed |

   - `excluded` is allowed only on measured findings, and keeps every measured provenance requirement (`manifest_id`, `locator`, `sources`).
   - An exclusion note forces `excluded`, so an excluded value can never stay numerically available.
   - `curation_notes` is not allowed on interpretation findings, which use `limitations`.
   - Source files are never edited to remove a value.
   - **Exact flag mapping** (machine-readable as `x-flag-ranking-use` on `curation_note.kind`; rule S10): flag `caution` → note `kind: "caution"`; flag `exclude` → note `kind: "exclusion"` plus `excluded`; flag `not_available` → `not_reported`, and **no note is created for that flag**. There are no other cases. Every note carries a `flag_ref` and a `source` with a recorded quote, so FlameGuard-SI text on a measured value always traces back to a reviewed flag and the source passage behind it. A whole-row caution can still add a caution note to a `not_reported` finding; what is forbidden is a note that comes from a `not_available` flag.
   - **Quotes are verified, not just present.** The schema checks only shapes. Each referenced flag row's NASA quote and page must be verified against the registered source document's text (S10). A non-empty string in JSON does not count as verification. A **recorded** quote (present in the data, which the schema checks) is never called an **authenticated** quote until S10(d) has passed and Member 5's Q3 check has logged it. `tests/test_curation_attribution.py` shows that an invented quote with a valid shape still passes the schema.
10. **`uncertainty` is source text only.** FlameGuard-SI judgments never go in it. The Q3 spot check verifies `uncertainty` against the source, along with values and quotes.

## Rules schemas cannot express

These rules span several files or depend on computed values. Each one has a member who enforces it in code and a different member who tests it independently (spec §4.4).

| Rule | Statement | Enforced by / independently tested by |
|---|---|---|
| S0 | Registered JSON files contain no `NaN` or `Infinity` | `tools/check_data_provenance.py` (done; Member 3) / `tests/test_provenance.py` |
| S1 | A measured finding's `manifest_id` points to a `measured` manifest entry whose file contains that finding | M3 (D4) / M1 (B1 loader) |
| S2 | `data/curated/findings/<id>.json` contains only findings with `investigation_id == <id>` | M3 (D4) / M1 (B1 loader) |
| S3 | `derived_from` ids resolve to measured or interpretation findings, with no cycles. An interpretation that depends on an `excluded` finding at any depth is restricted by S9 | M5 (R2, R3) / M3 (D4) |
| S4 | `Investigation.datasets` ids resolve to manifest entries | M3 (D4) / M1 (B1 loader) |
| S5 | **Comparison.** `comparable` is `false` when any row is not `reported`, when a condition key is reported with different values across rows, or when a condition key is reported for some rows and `null` for others. Each such case gives one reason. Every row's `finding_id` resolves to a measured finding with the same `quantity` and `unit`. | M1 (B3) / M5 (Q2) |
| S6 | **Ranking.** Weights sum to 1. Each item has exactly one score per criterion, using ids from `criteria`. `score` = Σ weight × criterion score within 1e-9. Ranks are 1 to n, unique and ordered by descending score. No investigation appears in both `items` and `excluded`. Every input resolves. | M1 (B4) / M5 (Q2) |
| S7 | List `total` equals `len(items)` | M1 (B2) / M1 (Q1 integration) and M2 (Q4) |
| S8 | Each assistant citation's `finding_id` resolves, and its `source` is one of that finding's sources, and was returned by `retrieve()` | M1 (B6) with M3 (T1) / M5 (Q2) |
| S9 | **Excluded findings** are never ranking inputs, never count as reported evidence in a score, and appear in `/api/compare` only as non-comparable rows (the schema already forbids `comparable: true` with them). TARS may cite one only to explain an exclusion, and never states the excluded value. It never cites one as support for a scientific claim. Testable form: for every cited `excluded` finding, the answer text does not contain the value printed at its `locator`, and the citation sits only in a sentence about the exclusion. **S9 is transitive.** A finding is *exclusion-dependent* if it is `excluded`, or if any `derived_from` ancestor at any depth is `excluded`. An exclusion-dependent interpretation may exist **only to explain an exclusion**: its `value` and `quantity` are `null`, its `limitations` say it explains an excluded value, it carries no `relevant_environments` (so it is never a Moon/Mars recommendation), and its explanation stays traceable through `derived_from` to the exclusion notes. It is never a ranking input or part of a criterion score, never a comparable row, and never TARS evidence for a conclusion. TARS may cite it only in an answer whose `limitations` explain the exclusion, and never states the excluded value. A `derived_from` cycle or an unresolved id makes the whole chain invalid (S3), never "not dependent". Contract oracle: `tests/test_exclusion_dependency.py` (identified by Member 2, PR #1). | M1 (B3, B4, B6) / M5 (Q2) |
| S10 | **Flags to findings** (convention 9 mapping). (a) Each `curation_notes[].flag_ref` resolves to a row of a manifest-registered, interpretation-class quality-flags file whose `ranking_use` equals `x-flag-ranking-use[kind]`, whose test or row matches the finding's `locator`, and whose field is the finding's field or `*`. (b) Coverage: every `exclude` row that applies to an emitted finding makes it `excluded` with an exclusion note for that row, and every `caution` row gives a caution note on each finding it applies to. (c) Every `not_available` cell is `not_reported`, and no note references a `not_available` row. (d) Each referenced flag row's verbatim quote and page are verified against the registered source document's text. | M3 (derivation tool D4, `tests/data/`) / M5 (`tests/research/`, Q3) |

## Changing the contract

Follow spec §5.4. The PR touches only `contracts/`, the spec and the version constant. Members 1 and 2 approve it; Members 3 and 5 approve as well when a data, interpretation or ranking rule changes. Bump `CONTRACT_VERSION`, the spec version and `vocabulary_version` together, since a test checks that they match. When you change `vocabulary.json`, update `quantity_rules.schema.json` to match exactly; a test checks this too.

## Changes from v0.1.0

| Change | Why |
|---|---|
| Removed `illustrative_simulation` from `Finding`; `additionalProperties: false` on findings and both provenance shapes | v0.1.0 accepted a simulation as a valid `Finding`, and later drafts still accepted `model` or `label` keys on a measured finding |
| Comparison rows require `evidence_class: "measured"` and follow the value/status rule; `comparable: true` needs at least 2 reported rows and no reasons | Rows could omit their class, fill a missing value, or claim to be comparable with a missing value |
| `quantity_rules` (enum, unit and bounds per quantity) applied to findings and comparisons | Unknown quantities, wrong units, numbers stored as strings and negative rates were accepted |
| `locator` on measured provenance; `value_status`; `vocabulary.json` | A value could be traced to a file but not to a place in it, and "not reported" could not be told apart from "not applicable" |
| `conditions` with every key required | Absent vs. `null` was ambiguous, so comparison was undefined |
| `comparison`, `ranking`, `assistant_*`, `finding_list` and `investigation_list` schemas | These existed only as prose, and a generic list envelope did not say what its items were |
| Ranking: at least 1 criterion score; a non-zero criterion score must cite inputs | Scores could appear with no trace to evidence |
| Date pattern, `http(s)` URL pattern, non-empty strings or `null` | `"retrieved": "yesterday"`, `"url": "x"` and empty quotes were accepted |
| Manifest schema mirrors the provenance checker (a test checks they agree); interpretations live under `data/curated/interpretations/` | The schema accepted measured entries with no sources or rights status, which the tool rejected |
| Strict JSON parsing (S0) | `NaN` passed every numeric bound |
| **Attribution correction (CP1):** `curation_notes` (FlameGuard-SI cautions and exclusions, each with a required `flag_ref` and `source` quote); `value_status: "excluded"`; `uncertainty` reserved for source text; exact flag mapping (`x-flag-ranking-use`), rule S10 and the frontend display rules. The required `flag_ref`, the source quote per note, S10, the flag mapping and the `excluded` name were **contributed by Member 2 (`buihhlong-a11y`, PR #7)** | C3 had put FlameGuard-SI caution text into `uncertainty` ("as reported by the source"), and excluded values simply vanished. Readers could not tell source uncertainty from curator judgment, or an excluded value from a missing one. The change is additive: every document that was valid before is still valid |
| **Transitive exclusion protection (CP1, Command Center Option (a)):** S9 extended to every `derived_from` descendant of an `excluded` finding; S3 cross-reference; no schema change | An interpretation built on an excluded value could otherwise reach a ranking, a comparison, a TARS conclusion or a Moon/Mars recommendation through its `derived_from` chain. Gap identified by Member 2 (`buihhlong-a11y`) |
| `/api/compare` (501 stub); `error.code` enum; shared `common.schema.json` | Comparison had no endpoint, and environment and id rules were duplicated |
| Removed `validated_against_measured` from simulations | No reference format exists for it yet |
| **P0 additions (PR #5):** `Finding.relevant_environments` and `Finding.limitations` (interpretation only; limitations required there); `AssistantAnswer.limitations` (required; at least 1 in `ai`/`fallback_quotes`) | Moon/Mars recommendations (R3) need an environment tag, and TARS must identify uncertainty. Both schemas forbid extra keys, so adding the fields after CP1 would be a breaking change |
