# Proposal: selecting individual tests in `/api/compare` (contract v0.3 candidate)

Status: **DRAFT PROPOSAL. Not approved, not implemented, not part of any contract version.**
Contract v0.2.2 (PR #17) and the B3 engine (PR #37) are unchanged by this document. Nothing
here may be built before the contract change is approved under the contract rule (Members 1 and
2, plus 3 and 5).

Author: Member 1. Reviewers needed: Member 5 (scientific), Member 2 (frontend), Member 3 (data).

## 1. The limitation

`GET /api/compare?quantity=<key>&investigation_ids=a,b` selects by quantity and investigation.
Every measured finding of the quantity in those investigations becomes a row, and S5 judges the
rows together.

An investigation that holds many different tests can therefore never be compared, as a whole
or in part. A dry run of the B3 engine on the local, unregistered FLEX candidate (one
investigation, ten tests, four quantities) returns `comparable: false` for all four quantities,
because fuel, diluent, pressure and outcome differ somewhere among the ten tests. Two tests run
under the same reported conditions cannot be put side by side, because there is no way to ask
for just those two.

## 2. Proposed change in one paragraph

Add one optional parameter, `finding_ids`, that names the exact measured findings to compare,
and one optional convenience parameter, `tests`, that names tests by investigation and test
identifier. With neither parameter the endpoint behaves exactly as in v0.2.2. The comparability
rules (S5, S9, S11) do not change: they are applied to the selected rows instead of to every
row. The response gains an optional `selection` object so a reader can see that the rows were
chosen and how many were left out.

## 3. Request

| Parameter | Form | Meaning |
| --- | --- | --- |
| `quantity` | vocabulary key | Required, as today |
| `investigation_ids` | `a,b` | As today |
| `finding_ids` (new) | `f1,f2,...` | Exactly these findings, in this order |
| `tests` (new) | `inv:TEST-1,inv:TEST-2,...` | For each pair, the measured finding of `quantity` whose `investigation_id` and `test_id` match exactly |

Rules:

1. `investigation_ids`, `finding_ids` and `tests` are mutually exclusive. Giving two of them is
   400 `invalid_request`. This keeps one unambiguous meaning per request.
2. A test identifier is the source's own label and is unique only inside its investigation, so
   `tests` always qualifies it with the investigation id. The separator is the first `:`; ids
   cannot contain `:` or `,` (the `id` and `test_id` patterns already forbid both).
3. Matching is exact and case-sensitive. No trimming, no normalization, no prefix match.
4. At most 50 selections per request (to be confirmed), 400 beyond that.

## 4. Backward compatibility

- A request without `finding_ids` and `tests` returns a response identical to v0.2.2, byte for
  byte apart from `contract_version`. An oracle test pins this (section 9, P1).
- `selection` is optional in the schema and absent for such requests, so a v0.2.2 client that
  validates responses keeps working for the requests it can make.
- A v0.2.2 server answers a request carrying the new parameters with 400 (unknown parameter).
  The frontend must read `contract_version` before offering test selection.
- The change adds parameters and an optional response property, so it is a minor version
  (0.3.0), not a patch.

## 5. Selecting tests from the same investigation

Allowed. Rows may all come from one investigation. S11 already guarantees that inside an
investigation either every measured finding has a `test_id` or none has, so a `tests` selection
inside an investigation is well defined whenever that investigation identifies its tests.

Selecting the same finding twice is 400. Selecting one finding is accepted and answered
`comparable: false` with the existing "fewer than two" reason, as today.

## 6. Missing, conflicting or ambiguous identities

The endpoint never guesses and never silently drops a selection. Every case below is 400
`invalid_request` with a message naming the offending item, unless stated otherwise.

| Case | Answer |
| --- | --- |
| `finding_ids` names an id that is not a loaded finding (unknown, or rejected by the loader) | 400. If files were rejected, the response carries the existing rejected-entries header |
| The finding is an interpretation, not `measured` | 400 |
| The finding's `quantity` is not the requested one | 400 |
| `tests` names an unknown investigation | 400 |
| `tests` names an investigation whose findings carry no `test_id` (legacy rows) | 400, message says to use `finding_ids` |
| `tests` names a `test_id` that no measured finding of that investigation carries | 400 |
| The test exists but has no measured finding of the requested quantity | 400 (the test cannot be a row; it is not a "not reported" row unless such a finding exists) |
| **Ambiguous:** the test has more than one measured finding of the quantity | 400 naming the candidate finding ids; the caller must use `finding_ids`. The server never picks one |
| The same `test_id` exists in two investigations | Not a conflict: the pair `investigation:test` is the identity |
| Two selections resolve to the same finding | 400 |
| A selected finding has a `test_id` but no `test_outcome` | Accepted as a row; S5 makes the rows not comparable, with the existing reason |
| A selected finding is `excluded`, `not_reported` or `not_applicable` | Accepted as a row with a null value; S5/S9 make the rows not comparable. Its value never appears |

## 7. Outcome compatibility and condition matching

No rule changes. For the selected rows:

- Outcomes: different outcomes, outcomes on some rows only, or a `test_id` without an outcome
  each make the rows not comparable (S5, v0.2.2). Outcomes are copied from `test_outcome` and
  never inferred from prose or values.
- Conditions: a condition reported with different values, or reported for some rows and null
  for others, makes the rows not comparable. Equality is exact, with no tolerance. A condition
  that is null on every row gives no reason in v0.2.2; whether v0.3 should adopt the stricter
  mode is a separate open decision and is not settled here.
- Values: only `reported` rows can be comparable. The server never converts, interpolates,
  averages, ranks or subtracts.

The server does **not** search for comparable subsets. Selection is always the caller's.

## 8. Scientific limitations this change introduces or exposes

1. **Selection bias.** Letting a user pick tests makes it possible to pick only the tests that
   agree. The response therefore reports how many measured findings of the quantity exist in
   the same investigations and were not selected (`selection.not_selected`), and the page must
   show it ("2 of 10 tests selected").
2. **`comparable` is a screen, not a verdict.** It means the eight contract conditions and the
   outcome do not contradict each other. It does not mean the experiments are equivalent.
   Differences the contract does not model (for example initial droplet diameter, which is a
   quantity and not a condition, or apparatus and ignition details) are invisible to S5. The
   page must say so next to every comparable result.
3. **Exact matching** treats 0.21 and 0.2101 as different, and treats values the source rounded
   differently as different. That is deliberate: no tolerance is proposed, because a tolerance
   is a scientific criterion that only Member 5 can set.
4. **No statistics.** Two rows side by side are two numbers. No difference, trend or
   significance is stated.
5. **Excluded values** stay withheld under any selection, including a selection of one
   excluded finding.

## 9. Required changes

Contract (one contract PR, version 0.3.0):

- `contracts/README.md`: extend the S5 row ("applied to the selected rows"); add a rule for
  selection (resolution, exclusivity, ambiguity is an error, never a guess); endpoint table.
- `contracts/schemas/comparison.schema.json`: optional `selection` object:
  `{"mode": "findings" | "tests", "requested": [string, ...], "not_selected": integer >= 0}`.
  Present exactly when the request used `finding_ids` or `tests`.
- Examples: one comparable selection, one non-comparable selection.
- Master spec 5.1: the endpoint line and the parameter rule.

Backend (after approval only; not started):

- The B3 engine accepts an explicit list of findings in place of the investigation filter. The
  decision functions are untouched.
- The handler resolves and validates the selection as in section 6.
- The served endpoint stays at 501 until B3 itself is validated and approved.

Frontend (Member 2, after approval only):

- In Compare, let the user tick tests (the dashboard already groups findings by `test_id`).
- Send `finding_ids`; show the backend's decision and every reason; show "n of m selected" and
  the limitation text of section 8, item 2. Never compute comparability in the browser.
- Offer selection only when the API's `contract_version` supports it.

## 10. Test oracles

All data synthetic. `C` is the response, `S5` the existing rules.

Positive:

| Id | Given | Expect |
| --- | --- | --- |
| P1 | Any request without the new parameters | Response equals the v0.2.2 response for the same data; no `selection` |
| P2 | Two findings of one investigation, same conditions, same outcome, selected by `finding_ids` | 200, exactly those rows in request order, `comparable: true`, `selection.mode = "findings"` |
| P3 | The same two selected by `tests=inv:T-1,inv:T-2` | Same rows and decision as P2, `selection.mode = "tests"` |
| P4 | Ten tests with differing conditions; two like-for-like ones selected | `comparable: true`, `not_selected = 8`; the unselected request (P1 form) stays `comparable: false` |
| P5 | Selections from two investigations that reuse the same `test_id` | Each resolves to its own investigation's finding |
| P6 | Legacy findings without test identity selected by `finding_ids` | Rows without `test_id`/`test_outcome`; S5 as today |

Negative:

| Id | Given | Expect |
| --- | --- | --- |
| N1 | Two of `investigation_ids`, `finding_ids`, `tests` together | 400 |
| N2 | Unknown finding id; interpretation id; finding of another quantity | 400 each, item named |
| N3 | `tests` on an investigation without test ids | 400 |
| N4 | Unknown `test_id`; wrong case (`t-1` for `T-1`); trailing space | 400 each |
| N5 | A test with two measured findings of the quantity | 400 listing both finding ids; never a row |
| N6 | The same finding twice, directly or through `tests` | 400 |
| N7 | Selected rows with different outcomes | 200, `comparable: false`, outcome reason |
| N8 | Selected rows where one has a `test_id` and no outcome | 200, `comparable: false` |
| N9 | Selected rows with a differing or partly null condition | 200, `comparable: false`, condition reason |
| N10 | A selected `excluded` or `not_reported` finding | 200, row value null, `comparable: false`; the printed number appears nowhere in the response |
| N11 | A selected finding whose file the loader rejected | 400, rejected-entries header present |
| N12 | For every response with `selection`: rows equal the resolved selection, in order, nothing added or dropped; `not_selected` equals the count of other measured findings of the quantity in the rows' investigations | holds |
| N13 | For every response: the existing `outcome_violations` oracle and `comparison.schema.json` | no violations |

Member 5's independent tests should include an oracle that resolves a selection from the
loaded findings without using the backend's code, and compares.

## 11. Decisions requested

1. Adopt `finding_ids` (normative) and `tests` (convenience)? Or `finding_ids` only?
2. Is `selection.not_selected` an adequate guard against cherry-picking, or should the response
   also list the unselected finding ids?
3. Should a test with no finding of the quantity be an error (proposed) or a reason?
4. Confirm exact condition equality for v0.3, or have Member 5 define a tolerance with a
   citation.
5. Decide the "null on every row" stricter mode together with this change, or separately.
6. The selection limit (50 proposed).
