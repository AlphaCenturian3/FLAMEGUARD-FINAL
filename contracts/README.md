# Integration contract v0.2.0 (proposed for CP1)

This is the agreement between Members 1 (backend), 2 (frontend), 3 (data and TARS evidence) and 5 (research), so each can develop independently. The summary is in master spec §5. The change log from v0.1.0 is at the bottom.

## Files

| Schema | Used by |
|---|---|
| `schemas/common.schema.json` | Shared definitions: ids, environments, value status, dates, URLs |
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
4. **Units** are exactly the strings in `vocabulary.json`. `"1"` means dimensionless. Never convert units. If a source uses a different unit, raise a contract PR before you enter the value.
5. **Strings vs. numbers.** A quantity's value is a number, or `null` when missing. A string `value` is allowed only for a qualitative statement, and then `quantity` and `unit` are `null`.
6. **IDs** use one pattern (`^[a-z0-9][a-z0-9_.-]*$`, at most 128 characters) in three separate spaces: manifest ids, investigation ids and finding ids. Each id is unique within its own space. `Finding.provenance.derived_from` uses finding ids. `manifest.derived_from` uses manifest ids.
7. **Simulations** exist only as `SimulationResult`. The `Finding`, `Comparison`, `Ranking` and `AssistantAnswer` schemas reject `illustrative_simulation`, and no extra keys are allowed that could carry simulated values.
8. **Planned endpoints** return `501` with an `Error` body until they are implemented.

## Rules schemas cannot express

These rules span several files or depend on computed values. Each one has a member who enforces it in code and a different member who tests it independently (spec §4.4).

| Rule | Statement | Enforced by / independently tested by |
|---|---|---|
| S0 | Registered JSON files contain no `NaN` or `Infinity` | `tools/check_data_provenance.py` (done; Member 3) / `tests/test_provenance.py` |
| S1 | A measured finding's `manifest_id` points to a `measured` manifest entry whose file contains that finding | M3 (D4) / M1 (B1 loader) |
| S2 | `data/curated/findings/<id>.json` contains only findings with `investigation_id == <id>` | M3 (D4) / M1 (B1 loader) |
| S3 | `derived_from` ids resolve to measured or interpretation findings, with no cycles | M5 (R2, R3) / M3 (D4) |
| S4 | `Investigation.datasets` ids resolve to manifest entries | M3 (D4) / M1 (B1 loader) |
| S5 | **Comparison.** `comparable` is `false` when any row is not `reported`, when a condition key is reported with different values across rows, or when a condition key is reported for some rows and `null` for others. Each such case gives one reason. Every row's `finding_id` resolves to a measured finding with the same `quantity` and `unit`. | M1 (B3) / M5 (Q2) |
| S6 | **Ranking.** Weights sum to 1. Each item has exactly one score per criterion, using ids from `criteria`. `score` = Σ weight × criterion score within 1e-9. Ranks are 1 to n, unique and ordered by descending score. No investigation appears in both `items` and `excluded`. Every input resolves. | M1 (B4) / M5 (Q2) |
| S7 | List `total` equals `len(items)` | M1 (B2) / M1 (Q1 integration) and M2 (Q4) |
| S8 | Each assistant citation's `finding_id` resolves, and its `source` is one of that finding's sources, and was returned by `retrieve()` | M1 (B6) with M3 (T1) / M5 (Q2) |

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
| `/api/compare` (501 stub); `error.code` enum; shared `common.schema.json` | Comparison had no endpoint, and environment and id rules were duplicated |
| Removed `validated_against_measured` from simulations | No reference format exists for it yet |
| **P0 additions (PR #5):** `Finding.relevant_environments` and `Finding.limitations` (interpretation only; limitations required there); `AssistantAnswer.limitations` (required; at least 1 in `ai`/`fallback_quotes`) | Moon/Mars recommendations (R3) need an environment tag, and TARS must identify uncertainty. Both schemas forbid extra keys, so adding the fields after CP1 would be a breaking change |
