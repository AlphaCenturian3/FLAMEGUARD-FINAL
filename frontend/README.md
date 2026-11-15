# Frontend

Owner: Member 2 (`feat/frontend-dashboard`). Also owns `tests/frontend/`, `tests/e2e/` and `tests/fixtures/frontend/` (spec §4).

**Status:** implements **contract v0.2.2** and accepts exactly the explicitly tested versions 0.2.0, 0.2.1 and 0.2.2 (`SUPPORTED_CONTRACT_VERSIONS` in `static/js/config.js`; any other version shows a warning). Originally built against **contract v0.2.0** (CP1, merged at `f7cef55`). No curated NASA data or backend endpoint (other than `/api/health`) exists yet. The dashboard therefore shows either backend responses (HTTP 501 for planned endpoints) or, with `?fixtures=1`, the contract examples, labelled **FIXTURE DATA. NOT NASA DATA.** on every page.

Stack (spec §3): static HTML, CSS, and vanilla JavaScript ES modules. No build step, no dependencies.

## Run it

The page must be served over HTTP, because ES modules and `fetch` do not work from `file://`.

**With contract fixtures** (serve the repository root so `contracts/examples/` is reachable):

```bash
python3 -m http.server 8765                      # from the repository root
# Windows without Python:
powershell -ExecutionPolicy Bypass -File frontend/tools/serve.ps1
```

Open <http://localhost:8765/frontend/index.html?fixtures=1>.

**Against the backend** (once Member 1 serves `frontend/` at `/`, B7): open `/`. The default source is the API at the same origin. Fixture files are never requested in this mode (browser-checked).

| Query parameter | Meaning |
|---|---|
| `fixtures=1` | Read `contracts/examples/*.json`. A permanent banner and per-record badges mark everything as a fixture. |
| `api=URL` | API base URL (default: same origin; a different origin needs CORS on the backend). |
| `fixtures_base=URL` | Location of `contracts/examples/` (default `../contracts/examples/`). |

**Rejected evidence.** If the backend withheld evidence files that failed its checks, it sends `X-FlameGuard-Rejected-Entries: <n>` on the list responses. The dashboard then shows a warning that the lists are incomplete, and still shows what was served. No header, or `0`, shows nothing. An unreadable value is shown as "some files were rejected", never read as zero. A page served from a different origin only sees this header if the backend sends `Access-Control-Expose-Headers`. Fixture mode never shows it.

The three situations look different on purpose: **evidence** (live, possibly with the rejected-files warning), **unavailable** (an error panel, no data, e.g. HTTP 503 or an unreachable API) and **fixtures** (the permanent "FIXTURE DATA. NOT NASA DATA." banner).

**Test identity (v0.2.2).** Findings that carry `test_id` are grouped by it, and the source's printed outcome is shown verbatim as "Test end as printed: ..." (the label the source prints; not a FlameGuard-SI classification). Findings without a `test_id` keep the older grouping by exact `locator`. Two different outcomes inside one test are shown as a conflict, never resolved. The dashboard never uses the outcome to decide comparability.

If the API is unreachable, the page says so and offers a link to fixture mode. It never switches to fixtures silently. If `/api/health` or a list response reports a contract version other than 0.2.0, a warning is shown.

**Fixture mode when FastAPI serves `frontend/` at `/`:** asset paths are relative and work at `/`. The default fixture location resolves to `/contracts/examples/`, which works only if the backend also mounts that directory. Without the mount, `?fixtures=1` shows an explicit HTTP 404 fixture error and no data.

## What each page does (contract v0.2.0)

| Page | Behaviour |
|---|---|
| Explorer (P1, P2) | Every finding shows evidence class, value status, value, source-reported uncertainty, all 8 conditions, locator, sources and recorded quotes. Investigations with more than 6 measured findings (e.g. FLEX) are grouped by test row (`locator`), with the row's conditions shown once. |
| Compare (P3) | Calls `GET /api/compare` and shows `comparable` and `non_comparable_reasons` exactly as returned. **The browser never decides comparability.** A chart is drawn only when the backend says comparable and the response is consistent: every row must resolve to a loaded measured finding with the same quantity, unit and reported value (S5). The table applies the same check per row: a number is shown only for a consistent row; otherwise the loaded finding's status (e.g. "Excluded by FlameGuard-SI") or "Withheld by dashboard check" is shown with the reason. Missing and excluded values are never plotted or printed. |
| Rank (P4) | Shows criteria and weights, criteria version, each criterion score and its input findings, the rationale, and investigations not ranked (`excluded[]`) with their reason, in the backend's `rank` order. Scores are never recomputed or checked. |
| Interpret & Insight (P8) | Uses each interpretation's own `relevant_environments`, and shows method, version and limitations. Exclusion-dependent interpretations appear only as **exclusion explanations**; broken chains are withheld with reasons. |
| TARS assistant (P5) | Shows the mode (AI / quotes only / no evidence), "Generated by FlameGuard-SI", limitations, and citations linked to findings. Citations that depend on an excluded value are shown separately as exclusion explanations. The answer is withheld unless its `limitations` quote an exclusion note of **every** excluded ancestor (S9); the answer text alone does not count. |
| Integrations | Read-only probe of every contract endpoint (the assistant is not probed, because it may call an AI model), plus the isolated simulation panel. |

