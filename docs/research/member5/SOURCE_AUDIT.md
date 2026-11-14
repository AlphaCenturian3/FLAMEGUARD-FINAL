# Source quote verification audit (Member 5)

**Run date:** 2026-11-14 (re-run after Member 1's review trimmed the BASS-II flare-up quote to its observational clause). **Scope:** every quote citation in `investigations.json` and `evidence_reported.json`.

**Result:** 21 quote citations (17 distinct quotes). **19 verified automatically**, **2 verified manually**, **0 failed**.

## Methods

- **Automated:** `python -m flameguard.research.verify_sources docs/research/member5/evidence_reported.json docs/research/member5/investigations.json`. The tool fetches each URL and checks that the quote appears after normalising whitespace and HTML entities only. For `ntrs.nasa.gov/citations/<id>` it checks the public NTRS API record (title and abstract), because the citation page renders with JavaScript.
- **Manual:** PDF sources are not parsed by the tool (that would need a new dependency, which is Member 1's decision). The PDF was downloaded on 2026-11-14 (SHA-256 `0e313e8f833a216e36f0f9a7effd4def7c2f3d5c985248615bb80653e8b8979a`), its text was extracted with `pypdf` in a scratch environment outside the repository, and the whitespace-normalised quote was found on **page 4**. The check was done by Claude (executor), not yet by an independent person.
- **Independent check:** not done yet. Member 1 assigned the quote and source check to Member 3 (PR #3). Under spec §4.2 a member other than the author should spot-check these entries and sign below.

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
| 15 | `investigations.json` | `bass-ii` | https://ntrs.nasa.gov/citations/20210011385 | automated: NTRS API title+abstract | match |
| 16 | `investigations.json` | `flex` | https://www1.grc.nasa.gov/space/iss-research/iss-fcf/combustion-science/ | automated: live HTML text | match |
| 17 | `investigations.json` | `flex` | https://ntrs.nasa.gov/citations/20150023456 | automated: NTRS API title+abstract | match |
| 18 | `investigations.json` | `sofie` | https://ntrs.nasa.gov/citations/20200000361 | automated: NTRS API title+abstract | match |
| 19 | `investigations.json` | `saffire` | https://ntrs.nasa.gov/citations/20240002981 | automated: NTRS API title+abstract | match |
| 20 | `investigations.json` | `fm2` | https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/flammability-of-materials-on-the-moon-fm2/ | automated: live HTML text | match |
| 21 | `investigations.json` | `partial-gravity-synthesis` | https://smd-cms.nasa.gov/wp-content/uploads/2023/05/60_afb22b1e538432728848e83bb3ade8c2_LiaoYaTingT.pdf | manual: PDF text extracted with pypdf (scratch env), whitespace-normalised substring match | match (manual, 2026-11-14) |

## Independent spot check (to be completed)

| Reviewer (member, GitHub account) | Date | Entries checked | Mismatches | Signature |
|---|---|---|---|---|
| _pending_ | | | | |

Re-run this audit whenever a quote, URL or source changes. A mismatch blocks use of that record until fixed.
