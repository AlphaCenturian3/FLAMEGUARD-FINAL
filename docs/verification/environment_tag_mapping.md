# Source-to-environment tag mapping (Member 3 preparation for M3-T1 / Q-1)

**Status:** preparation, 2026-11-14. **Not a decision.** It changes no data, tag or contract. It applies Member 1's Q-1 resolution as recorded on PR #3: investigation tags hold "only environments the investigation's own sources state", and wider applicability goes in Member 5's **interpretation** findings, never in tags.

## Three separate things that must not be mixed

| | Meaning | Where it lives (PR #1 v0.2.0) |
|---|---|---|
| **Measured environment** | Where the experiment physically ran (gravity, platform) | `conditions.gravity_environment` and the investigation `platform` on measured findings |
| **Source-stated relevance** | An environment the investigation's own NASA source names as what the work is for | Investigation tag, with the quote that states it |
| **Extrapolation** | Our argument that results may apply to Moon, Mars or rovers | Member 5 `interpretation` findings with `relevant_environments` and required `limitations`. Never a tag, never measured |

**Rule of thumb:** none of BASS-II, FLEX, SoFIE or Saffire ran in lunar or Martian gravity. Their measured evidence is **ISS or orbital microgravity**. Applying it to partial gravity is extrapolation. The Liao synthesis states that partial-gravity behaviour "cannot be expected to be interpolated between the data obtained in normal and microgravity conditions" (printed p. 3, PDF p. 4; text match verified in the citation audit #14).

## Mapping (evidence = sentences found in each investigation's own cited sources on 2026-11-14)

How I checked:
- **Sources searched:** the NTRS API title and abstract, the live NASA pages, and the full FLEX report PDF.
- **Not searched:** PSI pages (they render client-side and need a login), and the full BASS-II TM (restrictive rights; not downloaded).
- **"Not found" means** not found in the text checked. It does not mean the claim is stated nowhere.

| Investigation | Member 5 tags (PR #3 `a0fa130`) | Measured environment | Source-stated (keep as tag) | Not source-stated in checked text (move to interpretation, or find a quote) |
|---|---|---|---|---|
| `bass-ii` | spacecraft, space_station, lunar_base, pressurized_rover | ISS microgravity (MSG) | **space_station**: "The Burning and Suppression of Solids-II (BASS-II) experiment was performed on the International Space Station." (NTRS 20160000593). **spacecraft**: "There are several important implications related to fundamental combustion research as well as spacecraft fire safety." (same) | **lunar_base, pressurized_rover**: no Moon or rover statement in NTRS 20160000593 or 20210011385 abstracts |
| `flex` | spacecraft, space_station, lunar_base | ISS microgravity (CIR/MDCA) | **space_station**: "The Flame Extinguishment Experiment (FLEX) is a droplet combustion experiment performed on the International Space Station (ISS)." (FLEX TP). **spacecraft**: "This objective reflected the FLEX focus on investigating fire safety in spacecraft." (FLEX TP) | **lunar_base**: the FLEX report has no lunar, Moon or Mars statement (full-text search). Its closest is "the maximum proposed oxygen mole fraction on future exploration vehicles" (printed p. 13, PDF p. 19), which names exploration *vehicles*, not a lunar base |
| `sofie` | spacecraft, space_station, lunar_base, martian_base | ISS microgravity (CIR) | **space_station**: "Solid Fuel Ignition and Extinction (SoFIE) Project on ISS." (NTRS 20200000361). **spacecraft**: "studies ignition and flammability of solid spacecraft materials" (same) | **lunar_base: borderline.** science.nasa.gov SoFIE page: "At reduced gravity, such as on the International Space Station (microgravity) or on the Moon (lunar gravity), fire acts differently…". That is general context, not a statement that SoFIE results target lunar bases, so it's a team call. **martian_base**: not found |
| `saffire` | spacecraft, lunar_base, martian_base, pressurized_rover | Orbital microgravity, uncrewed Cygnus (not ISS) | **spacecraft**: "These experiments directly address the risks associated with our understanding of spacecraft fire behavior at practical length scales and geometries." (NTRS 20240002981) | **lunar_base, martian_base, pressurized_rover**: not found in NTRS 20240002981 or 20180005168 abstracts. (`space_station` is correctly absent: Saffire ran on Cygnus after it left the ISS) |
| `fm2` | lunar_base | **None yet.** Planned lunar payload; flight and data status not verified | **lunar_base**: "This means that some things that are not flammable on Earth, may be flammable in potential habitats on the Moon and other places with reduced gravity." and "The experiment burns four fuel samples individually in atmospheric conditions planned for future lunar habitats or vehicles." (NASA FM2 page) | none. But there is no measured evidence; it is objectives only |
| `partial-gravity-synthesis` | lunar_base, martian_base | **None.** Research-needs synthesis, not an experiment | **lunar_base**: "…mitigation strategies to stop flame spread and prevent flashover in Lunar habitats…" (Liao printed p. 5, PDF p. 6). **martian_base**: "The partial gravity conditions after landing on the Moon or Mars, as well as the high oxygen concentration proposed for the Lunar habitat, bring in additional challenges for spacecraft fire safety." (Liao PDF p. 2). Names Mars surface operations, not a "base" as such, so the team should confirm | none |

The quotes in this table were extracted by script from the fetched text and are verbatim in that text. They have not yet been human-checked in context (same rule as the citation audit).

## Member 3 tag rule (applied in `environment_tags_source_supported.json`)

An Investigation tag is kept **only** if a sentence in that investigation's own cited source **directly** names the environment as what the work addresses. "Directly" means the source names that environment for this work, not general context. Borderline cases are **left out** until a direct quote is supplied. Unsupported Moon, Mars and rover applicability is never an Investigation tag; it belongs in Member 5's interpretation findings with limitations.

| Investigation | Tags kept (each with its quote) | Left out of tags |
|---|---|---|
| `bass-ii` | `space_station`, `spacecraft` | `lunar_base`, `pressurized_rover`: no source statement found |
| `flex` | `space_station`, `spacecraft` | `lunar_base`: no source statement found |
| `sofie` | `space_station`, `spacecraft` | `lunar_base`: borderline, general context only. `martian_base`: not found |
| `saffire` | `spacecraft` | `lunar_base`, `martian_base`, `pressurized_rover`: not found |
| `fm2` | `lunar_base` | none |
| `partial-gravity-synthesis` | `lunar_base` | `martian_base`: borderline (names Mars landing conditions, not a Mars base or habitat) |

Member 5 may argue any left-out environment as an **interpretation** finding (`relevant_environments` + required `limitations`). It should cite Liao's caution that partial-gravity fire behaviour "cannot be expected to be interpolated between the data obtained in normal and microgravity conditions". Under PR #1's transitive S9, no such interpretation may depend on an `excluded` finding.
3. **Rankings stay disabled.** This mapping is an input for the applicability gate (E2/G2 in Member 5's criteria). It does not activate anything, and no weights are frozen.

| Decision | Owner |
|---|---|
| Accept the tag removals or supply quotes | Member 5 (owner of `investigations.json`), with Member 3's provenance view |
| SoFIE `lunar_base` (borderline) and synthesis `martian_base` wording | Team |
| Tag-provenance rule wording (Q-1) | Member 1 + Member 3 |
