# PDF source evidence for the FLEX vocabulary, S10 coverage and derivation design

**Member 5 record, 2026-11-14.** This is an executor check run with the account holder's authorization. It is evidence for owner decisions on PRs #12, #13 and #15. It approves nothing, and it changes no data, flag, manifest entry or contract.

## Source authentication

| Item | Result |
|---|---|
| Document | NASA/TP-2015-216046, *Detailed Results from the Flame Extinguishment Experiment (FLEX)* |
| Retrieved | 2026-11-14 from `https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf` |
| Local path | `data/raw/NASA-TP-2015-216046_FLEX.pdf` (ignored by `.gitignore` rule `*.pdf`; **not committed**) |
| Size, pages | 42,900,650 bytes; 314 pages |
| SHA-256 | `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d`, **matches** the value registered in `data/manifest.json` |
| `tools/verify_flex_table_ix.py` (PyMuPDF, local venv) | "FLEX Table IX verification passed: 10 rows, 150 cells match the PDF; PDF sha256 matches; manifest quotes found verbatim; 45 flags valid with verbatim quotes; 22 quotes inside flag reasons verbatim." |
| Page offset | PDF page = printed page + 6 for every cited page checked |

## 1. Column definitions (Appendix A.1, printed p. 19, PDF p. 25), quoted verbatim

- **Actual D0:** "initial droplet diameter or droplet diameter at time zero where time zero is the time when the igniters are turned ON"
- **Burning rate:** "average burning rate constant from a linear fit of the droplet diameter squared versus time from shortly after ignition to extinction"
- **Visible flame extinction diameter:** "droplet diameter at the time the visible flame extinguished, where "-" indicates flame extinction did not occur either because the droplet burned to completion or because a droplet disruption ended the test. For cases where the droplet left the HiBMs field of view (FOV) before extinction, we did estimate (extrapolate the burning history) to determine the extinction droplet diameter if there was sufficient burning history and the length of time to extrapolate was not that long. If the droplet was not in the HiBMS FOV for enough time, the extinction droplet diameter is not listed."
- **Burn time** and **Test end:** **not defined** in A.1. They are column headings of Table IX (printed p. 20) only.

Consequences for PR #12, posted as Member 5's change request ([review 5907983490](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/12#pullrequestreview-5907983490)):
- K is the positive **magnitude** of the decrease of D², averaged by a linear fit. It is not the signed slope, which is negative.
- An extinction diameter can be a source **estimate** by extrapolation, and Table IX does not mark which ones are.
- `burn_time` has no source definition, consistent with flag F045.

## 2. Outcome versus reported value (F1, O2)

The source's own "-" rule does not hold row by row, so no outcome may be inferred from whether a value is present or absent:

| Test | Printed outcome | Extinction diameter | Source context |
|---|---|---|---|
| FLEX-001 | Disruption | 0.89 | Fig. 5 (printed p. 29): "The droplet probably disrupted at the end of the test coincident with flame extinction." |
| FLEX-010 | Extinction | – | Fig. 14 (printed p. 38): "Because the droplet was in the HiBMs FOV for only a short time, no burning rate constant or extinction droplet diameter is reported." |
| FLEX-020 | Completion | 1.56 | Table IX, printed p. 20 (outside the registered 001–010 range; cited only as a counterexample) |
| FLEX-021 | Disruption | .95 | as above |

## 3. Extrapolation exposure in FLEX-001 to FLEX-010

Field-of-view statements from the Appendix B captions (printed pp. 29–38):

| Test | Ext. diameter | Caption statement on the field of view | Extrapolation possible? |
|---|---|---|---|
| FLEX-001 | 0.89 | "remained in the fields of view (FOVs) of all the cameras for the entire test" | No |
| FLEX-002 | .94 | same, "and extinguished diffusively" | No |
| FLEX-003 | .92 | "remained in the fields of view (FOVs) of all the cameras for the entire test" | No |
| FLEX-004 | – | "leaving the HiBMs FOV one-third of the way through the burn" | n/a (not listed) |
| FLEX-005 | .81 | "remained in the fields of view (FOVs) of all the cameras" | No |
| FLEX-006 | 1.53 | "drifted out of the … (HiBMs) field of view (FOV) and then drifted back in the FOV" | **Cannot be excluded**; already covered by caution **F022** |
| FLEX-007 | – | "remained within the … (HiBMs) field of view (FOV) for the entire test" | n/a |
| FLEX-008 | – | "drifted southeast out of the … (HiBMs) field of view (FOV) a few seconds after the igniter was withdrawn" | n/a; K covered by caution F029 |
| FLEX-009 | – | "drifted out of the fields of view (FOVs) of all the cameras very shortly after deployment and ignition" | n/a |
| FLEX-010 | – | "quickly moved west out of the fields of view (FOVs)" | n/a; K excluded by F042 |

Within the registered rows, the only extinction diameter that may be extrapolated is FLEX-006's, and it already carries a caution. The PR #12 wording correction is still needed, because the vocabulary applies to every later FLEX row and every other source.

## 4. S10 coverage: flags that need a registered, quoted passage (PR #13)

All 45 flag quotes are verbatim on their cited PDF page, and every Appendix B caption names the same test as its flag. **24** `caution` or `exclude` flags have a quote that is not contained in any registered `Source.quote` on that page. That is 10 on unregistered pages and 14 on registered pages. The only `exclude` flag, F042, is already covered.

