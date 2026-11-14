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
2. **Per-test measured values.** No table of BASS flame-spread rates or extinction limits has been located in a source whose rights are confirmed.
3. **ICES-2015-196.** I downloaded it locally (git-ignored; SHA-256 `e9c1286f0903700c0ae180a574debb6826f3676a072df2eeb926c22955a09831`). It has **no tables**; all results are figures. Reading values off its plots would be digitizing, which is `interpretation`, not `measured`. Do not ingest it as measured data.
4. **The summary report TM.** Its rights statement is restrictive. Check whether it has a test-matrix table, and get the rights reviewed, before using it.

## Major limitations to carry if ingested

- Ambient oxygen came from a model-guided nitrogen dilution, calibrated against onboard sensors. The ICES paper describes CSA-CP readings that were out of calibration and corrected for offset (Figure 4 caption). Oxygen values therefore need their stated correction method attached.
- Heat release rates in these papers were **estimated** from oxygen consumption (ICES-2015-196). They are derived values, so `interpretation`, not `measured`.
- Results vary strongly with flow speed in the 0–5 cm/s range (NTRS 20160000593 abstract). Comparisons must keep flow speed and direction explicit.
- Thin-fuel and thick-fuel samples, and opposed and concurrent flow, are different regimes. Do not pool them.

## Recommended next step

1. A team member registers on PSI and downloads the PSI-25 file list and any per-test summary file into `data/raw/`. Record the SHA-256, the CC0 terms as shown on the page, and the exact file names.
2. If PSI-25 has a per-test table (sample, geometry, flow, O₂, outcome, spread rate), curate a first slice with the same method as FLEX: transcribe as provided, keep dashes and blanks as missing, add a flags file, and verify locally.
3. If it only has video or images, BASS stays a cited investigation (an `Investigation` record with sources) without measured Findings until values are published in a citable table.