## Scientific-integrity behaviour

- **Value status wording:** `reported` shows the value; `not_reported` → "Not reported"; `not_applicable` → "Not applicable"; `excluded` → "Excluded by FlameGuard-SI". An excluded value is never displayed as a number, even if a malformed record carries one.
- `uncertainty` is labelled "Reported by the source". FlameGuard-SI cautions and exclusions (`curation_notes`) are shown separately as FlameGuard-SI assessments, with their quality-flag reference and recorded quote. **A recorded quote is never called "verified"**; verification is S10(d) (Member 3) and Q3 (Member 5).
- Missing values and unreported conditions are shown as missing. Nothing is interpolated, converted or filled.
- **Display guards (spec §4.3) fail closed and never compute.** `model/trace.js` walks `derived_from` and treats an `excluded` finding at any depth as non-supporting (S9, transitive), alongside unresolved ids, cycles, simulations and provenance problems. The ranking, interpretation, comparison and TARS views withhold, with reasons, anything that fails.
- Interpretations and answers are labelled "Generated by FlameGuard-SI. Not a NASA statement." The phrase "according to NASA" appears in no frontend module (tested).
- Simulations are not Findings in v0.2.0; one appearing among findings is flagged. Ranking, interpretation, comparison and TARS modules never import simulation code (import-graph test).
- Data is inserted as text nodes only, and only `http(s)` URLs become links.

## Tests

```bash
python frontend/tools/browser_check.py [--chrome PATH] [--out-dir DIR] [--headed]   # 47 browser checks, any OS
powershell -ExecutionPolicy Bypass -File frontend/tools/run-tests.ps1               # unit + accessibility tests, headless Chrome/Edge (CI: PR #16 runner)
```

- **`run-tests.ps1`** loads `frontend/tests/index.html` and exits non-zero on failure. It covers:
  - filters and row grouping;
  - the comparison display review (no browser-side decision code exists);
  - value-status wording and the rule that excluded values are never formatted;
  - v0.2.0 provenance rules, including curation notes;
  - transitive exclusion (direct, depth 2, mixed parents);
  - ranking rank-order and withholding, with no score recomputation;
  - the fixture adapter against every merged example;
  - TARS modes and exclusion explanations;
  - 400/404/501/network errors, isolation, and attribution.
- **`browser_check.py`** (Python 3.10+ standard library only; it replaces the Windows-only `browser-check.ps1`) drives Chrome, Chromium or Edge on Windows, macOS or Linux through the DevTools Protocol. It uses real key events (`Input.dispatchKeyEvent`), real device-metrics emulation and three local servers on `127.0.0.1` (repository root; `frontend/` at `/`; `frontend/` at `/` plus a `/contracts/examples` mount). It prints `ok`/`FAIL` per check and **exits 0 only if all 47 checks ran and passed**. A missing browser (exit 2), any exception, any failure, or a different check count (exit 1) fails. An explicit `--chrome`/`CHROME` path is authoritative. It covers:
  - skip link, Tab order and focus rings, and the demo by keyboard;
  - the light/dark theme toggle;
  - Compare and Rank flows in fixture mode;
  - a 360 px viewport on every route, judged against the fixed 360 px width (Chrome widens the layout viewport otherwise);
  - a 40-finding grouped investigation at 360 px (`frontend/tests/layout.html`);
  - the fixture banner on every route;
  - **no fixture requests in API mode**;
  - serving at `/` with and without a `/contracts/examples` mount.
