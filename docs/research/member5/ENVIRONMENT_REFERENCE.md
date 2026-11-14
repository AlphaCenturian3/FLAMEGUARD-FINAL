# Environmental reference conditions (D-01, condition 2)

**Status:** draft for Member 1 and Member 3 review. Machine-readable version with every citation: `environment_reference.json`. All sources were retrieved on 2026-11-14.

**Rules used:**

- **Physical** conditions (properties of the Moon, Mars, Earth or orbital free fall) are kept separate from **design assumptions** (spacecraft or habitat cabin atmospheres).
- A value no reviewed source gives is **unknown**. Nothing is estimated.
- The only conversions are exact defined factors (1 mb = 0.1 kPa; 1 bar = 100 kPa; percent ÷ 100). The as-printed value is kept in the JSON.
- None of these values is a measurement from a combustion experiment.

## Physical conditions

| Context | Gravity | Contract category | External pressure | External O₂ | Source |
|---|---|---|---|---|---|
| `space_station` | microgravity (orbital free fall) | microgravity | not applicable (fires are inside the cabin) | not applicable | NASA, *Studying Combustion and Fire Safety* |
| `spacecraft` | microgravity in orbit or transit | microgravity (**editorial classification**, Member 1 to confirm) | not applicable | not applicable | none; classification by Member 5 |
| `lunar_base` | 1.62 m/s² (0.165 × Earth) | partial_gravity | 3 × 10⁻¹⁵ bar at night (effectively vacuum) | not applicable | NASA NSSDC Moon Fact Sheet |
| `martian_base` | 3.73 m/s² mean (0.380 × Earth) | partial_gravity | 0.636 kPa (6.36 mb at mean radius; 4.0–8.7 mb by season) | 0.0016 (0.16 %; atmosphere 95.1 % CO₂) | NASA NSSDC Mars Fact Sheet |
| `pressurized_rover` | **location-dependent** (Artemis PR is a lunar surface element) | partial_gravity for a lunar or Martian rover | location-dependent | location-dependent | Artemis Deep Space Habitation paper (NTRS 20220000245), p. 2 |
| `earth` | 9.820 m/s² mean | normal_gravity | 101.4 kPa (1014 mb) | 0.2095 (20.95 %, dry air) | NASA NSSDC Earth Fact Sheet |

## Design assumptions (cabin and habitat atmospheres)

| Context | Atmosphere | Pressure (kPa) | O₂ mole fraction | Status | Source |
|---|---|---|---|---|---|
| `space_station` | ISS cabin, typical | 101.3 (14.7 psia) | 0.21 | **operational** | NASA OCHMO-TB-003 Rev A, pp. 8 and 2 |
| `spacecraft` | Gateway nominal (assumed for the Mars Transit Habitat, hatch open) | 70.3 (10.2 psia) | 0.265 | design assumption | NASA/TM-20220000524 (M2M Habitation Considerations), p. 20 |
| `spacecraft` | Mars Transit Habitat, hatch closed | 101.4 (14.7 psia) | **unknown** (not stated) | design assumption | NASA/TM-20220000524, p. 20 |
| `lunar_base` | Surface Habitat, nominal | 70.3 (10.2 psia) | 0.265 | design assumption | NASA/TM-20220000524, p. 14; NTRS 20220000245, p. 4 (trade studies ongoing) |
| `lunar_base` | Surface Habitat, capability | 56.5 (8.2 psi) | 0.34 | design assumption | NASA/TM-20220000524, p. 14 |
| `martian_base` | Martian surface habitat, current design | **unknown** | **unknown** | unknown | no reviewed NASA source gives a current design |
| `martian_base` (context only) | Long-duration planetary-surface outpost habitats, 2010 recommendation | 7.6–8.0 psia (kPa left unconverted) | 0.32 | **historical recommendation**: not a current design, not used for matching | NASA/TP-2010-216134, PDF p. 117 |
| `pressurized_rover` | Pressurized Rover cabin | **unknown** | **unknown** | unknown | no reviewed NASA source gives it |
| `earth` | none (physical atmosphere is the reference) | — | — | not applicable | — |

## Verification

19 quote citations in `environment_reference.json`:

- **10** were verified automatically against the live pages (NSSDC fact sheets; NASA combustion page) with `python -m flameguard.research.verify_sources docs/research/member5/environment_reference.json`.
- **9** are PDF sources and were verified **manually**: the PDF text was extracted with `pypdf` in a scratch environment and the whitespace-normalised quote was found on the cited page. Quotes avoid fragments where text extraction merged words.

PDF SHA-256 values at retrieval:

| Document | SHA-256 |
|---|---|
| OCHMO-TB-003 Rev A | `a53c44aef8248a7e4858c50ed95faaf8f0521a0c9ec7f3268f4592a355e77163` |
| NASA/TM-20220000524 | `bf33281400853a5053350455112cd2668a719c153f0d2cf04bb049403f70b179` |
| NTRS 20220000245 | `3e0ab65901986a20fe509cfb0f16cefa238c5db5da60628ce6027e11f9b64d83` |
| NASA/TP-2010-216134 | `11f1a69be301d7d6ab40c90585c70cf95b2beb5cc88b3260ea85c16ddbf2de91` |

An independent check by Member 3 is still pending, as for `SOURCE_AUDIT.md`.

## Known gaps

- No NASA source reviewed gives a **current** Martian surface habitat or Pressurized Rover cabin atmosphere. The only Mars-surface value found is the 2010 working-group recommendation (7.6–8.0 psia, 32 % O₂), recorded as historical context and not used for matching. Search results indicate later revisions toward 8.2 psia / 34 % O₂ for exploration vehicles; that revision is not verified here.
- Habitat atmospheres are design assumptions and may change (NTRS 20220000245 states trade studies are ongoing).
- Lunar and Martian gravity both map to the contract category `partial_gravity`.
