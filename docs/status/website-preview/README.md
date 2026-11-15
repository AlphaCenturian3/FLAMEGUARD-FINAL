# Website preview: integration evidence (2026-11-15)

Branch `integration/website-preview`. One process (`python -m flameguard serve --fixtures`)
serves the dashboard at `/` and the API at `/api/*`. Windows 11, Chrome, Python 3.12.

| Suite | Result |
|---|---|
| pytest (backend, contracts, B7 full-application browser tests, browser-runner unit tests) | 547 passed, 0 failed, 0 skipped |
| Frontend unit + accessibility harness (`frontend/tools/run-tests.ps1`) | 104 passed, 0 failed |
| Browser QA, 47 checks (`frontend/tools/browser_check.py`) | 47 passed, 0 failed |
| Live-site check (`frontend/tools/site_check.py`), approved evidence (empty) | 92 passed, 0 failed, 1 skipped |
| Same check on the container's exact start command and file set | 92 passed, 0 failed, 1 skipped |
| Same check on a throwaway, uncommitted tree with the 40 candidate FLEX Findings (PR #31) | 84 passed, 0 failed, 0 skipped (an earlier checker revision, without the preview-notice checks) |
| ruff check / ruff format --check | clean |

The skipped check needs an excluded value in registered evidence; none is registered. It passed
on the candidate tree, where the FLEX-010 burning rate printed as `.37` appears on no page.

Screenshots (approved state, no NASA evidence registered): `live-overview.png`,
`live-explorer.png` (honest empty state), `live-rank.png` (truthful 501),
`fixture-overview.png` and `fixture-explorer.png` (banner `FIXTURE DATA. NOT NASA DATA.`),
`mobile-menu-open.png` (360 px).