| Flag | Test | Field | Printed p. | PDF p. | Page registered | Caption |
|---|---|---|---|---|---|---|
| F002 | FLEX-001 | `initial_droplet_diameter_mm` | 29 | 35 | no | Fig. 5 |
| F003 | FLEX-001 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F005 | FLEX-001 | `test_end` | 29 | 35 | no | Fig. 5 |
| F006 | FLEX-002 | `*` | 30 | 36 | no | Fig. 6 |
| F008 | FLEX-002 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F009 | FLEX-003 | `*` | 31 | 37 | no | Fig. 7 |
| F011 | FLEX-003 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F012 | FLEX-004 | `*` | 32 | 38 | yes | Fig. 8 |
| F014 | FLEX-004 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F016 | FLEX-005 | `*` | 33 | 39 | no | Fig. 9 |
| F018 | FLEX-005 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F019 | FLEX-006 | `*` | 34 | 40 | no | Fig. 10 |
| F021 | FLEX-006 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F022 | FLEX-006 | `visible_flame_extinction_diameter_mm` | 34 | 40 | no | Fig. 10 |
| F024 | FLEX-007 | `burning_rate_constant_mm2_per_s` | 35 | 41 | no | Fig. 11 |
| F025 | FLEX-007 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F026 | FLEX-007 | `test_end` | 17 | 23 | yes | – |
| F029 | FLEX-008 | `burning_rate_constant_mm2_per_s` | 36 | 42 | no | Fig. 12 |
| F030 | FLEX-008 | `initial_droplet_diameter_mm` | 16 | 22 | yes | – |
| F031 | FLEX-008 | `initial_droplet_diameter_mm` | 36 | 42 | no | Fig. 12 |
| F032 | FLEX-008 | `test_end` | 17 | 23 | yes | – |
| F038 | FLEX-009 | `test_end` | 17 | 23 | yes | – |
| F044 | FLEX-010 | `initial_droplet_diameter_mm` | 38 | 44 | yes | Fig. 14 |
| F045 | FLEX-010 | `burn_time_s` | 38 | 44 | yes | Fig. 14 |

**The same quote appears on more than one page.** "Because this was a calibration run" (F006, F009, F016) occurs on PDF pp. 36, 37 and 39. A quote-only check would pass on the wrong caption page, so any registered source and the S10 test must pin **page and caption test id** together, not the quote alone.

Not in the table: the 5 `not_available` flags on unregistered pages (F035–F037, F039, F040). Under S10(c) they produce no note.

## 5. Inputs for the derivation design (PR #15)

- R-2 (row-wide cautions on non-reported findings) and R-3 (no excluded value in text) stand as requested on PR #15.
- From §3: a derived FLEX-006 `visible_flame_extinction_diameter` Finding must carry F022. Any later FLEX row whose caption reports leaving the HiBMs FOV needs a limitation stating that the source may have extrapolated the value.
- From §1: a derived `burn_time` Finding should state that the source does not define its start and end points.

## 6. Table IX outcome vocabulary (P1 for PR #17, contract v0.2.2)

Decision posted on PR #17 at `9c3d698` ([comment 6886309607](https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL/pull/17#issuecomment-6886309607)). That comment is not an approval of PR #17.

| Item | Verified result |
|---|---|
| Extent | Table IX covers printed pp. 20–28 (PDF pp. 26–34): 276 rows, FLEX-001 to FLEX-280. FLEX-156, 205, 213 and 228 are not printed anywhere in the report |
| "Test end" values | Exactly three, as printed: `Extinction` 186, `Disruption` 62, `Completion` 28. No other value, blank, dash or footnote marker |
| Definition | None: A.1 (printed p. 19) does not define "Test end" or "Burn time" |
| Prose-only terms | "radiative extinction" and "diffusive extinction" (printed p. 2), "disruptive extinction" (printed p. 17). None of these is a table value |
| Label versus value | The A.1 dash rule disagrees with the label in 66 of 276 rows: 24 Disruption and 15 Completion rows print an extinction diameter; 27 Extinction rows print a dash |
| Other cells | Burn time printed as `~6` (FLEX-227) and `~9` (FLEX-229): approximate, not exact numbers |
| Printed test id | `FLEX–001` with an en dash (U+2013). The registered CSV uses ASCII `FLEX-001` |

P1 decision: `["Extinction", "Disruption", "Completion"]`, each meaning only "the label printed in Table IX". The decision has seven conditions; the comment gives them in full. The two that affect implementation:
- The `test_end` cautions (F004, F005, F026, F032, F038) must attach to every Finding that carries that test's outcome.
- Every derived FLEX measured Finding must carry a non-null `test_id` and `test_outcome`. A comparison row with neither field still validates as `comparable: true`.

S5 probes against PR #17's schemas, using its real generator in a temporary copy: differing, partial, null, absent, mis-cased, padded, empty and combined outcomes are all rejected for `comparable: true`. With the shipped empty list, no row that carries a `test_id` can be comparable. PR #17's suite: 333 passed at `9c3d698`.

## Reproduce

```
python -m pip install pymupdf          # local venv only; not a project dependency
python tools/verify_flex_table_ix.py   # needs the PDF at data/raw/NASA-TP-2015-216046_FLEX.pdf
```

The coverage table in §4 compares `data/manifest.json` source quotes on `main` (`ef71422`) with the flags file (SHA-256 `19e7f951…f8999d`), and then searches each quote in the PDF text extracted with PyMuPDF (whitespace and dash characters normalized).
