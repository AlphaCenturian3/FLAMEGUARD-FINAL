# Demo workflow (development preview)

One-page version: `LAUNCH_CARD.md`. Timed script: `PRESENTATION_SCRIPT.md`.

Written for the project owner. This is a **development preview**: unfinished parts say so on screen, and nothing is invented to fill the gaps. Everything below was checked against the running preview (42/42 smoke checks).

## 1. Start it (5 minutes before)
1. Double-click **Start-Preview-Mac.command** (Mac) or **Start-Preview-Windows.bat** (Windows) in the `preview` folder, or run `python preview/run.py`. Details: `preview/README.md`.
2. Open **http://127.0.0.1:8790/**. The first start downloads packages (1 to 3 minutes).
3. **"Port 8790 is already in use"** means an older preview is still running. Either start on another port (`python preview/run.py --port 8791`, then use 8791 everywhere below), or stop the old one: Mac `lsof -nP -iTCP:8790 -sTCP:LISTEN` then `kill <PID shown>`; Windows `netstat -ano | findstr :8790` then `taskkill /PID <PID>`. Only stop a process you recognise as an old FlameGuard preview.
4. **Self-check (about 2 minutes, optional but recommended):** `python preview/run.py --port 8791 --smoke`. It must end with `0 failed`.
5. The exact commits being shown are printed at startup and saved in `.preview/versions.txt`.

## 2. What is real and what is not (say this first)
- **Real and demonstrable:** the evidence explorer (API and page), fail-closed loading, excluded and missing values shown honestly, clear error pages, fixture labelling, the guided tour.
- **Not built yet:** NASA findings in the app, comparison and ranking from real data, the TARS assistant, simulation results.
- The NASA FLEX data has been **prepared and audited but is deliberately not loaded**: it is held back until the independent scientific review and contract approvals are complete. The app therefore shows no NASA findings. That is by design, not a bug.

## 3. Judge sequence (about 4 minutes)
| Step | Do this | Say this |
|---|---|---|
| 1. Honest start | Open `http://127.0.0.1:8790/`. The overview shows **0 investigations, 0 findings loaded**. Click **Evidence Explorer**: "No investigations available". Click **Rank**: "HTTP 501". | "The live system only shows NASA evidence that has passed our checks. Approval is still in progress, so it shows nothing instead of guessing." |
| 2. How it will look | Open `http://127.0.0.1:8790/?fixtures=1`. Point at the banner **FIXTURE DATA. NOT NASA DATA.** The overview now says "6 of these records are contract fixtures". | "These are invented placeholders that show the design. They are not results." |
| 3. Safeguards | In Evidence Explorer (fixture mode) open the excluded finding: "Excluded by FlameGuard-SI, value not shown", with the reason and the recorded source quote. | "When a source value conflicts with its own caption we exclude it, say why, and never display the number." |
| 4. Guided tour | On the overview click **Start 90-second demo** (fixture mode). Five steps: Discover, Compare, Rank, Interpret, Safety Insight. | "Same flow a researcher would follow, on placeholder data." |
| 5. Be careful with Rank | In fixture mode the Rank page shows a ranking with "Fixture · not NASA data" badges. | "That ranking is a fixture. No real ranking exists: the live backend returns 501 for rankings until approved evidence exists." |
| 6. Illustrations (optional) | Show the four images in `visualization/renders/` (earth, mars, moon, microgravity; on the Blender branch, PR #20). | "Illustration only. Not a validated combustion simulation. Not NASA data." The words are inside each image; read them out. |

## 4. Never say
- "NASA data shows..." or any FLEX number: no FLEX finding is loaded or approved.
- That the rankings, comparisons or the assistant work on real evidence.
- That the Blender images are simulations or predictions of real flames.
- That the 42 checks or the audits are a scientific approval. They check the software and the data preparation; the independent scientific review is still open.

## 5. If something goes wrong
| Symptom | Do this |
|---|---|
| Page will not load | Check the black window is still open; restart the launcher; try another port. |
| "The API could not be reached" | The backend stopped. Restart it. The page will not show fake data. |
| "Service unavailable" (503) | An evidence file failed a check. By design the page shows no data. Read the server window for the reason, or show `/?fixtures=1` and say it is a fixture. |
| A yellow warning "evidence files were rejected" | The backend withheld some files and says the lists are incomplete. Say so. (Needs the frontend fixes of PR #21, which the pinned preview includes.) |
| Data on screen without the **FIXTURE DATA. NOT NASA DATA.** banner that looks like placeholders | Stop the demo, close the window, restart without `--scenario`. |
