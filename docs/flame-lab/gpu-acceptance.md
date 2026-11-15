# Flame Lab: real-GPU acceptance (one machine, 2026-11-15)

These results describe **one Mac**. They say nothing about other GPUs, Windows, phones or other
browsers, none of which were tested.

## Machine

| | |
| --- | --- |
| Computer | MacBook Pro, Apple M1 Pro (14-core GPU), 16 GB, built-in Liquid Retina XDR display (up to 120 Hz) |
| System | macOS 26.6.2 (25G83), on battery power |
| Browser | Google Chrome 157.0.8103.51 |
| WebGL renderer reported by the page | `ANGLE (Apple, ANGLE Metal Renderer: Apple M1 Pro, Unspecified Version)` |

## Method

- The page was served locally by the preview launcher (`preview/run.py`) and driven over the
  Chrome DevTools Protocol with a fresh browser profile and the HTTP cache disabled.
- Chrome was started with `--use-angle=metal --enable-gpu`. The renderer string above was read
  from `WEBGL_debug_renderer_info` in every run, so no run used software rendering.
- Frame rate: the page's own `requestAnimationFrame` timestamps over 5 seconds, after 2.5
  seconds of warm-up. Reported as frames per second, median and 95th-percentile frame time, and
  the number of frames longer than 33.4 ms.
- Load: resource timing of the page (requests and transferred bytes) and the time from
  navigation until the scene reported ready.
- Viewports: 1440x900 at device pixel ratio 2, and 390x844 at device pixel ratio 3 with mobile
  emulation. The mobile result is an emulated viewport on the same Mac, **not a phone**.
- The scene caps its own render pixel ratio at 1.75.

Two kinds of run were made:

| Run | Build | What it shows |
| --- | --- | --- |
| Visible window | `307a22d` (PR #34) | Frame rate at the display's refresh rate |
| Headless | `307a22d` and `13bc16d` (this branch) | Frame rate capped at 60 by headless Chrome; used for the screenshots and the reduced-motion check |

## Results

| Measure | Visible window, `307a22d` | Headless, `13bc16d` |
| --- | --- | --- |
| Frame rate, desktop viewport | 120 fps, median 8.3 ms, p95 9.2 ms, 0 frames over 33.4 ms | 60 fps, median 16.7 ms, p95 16.8 ms, 0 over 33.4 ms |
| Frame rate, mobile viewport (emulated) | 120 fps, median 8.3 ms, p95 9.2 ms, 0 over 33.4 ms | 60 fps, median 16.7 ms, 0 over 33.4 ms |
| Draw calls / triangles | 31 / about 13,100 (28 / about 10,500 with the solid sample) | same |
| Page with the scene | 46 requests, 944 kB transferred; three.js is 740 kB and is fetched only on this route | 46 requests, 945 kB |
| Scene ready after navigation | 0.35 to 0.4 s; 1.2 s in the first visible window and 2.3 s in the first headless launch | 0.25 to 0.4 s |
| WebGL fallback (`?scene=off`) | 33 requests, 182 kB, no three.js | not re-measured |
| Console errors, horizontal overflow | none | none |

Reduced motion (`prefers-reduced-motion: reduce`), headless:

| | `307a22d` | `13bc16d` |
| --- | --- | --- |
| Frames drawn in 1.5 s with nothing changing | 100 | 0 |
| Picture between two captures | identical | identical to within 1 level per channel |
| Drag to orbit | redraws | 10 frames, picture changes, then 0 |
| Change a control | picture updates | picture updates |
| Pause motion / Resume motion | | idles / returns to 60 fps |

## Limits of these numbers

- One machine, one browser, one day, on battery. Not a benchmark.
- The 120 fps figures were measured before the reduced-motion fix. The fix does not touch the
  animated path, and the headless frame rate is unchanged, but 120 fps was not re-measured on
  `13bc16d`.
- Visible test windows received stray pointer and scroll input during the session. Their frame
  timings are reported above; their screenshots are **not** kept, because two of them showed
  control states that the test had not set.
- Not tested: Windows, Linux, Safari, Firefox, any phone or tablet, integrated or older GPUs,
  thermal throttling over long sessions.

## Screenshots (headless, Metal GPU, build `13bc16d`)

Each control state was read back from the page before capture and matched what the test set.
The screenshots show only the application.

| File | Viewport | Controls read back from the page |
| --- | --- | --- |
| [gpu/desktop-microgravity.png](gpu/desktop-microgravity.png) | 1440x900 | Microgravity, 21%, still, low-soot liquid |
| [gpu/desktop-earth-sooty-airflow.png](gpu/desktop-earth-sooty-airflow.png) | 1440x900 | Earth 1 g, 30%, moderate airflow, sooty liquid |
| [gpu/mobile-earth-solid.png](gpu/mobile-earth-solid.png) | 390x844, emulated | Earth 1 g, 21%, still, solid sample |
| [gpu/desktop-reduced-motion.png](gpu/desktop-reduced-motion.png) | 1440x900, reduced motion | Microgravity, 21%, still, low-soot liquid; scene idle |

Everything shown is an illustration. No flame behaviour in these pictures is a measurement or a
prediction.
