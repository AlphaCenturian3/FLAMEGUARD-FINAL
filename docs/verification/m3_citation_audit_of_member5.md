# Member 3 independent audit of Member 5's 43 citations

**Audit status: NOT APPROVED.** Only check T (text match) has evidence. Checks C and R are open. The audit can be approved only by Member 3 personally, after independent human review of C and R for every entry. The executor (Claude, working for Member 3) does not approve or sign.

| | |
|---|---|
| Audited files | `docs/research/member5/evidence_reported.json` (17), `investigations.json` (7), `environment_reference.json` (19), at PR #3 head `a0fa130` |
| Assigned by | Member 1 (PR #3 comment 6883984161). This is reciprocal to Member 5's Q3 check of Member 3's FLEX data; neither member authenticates their own work |
| Revised | 2026-11-14: split into T, C and R; printed and PDF page numbers added |

## Three separate checks: a pass on one says nothing about the others

| Check | Question | Who and how | Status |
|---|---|---|---|
| **T: text match** | Does the quoted text appear verbatim in the cited source, at the cited page or locator? | Machine, independent of Member 5's tool (method below), plus human spot-confirmation | **Evidence complete: 43 of 43 found.** Human spot-confirmation open |
| **C: contextual scientific validity** | Read in its surrounding text, does the quote support the record's `statement` and classification, without overreach? Is the claim about what the record says it is about (investigation, gravity level, quantity)? Does the full document contradict an abstract-only quote? | **Human only**, Member 3 | **Open: 0 of 43** |
| **R: rights and source authority** | Is the source an appropriate authority for this claim, and do its stated rights allow our use (quote, display, redistribution)? | **Human only**, Member 3, recording the rights statement seen | **Open: 0 of 43** |

## T: machine method and results

- **Independent of Member 5:** I did not use Member 5's `verify_sources` tool or their pypdf extraction.
- **NTRS citations:** the public NTRS API record (title and abstract), fetched fresh.
- **HTML pages:** fetched live, with scripts and styles removed and tags stripped.
- **PDFs:** downloaded fresh into git-ignored `data/raw/m3-audit/`, text extracted with **PyMuPDF**, and every page searched.
- **Matching levels:** exact, then after whitespace, dash and quote normalisation, then whitespace-insensitive.

**Results:**
- 24 exact matches: 22 NTRS or HTML, plus PDF #27 and #33.
- 19 matched only after normalisation: 7 NSSDC table rows, where superscript markup splits "m/s 2", and 12 PDF quotes that span line breaks.
- Every PDF quote is on the PDF page Member 5 cites, and on no other page.
- **All 6 PDF SHA-256 hashes match** the hashes Member 5 recorded:
  - Liao `0e313e8f833a…`
  - FLEX TP `b4f6ca983e27…`
  - OCHMO-TB-003 `a53c44aef824…`
  - M2M TM `bf3328140085…`
  - Artemis `3e0ab6590198…`
  - TP-2010-216134 `11f1a69be301…`

## Page numbers: printed vs PDF

Member 5 cites **PDF page indices**. Printed page labels were read from rendered header and footer strips of each cited page (2026-11-14).

| Document | Cited PDF page → printed page | Differs? |
|---|---|---|
| Liao et al. partial-gravity white paper | 4 → 3 | **yes** |
| NASA/TP-2015-216046 (FLEX) | 8 → 2; 19 → 13 (offset 6 throughout) | **yes** |
| NASA/TM-20220000524 (M2M) | 20 → 18; 14 → 12 | **yes** |
| NASA/TP-2010-216134 | 117 → 107 | **yes** |
| OCHMO-TB-003 Rev A | 8 → 8; 2 → 2 | no |
| NTRS 20220000245 (Artemis) | 4 → 4; 2 → 2 | no |

PR #4 (FLEX data) cites **printed** pages and now also lists the PDF page for each (`data/docs/flex_table_ix.md`, "Cited pages"). **Team decision still needed** on one convention for `Source.page`. Recommendation: the printed page in `page`, with the PDF index in the locator or note whenever they differ.

## Other findings for Member 5 (not mismatches)

- **F2.** Entry 6 quotes "impelements". The misspelling is in the live NASA page text, so the quote is verbatim and correct.
- **F3.** Entries 30–43 cite NSSDC fact sheets and habitat documents for environment constants. They are not combustion evidence. Check C should confirm they are used only as environment context.

## Per-entry checklist

"Printed" and "PDF" are page numbers; **bold** means they differ. T is the machine result. **C and R are unticked until the human check is done.**

| # | Record | Source checked | Printed | PDF | T: text match (machine) | C | R |
|---|---|---|---|---|---|---|---|
| 1 | `m5-bass2-flow-flareup` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 2 | `m5-bass2-co-co2-trend` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 3 | `m5-saffire6-co-co2` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 4 | `m5-saffire-enclosure-effect` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 5 | `m5-sofie-material-selection` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 6 | `m5-sofie-std6001-concern` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 7 | `m5-fm2-lower-oxygen-hypothesis` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 8 | `m5-moon-hypothesis` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 9 | `m5-moon-scaling-objective` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 10 | `m5-flex-objective` | live HTML | n/a | n/a | found (re-run after transient SSL error; identical quote+URL to #19, exact) | ☐ | ☐ |
| 11 | `m5-flex-dataset` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 12 | `m5-bass-ground-methods` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 13 | `m5-sofie-gel-model-trends` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 14 | `m5-partial-gravity-not-interpolated` | PDF (PyMuPDF) | **3** (differs) | 4 | found, line-break normalised | ☐ | ☐ |
| 15 | `m5-flex-prediluted-ambient` | PDF (PyMuPDF) | **2** (differs) | 8 | found, line-break normalised | ☐ | ☐ |
| 16 | `m5-flex-prediluted-ambient` | PDF (PyMuPDF) | **13** (differs) | 19 | found, line-break normalised | ☐ | ☐ |
| 17 | `m5-flex-prediluted-ambient` | PDF (PyMuPDF) | **13** (differs) | 19 | found, line-break normalised | ☐ | ☐ |
| 18 | `bass-ii` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 19 | `flex` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 20 | `flex` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 21 | `sofie` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 22 | `saffire` | NTRS API abstract | n/a | n/a | found, exact | ☐ | ☐ |
| 23 | `fm2` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 24 | `partial-gravity-synthesis` | PDF (PyMuPDF) | **3** (differs) | 4 | found, line-break normalised | ☐ | ☐ |
| 25 | `env-space-station` | live HTML | n/a | n/a | found, exact | ☐ | ☐ |
| 26 | `env-space-station` | PDF (PyMuPDF) | 8 | 8 | found, line-break normalised | ☐ | ☐ |
| 27 | `env-space-station` | PDF (PyMuPDF) | 2 | 2 | found, exact | ☐ | ☐ |
| 28 | `env-spacecraft` | PDF (PyMuPDF) | **18** (differs) | 20 | found, line-break normalised | ☐ | ☐ |
| 29 | `env-spacecraft` | PDF (PyMuPDF) | **18** (differs) | 20 | found, line-break normalised | ☐ | ☐ |
| 30 | `env-lunar-base` | live HTML; locator: Bulk parameters table, row 'Surface gravity' (Moon, Earth, ratio) | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 31 | `env-lunar-base` | live HTML; locator: Lunar Atmosphere | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 32 | `env-lunar-base` | PDF (PyMuPDF) | **12** (differs) | 14 | found, line-break normalised | ☐ | ☐ |
| 33 | `env-lunar-base` | PDF (PyMuPDF) | **12** (differs) | 14 | found, exact | ☐ | ☐ |
| 34 | `env-lunar-base` | PDF (PyMuPDF) | 4 | 4 | found, line-break normalised | ☐ | ☐ |
| 35 | `env-martian-base` | live HTML; locator: Bulk parameters table, row 'Surface gravity (mean)' (Mars, Earth, ratio) | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 36 | `env-martian-base` | live HTML; locator: Martian Atmosphere | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 37 | `env-martian-base` | live HTML; locator: Martian Atmosphere, composition | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 38 | `env-martian-base` | live HTML; locator: Martian Atmosphere, minor constituents | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 39 | `env-martian-base` | PDF (PyMuPDF) | **107** (differs) | 117 | found, line-break normalised | ☐ | ☐ |
| 40 | `env-pressurized-rover` | PDF (PyMuPDF) | 2 | 2 | found, line-break normalised | ☐ | ☐ |
| 41 | `env-earth` | live HTML; locator: Bulk parameters table, row 'Surface gravity (mean)' | n/a | n/a | found, whitespace-normalised | ☐ | ☐ |
| 42 | `env-earth` | live HTML; locator: Terrestrial Atmosphere | n/a | n/a | found, exact | ☐ | ☐ |
| 43 | `env-earth` | live HTML; locator: Terrestrial Atmosphere, composition | n/a | n/a | found, exact | ☐ | ☐ |

## Approval (Member 3 only, after C and R are done for all 43)

| Member 3 GitHub account | Date | T confirmed | C passed | R passed | Mismatches | Decision |
|---|---|---|---|---|---|---|
| _pending_ | | | | | | **not approved** |

A failure on any of T, C or R blocks that record until Member 5 fixes it. Once approved, post the result on PR #3, so Member 5's `SOURCE_AUDIT.md` can reference it. Member 3 does not edit Member 5's file.
