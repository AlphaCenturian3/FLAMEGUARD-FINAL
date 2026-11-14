# Integration contract v0.1.0

This is the agreement between the backend, frontend, and data workstreams, so each can develop independently. The summary is in master spec §5.

## Files

| Schema | Used by |
|---|---|
| `schemas/source.schema.json` | Citation embedded in every scientific object |
| `schemas/finding.schema.json` | `/api/findings`, ranking inputs, assistant citations |
| `schemas/investigation.schema.json` | `/api/investigations` |
| `schemas/simulation_result.schema.json` | `/api/simulations/{id}` |
| `schemas/data_manifest.schema.json` | `data/manifest.json` |
| `schemas/health.schema.json` | `/api/health` |
| `schemas/error.schema.json` | Every non-2xx response, including 501 for planned endpoints |

`examples/*.json` are **fixtures**. Each has `"fixture": true` and invented placeholder content, and none of them is NASA data. CI validates each example against its schema (see `tests/test_contracts.py`), so the examples and schemas cannot drift apart.

## Rules

- Each `Finding` has exactly one `evidence_class`: `measured`, `interpretation`, or `illustrative_simulation`.
- A `measured` finding must include `provenance.manifest_id` that points to a manifest entry.
- An `interpretation` must list `derived_from` (finding IDs) and a `method`.
- A `SimulationResult` must carry the exact label in `label`.
- The API returns JSON with `contract_version` on list responses.
- Planned endpoints return `501` with an `Error` body until implemented.

## Changing the contract

Follow spec §5.4: a PR that touches only `contracts/`, bumps the version, and is approved by both the backend and frontend owners.
