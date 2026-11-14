# Q3 independent spot-check of Member 3's FLEX material (PR #4 and PR #6)

**Reviewer:** Member 5's executor (Claude), working for Member 5 (`16trtuoiloz-ducdo`). This is a review **record**, not Member 5's personal sign-off, and not an approval of PR #4 or PR #6. Read-only: no Member 3 branch was changed.
**Date:** 2026-11-14. **Commits reviewed:** PR #4 `e9c89aa5f9c0d613fdcd6666c2242c238523663f`; PR #6 `e4d38920a0147c6bed51ce8d08c87291b2a1f147`.
**Destination after CP1:** `docs/verification/source_spotcheck.md` (Member 5, spec §4.2). That folder does not exist on this branch yet.

## Source and method

- **Source:** *Detailed Results From the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011*, NASA/TP-2015-216046 (NTRS 20150023456). It was downloaded independently by Member 5 on 2026-11-14 from `https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf`. **SHA-256 `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d`**, identical to the hash recorded in PR #4's manifest, so both workstreams checked the same file.
- **Text extraction:** `pypdf` in a scratch environment (Member 3 used PyMuPDF and their own `tools/verify_flex_table_ix.py`; this check uses neither). Pages are referenced as printed page / PDF index; **the offset is +6** (printed p. 20 = PDF p. 26).
- **Coverage:** Q3 asks for a sample of max(5, 10 %). This check covers **100 %**: every cell of FLEX-001 to FLEX-010, all 43 flags, and both manifest hashes. No seed is needed.
- **Not checked:** PSI electronic data (PSI-69; client-rendered pages, not accessed), and Table IX rows beyond FLEX-010 (not in PR #4).

## A. Transcription of Table IX (printed p. 20 / PDF p. 26)

| Check | Source | Result | Status |
|---|---|---|---|
| 10 rows × 14 printed columns (identifier, date, GMT, fuel, pressure mmHg, O₂/N₂/CO₂/He mole fractions, initial diameter mm, extinction diameter mm, burning rate mm²/s, burn time s, test end) | Table IX | **140 of 140 cells match** (numeric equality; leading-zero forms such as ".21" = 0.21) | **Verified** |
| Printed dashes → empty cells, each declared in `source_dash_fields` | Table IX | 9 dash cells (FLEX-004, -007, -008, -010 extinction diameter; FLEX-009 time, initial diameter, extinction diameter, burning rate, burn time); all empty and declared; no undeclared blanks | **Verified** |
| `test_date_iso` from printed M/D/YY | Table IX | All 10 correct | **Verified** |
| Mole fractions sum to 1 | Table IX | All 10 rows sum to 1.0 | **Verified** |
| Units in the column names | Table IX headings | mmHg, mole fraction, mm, mm²/s, s: match the printed headings | **Verified** |
| Page fields | Table IX | `source_printed_page` 20, `source_pdf_page` 26 on every row | **Verified** |
| Conditions in the captions match the row | Appendix B, Figures 5–14 (printed pp. 29–38) | FLEX-001 to 009: "cabin air (0.21/0.79 O2/N2), 1.0-atm"; FLEX-010: "0.21/0.09/0.70 O2/N2/CO2, 3.0-atm" (2319.7 mmHg ≈ 3.05 atm). Every caption says "Free-floating" | **Verified** |
| Manifest SHA-256 of the CSV and the flags file | PR #4 `data/manifest.json` | Both match the committed blobs (`data/.gitattributes` keeps them byte-exact) | **Verified** |

**Transcription discrepancies found: 0.**

## B. Quality flags (`data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv`)

| Check | Result | Status |
|---|---|---|
| 43 flags: 1 `exclude`, 9 `not_available`, 33 `caution` | Counts confirmed; PR #6's breakdown (15 row-level, 10 initial diameter, 2 burning rate, 1 extinction diameter, 5 test end) also confirmed | **Verified** |
| Each `source_quote` on its cited printed page | **43 of 43** found verbatim on PDF page = printed + 6 | **Verified** |
| Every dash cell has a `not_available` flag, and no such flag lacks a dash | 9 = 9; none missing, none extra | **Verified** |
| F027/F033: two meanings of a dash | A.1 (printed p. 19): "'–' indicates flame extinction did not occur either because the droplet burned to completion or because a droplet disruption ended the test" and "If the droplet was not in the HiBMS FOV for enough time, the extinction droplet diameter is not listed." | **Verified** |
| F022: extinction diameters may be extrapolated | A.1: "we did estimate (extrapolate the burning history) to determine the extinction droplet diameter if there was sufficient burning history" | **Verified** |
| F003 and others: 1/30 s shutter for FLEX-001 to 009 | §5.1 (printed p. 16): "This was especially present from the FLEX-001 test to the FLEX-009 test. For these tests, the shutter speed … was 1/30 s" | **Verified** |
| Contamination caveat on all 10 rows ("all tests in this report") | §5.2 (printed p. 16): coated needles; "All tests subsequent to these (to be reported in the future) will not have contamination" | **Verified** (scope supported) |
| F042 FLEX-010 burning rate `exclude` | Table IX prints `.37`; Figure 14 caption (printed p. 38): "no burning rate constant or extinction droplet diameter is reported" | **Verified**: genuine internal inconsistency in the NASA report; `exclude` is justified |

## C. Findings

### Source discrepancies (in the NASA report or the data, not the contract)

| # | Source | Checked value | Observation | Status / recommendation (Member 3 decides) |
|---|---|---|---|---|
| S-1 | Table IX vs Figure 14 caption (printed pp. 20, 38) | FLEX-010 burning rate `.37` mm²/s | The table prints a value; the caption says none is reported | **Handled correctly** by F042 (`exclude`, value kept as printed). Resolution against PSI electronic data is **blocked** (PSI not accessed) |
| S-2 | Figure 14 caption (printed p. 38) | FLEX-010 initial diameter `3.86` mm | Caption: "The HiBMs produced a saturated image that influenced the droplet size measurement … the droplet size measurement was a function of which 'quad-slice' the droplet was in" | **Gap:** no imaging caution on FLEX-010 `initial_droplet_diameter_mm` (only the row-level contamination flag). Recommend adding a `caution` flag quoting this sentence |
| S-3 | Figure 14 caption (printed p. 38) | FLEX-010 burn time `13.6` s | Caption: the droplet "quickly moved west out of the fields of view (FOVs) of the … HiBMs, LLUV, and color camera". The report does not say how the printed burn time was obtained | **Open question**, not an error. Recommend a `caution` flag or a note until PSI data clarifies it |
| S-4 | Table IX; Figure 5 caption (printed p. 29) | FLEX-001 test end "Disruption" with extinction diameter 0.89 | Outcome ambiguous | **Handled** by F005 |
| S-5 | §5.2 (printed p. 17) | Contamination cautions | The authors assert burning-rate constants and droplet histories were "minimally influenced by the contaminant" | **Observation:** the blanket caution is conservative. Consider quoting the p. 17 assertion in the reason so the caution is balanced |
| S-6 | Table IX identifiers; captions | FLEX-001, -007, -008, -009 identifiers contain "CAL", but their captions do not say "calibration" | Flags follow the caption text, which is correct; this check does not infer a meaning for "CAL" | **No action**; noted for Member 3 |

### Unresolved contract interpretations (not source discrepancies; decided through PR #1 or D5)

| # | Topic | Where | Status |
|---|---|---|---|
| C-1 | **Page-number convention.** Printed pages (PR #4) vs PDF index (Member 5's FLEX citations). PR #4's manifest also attaches printed page numbers to a PDF download URL | PR #6 audit F1 | **Team decision needed.** Member 5 agrees with Member 3's recommendation: `Source.page` = printed page, PDF index in the locator |
| C-2 | Test outcome (`test_end`) has no vocabulary home; 5 cautions sit on it | PR #6 G2 | Open (Member 1 and Member 2) |
| C-3 | `not_available` on a non-quantity field (FLEX-009 time) | PR #6 G3 | Open |
| C-4 | S10(d) quote verification without the PDF in CI | PR #6 G5 | Open. **This Q3 check is independent evidence for option (a)**: 43 of 43 flag quotes and 140 of 140 cells verified against the same SHA-256 file |
| C-5 | mmHg → kPa: exact factor (1 mmHg = 133.322387415 Pa), unrounded storage | PR #6 G7 | Examples reproduced exactly (757.7 → 101.0183729443; 760 → 101.3250144354; 2319.7 → 309.2679420866 kPa). Storage and display rule open (Member 1, Member 2) |
| C-6 | `flow_configuration` (`quiescent` vs `null`), `diluent` naming, "heptane" vs "n-heptane" | PR #6 G7 | Open. Member 5 supports `null` for flow (a judgement, not printed). Captions say "heptane" and §6 says "n-heptane" |
| C-7 | FLEX quantities not in the vocabulary | C4 / D5 | Open. Blocks any FLEX `Finding` |
| C-8 | Rights: manifest `permitted_with_citation`; NTRS "Public Use Permitted"; PSI-69 dataset CC0 (DataCite) applies to the PSI dataset, not this report | PR #4 manifest | Consistent; Member 3's decision |

## D. Verification blockers

- **PSI electronic data (PSI-69)** was not accessed (client-rendered pages). S-1 and S-3 cannot be resolved against it.
- **Rows FLEX-011 and later** are outside PR #4 and were not checked.
- **This is an executor record.** Member 5's personal confirmation of these results, if wanted, is the account holder's act.

## E. Related: Member 3's audit of Member 5's citations (PR #6)

`docs/verification/m3_citation_audit_of_member5.md` at PR #6 `e4d3892` is a **machine check by Member 3's executor**, independent of Member 5's tool (PyMuPDF, fresh downloads): **43 of 43 quotes found, all 6 PDF hashes match.** It is explicitly **"NOT SIGNED OFF"**. The human checks (does the quote support the statement; is the source authoritative; are the rights appropriate) and the signature are Member 3's. Member 5's audit therefore stays **recorded, not independently authenticated**.

Member 3's findings and the related tag-mapping proposal (`docs/verification/environment_tag_mapping.md`) need **Member 5 decisions**. They are recorded in `COORDINATION.md`, not applied here.

## F. Member 3 disposition (2026-11-14, 21:20 UTC)

Findings sent on PR #4 ([comment 6884315288](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884315288)). Member 3's account replied ([comment 6884374215](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884374215)), labelled "Coordinator disposition … proposed fixes authorized, not scientific sign-off":

| Finding | Disposition (quoted) | Next step |
|---|---|---|
| S-2 | "ACCEPT: add a caution imaging flag for FLEX-010 initial_droplet_diameter_mm" | Member 3 proposes it on PR #4 |
| S-3 | "ACCEPT WITH QUALIFICATION … Do not call 13.6 s incorrect, guessed, or experimentally disproven." | Member 3 proposes a caution on PR #4 |
| S-5 | "ACCEPT WITH QUALIFICATION: include the report's mitigating phrase … as an attributed source assertion" | Member 3 proposes it on PR #4 |

Member 3 will then request **Member 5's renewed independent review of the changed flags**. "No merge or owner approval is implied."

## G. Renewed review of the revised flags (PR #4 `d117ba90afc78416c4769963f15adaa98a17ed39`, 2026-11-14)

Commit `d117ba9` ("data: add FLEX-010 cautions and contamination context from Member 5 Q3 (S-2, S-3, S-5)"). Checked read-only against the same PDF (SHA-256 `b4f6ca98…`).

| Check | Result | Status |
|---|---|---|
| Data CSV | unchanged | **Verified** |
| Flags manifest SHA-256 | `80e73f19…` matches the committed flags blob | **Verified** |
| Flag counts | 45 (1 `exclude`, 35 `caution`, 9 `not_available`) | **Verified** |
| All 45 `source_quote` values on their cited printed page | 45 of 45 verbatim | **Verified** |
| S-2 → F044: FLEX-010 `initial_droplet_diameter_mm`, `caution`, printed p. 38, "The HiBMs produced a saturated image that influenced the droplet size measurement." | Correct field, status and quote; value untouched | **Verified** |
| S-3 → F045: FLEX-010 `burn_time_s`, `caution`, printed p. 38; reason: "The printed value is kept as reported and is not judged incorrect." | Correct field and status; quote verbatim | **Verified**, with one wording note (below) |
| S-5 → F001, F007, F010, F013, F017, F020, F023, F028, F034, F041: reason now quotes printed p. 17 assertions (1) and (2), labelled "the authors' assessments, not independent measurements" | Both sentences are in the source (sentence (1) matches whitespace-insensitively, because of a pypdf word split, not an error) | **Verified** |
| F042 FLEX-010 burning rate | still `exclude` | **Verified** |
| CI on `d117ba9` | runs 43642566376 and 43642570754: backend 3.11, 3.12, secrets-and-raw-data all pass | **Verified** (observed) |

**Wording note (minor, Member 3's call):** F045's reason says the droplet left the fields of view "early in the test". The caption does not say "early"; it says the droplet "quickly moved west out of the fields of view" and was "in the HiBMs FOV for only a short time". Quoting those words would be exact. This is not a data error.

**Q3 status:** the PR #4 transcription and flags are verified at `d117ba9` by Member 5's executor. This is not an approval of PR #4, and it does not resolve S-1 or S-3 against PSI data (still blocked).

## H. Status: second verification completed (2026-11-14)

The second FLEX transcription and quality-flag verification (PR #4 `d117ba9`, §G) is **completed**. Member 3's follow-up items 4 and 5 were answered ([comment 6884483333](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884483333)): F001–F043 keep their meaning (only the 10 contamination reasons were extended; type, field, `ranking_use`, page and quote unchanged); `derivation_unverified` → `caution` is appropriate. **Open for Member 3:** F045's wording ("early in the test"). **Still blocked:** S-1 and S-3 against PSI data. Not an approval of PR #4.

## I. F045 final wording (PR #4 `2092cdd8c70616d6f51c72c767d28cf6c4eb23c2`)

Only F045 changed. Both quoted phrases are verbatim in the Figure 14 caption (printed p. 38), and "early in the test" is removed. It is still `derivation_unverified` → `caution`; 13.6 s is untouched. The flags SHA-256 `19e7f951…` matches the blob and the manifest; the CSV is unchanged; 45 of 45 quotes are on their cited pages. **Wording confirmed** ([comment 6884613550](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884613550)). Not an approval of PR #4. S-1 and S-3 remain blocked on PSI data.

## J. Member 5 formal scientific-review approval (account holder)

**"Member 5 — FLEX Scientific Review: APPROVED at `2092cdd8c70616d6f51c72c767d28cf6c4eb23c2`"** ([comment 6884636950](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/4#issuecomment-6884636950)), posted from the Member 5 account on the account holder's instruction. The account holder's text named `d117ba9`; on their choice it was updated to the current head `2092cdd`, with the F045 refinement recorded as done. **Scope:** NASA source transcription, scientific interpretation and quality-flag consistency only. **Not** an approval of shared contracts, integration readiness or merging PR #4.
