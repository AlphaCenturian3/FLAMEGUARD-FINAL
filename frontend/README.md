# Frontend

Owner: `feat/frontend-dashboard`.

**Status:** Evidence Explorer, Comparison, Ranking, Interpretation & Safety Insight, Integrations, and the guided judge demo are built against contract v0.1.0. No real NASA data exists in the repository yet, so the dashboard shows either backend responses (all `501` except `/api/health`) or the contract fixtures, which are clearly labelled as not NASA data.

Stack (spec §3): static HTML, CSS, and vanilla JavaScript ES modules. No build step, no dependencies.

## Run it

The page must be served over HTTP because ES modules and `fetch` do not work from `file://`.

**With contract fixtures** (serve the repository root so `contracts/examples/` is reachable):

```bash
python3 -m http.server 8765                      # from the repository root
# Windows without Python:
powershell -ExecutionPolicy Bypass -File frontend/tools/serve.ps1
```

Open <http://localhost:8765/frontend/index.html?source=fixtures>.

**Against the backend** (once it serves `frontend/` at `/`): open `/`. The default source is the API at the same origin. To point at a separate API host, add `?api=http://127.0.0.1:8000`. The backend then needs CORS enabled.

**Fixture mode when FastAPI serves `frontend/` at `/`:** all asset paths are relative and work at `/` (verified by `browser-check.ps1`). The default fixture location resolves to `/contracts/examples/`, which works **only if the backend also mounts that directory** (for example `app.mount("/contracts/examples", StaticFiles(directory="contracts/examples"))`). Without the mount, `?source=fixtures` shows an explicit "Could not load fixture … HTTP 404" error and no data. This is a backend decision; the frontend does not require it.

| Query parameter | Meaning |
|---|---|
| `source=fixtures` | Read `contracts/examples/*.json`. A striped banner and per-record badges mark everything as a fixture. |
| `api=URL` | API base URL (default: same origin). |
| `fixtures=URL` | Location of `contracts/examples/` (default: `../contracts/examples/`). |

If the API is unreachable the page says so and offers a link to fixture mode. It never switches to fixtures silently.

## Tests

```powershell
powershell -ExecutionPolicy Bypass -File frontend/tools/run-tests.ps1
```

This starts the static server, loads `frontend/tests/index.html` in headless Chrome or Edge, prints each result, and exits non-zero on failure. On any OS you can also serve the repository root and open `/frontend/tests/index.html` in a browser.

The tests cover filtering, comparison compatibility messages, provenance and evidence-class labels, missing-data display, HTTP 501 handling, ranking guards (unresolved inputs, simulations reached directly or through interpretations, broken provenance, cycles), withheld interpretations, assistant attribution, the simulation label, isolation of simulation modules (import-graph check), HTML-injection safety, and the demo step order.

Base test records live in `tests/fixtures/frontend/records.json` (spec §2.2: mock data only in `tests/fixtures/`; that directory is owned by `test/qa-demo`). `frontend/tests/samples.js` only clones them and applies per-test overrides. All are marked `"fixture": true`, use `example.invalid` URLs, and are never loaded by the app.

### Browser checks (keyboard, mobile, served at `/`)

```powershell
powershell -ExecutionPolicy Bypass -File frontend/tools/browser-check.ps1 [-OutDir shots] [-Headed]
```

Drives Chrome/Edge through the DevTools Protocol with real key events: skip link, Tab order and visible focus rings, Enter/Space activation, search empty state, the judge demo by keyboard (focus stays in the demo bar), and the mobile menu (Enter opens it, Escape closes it and returns focus). It emulates a 390 px mobile viewport on every route and checks for horizontal scroll. It also serves `frontend/` at `/` as FastAPI would and checks asset paths, same-origin API calls, and fixture mode with and without a `/contracts/examples` mount. Use `-Headed` to watch it.

### Ranking and interpretation guards

`static/js/model/trace.js` walks each finding's `derived_from` chain. A finding counts as evidence-backed only if every link resolves to a loaded finding, every node passes the schema's provenance rules, there are no cycles, no node is an `illustrative_simulation`, and the chain ends in at least one `measured` finding. Rankings withhold any item whose inputs fail this. The Interpretation view withholds failing interpretations: their statement is hidden and the reasons are listed.

