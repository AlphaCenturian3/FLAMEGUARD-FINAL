# FLEX Finding derivation — deterministic design proposal (D2/D4/S9/S10)

**Status:** Design only, for Members 1, 2, 3, and 5 to review. No derivation script, Findings JSON, manifest edits, TARS activation, or Moon/Mars recommendations are authorized by this document.  
**Base:** `main` after PR #4, merge commit `ef71422964ed04b5e83c84c64dadc82afa711202` (contract v0.2.0; FLEX source/flags).  
**Dependencies:** D5/C4 vocabulary PR #12 and its F1/F2/O1–O4 decisions; S10 source-page proposal PR #13; Member 1's B1 evidence loader and later comparison rules. PR #14 is a separate TARS documentation correction.

## Objective and contract boundary

Design a reproducible, fail-closed transformation of **NASA-as-printed Table IX rows FLEX-001 through FLEX-010** into contract-valid, measured `Finding` JSON, with one FLEX `Investigation` and registered output artifacts. The transformation is **curation/representation**, not a new physical measurement, scientific inference, risk score, extrapolation, or simulation.

Inputs must be exclusively manifest-registered, hash-verified:
- `data/curated/flex_tp2015216046_table_ix_001_010.csv`, manifest id `nasa-tp-2015-216046.table-ix.flex-001-010`, SHA-256 `67f2d86d4d1b7c5de6d57ad3c870967f1628b14323ac61d8028f332091a0dea1`;
- `data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv`, manifest id `nasa-tp-2015-216046.table-ix.flex-001-010.flags`, SHA-256 `19e7f951ac9ccb92de2c3eeea4988cef8da22fd1fcdfc57d976f675726f8999d` (45 flags: 35 caution, 9 not_available, 1 exclude);
- `data/manifest.json`, approved vocabulary, contract schemas and registered NASA source passages.

The output design is:
- `data/curated/investigations.json`: FLEX investigation entry, merged with existing investigations when they exist; no removal or replacement of other investigations;
- `data/curated/findings/flex.json`: measured Finding objects only;
- `data/manifest.json`: new `measured` entries for the generated JSON files with computed SHA-256, real `sources`, `rights_status`, and descriptions; `Investigation.datasets` must resolve to the manifest id of the **findings JSON** entry (not the source CSV alone).
- A future `tools/derive_flex_findings.py` and `tests/data/` are **proposed**, not created here.

Do not copy the CSV into the API as Findings: B1 correctly skips non-JSON registered files.

## Proposed field-to-quantity mapping (subject to D5 approval)

| CSV field | Proposed Finding quantity | Unit | Emission rule |
|---|---|---|---|
| `initial_droplet_diameter_mm` | `initial_droplet_diameter` | `mm` | Number → reported; printed dash → not_reported |
| `visible_flame_extinction_diameter_mm` | `visible_flame_extinction_diameter` | `mm` | Report as printed, **regardless of `test_end`**; dash → not_reported |
| `burning_rate_constant_mm2_per_s` | `burning_rate_constant` | `mm2/s` **provisional** | Reported unless an applicable `exclude` flag; FLEX-010 → excluded, null |
| `burn_time_s` | `burn_time` | `s` | Number → reported; printed dash → not_reported |

All numeric values derive by strict decimal parsing from the exact source cell; no interpolation, rounding, unit transformation, invented uncertainty or default zero. The Finding schema stores JSON numbers, not strings. Reject blank cells that lack a matching `not_available` flag.

**Important F1 counterexample:** FLEX-001 is labeled `Disruption` in `test_end` but has source-printed `visible_flame_extinction_diameter_mm = 0.89`. Do not delete, silently discard, relabel, or treat that value as independent proof of an `Extinction` test outcome. Figure 5 reports probable disruption coincident with flame extinction, which is a source caveat, not license to change the table. Member 5 must approve the vocabulary description and applicability. 

**Non-numeric columns:** `test_end` is a separately source-reported categorical outcome, not an approved quantitative vocabulary quantity; `test_time_gmt` and identifier/date columns provide metadata/locator, not Findings of an invented quantity. A measured qualitative outcome Finding (`quantity: null, value: null, unit: null, value_status: not_applicable`) is a **separate owner-dependent proposal**, not included by default. If included later, its exact source statement, S10 flags (including outcome cautions), citation, and comparability semantics require tests.

## Identity, ordering, and source tracing

Proposed stable IDs: `flex.flex-001.initial_droplet_diameter` through `flex.flex-010.burn_time`, generated in source row order and a fixed quantity order. `investigation_id: "flex"` and file `findings/flex.json`. Every ID must be lowercase, unique, and schema-valid. A byte-identical input and versioned mapping configuration must produce byte-identical sorted JSON and checksums on repeated runs.

