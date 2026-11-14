# Source candidates: BASS and BASS-II (not ingested)

**Status:** research notes from `feat/nasa-data-tars`, 2026-11-14. **No BASS data is ingested.** No value from these sources may enter `data/curated/` until the exact file or table is verified as described below.

## Why BASS

Burning and Suppression of Solids (BASS, BASS-II) burned solid fuels (PMMA and other samples) in a small flow duct in the Microgravity Science Glovebox on the ISS. The tests varied flow speed and direction, ambient oxygen, and sample geometry. Solid-fuel flame spread and extinction are directly relevant to spacecraft fire safety, and they complement FLEX droplet combustion.

## Verified records

Each was checked on 2026-11-14 against the record itself (NTRS page or the DataCite/doi.org registry), not a search snippet.

| Record | What it is | Identifier | Rights as stated by the record |
|---|---|---|---|
| **PSI-25**, *Burning and Suppression of Solids - II* | NASA PSI investigation dataset. Creators: Ferkul, Fernandez-Pello, Miller, T'ien, Bhattacharjee. Available 2022-12-31 | DOI [10.60555/4qc4-de67](https://doi.org/10.60555/4qc4-de67), resolves to `https://psi.nasa.gov/physci/repo/data/investigations/PSI-25` | DataCite: **Creative Commons Zero v1.0 Universal** |
| **PSI-26**, *Burning and Suppression of Solids* (BASS-I) | NASA PSI investigation dataset, 2013 | DOI [10.60555/58h4-dy80](https://doi.org/10.60555/58h4-dy80), resolves to `.../investigations/PSI-26` | DataCite: **CC0 1.0** |
| *Burning and Suppression of Solids–II (BASS-II) Summary Report*, Olson, Ferkul, Bhattacharjee, Miller, Fernandez-Pello, Link, T'ien, Wichman | NASA Technical Memorandum, 2021-10-01, report E-19939 | [NTRS 20210011385](https://ntrs.nasa.gov/citations/20210011385) | NTRS: "Use by or on behalf of the US Gov. Permitted." **Not** "Public Use Permitted", so treat it as restricted until reviewed |
| *Results from On-Board CSA-CP and CDM Sensor Readings During the BASS-II Experiment in the MSG*, Olson et al. | Conference paper ICES-2015-196, 2015-07-12 | [NTRS 20150019858](https://ntrs.nasa.gov/citations/20150019858) | NTRS: "Public Use Permitted" |
| *Combustion of Solids in Microgravity: Results from the BASS-II Experiment*, Ferkul et al. | Presentation, ASGSR 2014-10-23 | [NTRS 20160000593](https://ntrs.nasa.gov/citations/20160000593) | NTRS: "Public Use Permitted" |

## Experimental variables (as described by the records above)

- From the PSI-25 DataCite description and the NTRS 20210011385 abstract:
  - forced flow velocity (speed and direction)
  - ambient oxygen concentration (set by nitrogen dilution of the glovebox working volume)
  - sample geometry (rods, spherical sections, slabs, films, fabric sheets)
  - fuel type and thickness
- From the ICES-2015-196 abstract: oxygen, CO and CO₂ were measured before and after each test by the onboard CSA-CP and CDM sensors.
- From the NTRS 20160000593 abstract: flow speeds up to 53 cm/s.

## What is NOT verified yet

1. **Contents of PSI-25 and PSI-26.** The PSI pages render client-side, and the FLEX report states PSI downloads need registration. File names, formats, per-test tables and units are unknown. Search snippets and third-party projects mention test counts and file types; those are **not** used here.
2. **Per-test measured values.** Not yet in a NASA record with confirmed rights. One open-licence table has been found; see "Candidate table" below.
3. **ICES-2015-196.** I downloaded it locally (git-ignored; SHA-256 `e9c1286f0903700c0ae180a574debb6826f3676a072df2eeb926c22955a09831`). It has **no tables**; all results are figures. Reading values off its plots would be digitizing, which is `interpretation`, not `measured`. Do not ingest it as measured data.
4. **The summary report TM.** Its rights statement is restrictive. Check whether it has a test-matrix table, and get the rights reviewed, before using it.

## Candidate table: Link et al. 2018, Supplementary Table S1 (found 2026-11-14, not ingested)

| | |
|---|---|
| Article | Link, S., Huang, X., Fernandez-Pello, C., Olson, S., Ferkul, P., "The Effect of Gravity on Flame Spread over PMMA Cylinders", *Scientific Reports* (2018), DOI [10.1038/s41598-017-18398-4](https://doi.org/10.1038/s41598-017-18398-4), PMC5760683 |
| Licence | **CC BY 4.0** (Crossref licence record, and the article's own statement on PMC). Whether the supplementary file is covered "unless indicated otherwise" still needs a check; no other terms appear on the SI pages |
| BASS-II link | Article text on PMC (checked against the page text 2026-11-14; reference markers 21–23 omitted): "The microgravity experiments were conducted in ISS as a part of the Burning and Suppression of Solids-II (BASS-II) project". Flow direction: "The scientific objective of the BASS-II opposed flow flame spread tests was to understand further the mechanisms controlling the spread of flames over the surface of solid combustible materials, particularly in a microgravity environment." |
| Test method (from the article) | "each PMMA sample was ignited at a relatively high opposed flow velocity by a hot coil, and the steady-state flame spread was achieved within 1 min." and "Then, the opposed flow velocity was subsequently reduced until extinction was observed, pausing (about 30 s) along the way to allow for steady state flame spread at each new flow velocity." So **rows sharing a Sample No. are successive flow steps within one burn, not independent tests.** |
| File | Supplementary PDF `41598_2017_18398_MOESM1_ESM.pdf` (filename as listed on PMC). PMC served a browser challenge page instead of the file, so I did not work around it. I downloaded it from the publisher's static host (`static-content.springer.com/esm/…`): 645,055 bytes, matching PMC's listed 629.9 KB. SHA-256 `e17c9511c4b4b253cd0795b3984ffb9347ad5db6354c4ce792adcaf805f21b23`. Local `data/raw/` only, git-ignored |
| Table S1 | "The raw and processed microgravity data in International Space Station, where B and C means black and clear PMMA samples, respectively." Columns: d (cm), X_O2 (%), Sample No., V_g (cm/s), Δt (s), V_f×10³. About 50 rows over rod diameters 1.27, 0.95 and 0.64 cm |
| Table S2 | Normal-gravity (Earth) data. **Not BASS-II**; only a 1 g comparison |

**Problems that must be decided before any transcription:**

1. **Unit conflict in the printed header (investigated 2026-11-14, NOT resolved).** The left half of Table S1 (d = 1.27 and 0.95 cm) labels V_f×10³ as **(cm/s)**; the right half (d = 0.64 cm) as **(mm/s)**.

   Evidence gathered from the article itself, PMC5760683. The figure images are from the PMC page and were read by eye:

   | Source element | Unit printed for V_f×10³ | Which rows it shows |
   |---|---|---|
   | Table S1 left half | cm/s | d = 1.27, 0.95 cm |
   | Table S1 right half | **mm/s** | d = 0.64 cm |
   | Table S2 (1 g, both halves) | cm/s | 1 g only |
   | Fig. 5 y-axis, "Flame spread rate, V_f × 10³ (cm/s)" | cm/s | All three diameters on **one** axis, including d = 0.64 cm. Its 0.64 cm points reach ≈10 at X_O2 ≈ 18.9%, alongside Table S1 right-half values 10.00 / 9.74 / 8.32 at 18.9% |
   | Fig. 6a y-axis, same label | cm/s | X_O2 = 18.2% and 17.5% (μg). The plotted points sit at about the values in Table S1 rows B16 (18.2%) and B19 (17.5%), which are **d = 0.64 cm, right half** |
   | Fig. 7 y-axis, same label | cm/s | μg points per diameter, including 0.64 cm |
   | Article text | No numeric V_f with units found (flow speeds only, in cm/s) | — |
   | Crossref | No correction or erratum registered (`updates:` filter, 0 results) | — |

   **What the evidence shows:** every other place in the article that presents these same 0.64 cm values labels them cm/s. The right-half "(mm/s)" header is the only place that differs.

   **What it does not settle:** this rests on reading plotted points against table values by eye, and it is the authors' table. **No corrected value is inferred or published.**

   **Recommendation: (a) ask the corresponding author to clarify.** The supplementary PDF names the corresponding author (University of California, Berkeley). A team member should send the question from their own account; the executor sends nothing. Draft:

   > Supplementary Table S1 of "The Effect of Gravity on Flame Spread over PMMA Cylinders" (Sci. Rep., doi:10.1038/s41598-017-18398-4) labels V_f × 10³ as (cm/s) for d = 1.27 and 0.95 cm, but as (mm/s) for d = 0.64 cm. Figures 5–7 label the same quantity in cm/s for all diameters. Could you confirm the intended unit for the d = 0.64 cm columns?

   **Until the author answers, the disputed rates stay excluded:**
   - If BASS-II is ever curated from this table, every V_f cell in the right half (d = 0.64 cm) gets a quality flag with `ranking_use: exclude`, giving `value_status: "excluded"` under PR #1. Its reason is the printed unit conflict, and the printed value stays in the registered source file.
   - Under PR #1's transitive S9 (head `eaae6d6`), nothing derived from those cells may support a ranking, comparison, TARS conclusion or Moon/Mars recommendation.
   - Fallbacks if no answer comes: (b) a documented FlameGuard-SI judgment ("header typo, cm/s") as an interpretation-class flag with the evidence above, which needs team approval; or (c) curate the left half only.
   - No BASS-II data is curated now.
2. **Merged cells.** d, X_O2 and Sample No. span several rows. Expanding them to every row is a layout reading that a second person must confirm.
3. **Whether it counts as a NASA record (spec §2.1).** This is a peer-reviewed journal supplement with NASA co-authors (Olson, Ferkul), not a NASA archive record. Registering it as `measured` is a team decision.
4. **Mapping.** V_f fits PR #1's existing `flame_spread_rate` (mm/s) only after the unit conflict is resolved. V_g fits `flow_velocity_mm_s` after an exact ×10 conversion. `flow_configuration` = `opposed`, per the article text quoted above. Rows within one sample are not independent, so statistics must not treat them as separate tests.

## Related verification (2026-11-14)

- **FLEX PSI dataset:** DataCite lists DOI `10.60555/mbq8-0451` as *Flame Extinguishment Experiment*, NASA PSI 2016, CC0 1.0, URL `.../investigations/PSI-69`. Member 5 recorded this first (PR #3). PSI-69 is the route to resolving the FLEX-010 burning-rate conflict. PR #4's `permitted_with_citation` applies to the NASA/TP report we transcribed, not to the PSI dataset.

## Major limitations to carry if ingested

- Ambient oxygen came from a model-guided nitrogen dilution, calibrated against onboard sensors. The ICES paper describes CSA-CP readings that were out of calibration and corrected for offset (Figure 4 caption). Oxygen values therefore need their stated correction method attached.
- Heat release rates in these papers were **estimated** from oxygen consumption (ICES-2015-196). They are derived values, so `interpretation`, not `measured`.
- Results vary strongly with flow speed in the 0–5 cm/s range (NTRS 20160000593 abstract). Comparisons must keep flow speed and direction explicit.
- Thin-fuel and thick-fuel samples, and opposed and concurrent flow, are different regimes. Do not pool them.

## Recommended next step

1. A team member registers on PSI and downloads the PSI-25 file list and any per-test summary file into `data/raw/`. Record the SHA-256, the CC0 terms as shown on the page, and the exact file names.
2. If PSI-25 has a per-test table (sample, geometry, flow, O₂, outcome, spread rate), curate a first slice with the same method as FLEX: transcribe as provided, keep dashes and blanks as missing, add a flags file, and verify locally.
3. If it only has video or images, BASS stays a cited investigation (an `Investigation` record with sources) without measured Findings until values are published in a citable table.