- Base test records are in `tests/fixtures/frontend/records.json` (v0.2.0 shapes, `fixture: true`, `example.invalid` URLs, never loaded by the app). `frontend/tests/samples.js` only clones them and applies overrides.
- Mutation-checked: seven deliberate breaks of the display guards were each caught by at least one test (see the PR #2 checkpoint comment).

- The runner's own machinery (WebSocket framing and handshake, fail-closed accounting, glob matching, path confinement, MIME types, browser selection) is unit-tested in `tests/frontend/test_browser_check_runner.py`. Those tests run in the existing pytest CI job and need no browser.

**CI (Member 1 owns `.github/workflows/`).** PR #16 runs the 65 unit tests in headless Chrome. To add the 47 browser checks, append one step to that `frontend` job (ubuntu runners include `google-chrome`, and `CI` makes the runner add `--no-sandbox`):

```yaml
      - name: Frontend browser checks (keyboard, 360 px, fixture isolation)
        run: python frontend/tools/browser_check.py --out-dir browser-check-shots
```

Tested so far on **Windows 11 only** (Chrome 157, Python 3.12). Linux and macOS have not been run yet; the first Linux run would be that CI step.

## Accessibility (WCAG 2.2 AA, automated checks)

`frontend/tests/a11y.test.js` loads all seven pages in real Chrome (same-origin iframes at 1280, 360 and 320 CSS px) in the dark **and** light themes, and checks:

- **Text contrast:** at least 4.5:1, or 3:1 for large text, computed from rendered colours, including gradients.
- **Form-control boundaries:** at least 3:1.
- **Pointer targets:** at least 24×24 px.
- **Reflow:** no horizontal scrolling at 320 px.
- **Structure:**
  - every visible text in a landmark;
  - exactly one `h1` with no skipped heading levels;
  - an accessible name on every control;
  - no duplicate ids.
- **Specific regressions:**
  - the labelled notices region keeps the permanent fixture warning;
  - Explorer results are not a live region, and the count is `role=status`;
  - each Compare checkbox's name includes its investigation;
  - the theme button keeps the name "Light theme" with `aria-pressed` carrying the state;
  - the TARS empty-question error is text, `role=alert`, `aria-invalid`/`aria-describedby`, and moves focus;
  - comparison results are announced as one line;
  - `prefers-reduced-motion` turns off animations, transitions and smooth scrolling;
  - scroll padding keeps focused content clear of the sticky header and the demo bar (2.4.11);
  - states read as text, not colour.

The helpers live in `frontend/tests/a11y-audit.js`, which is first-party with no third-party engine. They run inside the existing harness, including PR #16's CI runner.

**Not covered by automation:** a screen-reader pass (NVDA, JAWS, VoiceOver), a check by a person on a phone, zoom to 400% on desktop, and user testing. Those still need a person.

## Layout

```
frontend/
  index.html                 App shell (skip link, theme button)
  static/css/app.css         Styles; dark and light themes
  static/js/
    main.js                  Router, nav, fixture banner, version and list warnings, theme
    config.js                ?fixtures=1, CONTRACT_VERSION 0.2.0, version check
    store.js                 Loads lists; S7 total and version warnings
    demo.js                  90-second guided walkthrough
    api/                     types.js (v0.2.0 JSDoc), errors.js, http.js (incl. /api/compare), fixtures.js
    model/                   Pure logic, no DOM: evidence.js, trace.js (S9), group.js (P2),
                             filter.js, compare.js (display review only), ranking.js (display guard only)
    ui/                      dom.js (safe element builder), components.js, chart.js, announce.js (status region, reduced motion)
    views/                   dashboard, explorer, compare, rank, interpret, tars, integrations, context
    integrations/            assistant.js (TARS UI), simulation.js (isolated)
  tests/                     Browser test harness, tests, layout.html (360 px page), a11y-audit.js + a11y.test.js
  tools/                     browser_check.py (47 browser checks, any OS), run-tests.ps1, serve.ps1
tests/fixtures/frontend/     Base test records (Member 2)
tests/frontend/              Unit tests of the browser-check runner (Member 2)
```

## Integration points

| Member | What the frontend needs |
|---|---|
| 1 (backend) | B1 loader, B2 lists (`investigation_list`, `finding_list` with `total`), B3 `/api/compare`, B4 `/api/rankings`, B6 `/api/assistant/ask`, and B7: mount `frontend/` at `/`. Optionally mount `contracts/examples` at `/contracts/examples` for fixture mode. Q4: Playwright dependency PR and CI job. |
| 3 (data) | Curated FLEX `Finding` JSON: measured findings of one test row share one `locator` (used for P2 grouping and S10a); every caution and exclusion is a `curation_notes` entry with `flag_ref` and a recorded `source` quote; FLEX-010 burning rate is `excluded`. The FLEX vocabulary contract PR (C4) is needed before any FLEX numeric finding. |
| 5 (research) | Independent review of the display wording and labels (spec §4.4). Ranking criteria (R1) before any real ranking. |

## Judge demo limitation

Until the backend serves rankings, comparisons and the assistant, and real NASA records are curated, the walkthrough **cannot show a real ranking, comparison or safety insight**. In API mode those steps show HTTP 501; in fixture mode they show the labelled contract fixtures. Compare and Rank also need a second curated investigation that shares a quantity with FLEX.