Each measured Finding must contain `id`, `investigation_id`, `evidence_class: "measured"`, a source-grounded `statement`, approved `quantity`, `value`, `unit`, `value_status`, `conditions`, and `provenance`. `provenance.manifest_id` points to the **registered findings JSON file's own manifest entry**, per S1. The `locator` identifies the report, printed page 20 (PDF page 26), FLEX test id, exact source CSV field and physical CSV line number. `provenance.sources` contains real registered NASA `Source` objects; use the Table IX source for row data and any additional source passage only when attributable and registered. Numeric cells need a precise table locator; do not fabricate a direct prose quote for each number.

All caution/exclusion `curation_notes[].source` must be registered, page-consistent passages with verbatim NASA quotes; never use a generic Table IX quote to masquerade as a Figure-caption quote. The S10 register/verification gap remains open until PR #13's owner decision and implementation. A valid JSON schema alone does **not** establish S10.

## Conditions: literal mapping, null where unknown

For measured FLEX findings:
- `gravity_environment: "microgravity"` (ISS experiment; not a Moon/Mars partial-gravity measurement).
- `oxygen_mole_fraction`: strictly parse the row's `o2_mole_fraction`; do not modify reported precision.
- `pressure_kpa`: convert source `ambient_pressure_mmhg` using **0.133322387415 kPa/mmHg**, not the torr factor. Use Decimal arithmetic until deterministic JSON serialization. Keep the as-printed mmHg and original row reference in the locator / registered CSV; never imply converted precision was measured.
- `flow_velocity_mm_s: null` where no experimental velocity is reported.
- `flow_configuration: null` absent an approved source classification; free-floating droplets are **not** automatically `quiescent`.
- `diluent`: source-grounded gas-composition representation, **format pending Member 1/2 G7 decision**; do not infer a single `N2` for a mixed `N2+CO2` row.
- `fuel_or_material`: use a consistent source-grounded `methanol` / `heptane` normalization only after owner confirmation; do not silently substitute `n-heptane` for the printed `Heptane`.
- `sample_geometry`: source-grounded, conservative label for free-floating fuel droplets, after owner approval.
- All required condition keys must be present; unknown means JSON `null`, never guessed.

Keep these values consistent for all quantities in a test row. If units/formatting/conditions conventions are unsettled, fail closed before publishing a measured Finding.

## S10 quality-flag mapping: strict, field-aware

For each emitted Finding, collect **all** flags whose `flex_test` equals its source row and whose `field` equals the original CSV field or `*`. Fail on duplicate flag ids, unknown test/field, ambiguous mapping, unregistered flag manifest id, missing NASA source quote or wrong page.

- `ranking_use: "exclude"`: `value_status: "excluded"`, `value: null` and an attributed `curation_notes` entry with `kind: "exclusion"`, `generated_by: "FlameGuard-SI"`, the exact `flag_ref` (flags manifest id + flag id), the reason, and a correctly registered/cited NASA `source`. The disputed source cell remains untouched.
- `ranking_use: "caution"`: keep the source value/status and add a `kind: "caution"` note for **every** applicable field, including any row-wide (`*`) caveat. Do not put curator judgments into `uncertainty`.
- `ranking_use: "not_available"`: requires an actual printed dash, maps to `value_status: "not_reported"` with `value: null`, and **never** becomes a curation note.
- Source-reported uncertainty enters `uncertainty` only if reported verbatim; do not use it to paraphrase flags.

**Known mandatory cases:**
- FLEX-010 `burning_rate_constant_mm2_per_s` has flag F042: original CSV preserves `0.37` (Table IX prints `.37`); its Finding is **excluded with null value and a source-grounded exclusion note**. Neither number nor a surrogate may be emitted as quantitative evidence.
- FLEX-010 F044 initial-droplet imaging caution and F045 burn-time derivation caution remain attached to their respective numeric Findings, keeping values as reported; F045 does **not** declare 13.6 s incorrect.
- FLEX-009 has five printed dashes (four mapped numeric columns plus metadata time); these are part of the nine printed dashes across all ten FLEX rows. Only the four numeric Finding fields become `not_reported`. Never create a numeric Finding for the missing `test_time_gmt` metadata column.
- Row-wide contamination cautions apply to all emitted numeric Findings for the affected test.

Each flag cited by a generated note must have its recorded quote verifiable against the **registered source document text**, not merely pass a CSV-internal consistency test. Run Member 3's local PDF text verifier and Member 5's independent source audit; CI that cannot access the PDF must not be described as physical-source authentication.

## Exclusions, comparisons, and TARS

S9 is transitive: an excluded Finding and **every** interpretation depending on it, at any `derived_from` depth, is prohibited as ranking/comparison/TARS supporting evidence. An exclusion-dependent interpretation is explanation-only, with `value: null`, `quantity: null`, appropriate limitations, and **no** `relevant_environments`. Broken/cyclic provenance fails closed. B6/T1 must route exclusion explanations separately, without exposing the source-printed excluded number in user-facing answers.

