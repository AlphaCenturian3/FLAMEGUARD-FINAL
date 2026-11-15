# Demo workflow (development preview)

Written for the project owner. Everything below is a **development preview**: unfinished parts say so on screen, and nothing is invented to fill the gaps.

## Before the demo (5 minutes)
1. Start it (see `preview/README.md`): double-click the Mac or Windows launcher, or `python preview/run.py`. Open **http://127.0.0.1:8790/**.
2. If it says the port is in use, an older preview is running. To stop it on a Mac: open Terminal and run `lsof -nP -iTCP:8790 -sTCP:LISTEN`, then `kill <the PID shown>`. On Windows: open Command Prompt, run `netstat -ano | findstr :8790`, then `taskkill /PID <the PID> /F`. Or start on another port: `python preview/run.py --port 8791`.
3. Optional self-check: `python preview/run.py --port 8791 --smoke` (about 2 minutes). It must end with `0 failed`.

## Judge sequence (about 4 minutes)
| Step | Show | Say |
|---|---|---|
| 1. Honest start (live mode, `/`) | Evidence Explorer: **"No investigations available"**; Rank page: HTTP 501 | "The live system only shows NASA evidence that has passed our checks. None is approved yet, so it shows nothing instead of guessing." |
| 2. How it will look (`/?fixtures=1`) | Click through Explorer, Compare, Rank, Interpret. Point at the banner **FIXTURE DATA. NOT NASA DATA.** | "These are placeholder examples to show the design. They are not results." |
| 3. Safeguards | Open an excluded fixture finding: "Excluded by FlameGuard-SI, value not shown", with the reason and the recorded source quote | "When a source value conflicts with its own caption we exclude it, say why, and never display the number." |
| 4. Judge demo button | The 5-step guided tour (Discover, Compare, Rank, Interpret, Safety Insight) | Use it in fixture mode only. |
| 5. Illustration (optional) | The four gravity images in `visualization/out/` | "Illustration only. Not a simulation, not NASA data." |

## Demonstrated vs planned (say this out loud)
- **Demonstrated:** evidence explorer API and page, fail-closed loading, excluded and missing value handling, error pages (400/404/503), fixture labelling, the guided tour.
- **Planned, not built:** real NASA findings in the app (waiting on independent scientific review), comparison and ranking from real data, the TARS assistant, simulation results.

## If something goes wrong
| Symptom | Do this |
|---|---|
| Page will not load | Check the black window is still open; restart the launcher; use another port. |
| "The API could not be reached" | The backend stopped. Restart. The page will not show fake data. |
| "Service unavailable" (503) | The evidence files failed a check. This is by design; read the server window for the reason. Show `/?fixtures=1` instead and say it is a fixture. |
| Banner missing but data looks like placeholders | Stop the demo: close the window, restart without `--scenario`. |
