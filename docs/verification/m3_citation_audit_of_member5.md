# Member 3 independent audit of Member 5's 43 citations: checklist and machine evidence

**Status: NOT SIGNED OFF.** This file holds evidence and a checklist. Sign-off is Member 3's own act, by the person, after the human checks below. The executor (Claude, working for Member 3) does not sign.

| | |
|---|---|
| Audited files | `docs/research/member5/evidence_reported.json` (17), `investigations.json` (7), `environment_reference.json` (19), at PR #3 head `a0fa130` |
| Assigned by | Member 1 (PR #3 comment 6883984161): Member 3 authenticates Member 5's citations. This is reciprocal to Member 5's Q3 check of Member 3's FLEX data; neither member authenticates their own work |
| Date | 2026-11-14 |

## Machine evidence (independent of Member 5's tool)

I did **not** use Member 5's `verify_sources` tool or their pypdf extraction. Method:
- **NTRS citations:** the public NTRS API record (title and abstract), fetched fresh.
- **HTML pages:** fetched live, with scripts and styles removed and tags stripped.
- **PDFs:** downloaded fresh into git-ignored `data/raw/m3-audit/`, text extracted with **PyMuPDF**, and every page searched, so the page where the quote sits is found independently of the cited page.
- **Matching:** each quote was tested exactly, then after whitespace, dash and quote normalisation, then whitespace-insensitive. Each level is reported separately.

**Result: 43 of 43 quotes found.**
- 24 match exactly: 22 NTRS or HTML, including #10 (see its row), plus 2 PDF (#27, #33).
- 19 match only after whitespace or line-break normalisation: 7 NSSDC HTML table rows, where superscript markup splits "m/s 2", and 12 PDF quotes that span line breaks.
- Every PDF quote was found on the page number Member 5 cites, and on no other page.
- **All 6 PDF SHA-256 hashes match** the hashes Member 5 recorded at retrieval:
  - Liao `0e313e8f833a…`
  - FLEX TP `b4f6ca983e27…`
  - OCHMO-TB-003 `a53c44aef824…`
  - M2M TM `bf3328140085…`
  - Artemis `3e0ab6590198…`
  - TP-2010-216134 `11f1a69be301…`

**What the machine check does NOT establish** (these are the human checks):
1. That the quote **supports the statement** Member 5 attaches to it, without overreach. This means reading the record's `statement` and `classification` against the quote in context.
2. That the **source is authoritative** for the claim, and that its **rights** allow our use.
3. That the **cited page or locator** is the right convention (see finding F1).
4. For NTRS-abstract citations, that the full document does not contradict the abstract.

## Findings for Member 5 (not mismatches)

- **F1. Page-number convention differs between workstreams.** Member 5 cites the FLEX report as pages 8 and 19, which are **PDF page indices**. PR #4 cites **printed** pages: printed p. 13 is PDF p. 19, an offset of 6. Both are internally correct, but a reader following "p. 19" would land in different places. **Team decision needed:** one convention for `Source.page` (recommendation: printed page, with the PDF index in the locator).
- **F2. Entry 6 quotes "impelements".** This spelling error is in the live NASA page text (exact match), so the quote is verbatim. Keep it, optionally with "[sic]" in display only.
- **F3. Quotes 30–43 cite NSSDC fact sheets** for planetary constants. These are environment-reference facts, not combustion evidence. They are correct as quotes, but the human check should confirm they are only used as environment context (Member 1's D-01.2 labels).

## Human checklist (Member 3 fills in; one row per entry below)

For each entry tick **Q** (quote supports the statement, read in context) and **S** (source and rights appropriate for the use). Record any mismatch, which blocks that record until fixed.

| # | File | Record | Machine method | Cited page | Machine result | Q | S |
|---|---|---|---|---|---|---|---|
| 1 | `evidence_reported` | `m5-bass2-flow-flareup` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 2 | `evidence_reported` | `m5-bass2-co-co2-trend` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 3 | `evidence_reported` | `m5-saffire6-co-co2` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 4 | `evidence_reported` | `m5-saffire-enclosure-effect` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 5 | `evidence_reported` | `m5-sofie-material-selection` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 6 | `evidence_reported` | `m5-sofie-std6001-concern` | live HTML text | — | match, exact | ☐ | ☐ |
| 7 | `evidence_reported` | `m5-fm2-lower-oxygen-hypothesis` | live HTML text | — | match, exact | ☐ | ☐ |
| 8 | `evidence_reported` | `m5-moon-hypothesis` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 9 | `evidence_reported` | `m5-moon-scaling-objective` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 10 | `evidence_reported` | `m5-flex-objective` | live HTML text (re-run) | — | match. The first attempt hit a transient SSL error; the re-run matched after whitespace normalisation. The quote and URL are identical to #19, which matched exactly | ☐ | ☐ |
| 11 | `evidence_reported` | `m5-flex-dataset` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 12 | `evidence_reported` | `m5-bass-ground-methods` | live HTML text | — | match, exact | ☐ | ☐ |
| 13 | `evidence_reported` | `m5-sofie-gel-model-trends` | live HTML text | — | match, exact | ☐ | ☐ |
| 14 | `evidence_reported` | `m5-partial-gravity-not-interpolated` | PDF text (PyMuPDF) | 4 | match, PDF page(s) [4] (line-break normalised) | ☐ | ☐ |
| 15 | `evidence_reported` | `m5-flex-prediluted-ambient` | PDF text (PyMuPDF) | 8 | match, PDF page(s) [8] (line-break normalised) | ☐ | ☐ |
| 16 | `evidence_reported` | `m5-flex-prediluted-ambient` | PDF text (PyMuPDF) | 19 | match, PDF page(s) [19] (line-break normalised) | ☐ | ☐ |
| 17 | `evidence_reported` | `m5-flex-prediluted-ambient` | PDF text (PyMuPDF) | 19 | match, PDF page(s) [19] (line-break normalised) | ☐ | ☐ |
| 18 | `investigations` | `bass-ii` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 19 | `investigations` | `flex` | live HTML text | — | match, exact | ☐ | ☐ |
| 20 | `investigations` | `flex` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 21 | `investigations` | `sofie` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 22 | `investigations` | `saffire` | NTRS API title+abstract | Abstract | match, exact | ☐ | ☐ |
| 23 | `investigations` | `fm2` | live HTML text | — | match, exact | ☐ | ☐ |
| 24 | `investigations` | `partial-gravity-synthesis` | PDF text (PyMuPDF) | 4 | match, PDF page(s) [4] (line-break normalised) | ☐ | ☐ |
| 25 | `environment_reference` | `env-space-station` | live HTML text | — | match, exact | ☐ | ☐ |
| 26 | `environment_reference` | `env-space-station` | PDF text (PyMuPDF) | 8 | match, PDF page(s) [8] (line-break normalised) | ☐ | ☐ |
| 27 | `environment_reference` | `env-space-station` | PDF text (PyMuPDF) | 2 | match, PDF page(s) [2] (line-break normalised) | ☐ | ☐ |
| 28 | `environment_reference` | `env-spacecraft` | PDF text (PyMuPDF) | 20 | match, PDF page(s) [20] (line-break normalised) | ☐ | ☐ |
| 29 | `environment_reference` | `env-spacecraft` | PDF text (PyMuPDF) | 20 | match, PDF page(s) [20] (line-break normalised) | ☐ | ☐ |
| 30 | `environment_reference` | `env-lunar-base` | live HTML text | Bulk parameters table, row 'Surface gravity' (Moon, Earth, ratio) | match after whitespace normalisation | ☐ | ☐ |
| 31 | `environment_reference` | `env-lunar-base` | live HTML text | Lunar Atmosphere | match after whitespace normalisation | ☐ | ☐ |
| 32 | `environment_reference` | `env-lunar-base` | PDF text (PyMuPDF) | 14 | match, PDF page(s) [14] (line-break normalised) | ☐ | ☐ |
| 33 | `environment_reference` | `env-lunar-base` | PDF text (PyMuPDF) | 14 | match, PDF page(s) [14] (line-break normalised) | ☐ | ☐ |
| 34 | `environment_reference` | `env-lunar-base` | PDF text (PyMuPDF) | 4 | match, PDF page(s) [4] (line-break normalised) | ☐ | ☐ |
| 35 | `environment_reference` | `env-martian-base` | live HTML text | Bulk parameters table, row 'Surface gravity (mean)' (Mars, Earth, ratio) | match after whitespace normalisation | ☐ | ☐ |
| 36 | `environment_reference` | `env-martian-base` | live HTML text | Martian Atmosphere | match after whitespace normalisation | ☐ | ☐ |
| 37 | `environment_reference` | `env-martian-base` | live HTML text | Martian Atmosphere, composition | match after whitespace normalisation | ☐ | ☐ |
| 38 | `environment_reference` | `env-martian-base` | live HTML text | Martian Atmosphere, minor constituents | match after whitespace normalisation | ☐ | ☐ |
| 39 | `environment_reference` | `env-martian-base` | PDF text (PyMuPDF) | 117 | match, PDF page(s) [117] (line-break normalised) | ☐ | ☐ |
| 40 | `environment_reference` | `env-pressurized-rover` | PDF text (PyMuPDF) | 2 | match, PDF page(s) [2] (line-break normalised) | ☐ | ☐ |
| 41 | `environment_reference` | `env-earth` | live HTML text | Bulk parameters table, row 'Surface gravity (mean)' | match after whitespace normalisation | ☐ | ☐ |
| 42 | `environment_reference` | `env-earth` | live HTML text | Terrestrial Atmosphere | match, exact | ☐ | ☐ |
| 43 | `environment_reference` | `env-earth` | live HTML text | Terrestrial Atmosphere, composition | match, exact | ☐ | ☐ |

## Sign-off (Member 3 only, after the human checks)

| Member 3 GitHub account | Date | Entries human-checked | Mismatches | Decision |
|---|---|---|---|---|
| _pending_ | | | | _pending_ |

Once signed, post the result on PR #3, so Member 5's `SOURCE_AUDIT.md` can reference it. Member 5's file is not edited by Member 3.
