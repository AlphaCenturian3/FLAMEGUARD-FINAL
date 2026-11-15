# Member 5: research interpretation, relevance ranking and Moon/Mars insights

**Status:** draft. Pending CP1 (contract v0.2.0) and scientific review. Nothing here is wired into the API, and nothing here is curated data. Ranking output is disabled until the criteria are approved and verified NASA measurements are imported.

## What is in this folder

| File | What it is |
|---|---|
| `investigations.json` | Register of the 5 initial investigations and 1 research synthesis, with verified NASA sources and dataset DOIs. `measured_records_imported` is 0 for each. |
| `evidence_reported.json` | 15 qualitative statements quoted exactly from their sources (`evidence_category: "reported"`). No numeric values. |
| `insight_cards.json` | 6 Moon/Mars insight cards (Finding → source → Interpretation → Moon/Mars implication → Limitation), each mapped to the kickoff with `kickoff_ref`. |
| `GAP_REPORT.md` | Requirements against implementation, including what is blocked. |
| `SOURCE_AUDIT.md` | Per-citation verification audit: 43 quote citations across three files, automated vs manual method, PDF hashes and pages. |
| `CRITERIA_ENVIRONMENT_CONTEXT.md` | The four criteria defined for the environment-only interface (D-01 condition 1). Proposal. |
| `ENVIRONMENT_REFERENCE.md`, `environment_reference.json` | Cited gravity, oxygen and pressure reference per environment; physical conditions separate from design assumptions; unknowns marked (D-01 condition 2). |
| `WEIGHT_SENSITIVITY.md` | ±0.05 weight-sensitivity method with synthetic worked examples (D-01 condition 3). No NASA data. |
| `RANKING_METHODOLOGY.md` | How the research-relevance score works, its gates, and what it is not. |
| `B3_COMPARE_REVIEW.md` | Scientific QA of B3 (PR #37) and the test-selection proposal (PR #38): confirmed defects, limitations, reference correction (D11), differential results, open evidence gates. Not an approval. |
| `COORDINATION.md` | Roster conflict, GitHub identities and approvals, ownership boundary, decision log D-01 to D-12 (provisional vs approved), CP1 rebase readiness. |

Code: `research/` (non-runtime reference implementation only; production ranking and comparison belong to Member 1). Proposed criteria: `config/research_relevance_criteria_v1.proposed.json`. Tests: `tests/research/`, with fixtures in `tests/fixtures/research/` (`fixture: true`; not NASA data).

Run the reference source checker from the repository root with `python -m research.verify_sources <files>`. The package is not part of the backend runtime.

## Kickoff reconciliation

The kickoff file (`FLAMEGUARD_MEMBER5_RESEARCH_KICKOFF_2026-11-14.md`) was read on 2026-11-14 and reconciled:

| Kickoff item | Result |
|---|---|
| M5-01 BASS-II PSI-25, DOI `10.60555/4qc4-de67` | Confirmed in DataCite and added |
| M5-02 FLEX PSI-69, DOI `10.60555/mbq8-0451` | Confirmed in DataCite and added |
| M5-03 SoFIE / SoFIE-GEL | NASA Science page added; the claim that GEL observations agree with model trends was verified and added as evidence |
| M5-04 Saffire VI NTRS 20240002981 | Already present; verified |
| M5-05 FM² | Already present. No lunar measurement asserted. |
| Cards M5-I01 to I04, recommendations D1 to D5 | Mapped to the 6 cards (`kickoff_ref`). I01's NASA caution about ground extinguishing methods was verified and is cited in the I03 card. I04's white paper was verified and is cited in the lunar and Martian cards. |
| Ranking design C.1 to C.6 | See `GAP_REPORT.md`. Open: the 0–3 rubric (D-02), the missing-value policy (D-03), and cohort fields not in the contract (D-07). |

The kickoff's wording was kept where a source supports it. Where the kickoff paraphrased a source, the cards quote the source directly.

## Verification

All sources were retrieved on 2026-11-14.

- **Quotes:** 43 quote citations in `evidence_reported.json` (17), `investigations.json` (7) and `environment_reference.json` (19). The current automated run of `python -m research.verify_sources` reported **29 found, 14 classified for manual checking, 0 failed**. The PDF checks and hashes are documented in `SOURCE_AUDIT.md`; an automated match is not claimed for those PDFs. For NTRS records the checker uses the public NTRS API record, because the citation pages render with JavaScript.
- **DOIs:** checked against the DataCite registry (`api.datacite.org/dois/<doi>`): title, publisher (NASA PSI), type (Dataset), landing URL and rights.

| Investigation | Subject | PSI / dataset DOI | Test-level data imported |
|---|---|---|---|
| BASS-II | Solid-material burning and flame spread | PSI-25 / `10.60555/4qc4-de67` | no |
| FLEX | Liquid-droplet combustion and extinction | PSI-69 / `10.60555/mbq8-0451` | no |
| SoFIE | Solid-fuel ignition and flammability | none found | no |
| Saffire | Larger-scale spacecraft fire behaviour | none found for flights IV–VI (PSI-98/99/100 are flights I–III and are not cited) | no |
| FM² | Lunar partial-gravity research objectives | none found | no |

Not verified, and not used as evidence: FM² flight status, any SoFIE, Saffire IV–VI or FM² dataset DOI, and `issresearchproject.grc.nasa.gov` (did not resolve).

## Credits and licences

- NASA PSI datasets: BASS-II (PSI-25, DOI 10.60555/4qc4-de67) and FLEX (PSI-69, DOI 10.60555/mbq8-0451), both **CC0-1.0** per their DataCite records. Cite them by DOI, as the PSI repository requests. No dataset files are committed.
- NASA Technical Reports Server records 20150023456, 20160000593, 20180005168, 20200000361, 20210011385, 20210020516 and 20240002981: cited by title, URL and short quoted abstract text.
- NASA web pages (nasa.gov, www1.grc.nasa.gov, science.nasa.gov): cited by title, URL and short quotes. NASA media guidelines apply: generated text is attributed to FlameGuard-SI, never to NASA.
- Liao et al., "Topical: Challenges and Research Needs for Micro- and Partial-Gravity Fires" (decadal-survey white paper hosted at smd-cms.nasa.gov): cited for one short quote. The rights of the full text were not reviewed.

## Integrity rules applied

- No NASA measurement, test id, result or uncertainty is invented. Missing values are `null` and listed by `missing_fields()`.
- `reported` statements are never upgraded to `measured`. Hypotheses (FM²) are `hypothesis_under_test`. The white paper is a `source_statement`, not a NASA finding.
- Interpretations and implications are FlameGuard-SI text. Implications are `engineering_hypothesis`. Every card says it is not a flight-qualified recommendation.
- Every lunar or Martian claim carries an `extrapolation_warning`.
- The ranking measures research relevance, not fire risk. It is disabled until the criteria are frozen, and it uses only verified manifest entries.