## Layout

```
frontend/
  index.html                 App shell
  static/css/app.css         All styles
  static/js/
    main.js                  Hash router, nav, data-source banner, health badge
    config.js                URL params -> data source
    store.js                 Loads investigations + findings; loading/ready/not_implemented/error states
    demo.js                  90-second guided walkthrough
    api/
      types.js               JSDoc mirrors of contracts/schemas
      errors.js              ApiError, 501 detection
      http.js                Backend adapter (spec §5.1 endpoints)
      fixtures.js            contracts/examples adapter (rankings/assistant -> 501)
    model/                   Pure logic, no DOM
      evidence.js            Evidence classes, provenance checks, missing fields
      filter.js              Explorer filters
      compare.js             Comparison model + chart compatibility rules
      ranking.js             Checks backend rankings; never computes scores
    ui/                      dom.js (safe element builder), components.js, chart.js (SVG bars)
    views/                   dashboard, explorer, compare, rank, interpret, integrations, context
    integrations/            assistant.js, simulation.js (isolated integration points)
  tests/                     Browser test harness and tests
  tools/                     serve.ps1, run-tests.ps1, browser-check.ps1
tests/fixtures/frontend/     Base test records (QA-owned directory)
```

## Judge demo limitation

Until the backend implements `GET /api/rankings` and the data workstream registers measured NASA records, the walkthrough **cannot show a real ranking or a real safety insight**. The Rank step shows the HTTP 501 "not implemented" state, and the demo text says so. In fixture mode, the Interpret step shows only the labelled placeholder interpretation.

## Scientific-integrity behaviour

- Every finding shows its evidence class (`measured`, `interpretation`, `illustrative_simulation`) as text plus colour, and a fixture badge when `fixture: true`.
- Missing values, units, uncertainty, and source fields are listed as missing. Nothing is interpolated.
- Uncertainty is shown as reported text. No error bars are drawn.
- Provenance rules from the schemas are re-checked on screen. A failing record shows a visible warning.
- Rankings are only displayed from the backend. Items citing an `illustrative_simulation` finding, or lacking a numeric score or rationale, are withheld and listed.
- Interpretations and assistant answers are labelled "Generated by FlameGuard-SI. Not a NASA statement."
- Simulation views always show "Fluid and thermal transport model. No combustion chemistry." Results with a different label are refused.
- Ranking, interpretation, and assistant modules never import simulation modules. A test enforces this.
- Data is inserted as text nodes only, and only `http(s)` source URLs become links.

## Integration points

| Workstream | What the frontend expects |
|---|---|
| Backend (`feat/backend-science`) | Endpoints in spec §5.1 with contract-shaped JSON and `Error` bodies on non-2xx. Serve `frontend/` at `/` (e.g. FastAPI `StaticFiles(directory="frontend", html=True)` mounted after the API routes). Rankings: `{items:[{investigation_id, score, rationale, inputs}]}`. An optional `criteria` array is displayed verbatim if present. |
| Data (`feat/nasa-data-tars`) | Investigations and findings with complete `sources` (title, url, retrieved, page, quote, archive_id where known). "TARS" is still undefined in spec §4, so `integrations/assistant.js` targets only `POST /api/assistant/ask`. |
| QA (`test/qa-demo`) | Owns `tests/fixtures/frontend/` and CI. `frontend/tools/run-tests.ps1` and `browser-check.ps1` exit codes; stable selectors: `#main`, `#nav a[href="#/explorer"]`, `.demo-bar`, `[data-status]` on the test page. The demo steps are in `static/js/demo.js` (`DEMO_STEPS`). |

## Proposed contract addition (not yet in v0.1.0)

Comparison charts need to know that two findings measure the same thing. Contract v0.1.0 has no such field, so **charts are currently disabled** and the page explains why. The frontend already reads an optional `quantity` string on `Finding` (for example `"flame_spread_rate"`). Charts appear only when two or more selected investigations report a `measured` numeric value for the same `quantity` with the same `unit`. Adding `quantity` (and, later, structured experimental parameters for Explorer filters) needs a contract PR under spec §5.4.
