# Source quote verification audit (Member 5)

**Run date:** 2026-11-14 (re-run after adding the FLEX report quotes and the environmental reference table). **Scope:** every quote citation in `evidence_reported.json`, `investigations.json` and `environment_reference.json`.

**Result:** 43 quote citations. **29 verified automatically**, **14 verified manually**, **0 failed**. Executor check only: these citations are **recorded, not independently authenticated** (Member 1, PR #3 comment 6883984161) until Member 3 completes the independent review.

| File | Citations | Automated | Manual | Failed |
|---|---|---|---|---|
| `evidence_reported.json` | 17 | 13 | 4 | 0 |
| `investigations.json` | 7 | 6 | 1 | 0 |
| `environment_reference.json` | 19 | 10 | 9 | 0 |

## Methods

- **Automated:** `python -m flameguard.research.verify_sources <files>`. The tool fetches each URL and checks that the quote appears after normalising whitespace and HTML entities only. For `ntrs.nasa.gov/citations/<id>` it checks the public NTRS API record (title and abstract), because the citation page renders with JavaScript.
- **Manual (PDF):** PDF sources are not parsed by the tool (that would need a new dependency, which is Member 1's decision). Each PDF was downloaded on 2026-11-14, its text was extracted with `pypdf` in a scratch environment outside the repository, and the whitespace-normalised quote was found on the cited PDF page. Quotes avoid fragments where text extraction merged or split words. The check was done by Claude (executor), not by an independent person.
- **Independent check:** pending. Member 1 assigned the quote and source check to Member 3 (PR #3). A member other than the author spot-checks and signs below.

### PDFs checked manually (SHA-256 at retrieval)

| Document | Cited pages: printed (PDF index) | SHA-256 |
|---|---|---|
| Liao et al., partial-gravity white paper | printed 3 (PDF 4) | `0e313e8f833a216e36f0f9a7effd4def7c2f3d5c985248615bb80653e8b8979a` |
| NASA/TP-2015-216046, FLEX detailed results (NTRS 20150023456) | printed 2, 13 (PDF 8, 19) | `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d` |
| NASA OCHMO-TB-003 Rev A, Habitable Atmosphere | PDF 2 (no printed number); printed 8 (PDF 8) | `a53c44aef8248a7e4858c50ed95faaf8f0521a0c9ec7f3268f4592a355e77163` |
| NASA/TM-20220000524, M2M Habitation Considerations | printed 12, 18 (PDF 14, 20) | `bf33281400853a5053350455112cd2668a719c153f0d2cf04bb049403f70b179` |
| NTRS 20220000245, Artemis Deep Space Habitation | printed 2, 4 (PDF 2, 4) | `3e0ab65901986a20fe509cfb0f16cefa238c5db5da60628ce6027e11f9b64d83` |
| NASA/TP-2010-216134, Exploration Atmospheres Working Group | printed 107 (PDF 117) | `11f1a69be301d7d6ab40c90585c70cf95b2beb5cc88b3260ea85c16ddbf2de91` |

**Independent machine check by Member 3's executor** (PR #6 `docs/verification/m3_citation_audit_of_member5.md`, head `e4d3892`): PyMuPDF and fresh downloads, independent of Member 5's tool. **43 of 43 quotes found; all 6 PDF hashes match.** It is explicitly **not signed off**: the human checks (does the quote support the statement; source authority; rights) and the signature remain Member 3's. These citations are therefore still **recorded, not independently authenticated**.

## Per-citation results

| # | File | Record | Source URL | Method | Result |
|---|---|---|---|---|---|
| 1 | `evidence_reported.json` | `m5-bass2-flow-flareup` | https://ntrs.nasa.gov/citations/20160000593 | automated: NTRS API title+abstract | match |
| 2 | `evidence_reported.json` | `m5-bass2-co-co2-trend` | https://ntrs.nasa.gov/citations/20210011385 | automated: NTRS API title+abstract | match |
| 3 | `evidence_reported.json` | `m5-saffire6-co-co2` | https://ntrs.nasa.gov/citations/20240002981 | automated: NTRS API title+abstract | match |
| 4 | `evidence_reported.json` | `m5-saffire-enclosure-effect` | https://ntrs.nasa.gov/citations/20180005168 | automated: NTRS API title+abstract | match |
| 5 | `evidence_reported.json` | `m5-sofie-material-selection` | https://ntrs.nasa.gov/citations/20200000361 | automated: NTRS API title+abstract | match |
| 6 | `evidence_reported.json` | `m5-sofie-std6001-concern` | https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/solid-fuel-ignition-and-extinction-sofie/ | automated: live HTML text | match |
| 7 | `evidence_reported.json` | `m5-fm2-lower-oxygen-hypothesis` | https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/flammability-of-materials-on-the-moon-fm2/ | automated: live HTML text | match |
| 8 | `evidence_reported.json` | `m5-moon-hypothesis` | https://ntrs.nasa.gov/citations/20210020516 | automated: NTRS API title+abstract | match |
| 9 | `evidence_reported.json` | `m5-moon-scaling-objective` | https://ntrs.nasa.gov/citations/20210020516 | automated: NTRS API title+abstract | match |
| 10 | `evidence_reported.json` | `m5-flex-objective` | https://www1.grc.nasa.gov/space/iss-research/iss-fcf/combustion-science/ | automated: live HTML text | match |
| 11 | `evidence_reported.json` | `m5-flex-dataset` | https://ntrs.nasa.gov/citations/20150023456 | automated: NTRS API title+abstract | match |
| 12 | `evidence_reported.json` | `m5-bass-ground-methods` | https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/ | automated: live HTML text | match |
| 13 | `evidence_reported.json` | `m5-sofie-gel-model-trends` | https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/ | automated: live HTML text | match |
| 14 | `evidence_reported.json` | `m5-partial-gravity-not-interpolated` | https://smd-cms.nasa.gov/wp-content/uploads/2023/05/60_afb22b1e538432728848e83bb3ade8c2_LiaoYaTingT.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 15 | `evidence_reported.json` | `m5-flex-prediluted-ambient` | https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 16 | `evidence_reported.json` | `m5-flex-prediluted-ambient` | https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 17 | `evidence_reported.json` | `m5-flex-prediluted-ambient` | https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 18 | `investigations.json` | `bass-ii` | https://ntrs.nasa.gov/citations/20210011385 | automated: NTRS API title+abstract | match |
| 19 | `investigations.json` | `flex` | https://www1.grc.nasa.gov/space/iss-research/iss-fcf/combustion-science/ | automated: live HTML text | match |
| 20 | `investigations.json` | `flex` | https://ntrs.nasa.gov/citations/20150023456 | automated: NTRS API title+abstract | match |
| 21 | `investigations.json` | `sofie` | https://ntrs.nasa.gov/citations/20200000361 | automated: NTRS API title+abstract | match |
| 22 | `investigations.json` | `saffire` | https://ntrs.nasa.gov/citations/20240002981 | automated: NTRS API title+abstract | match |
| 23 | `investigations.json` | `fm2` | https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/flammability-of-materials-on-the-moon-fm2/ | automated: live HTML text | match |
| 24 | `investigations.json` | `partial-gravity-synthesis` | https://smd-cms.nasa.gov/wp-content/uploads/2023/05/60_afb22b1e538432728848e83bb3ade8c2_LiaoYaTingT.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 25 | `environment_reference.json` | `env-space-station` | https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/ | automated: live HTML text | match |
| 26 | `environment_reference.json` | `env-space-station` | https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 27 | `environment_reference.json` | `env-space-station` | https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-003-habitable-atmosphere.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 28 | `environment_reference.json` | `env-spacecraft` | https://ntrs.nasa.gov/api/citations/20220000524/downloads/M2M%20Habitation%20Considerations%20TM%20-%20Final.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 29 | `environment_reference.json` | `env-spacecraft` | https://ntrs.nasa.gov/api/citations/20220000524/downloads/M2M%20Habitation%20Considerations%20TM%20-%20Final.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 30 | `environment_reference.json` | `env-lunar-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html | automated: live HTML text | match |
| 31 | `environment_reference.json` | `env-lunar-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html | automated: live HTML text | match |
| 32 | `environment_reference.json` | `env-lunar-base` | https://ntrs.nasa.gov/api/citations/20220000524/downloads/M2M%20Habitation%20Considerations%20TM%20-%20Final.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 33 | `environment_reference.json` | `env-lunar-base` | https://ntrs.nasa.gov/api/citations/20220000524/downloads/M2M%20Habitation%20Considerations%20TM%20-%20Final.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 34 | `environment_reference.json` | `env-lunar-base` | https://ntrs.nasa.gov/api/citations/20220000245/downloads/Artemis%20Deep%20Space%20Habitation%20Enabling%20a%20Sustained%20Human%20Presence%20on%20the%20Moon%20and%20Beyond%20(3).pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 35 | `environment_reference.json` | `env-martian-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html | automated: live HTML text | match |
| 36 | `environment_reference.json` | `env-martian-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html | automated: live HTML text | match |
| 37 | `environment_reference.json` | `env-martian-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html | automated: live HTML text | match |
| 38 | `environment_reference.json` | `env-martian-base` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html | automated: live HTML text | match |
| 39 | `environment_reference.json` | `env-martian-base` | https://www.nasa.gov/wp-content/uploads/2023/03/henninger-8.2-34-atm-tp216134-2010.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 40 | `environment_reference.json` | `env-pressurized-rover` | https://ntrs.nasa.gov/api/citations/20220000245/downloads/Artemis%20Deep%20Space%20Habitation%20Enabling%20a%20Sustained%20Human%20Presence%20on%20the%20Moon%20and%20Beyond%20(3).pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |
| 41 | `environment_reference.json` | `env-earth` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html | automated: live HTML text | match |
| 42 | `environment_reference.json` | `env-earth` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html | automated: live HTML text | match |
| 43 | `environment_reference.json` | `env-earth` | https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html | automated: live HTML text | match |

## Independent spot check (to be completed)

| Reviewer (member, GitHub account) | Date | Entries checked | Mismatches | Signature |
|---|---|---|---|---|
| _pending_ | | | | |

Re-run this audit whenever a quote, URL or source changes. A mismatch blocks use of that record until fixed.
