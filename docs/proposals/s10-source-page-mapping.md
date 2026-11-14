# Proposal: S10 source-page coverage for 15 FLEX quality flags

**Status:** read-only proposal from Member 3 (`feat/nasa-data-tars` workstream), 2026-11-14. **Nothing is changed:** no data file, flag, manifest entry or NASA value. Separate from PR #4 (merged into `main` as `ef71422`) and from the D5 vocabulary draft (PR #12). Implementation waits for owner review.

## The gap (Member 1's PR #4 integration review)

In `data/manifest.json` on `main`, the measured FLEX entry `nasa-tp-2015-216046.table-ix.flex-001-010` registers sources for printed pages **16, 17, 19, 20, 32 and 38** only. Fifteen of the 45 quality flags in `data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv` cite **other** printed pages: Appendix B figure captions on pp. 29–31 and 33–37. Their quotes are verified verbatim against the PDF by `tools/verify_flex_table_ix.py`, but those pages have **no registered `Source` entry**. S10 needs each note's `source` to rest on a registered source passage, so the derivation of `curation_notes` would have nothing registered to point to for these flags.

This is about **coverage** (which pages are registered), not page numbering.

## The 15 flags

Checked read-only on 2026-11-14 against the FLEX PDF (SHA-256 `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d`, local `data/raw/`, not committed):
- every quote is verbatim on the cited printed page (PDF page = printed + 6);
- each page's figure caption names the same test as the flag.

| Flag | Test | Field | `ranking_use` | Printed p. | PDF p. | Caption | Quote (as in the flags file) |
|---|---|---|---|---|---|---|---|
| F002 | FLEX-001 | `initial_droplet_diameter_mm` | `caution` | 29 | 35 | Fig. 5 | "so the droplet diameter could not be measured accurately." |
| F005 | FLEX-001 | `test_end` | `caution` | 29 | 35 | Fig. 5 | "The droplet probably disrupted at the end of the test coincident with flame extinction." |
| F006 | FLEX-002 | `*` | `caution` | 30 | 36 | Fig. 6 | "Because this was a calibration run" |
| F009 | FLEX-003 | `*` | `caution` | 31 | 37 | Fig. 7 | "Because this was a calibration run" |
| F016 | FLEX-005 | `*` | `caution` | 33 | 39 | Fig. 9 | "Because this was a calibration run" |
| F019 | FLEX-006 | `*` | `caution` | 34 | 40 | Fig. 10 | "This was a calibration test." |
| F022 | FLEX-006 | `visible_flame_extinction_diameter_mm` | `caution` | 34 | 40 | Fig. 10 | "The droplet drifted out of the High-Bit-Depth Multispectral (HiBMs) field of view (FOV) and then drifted back in the FOV." |
| F024 | FLEX-007 | `burning_rate_constant_mm2_per_s` | `caution` | 35 | 41 | Fig. 11 | "The last part of the droplet history was obscured by the luminous flame." |
| F029 | FLEX-008 | `burning_rate_constant_mm2_per_s` | `caution` | 36 | 42 | Fig. 12 | "There is a lot of noise in the droplet diameter data because of the soot" |
| F031 | FLEX-008 | `initial_droplet_diameter_mm` | `caution` | 36 | 42 | Fig. 12 | "There is a lot of noise in the droplet diameter data because of the soot" |
| F035 | FLEX-009 | `burn_time_s` | `not_available` | 37 | 43 | Fig. 13 | "No Image Processing and Storage Unit (IPSU) data were downlinked for this test." |
| F036 | FLEX-009 | `burning_rate_constant_mm2_per_s` | `not_available` | 37 | 43 | Fig. 13 | "No Image Processing and Storage Unit (IPSU) data were downlinked for this test." |
| F037 | FLEX-009 | `initial_droplet_diameter_mm` | `not_available` | 37 | 43 | Fig. 13 | "No Image Processing and Storage Unit (IPSU) data were downlinked for this test." |
| F039 | FLEX-009 | `test_time_gmt` | `not_available` | 37 | 43 | Fig. 13 | "No Image Processing and Storage Unit (IPSU) data were downlinked for this test." |
| F040 | FLEX-009 | `visible_flame_extinction_diameter_mm` | `not_available` | 37 | 43 | Fig. 13 | "No Image Processing and Storage Unit (IPSU) data were downlinked for this test." |

**Two groups:**
- **10 cautions** (F002, F005, F006, F009, F016, F019, F022, F024, F029, F031). Under S10(b) each becomes a caution note in `curation_notes`, so each note needs a registered `source`. **This is the real gap.**
- **5 `not_available`** (F035, F036, F037, F039, F040, all FLEX-009, Figure 13). Under S10(c) they produce **no note**: the finding is `not_reported`. S10(d) only verifies quotes of *referenced* flag rows, so these don't strictly need a registered source. Registering them anyway keeps the provenance complete.

## Options (owner decision)

| | What | Effect | Notes |
|---|---|---|---|
| **A** | Append **one `Source` per flag** (15 entries) to the measured entry's `sources`: title "NASA/TP-2015-216046, Appendix B, Figure N caption (Test FLEX-00X)", the report PDF URL, the page, the flag's exact quote, retrieved 2026-11-14, `archive_id` "NTRS 20150023456" | The derivation tool copies the registered `Source` into each note's `source` verbatim; S10(d) checks the same text | Manifest change only (no data bytes). Same pattern as the existing 7 sources |
| **B** | Append **one `Source` per caption page** (8 entries: pp. 29, 30, 31, 33, 34, 35, 36, 37) with `quote: null`; the note's quote comes from the flag row | Page coverage complete with fewer entries | The registered entry then doesn't carry the quote; S10(d) checks the flag quote against the page text |
| **C** | Register the sources on the **flags** (interpretation) entry instead of the measured entry | Keeps the measured entry's citations about the table itself | The schema allows `sources` on any entry, but the checker validates source fields only for `measured` entries, so this needs a check added |
| **D** | No manifest change; a documented mapping file | Smallest change | It would itself need registering (every curated file needs a manifest entry), and it is not a `Source` the contract can point to |

**Recommendation: A, on the measured entry**, covering the 10 cautions now and the 5 `not_available` rows for completeness:
- It gives S10 a registered, quoted `Source` for every flag that becomes a note.
- It uses the existing `Source` shape and the existing checker rules.
- It touches no data bytes.

The same pattern could later cover the 30 flags on already-registered pages, whose quotes differ from those pages' registered quotes. That's a separate decision.

## Questions for owners

1. **Option A, B, C or D?** Members 1 and 3 (Member 1 raised the gap; Member 3 owns the manifest).
2. **`page` value format** for new entries. Member 5 adopted "printed p. X (PDF p. Y)" for their citations. The existing FLEX entries use the printed page as a plain number ("20"). Choose one format for this manifest. If it's the combined string, `tools/verify_flex_table_ix.py` must parse it, because it currently reads `int(page)`.
3. **Register the 5 `not_available` rows too?** The recommendation is yes, for completeness.
4. **Review:** Member 5 independently re-checks the 15 quotes against the PDF after implementation (Q3).

## Implementation sketch (after approval only)

- Edit `data/manifest.json` only: append the agreed `Source` entries.
- The data CSV, flags CSV and their SHA-256 stay unchanged.
- Extend `tools/verify_flex_table_ix.py` to verify the new manifest quotes (it already checks every manifest quote on its page), and add a test that every `caution` and `exclude` flag's page has a registered `Source`.
- Run ruff, pytest, the provenance checker and the local PDF verifier, and paste the output in the PR.
