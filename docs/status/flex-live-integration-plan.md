# Plan: getting the 40 audited FLEX Findings into the live application

Written by Member 1 for Command Center, 2026-11-15. A plan, not an authorization. Nothing below registers, merges or approves anything.

## 1. What a local dress rehearsal proved (nothing pushed)
In a throwaway worktree I merged the whole prerequisite stack (B1 + B2 + S11 + contract v0.2.2 + S10 registration + derivation), staged the 40 Findings, **locally** registered the two staged files in the manifest (SHA-256 computed), and ran the real software on it:

| Check | Result |
|---|---|
| B1 loader (`load_evidence`) | manifest ok; investigation accepted (1), Findings file accepted (**40**); both source CSVs skipped as sources; 0 rejected. Schema, provenance, S1-S4, S9, S11 all passed |
| `tools/check_data_provenance.py` | passes with 4 registered datasets |
| Live API | `/api/investigations` total 1; `/api/findings` total **40** (31 reported, 8 not_reported, 1 excluded); no rejected-files header; quantity filter `burning_rate_constant` returns 10 |
| Excluded measurement | FLEX-010 burning rate: value `null`, status `excluded`, notes caution + exclusion; **the printed number appears nowhere in any API response** |
| `compare` and `rankings` | still HTTP 501 (nothing enabled) |
| Dashboard (pinned frontend `3c9ce44`) | Explorer lists the FLEX investigation and findings; the excluded finding is labelled "Excluded by FlameGuard-SI"; no number shown |

It also found **real gaps**, each with an owner below:
1. **Version warning (misleading):** the dashboard (implements 0.2.0) shows three banners "The API reports contract 0.2.2; this dashboard implements 0.2.0. Some fields may be missing or misread." Needs a frontend change (patch-tolerant version check). Member 2's follow-up, already anticipated in their #12 review.
2. **`test_id` and `test_outcome` are not displayed** by the dashboard (Member 2 asked for this in the #17 discussion). Without it, FLEX-001's printed Disruption is visible only inside a caution's text.
3. **Grouping:** the Explorer groups findings by exact `locator`; our locators name the field and CSV line, so there are **40 one-finding groups** instead of 10 test rows. Fix by grouping on the structured `test_id` (frontend) or by a row-level locator (derivation); Member 2 and Member 3 to choose. No data rule is violated either way.
4. **24 derivation tests and 1 isolation test fail once the files are registered**, because they assume only the two source CSV entries exist. Expected and fixable (listed in section 4); it is why registration must be its own PR with its own test updates.
5. **Production serving:** the frontend is not mounted by the production app (B7 is not built). The preview serves it. A "live dashboard" for the demo is the preview pinned to merged commits; a production deployment additionally needs B7.

## 2. Shortest safe path (every step needs its review and an explicit authorization to merge)

| # | Step | Needs | Notes |
|---|---|---|---|
| 1 | **Contract chain:** #12 with Member 5's two wording corrections (draft #28, commit 23cd7ad) then #17 | Member 3 adopts #28; Member 5 re-review; Members 1+2 re-approve on the new head; #17 needs 2, 3, 5 | Hard prerequisite: the Findings use `burning_rate_constant` and `test_id`/`test_outcome` |
| 2 | **Backend chain:** #9, #10, #11, then #18, then #26 | #10: Member 3; #11: Members 3+5; #18 and #26: independent reviewer | #26 enforces S11 and carries the isolation tests |
| 3 | **S10 chain:** #23 then #25 | #23: one independent approval (Member 3 preferred), squash; #25: Members 3 and 5 | 17 of 17 source passages registered |
| 4 | **Derivation tooling:** #24 (after rebase onto main; it duplicates #17/#25 history) | Member 3, Member 5 | Reproducible, byte-identical staging and audit |
| 5 | **Scientific acceptance** | Member 5: Q3 review of the 40 Findings using the audit report; **written F042-NOTE approval recording the exact note and reviewed SHA**; the three G7 condition decisions moved from `owner_provisional` to `approved` only by an independent scientist | The only steps no one but Member 5 can do |
| 6 | **Frontend compatibility** (gaps 1-3) as a small PR for Member 2's review | Member 2; frontend #2 and #21 merged first | Can be developed now on my own branch for Member 2 to adopt |
| 7 | **Registration PR** (separate, section 3) | Members 3, 5, plus 1; all of steps 1-5 merged; gates closed | The only PR that adds Findings to `data/` |
| 8 | **Verify and re-pin** the preview to the merged commits; update the demo contract and script | me | Live mode stops being empty, so the demo wording changes with it |

Everything in 1-4 can be reviewed in parallel; the merges are sequential in the order shown (each squash).

## 3. The registration PR (what it will and will not contain)
- **Adds only:** `data/curated/investigations.json`, `data/curated/findings/flex.json` (byte-identical to a fresh run of `tools/derive_flex_findings.py`), and two `measured` manifest entries (`...flex.investigations`, `...flex.findings`) with SHA-256, the Table IX numeric Source and `rights_status`.
- **Changes no** source CSV, flags CSV, schema, contract, vocabulary or other Source. No comparison, ranking or TARS change.
- **New tests:** registered files are byte-equal to a fresh derivation; the audit (with the PDF) still reports 0 failures; the loader accepts exactly 40 + 1; the API serves 40 and none states the F042 value; the S9/S11 oracles pass on the live store; ranking, compare and assistant remain 501.
- **Tests that must change in the same PR:** the 24 derivation fixtures (`make_root` should drop non-source manifest entries), `test_staging_changes_nothing...` (manifest ids), and `test_the_real_repository_serves_no_evidence_while_flex_is_only_staged` (now expects the 40; keep a guard that nothing else is served).
- **Gate:** `registrable` in the staging report must be true, which requires every gate in `tools/flex_derivation_gates.json` closed and every condition decision `approved`. Today six gates are open.

## 4. What the live dashboard will and will not show
- **Will:** one investigation, 40 measured Findings with values as printed, sources, cautions and the exclusion note; the excluded value withheld; contract-honest labels; the empty and error states unchanged.
- **Will not (still):** comparisons (O2 gate; B3 not built), rankings, TARS answers, simulations, any Moon or Mars conclusion.
- **Demo impact:** live mode would no longer say "0 Investigations loaded". The launch card, script and `demo_contract.json` change in the same step 8.

## 5. Authorizations requested (in order)
1. Authorize me to build the **frontend compatibility changes** (gaps 1-3) on my own branch, stacked on #21, for Member 2's review. No merge.
2. Authorize me to prepare the **registration PR as a draft** (tests updated, generated files) so it is ready the moment steps 1-5 are done. It stays draft and unmergeable until then.
3. Confirm who should be asked (when people are available) for: #23 approval (Member 3), the #28 adoption, and Member 5's Q3 and F042-NOTE reviews. I will not contact anyone without your say.
