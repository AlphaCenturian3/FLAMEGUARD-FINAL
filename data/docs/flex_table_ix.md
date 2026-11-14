# FLEX Table IX extract: FLEX-001 to FLEX-010

| | |
|---|---|
| Manifest id | `nasa-tp-2015-216046.table-ix.flex-001-010` |
| File | `data/curated/flex_tp2015216046_table_ix_001_010.csv` |
| Evidence class | `measured` (transcribed as printed; no derived values) |
| Rights status | `permitted_with_citation` (NTRS: distribution "Public", copyright "Public Use Permitted") |
| Source | Dietrich, D. L., Ferkul, P. V., Bryg, V. M., Nayagam, M. V., Hicks, M. C., Williams, F. A., Dryer, F. L., Shaw, B. D., Choi, M. Y., and Avedisian, C. T., *Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011*, NASA/TP-2015-216046, NASA Glenn Research Center, 2015. NTRS 20150023456: <https://ntrs.nasa.gov/citations/20150023456> |
| Table | Appendix A, Table IX "Results by test number and FLEX identifier", printed page 20 (PDF page 26) |
| Source PDF | `https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf`, retrieved 2026-11-14, 42,900,650 bytes, SHA-256 `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d`. Not committed (spec §2.4). |

## How it was transcribed and verified

1. The PDF was downloaded to `data/raw/` (git-ignored) and hashed.
2. Printed page 20 was rendered at 250 dpi. Every cell in rows FLEX-001 to FLEX-010 was read by eye from the image.
3. The same cells were extracted from the PDF text layer. Image and text layer agreed for all 150 cells.
4. `tools/verify_flex_table_ix.py` re-extracts the rows from the PDF and compares every CSV cell, checks the PDF hash, and checks each manifest quote verbatim on its cited page. Result on 2026-11-14: passed.

A second person should still review the CSV against the rendered page before this data is used in the demo.

### What GitHub CI checks, and what runs only locally

The raw PDF is never committed (spec §2.4), so **GitHub CI cannot compare the CSV with the PDF.**

| Check | Where it runs | Needs the PDF? |
|---|---|---|
| Manifest schema, file SHA-256, evidence-class rules (`tools/check_data_provenance.py`) | CI and local | No |
| CSV structure, dash cells empty and declared, no zero substitution, dates, flag rules (FLEX-010 `exclude`, every dash flagged `not_available`, contamination on every row) (`tests/test_flex_dataset.py`) | CI and local | No |
| Cell-by-cell CSV vs PDF (150 cells), PDF SHA-256, every manifest and flag quote verbatim on its cited page (`tools/verify_flex_table_ix.py`) | **Local only** (needs the PDF in `data/raw/` and PyMuPDF) | Yes |
| Visual check of every cell against a 250-dpi render | **Manual, local** | Yes |

A green CI run therefore shows that the files are internally consistent and match their registered checksums. It does **not** re-prove the transcription. Re-run `tools/verify_flex_table_ix.py` locally after any edit to the CSV, the flags or the manifest quotes, and paste its output in the PR. Last local run: 2026-11-14, passed (150 cells, 7 manifest quotes, 43 flags).

## Columns

| Column | Table IX heading | Unit | Notes |
|---|---|---|---|
| `flex_test` | FLEX Test | | Printed `FLEX–001` (en dash); stored with ASCII hyphen |
| `flex_identifier` | FLEX Identifier | | CIR engineering identifier |
| `test_date_as_printed` | Test Date | | As printed, M/D/YY |
| `test_date_iso` | (derived) | | ISO 8601 form of the printed date; the only derived column |
| `test_time_gmt` | Test Greenwich mean time | hh:mm:ss GMT | |
| `fuel` | Fuel | | Methanol or Heptane |
| `ambient_pressure_mmhg` | Ambient pressure | mmHg | |
| `o2_mole_fraction`, `n2_mole_fraction`, `co2_mole_fraction`, `he_mole_fraction` | Initial ambient composition | mole fraction | Printed to 2 decimals. Tables V–VIII of the same report give 3 decimals for some tests; not merged here |
| `initial_droplet_diameter_mm` | Droplet initial diameter | mm | A.1: diameter at time zero (igniters ON) |
| `visible_flame_extinction_diameter_mm` | Visible flame extinction diameter | mm | Droplet diameter when the visible flame extinguished |
| `burning_rate_constant_mm2_per_s` | Burning rate | mm²/s | A.1: average burning-rate constant from a linear fit of D² vs time |
| `burn_time_s` | Burn time | s | |
| `test_end` | Test end | | `Extinction`, `Disruption`, or `Completion`, as printed |
| `source_dash_fields` | — | | Semicolon-separated columns printed as "–" for this row |
| `source_printed_page`, `source_pdf_page` | — | | 20 and 26 |

### Normalizations (typographic only)

- A printed "–" becomes an empty cell **and** the column is listed in `source_dash_fields`. Empty never means zero.
- A printed `0` stays `0`. These are reported values; for example, CO₂ and He are 0 in cabin-air tests.
- A leading decimal point gets a zero: `.21` becomes `0.21`. No trailing zeros are added (`.6` becomes `0.6`, not `0.60`), and no digits are changed.

### What a "–" in the extinction-diameter column means

Appendix A.1 (printed page 19) gives two different meanings:

- extinction did not occur, because the droplet burned to completion or disruption ended the test; or
- the droplet was not in the HiBMs field of view long enough, so the value "is not listed".

The CSV records only that a dash was printed. It does not record which meaning applies. Where a row says `Extinction` and still has a dash (FLEX-004, FLEX-010), the second meaning is the only one consistent with A.1. The Figure 8 and Figure 14 captions confirm both droplets left the HiBMs field of view. That reading is an interpretation and belongs in an `interpretation` record, not here.

