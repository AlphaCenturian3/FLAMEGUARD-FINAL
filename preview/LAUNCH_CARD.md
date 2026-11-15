# FlameGuard-SI launch card (development preview, one page)

## Launch
| | Mac | Windows |
|---|---|---|
| Easiest | In the `preview` folder double-click **Start-Preview-Mac.command** (first time: right-click, **Open**) | In the `preview` folder double-click **Start-Preview-Windows.bat** (SmartScreen: **More info**, **Run anyway**) |
| Terminal | `python3 preview/run.py` | `py -3 preview\run.py` |

First start takes 1 to 3 minutes and needs internet (downloads packages); later starts work offline. Stop with `Ctrl+C`.
**Port conflict?** The double-click launchers handle it: if 8790 is busy (an old preview is still running) they use the next free port, **8791**, say so in the black window, and open that address in your browser. Typing it yourself: `python preview/run.py --port 8791` (Windows: `py -3 preview\run.py --port 8791`). Always use the address printed after **OPEN THIS ADDRESS** in the black window; use it in place of 8790 below if it differs.

## Addresses
- **Live dashboard:** http://127.0.0.1:8790/ (shows only evidence that passed our checks; today that is none)
- **Fixture mode (placeholders, clearly labelled):** http://127.0.0.1:8790/?fixtures=1 (banner: **FIXTURE DATA. NOT NASA DATA.**)
- **Blender illustrations (labelled, not NASA data):** http://127.0.0.1:8790/illustrations/

## Five steps (about 3 minutes)
1. Open the **live** address. The overview says **0 Investigations loaded**.
2. Click **Evidence Explorer**: "No investigations available". Click **Rank**: "HTTP 501".
3. Open the **fixture** address. Read the banner aloud.
4. In **Evidence Explorer** scroll to the excluded finding (no click needed): "Excluded by FlameGuard-SI", "value not shown".
5. On the overview click **Start 90-second demo** and press **Next** through the five steps: Discover, Compare, Rank, Interpret, Safety Insight. On **Interpret & Insight** choose **Lunar base** in the Application context list to see the placeholder interpretation and its limitation. Optional: open the illustrations address.

**What step 4 looks like** (fixture mode, banner at the top; the excluded finding shows its reason and no number): see `preview/screenshots/fixture-excluded-finding.png`.

## Implemented vs unavailable
| Working now | Not available (say so) |
|---|---|
| Evidence Explorer, honest empty state, clear errors (400, 404, 503) | **NASA findings in the app**: audited and prepared, deliberately not loaded until independent scientific review and approvals finish |
| Fail-closed loading: a file that fails a check is withheld and counted | **Rankings** and **comparisons** on real evidence (the live backend answers HTTP 501) |
| Excluded values withheld, with the reason and source quote | **TARS assistant** answers (planned; HTTP 501) |
| Fixture mode with a permanent banner; guided tour | **Simulation results** (planned; HTTP 501) |
| Four Blender gravity illustrations at `/illustrations/` | Any fire-risk score or safety rating |

## Never claim
- **NASA evidence:** that any number on screen is a NASA measurement. Fixtures are invented placeholders. No FLEX value is loaded or approved.
- **Ranking:** that FlameGuard-SI ranks investigations or materials from real evidence. The fixture ranking is a placeholder.
- **TARS:** that the assistant answers questions. It is planned, not built.
- **Blender:** that the images are simulations, predictions or validated physics. Say the words printed in every image: **ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.**
- That the smoke tests or audits are a scientific approval. They check the software and data preparation; independent scientific review is still open.

## Check before you present (2 minutes)
`python preview/run.py --port 8791 --smoke` must end with `0 failed`. Full script: `preview/PRESENTATION_SCRIPT.md`. Longer notes and recovery steps: `preview/DEMO.md`.
