# Resolution note: G2, G5, G7 (FLEX findings under contract v0.2.0)

**Status:** recommendations from `feat/nasa-data-tars` (Member 3), 2026-11-14. **Not decisions, and not implemented.** They assume the contract v0.2.0 proposal in PR #1 (head `a6876d1`) merges as written. Each item names who must approve it. The gaps are defined in [`flex-flags-to-curation-notes.md`](flex-flags-to-curation-notes.md).

All rule references are to PR #1's `contracts/README.md` and schemas at `a6876d1`, which I re-read for this note.

---

## G2. How the Table IX test outcome is represented

**Problem.** Table IX's "Test end" column (Extinction / Disruption / Completion) is not a vocabulary quantity (C4 lists four FLEX quantities, none of them outcome) and not a `conditions` key. The conditions keys are gravity, O₂, `pressure_kpa`, flow velocity, flow configuration, diluent, fuel and geometry. Yet:
- 5 caution flags sit on it, and S10(b) requires every caution row to be covered by a note on some finding;
- comparisons must never pool different outcomes.

**Recommendation for P0: option (a), a measured qualitative outcome finding per test.** It follows the pattern PR #1's workstream doc already uses for `experimental_result` records, so no new contract key is needed:

```json
{
  "id": "flex.flex-001.test-end",
  "investigation_id": "flex",
  "evidence_class": "measured",
  "statement": "NASA/TP-2015-216046 Table IX lists the test end of FLEX-001 as \"Disruption\".",
  "quantity": null, "value": null, "unit": null,
  "value_status": "not_applicable",
  "conditions": { "...": "same as the row's quantity findings" },
  "provenance": {
    "manifest_id": "nasa-tp-2015-216046.table-ix.flex-001-010",
    "locator": "Table IX, row FLEX-001, column Test end (data/curated/flex_tp2015216046_table_ix_001_010.csv line 2)",
    "sources": ["<Table IX source from the manifest>"]
  },
  "curation_notes": ["<caution notes from flags on field test_end and field *>"]
}
```

- The 5 `test_end` cautions (FLEX-001 outcome ambiguity; contaminant-related disruption for 001, 007, 008 and 009) become caution notes on this finding. S10(b) coverage is then met.
- The printed word stays in the CSV, which the locator points to.

**Known limitation of (a).** The outcome is then only in `statement` text, not a machine-readable field. Rule "never pool outcomes" in `/api/compare` would have to parse text, which it shouldn't. So:
- **For P0:** the derivation tool repeats the outcome in each quantity finding's `statement` (e.g. "…extinction diameter 0.89 mm (test ended in Disruption)…"), and compare treats FLEX rows from different outcomes as non-comparable by `locator` row. That is a Member 1 implementation detail and needs their agreement.
- **After P0, via D5:** add a machine-readable outcome, for example an enum condition-like field for droplet tests. That is a contract PR needing Member 1 and Member 2.

| Approves | Why |
|---|---|
| Member 1 | Loader and compare behaviour; B1 must accept qualitative findings for FLEX |
| Member 2 | UI shows the outcome finding next to the row's values |
| Member 5 | Reviews the outcome cautions (they review the flags) |

---

## G5. How source quotes are verified (S10(d))

**Problem.** S10(d) requires each referenced flag quote and page to be "verified against the registered source document's text". The FLEX source PDF is not committed and not registered (spec §2.4: raw NASA files are not committed until rights review). So CI has no source text to check against. Today all 43 flag quotes and 7 manifest quotes are checked **locally** by `tools/verify_flex_table_ix.py` against the PDF (SHA-256 `b4f6ca98…e79d`). Last run 2026-11-14: passed.

**Options.**

| | What | Pros | Cons |
|---|---|---|---|
| (a) | Keep the local check. Paste its output in each PR that touches CSV, flags or quotes, and log it in `docs/verification/`. Member 5's independent Q3 spot check is the second check | No rights question; works today | CI cannot enforce it. Relies on discipline and Q3 |
| (b) | Register a **text extract of only the cited pages** (printed pp. 16, 17, 19, 20, 29–38) as a source-text file, with its SHA-256 and the PDF's SHA-256, so CI checks quotes against it | CI enforces S10(d) | Needs a rights decision (NTRS: "Public Use Permitted"); needs a manifest class or field for source text, which is a contract question; the extract itself must be verified against the PDF |
| (c) | (a) now, (b) after the submission | Fits the deadline (submission closes 2026-11-15 23:59) | Two steps |