A.1 also states that extinction diameters were **extrapolated** by the authors when the droplet left the HiBMs field of view before extinction. The printed table does not mark which values were extrapolated (the "Notes" column in A.1 is not in the printed table). Within these 10 rows:

- The captions for FLEX-001, -002, -003 and -005 say the droplet remained in the cameras' fields of view, so the extrapolation condition does not apply to them.
- FLEX-006 drifted out of the HiBMs field of view and back in, so its 1.53 mm value may be extrapolated. It is flagged `possibly_extrapolated`.

## Exclusion and caution flags

Usage flags are in a separate file, `data/curated/flex_tp2015216046_table_ix_001_010.flags.csv`, with manifest id `nasa-tp-2015-216046.table-ix.flex-001-010.flags` and `evidence_class: interpretation`. They are FlameGuard-SI's judgments, so they are kept apart from the `measured` file, and **no measured value was changed or removed**. Each flag names the test, the field (`*` = whole row), a reason, and a printed page plus a verbatim quote from the report. `tools/verify_flex_table_ix.py` checks every quote against the PDF.

| `ranking_use` | Meaning for rankings, comparisons and the assistant |
|---|---|
| `exclude` | Must not be used until the flag is resolved |
| `not_available` | Printed dash. No value exists. Never zero, never estimated, never a confirmed no-extinction event |
| `caution` | Usable, but the caveat must be shown with the value |

The flags (43 in total):

- **Disputed:** FLEX-010 burning rate. `exclude`. The value stays `0.37` in the measured file; see the conflict below.
- **Printed dashes (9 cells):** all `not_available`.
  - FLEX-004 and FLEX-010 extinction diameter: the rows say Extinction, but the value was not listed.
  - FLEX-007 and FLEX-008 extinction diameter: the dash is ambiguous under A.1.
  - FLEX-009: time, initial diameter, extinction diameter, burning rate and burn time.
- **Estimated or uncertain values:**
  - FLEX-006 extinction diameter: possibly extrapolated.
  - FLEX-001 to FLEX-008 initial diameter: igniter-glow ambiguity with the 1/30 s shutter. FLEX-001 also has a caption saying it could not be measured accurately.
  - FLEX-007 burning rate: droplet obscured by the luminous flame.
  - FLEX-008 initial diameter and burning rate: soot noise.
  - FLEX-001 outcome: printed Disruption, but the caption says it probably coincided with extinction.
- **Contamination:** every row (`contamination_caveat`). Methanol disruption FLEX-001 is flagged as probably contaminant-driven; heptane disruptions FLEX-007, -008 and -009 as possibly contaminant-driven.
- **Calibration:** FLEX-002 to FLEX-006.

## Limitations and caveats

1. **Fuel-needle contamination (section 5.2, pages 16–17).** All tests in this report used conformally coated needles. The deployed droplet "contained an unknown amount of the conformal coating." The authors assert that burning-rate constants and flame histories were minimally influenced. They also state that disruptive extinction of methanol is probably due to the contaminant, and that disruptive extinction of heptane may be. **FLEX-001 is a methanol disruption, so treat that outcome as possibly contaminant-driven.**
2. **Early-test imaging (section 5.1, page 16).** FLEX-001 to FLEX-009 used a 1/30 s shutter. Igniter glow made droplet size ambiguous during ignition, and more so than in later tests.
3. **Calibration tests.** The Figure 6–10 captions describe FLEX-002 to FLEX-006 as calibration runs. The FLEX-001 caption calls it "the first FLEX test". The identifiers of FLEX-001 to FLEX-009 contain `CAL`, but the captions for 007 to 009 do not call them calibration runs. LLUV camera settings were not optimal for 001 to 006.
4. **Per-test notes from Appendix B captions:**
   - FLEX-001: the igniters overexposed the HiBMs at ignition, so droplet diameter "could not be measured accurately". The droplet "probably disrupted at the end of the test coincident with flame extinction", which is why the row lists both a disruption and an extinction diameter.
   - FLEX-004: the droplet left the HiBMs FOV one-third of the way through the burn.
   - FLEX-006: the droplet drifted out of the HiBMs FOV and back in.
   - FLEX-008: significant sooting; the droplet drifted out of the HiBMs and color FOVs.
   - FLEX-009: very poor deployment; the droplet left all FOVs shortly after ignition; no IPSU data was downlinked.
   - FLEX-010: see the conflict below.
5. **Unresolved conflict for FLEX-010.** Table IX prints a burning rate of `.37` mm²/s. The Figure 14 caption (printed page 38) says "no burning rate constant or extinction droplet diameter is reported". The CSV keeps the table value as printed. **Do not use FLEX-010's burning rate in any ranking or comparison until this is resolved,** for example against the PSI electronic data files.
6. **Scope.** ISS microgravity, free-floating droplets, near-ambient temperature. Rows 1–9 are near 1 atm air (O₂/N₂ 0.21/0.79); row 10 is about 3 atm O₂/N₂/CO₂ 0.21/0.09/0.70. The rows do not cover the full FLEX test matrix and are not a statistical sample.
7. **Report coverage note.** The report's title says March 2009 to December 2011, while Appendix A's text says "March 2009 through December 2010". Table IX itself runs to FLEX-280 (12/8/11).

## Not included (deliberately)

- Notes, Fiber, H₂O, ambient heptane and methanol vapor columns described in A.1. These are not printed in Table IX; A.1 says the electronic files on the DVD addendum and PSI (psi.nasa.gov, registration required) carry the detailed results.
- Rows beyond FLEX-010. They can be added the same way.