**F2/O2 remains unapproved.** Measured numeric Findings are not themselves permission to compare test outcomes. Until Member 1 and Member 2 approve a deterministic machine-readable rule for `test_end` and test identity, **all FLEX cross-row quantity comparisons are disabled/non-comparable with a fixed reason**. Parsing `statement` or `locator` prose to infer the outcome is forbidden. Do not change the single `/api/compare` implementation without its owner. No ranking, risk score or Moon/Mars recommendation is generated by this derivation.

TARS receives findings only after B1 validation and T1 `retrieve()` safeguards. It must not read CSV/flags directly or cite exclusion-dependent chains as scientific support. Nothing here is NASA-measured Moon/Mars partial-gravity data.

## Staged development plan (not yet authorized)

**Phase A — settle gates (no implementation):** PR #12 vocabulary wording, O1/O3/O4 and F1; F2/O2 outcome comparability; source-page registration / S10 verifier design from PR #13; Member 1's accepted evidence loader contract; remaining condition text conventions.

**Phase B — deterministic transformer (after approvals):** strict input hash and UTF-8 check; parse rows and flags; schema-bound quantity mapping; explicit row+field flag resolution; immutable manifest metadata; deterministic source objects/locators; render JSON only into a staging directory; no auto-commit and no network.

**Phase C — QA (before merge):** schema validation and S0–S4/S9/S10 checks; per-field coverage including all 10 FLEX tests; source PDF quote audit; no original-CSV or flags-CSV byte changes; independent Member 5 review. Register the generated files by hash only after all checks pass, then verify B1 loads the findings JSON.

**Phase D — integration:** Member 1 validates the evidence loader and fail-closed compare, Member 2 validates UI badges and caveats, Member 5 independently tests S9 exclusion leaks; enable TARS evidence only after the runtime exclusion gate passes.

## Required acceptance tests (future tests/data, not implemented here)

1. Input hashes and manifest ids match exactly; any mismatch/missing/extra flag, missing quote or unregistered source fails.
2. Exactly 10 source test ids are recognized; duplicate FLEX ids, unexpected columns and a dash without `not_available` fail.
3. Same source snapshot generates byte-identical output and stable ids twice.
4. Each numeric field yields a correctly typed Finding with the approved quantity/unit; no string numeric values, unsupported keys or invented uncertainty.
5. All reported source values remain source-equal; `0` remains `0`, not an empty cell; no additional significant digits claimed.
6. FLEX-001's `Disruption` and reported 0.89-mm extinction-diameter column both survive, with no fabricated `Extinction` outcome.
7. F042 excludes FLEX-010 burning-rate Finding (`null`), preserving `0.37` only in the source CSV; an exclusion leakage mutation test must fail.
8. F044 and F045 attach separate cautions to FLEX-010 fields with the original values retained and with no unsupported error claim.
9. Every applicable `*` caution appears on every emitted numeric Finding for that row, and all field-specific flags attach only to the mapped quantity.
10. All printed dashes map to `not_reported` when represented as Finding quantities; `not_available` produces no curation note.
11. Each note has a resolvable `flag_ref`, matching test/field, kind/flag status, and registered quote + correct page; all 15 missing source-page mappings are handled according to the approved S10 decision.
12. `Investigation.datasets`, `provenance.manifest_id`, manifest file paths/hashes, and Finding ids satisfy S1–S4; no simulations.
13. Pressure conversion uses `0.133322387415`, not the torr approximation; all required conditions keys present, unknowns null.
14. Before outcome enforcement is approved, cross-row FLEX comparisons must be rejected with a stable reason regardless of matching numeric quantities or conditions.
15. B1 loader accepts only the generated registered JSON, skips the source CSV and flags CSV, and never treats flags as measurements.
16. S9/T1/B6 tests verify an excluded Finding and transitive interpretation descendants cannot be used for ranking, comparable rows or TARS conclusions, including attached-unit number leaks and missing as-printed resolver values.

## Decisions / owners needed before code

| Item | Decision | Owners |
|---|---|---|
| D5 F1/O3 | Source-defensible extinction-diameter definition (FLEX-001 counterexample), descriptions and bounds | Member 5; Members 1/2 for contract |
| D5 O1/O4 | `mm2/s` notation and coordinated version change | Members 1 and 2 |
| D5 F2/O2 | Structured outcome/test identity, or deterministic fail-closed FLEX compare | Members 1 and 2; Member 5 scientific review |
| S10 PR #13 | Register source quotes on 15 flags; precise page convention and full-coverage scope | Members 1 and 3; Member 5 source audit |
| G7 | Fuel/diluent/sample geometry/flow representation; numeric pressure serialization | Members 1 and 2 |
| Integration | Loader registration/file shapes and S9/T1/B6 fail-closed routing | Member 1 backend, Member 3 data/retrieval, Member 5 independent QA |

**This proposal cannot resolve owner decisions through its own publication.** The first executable PR must wait for explicit signed decisions and green tests on its exact final SHA.
