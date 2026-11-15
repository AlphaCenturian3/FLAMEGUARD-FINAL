# G7: conditions representation for derived FLEX Findings

**Status:** implemented and tested as a **project-owner implementation decision** (Command Center, 2026-11-15). It is **not** an independent scientific approval or verification, and it does not make any Finding registrable. Registration still needs the open gates in `tools/flex_derivation_gates.json` (PR #12, PR #17, S10 registration, Q3 review, F042 note review, B1 S11).

## Decision

| Condition | Representation | Rule |
|---|---|---|
| `diluent` | text | The printed non-zero mole fractions of CO2, He and N2, species named, in the fixed order CO2, He, N2, fractions as printed (leading-zero typography only: `.7` is written `0.7`). Example: `"CO2 0.7; N2 0.09"`. All-zero gives `null`. |
| `fuel_or_material` | text | The printed fuel name, never rewritten (no `n-heptane`, no case folding). Missing fuel is an error. |
| `sample_geometry` | text or `null` | `null` unless a source explicitly supports a label. No source label is approved, so it is `null` everywhere. |
| `pressure_kpa` | number | Exact conversion `mmHg x 0.133322387415` (1 mmHg = 133.322387415 Pa by definition; not the torr approximation). No rounding in the data; rounding is for display only. The printed mmHg is kept in the Finding's locator. |
| `oxygen_mole_fraction` | number | The printed O2 fraction. |
| `flow_velocity_mm_s`, `flow_configuration` | `null` | No experimental velocity is reported, and a free-floating droplet is not assumed `quiescent`. |
| `gravity_environment` | `microgravity` | ISS experiment. |

Printed mole fractions must lie in 0..1 and add up to 1 within two-decimal rounding (0.02), or the derivation refuses.

## Acceptance criteria and evidence

| # | Criterion | How it is checked | Result |
|---|---|---|---|
| A1 | Every `diluent` equals the PDF's printed non-zero n2/co2/he tokens, species identified, fixed order | `tools/audit_flex_findings.py` condition check against the printed Table IX tokens; `tests/test_g7_acceptance.py`; collision and ordering tests in `tests/test_derive_flex_findings.py` | 40/40 match the real PDF |
| A2 | Every `fuel_or_material` equals the printed fuel word | audit against the PDF; fuel-preservation tests | 40/40 match |
| A3 | `sample_geometry` is `null` on all 40 | audit; schema accepts `null` (`text_or_null`) | 40/40 null |
| A4 | `pressure_kpa` equals Decimal(printed mmHg) x 0.133322387415 exactly, with no rounding; the printed mmHg is in the locator | audit against the PDF; `test_pressure_is_exact_never_rounded_and_the_printed_mmhg_is_kept`; torr-factor mutation caught | 40/40 exact |
| A5 | All conditions validate against `contracts/schemas/conditions.schema.json` (all 8 keys, types, bounds) | `tests/test_g7_acceptance.py` with the repository's schema validator | 40/40 valid |
| A6 | Ambiguity and collision: distinct mixtures never share a `diluent` string; swapped species stay distinct; fractions out of range or not summing to 1 are refused; fuel case is preserved | derivation tests | pass |
| A7 | The decision is recorded as provisional and not as scientific approval | gates file statuses `owner_provisional`; this document; tests assert the wording | recorded |

Closing the **G7 representation gate** means A1-A7 are documented and satisfied. The three condition decisions keep the status `owner_provisional`, and `registrable` still requires `approved`, so closing G7 does not make anything registrable.

## What this does not claim
Choices such as writing a mixture as text, or leaving `sample_geometry` null, are representation decisions. No independent scientist has verified that this is the best representation for comparing tests; Member 5's Q3 review remains open.
