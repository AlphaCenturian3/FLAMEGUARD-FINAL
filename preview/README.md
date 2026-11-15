# Development preview (not production)

A local, one-command preview of the FlameGuard-SI dashboard running against the B2 evidence
backend. It **merges nothing and changes no branch**. It exports two git refs into `.preview/`
(git-ignored) and serves them together:

| Part | Default ref | Exported paths |
|---|---|---|
| Backend, contract, data manifest | `origin/feat/backend-b2-explorer` (PR #18, draft, stacked on B1) | `backend/`, `contracts/`, `data/`, `tools/`, `pyproject.toml`, `README.md` |
| Frontend | `origin/feat/frontend-dashboard` (PR #2) | `frontend/` only |

## For the project owner: start it (no coding)

**One-time setup** (about 10 minutes): install [Git](https://git-scm.com/downloads), [Python 3.11 or newer](https://www.python.org/downloads/) (on Windows tick **"Add python.exe to PATH"** / keep the "py launcher" option) and [Google Chrome](https://www.google.com/chrome/). Download the repository once (`git clone https://github.com/AlphaCenturian3/FLAMEGUARD-FINAL.git`, or GitHub Desktop).

**Start**

- **Mac:** open the `preview` folder and double-click **Start-Preview-Mac.command**. The first time, macOS may refuse: right-click the file, choose **Open**, then **Open** again.
- **Windows:** open the `preview` folder and double-click **Start-Preview-Windows.bat**. If Windows SmartScreen warns, choose **More info**, then **Run anyway**.

A black window opens and installs what it needs (the first start takes 1 to 3 minutes and needs internet). Your browser then opens **http://127.0.0.1:8790/**. If it does not, type that address into Chrome.

**Stop:** click the black window and press `Ctrl+C` (Mac: `Ctrl+C` too), then close it.

**If it says "Port 8790 is already in use":** an older preview is still running. Close its window, or restart the computer.

### What you will see

| Address | What it shows |
|---|---|
| `http://127.0.0.1:8790/` | **Live mode.** The real backend. No NASA evidence has been approved and registered yet, so the Evidence Explorer says **"No investigations available"**. Compare shows nothing to compare. Rank, assistant and simulations say **HTTP 501, not implemented**. This is correct and honest; nothing is invented. |
| `http://127.0.0.1:8790/?fixtures=1` | **Fixture mode.** Placeholder examples from the contract. Every page carries the banner **"FIXTURE DATA. NOT NASA DATA."** Use it to show how the dashboard will look, never as results. |

## For developers

```bash
python preview/run.py                 # build, serve on http://127.0.0.1:8790/
python preview/run.py --smoke         # build, run every check below, stop (exit 1 on any failure)
python preview/run.py --scenario synthetic   # manual inspection of SYNTHETIC evidence (see below)
```

Requirements: Git, Python 3.11+, network the first time. Browser checks need Chrome, Chromium or Edge (set `CHROME` to override). The judge-demo check needs Node 22+. A check that cannot run is reported **SKIPPED (not verified)**, never passed.

Options: `--backend-ref`, `--frontend-ref`, `--port` (default 8790; the launcher refuses a port already in use), `--no-fetch`.

### What `--smoke` checks

1. **API (live preview):** health; the empty evidence lists are honest and empty; unknown investigation is 404; unknown parameter, simulation as evidence class, unknown quantity and unknown investigation filter are 400; compare, rankings, assistant and simulations remain 501; unknown `/api` paths are 404; fixtures are served only under `/contracts/examples/`.
2. **Browser, every route, live and `?fixtures=1`:** live never shows the fixture banner or fixture text; fixture mode always shows the banner; live Explorer says no investigations; live Rank says 501; an unreachable API is reported as such and **never** falls back to fixtures silently.
3. **Synthetic scenarios (throwaway ports, `preview/scenarios.py`):** an excluded value is `null` and "value not shown"; a missing value stays `not_reported`; a file with a wrong checksum is withheld, the rest is served, and `X-FlameGuard-Rejected-Entries: 1` is sent; an unreadable manifest gives 503 on every evidence endpoint and the page shows the error and no data.
4. **Judge-demo walkthrough** (5 steps) in both modes.

### Separation of fixtures, synthetic data and NASA evidence

- **NASA evidence:** only what the B1 loader accepts from `data/manifest.json` of the exported backend ref. Today that is nothing.
- **Fixtures:** `contracts/examples/*`, shown only at `?fixtures=1`, always bannered.
- **Synthetic scenarios:** generated into temporary folders from the contract examples, every statement says SYNTHETIC. They exist for the smoke tests, and `--scenario` for local inspection. In live mode the page does **not** carry a fixture banner, so `--scenario` prints a warning and must never be used for a demo.

### Safety rules (enforced by `tests/test_preview_isolation.py`)

- `preview/server.py` only dispatches `/api/*` to the **unmodified production app** and serves static files. It adds no routes, scores, data or fallbacks. Nothing in `backend/` imports it. This is not B7.
- The AI key is forced blank, and the server binds to `127.0.0.1` only.
- The evidence root is set explicitly (`FLAMEGUARD_DATA_ROOT`), because the backend is pip-installed.

## Known limits

- The frontend at PR #2 still prints "Contract v0.1.0" in its footer while the API badge says 0.2.0 (a Member 2 wording item; the version-mismatch warning itself is correct).
- The frontend does not read the `X-FlameGuard-Rejected-Entries` header, so a partial load is visible only in the server log and the header, not on the page. Reported to Command Center as a decision.
- No real NASA evidence is registered, so no real comparison, ranking, interpretation or TARS answer exists.