**Recommendation: (c).** Use (a) for P0. In `tests/data/`, CI checks that every flag referenced by a note has a non-empty quote and page that match the flags file byte for byte, so notes cannot drift from flags. Separately, a recorded local verifier result is required for the current flags file SHA-256. Revisit (b) after submission.

| Approves | Why |
|---|---|
| Member 5 | Q3 becomes the independent half of S10(d) |
| Member 1 | S10 wording in `contracts/README.md` ("registered source document's text") would need a footnote for (a) |
| Member 3 | Owns the verifier and `tests/data/` |

---

## G7. Units, conversions and vocabulary

### Pressure: `pressure_kpa`

Table IX prints **mmHg**. PR #1 convention 4 and decision C2 allow condition values to be converted "only by an exact defined factor, in Member 3's curation tool", with the as-printed value kept in the registered source file.

- **Factor:** 1 mmHg = **133.322387415 Pa** exactly (conventional millimetre of mercury). This is **not** the torr: 1 Torr = 101325/760 Pa = 133.3223684… Pa, a relative difference of 1.4 × 10⁻⁷. Table IX's unit is mmHg, so the mmHg factor applies.
- **Examples:**
  - 757.7 mmHg → 101.0183729443455 kPa
  - 760 mmHg → 101.3250144354 kPa
  - 2319.7 mmHg → 309.2679420865755 kPa
- **Recommendation:**
  - Store the exact product, unrounded. Rounding would be a second, unapproved transformation.
  - The UI shows it to the printed number of significant figures and also shows the as-printed mmHg from the locator.
  - The derivation tool records the factor in its `method` string.
- **Needs:** Member 1 to confirm that unrounded storage is acceptable, and Member 2 for the display rule.

### Other conditions for FLEX rows (proposed values, from Table IX and the report)

| Key | FLEX value | Basis |
|---|---|---|
| `gravity_environment` | `microgravity` | ISS (report title and abstract) |
| `oxygen_mole_fraction` | printed O₂ (e.g. 0.21) | Table IX, "initial ambient composition" |
| `pressure_kpa` | converted as above | Table IX |
| `flow_velocity_mm_s` | `null` | Table IX reports none; not estimated |
| `flow_configuration` | `quiescent`? | **Open.** Droplets were free-floating with residual drift (report §5.1), so `quiescent` is a judgment. Leaving it `null` is the conservative choice |
| `diluent` | e.g. `"N2"` (rows 1–9), `"N2+CO2"` (row 10) | Printed mole fractions; the naming format needs agreement |
| `fuel_or_material` | `"methanol"` / `"heptane"` | Table IX "Fuel" (A.1 gives C₇H₁₆; §6 Conclusions says "n-heptane", so which name to use needs agreeing) |
| `sample_geometry` | `"free-floating droplet"` | Report §5.1 and figure captions |

### Vocabulary (C4, D5)

PR #1's `contracts/vocabulary.json` at `a6876d1` has 5 quantities, none of them FLEX. Decision C4 accepted four FLEX quantities "after CP1 in a separate reviewed contract PR (Member 3, D5)". Proposed entries for that PR, with units exactly as Table IX prints them and nothing converted (convention 4: quantity values are never converted):

| Key | Unit | Bound | Table IX column |
|---|---|---|---|
| `initial_droplet_diameter` | `mm` | `minimum: 0` | Droplet initial diameter |
| `visible_flame_extinction_diameter` | `mm` | `minimum: 0` | Visible flame extinction diameter |
| `burning_rate_constant` | `mm2/s` (exact unit string to agree; vocabulary uses ASCII like `mm/s`) | `minimum: 0` | Burning rate (A.1: burning-rate constant) |
| `burn_time` | `s` | `minimum: 0` | Burn time |

**Order of work:** PR #1 merges, then the D5 vocabulary PR (Member 3 opens it; Member 1 and Member 2 approve), then the derivation tool and `data/curated/findings/flex.json`. None of this starts before PR #1 merges.

---

## Correction to the mapping doc

**G1 (row-level flags) is already resolved by PR #1.**
- S10(a) accepts a flag "whose field is the finding's field or `*`".
- Convention 9 says "a whole-row caution can still add a caution note to a `not_reported` finding".

No proposal is needed.
