# Member 5: research interpretation, relevance ranking and Moon/Mars insights

**Status:** draft. Pending CP1 (contract v0.2.0) and scientific review by Member 1. Nothing here is wired into the API, and nothing here is curated data.

## What is in this folder

| File | What it is |
|---|---|
| `investigations.json` | Register of the 5 initial investigations, with verified NASA sources. `measured_records_imported` is 0 for each. |
| `evidence_reported.json` | 11 qualitative statements quoted exactly from NASA sources (`evidence_category: "reported"`). No numeric values. |
| `insight_cards.json` | 6 Moon/Mars insight cards: Finding → NASA source → Interpretation → Moon/Mars implication → Limitation. |
| `RANKING_METHODOLOGY.md` | How the research-relevance score works, and what it is not. |
| `COORDINATION.md` | Open decisions for Members 1–4. |

Code lives in `backend/flameguard/research/`. The proposed criteria are in `config/research_relevance_criteria_v1.proposed.json`. Tests are in `tests/research/`, and their fixtures are in `tests/fixtures/research/` (marked `fixture: true`; not NASA data).

## Research subjects and verification

All sources were retrieved on 2026-11-14. Every quote in `investigations.json` and `evidence_reported.json` (17 quotes) was checked word-for-word against the live source text with:

```bash
python -m flameguard.research.verify_sources docs/research/member5/evidence_reported.json docs/research/member5/investigations.json
```

Result on 2026-11-14: 17/17 quotes found. For NTRS records the check uses the public NTRS API record (title and abstract), because the citation pages render with JavaScript.

| Investigation | Subject | Sources used | Verified | Test-level data imported |
|---|---|---|---|---|
| BASS-II | Solid-material burning and flame spread | NTRS 20160000593, NTRS 20210011385 | yes | no |
| FLEX | Liquid-droplet combustion and extinction | GRC Combustion Science page, NTRS 20150023456 | yes | no |
| SoFIE | Solid-fuel ignition and flammability | NTRS 20200000361, NASA SoFIE page | yes | no |
| Saffire | Larger-scale spacecraft fire behaviour | NTRS 20240002981, NTRS 20180005168 | yes | no |
| FM² | Lunar partial-gravity research objectives | NASA FM² page, NTRS 20210020516 | yes | no |

Not verified, and so not used as evidence:

- Whether FM² has flown or returned data.
- PSI dataset IDs found by web search (PSI-25, PSI-69, PSI-98). They are listed as candidate data locations only.
- `issresearchproject.grc.nasa.gov/Investigations/FLEX/`, which did not resolve from the verification machine.
- DOIs. None of the NTRS API records lists one, so `doi` is `null` everywhere.

## Missing input

The research kickoff file `FLAMEGUARD_MEMBER5_RESEARCH_KICKOFF_2026-11-14.md` and the folder `C:\Users\nhanb\FLAMEGUARD-MEMBER5-RESEARCH` were not available when this was built. The content above comes from the task brief's subject list and the NASA sources themselves. When the kickoff file is available, reconcile it with this folder and keep its original citations.

## Integrity rules applied

- No NASA measurement, test id, result or uncertainty is invented. Missing values are `null` and listed by `missing_fields()`.
- `reported` statements are never upgraded to `measured`. Hypotheses (FM²) are labelled `hypothesis_under_test`.
- Interpretations and implications are FlameGuard-SI text. Implications are labelled `engineering_hypothesis`. Every card says it is not a flight-qualified recommendation.
- Every lunar or Martian claim carries an `extrapolation_warning`.
- The ranking measures research relevance, not fire risk, and gives no probability.
