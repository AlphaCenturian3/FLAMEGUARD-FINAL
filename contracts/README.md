# Integration contract v0.2.0 (proposed for CP1)

This is the agreement between the backend, frontend and data workstreams, so each can develop independently. The summary is in master spec §5, and the change log from v0.1.0 is at the bottom of this file.

## Files

| Schema | Used by |
|---|---|
| `schemas/source.schema.json` | Citation embedded in every scientific object |
| `schemas/conditions.schema.json` | Experimental conditions on findings and comparison rows |
| `schemas/finding.schema.json` | `/api/findings`, curated findings files, ranking and assistant inputs |
| `schemas/investigation.schema.json` | `/api/investigations`, `data/curated/investigations.json` |
| `schemas/list_envelope.schema.json` | List responses |
| `schemas/comparison.schema.json` | `/api/compare` |
| `schemas/ranking.schema.json` | `/api/rankings` |
| `schemas/assistant_request.schema.json`, `assistant_answer.schema.json` | `/api/assistant/ask` |
| `schemas/simulation_result.schema.json` | `/api/simulations/{id}` |
| `schemas/data_manifest.schema.json` | `data/manifest.json` |
| `schemas/health.schema.json`, `error.schema.json` | Health and every non-2xx response |
| `vocabulary.json` | Allowed `quantity` keys and their units |

`examples/*.json` are **fixtures**. Each scientific example has `"fixture": true` and placeholder content. None of it is NASA data. CI validates every example against its schema (`tests/test_contracts.py`).

## Rules

- `Finding.evidence_class` is `measured` or `interpretation`. Simulations are only ever `SimulationResult`.
- A measured finding needs `provenance.manifest_id`, `provenance.locator` and at least one source.
- An interpretation needs `derived_from` (finding ids), `method`, `method_version` and `generated_by: "FlameGuard-SI"`.
- `value_status: reported` needs a non-null value. `not_reported` and `not_applicable` need `null`.
- A numeric value needs `quantity` and `unit`. Both must match `vocabulary.json`. Tests check the examples, and `tests/data/` must check curated files.
- Comparisons never convert units, interpolate or fill gaps. When a comparison is `comparable: false`, it must say why.
- A ranking score equals Σ(weight × criterion score). Inputs are measured or interpretation findings only.
- Assistant answers in `ai` or `fallback_quotes` mode need at least one citation. Use `no_evidence` when nothing relevant was found.
- Planned endpoints return `501` with an `Error` body until they are implemented.

## Changing the contract

Follow spec §5.4. The PR touches only `contracts/`, the spec and the version constant, and both the backend and frontend owners approve it. Bump `CONTRACT_VERSION`, the spec version and `vocabulary_version` together. A test checks that all three match.

## Changes from v0.1.0

| Change | Why |
|---|---|
| Removed `illustrative_simulation` from `Finding` | In v0.1.0 a simulation passed as a valid `Finding`, so it could reach `/api/findings`, rankings or the assistant. |
| Added `locator` to measured provenance | Without it, a value can be traced to a file but not to the place in that file. |
| Added `value_status`; `value`/`unit` rules; `vocabulary.json` | v0.1.0 accepted a number with no unit, and could not tell "not reported" apart from "not applicable". |
| Added `conditions` with keys that carry their units | Comparison was impossible without agreed condition fields. |
| Added `comparison`, `ranking`, `assistant_*` and `list_envelope` schemas | Those were described only in prose, so frontend and backend could not code against them. |
| Added `/api/compare` (501 stub) | Comparison is a priority feature and had no endpoint. |
| Tests enforce date format | v0.1.0 accepted `"retrieved": "yesterday"`. |
| Removed `validated_against_measured` | Nothing defined what a validation references. Add it back only with a defined reference format. |
| Made `error.code` an enum; added id patterns | Lets the frontend handle errors predictably, and keeps ids consistent across files. |
