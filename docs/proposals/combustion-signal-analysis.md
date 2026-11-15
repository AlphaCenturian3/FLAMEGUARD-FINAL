# Proposal: native Combustion Signal Analysis (retrospective)

State: **prepared, not built.** Blocked by master spec §2.5; see
`docs/decisions/pre-event-signal-analysis.md`. No analysis code, data or result is in this
repository, and no endpoint or page exists.

## What it would be

A read-only page that shows how the brightness signal of a recorded BASS-II burn was analysed
after the fact: the detrended signal, its Hann periodogram, the share of power in a fixed band,
and a short-time Fourier transform. It restates the earlier study's own verdicts, including
that the result did **not replicate** in the other recordings analysed.

## What it must never be

- Never a predictor. No output is used to forecast, score or warn of ignition, extinction, fire
  risk or suppression, and the page says so.
- Never NASA evidence. The series are reconstructed from video overlays and uncalibrated; they
  are not `Finding` objects, do not enter the evidence API, the ranking, compare or the
  assistant, and are labelled as FlameGuard-SI retrospective analysis, not NASA data.
- Never part of the Flame Lab. Separate route, separate modules, no shared state; the Flame Lab
  stays an illustration and imports nothing from here. Spatial and temporal Fourier analyses
  stay separate (spec §2.4).
- Never a rewrite of history. Method parameters and recorded values are shown as recorded, with
  the original date, commit and author.

## Shape once unblocked

| Piece | Location | Notes |
| --- | --- | --- |
| Spectral functions | `backend/flameguard/signal/spectral.py` | Port with attribution header; pure functions |
| Recorded results and provenance | `data/retrospective/bass2/` with a manifest entry of its own class | Not under `data/curated/findings/` |
| API | `GET /api/signal-analysis/*` | Returns 501 until the review below passes |
| Page | `#/signal-analysis`, `frontend/static/js/views/signal.js` | Fixed banner with the limits; no controls that change the method |

## Tests to write with the port

1. Known-answer tests on synthetic signals (a sine at a known frequency peaks there; a
   polynomial trend is removed; band share of white noise matches the band-width ratio).
2. Equivalence test against the original file, by SHA-256, when the source repository is
   available locally; skipped otherwise.
3. Recorded values equal the source outputs, byte for byte.
4. Wording guard: the page and API text contain the limits and none of "predict", "forecast",
   "early warning", "risk score".
5. Import guard: ranking, compare, assistant and Flame Lab modules do not import the signal
   package, and the signal package does not import them.
6. Evidence guard: nothing under `data/retrospective/` loads as a `Finding`.

## Review before the endpoint leaves 501

Independent scientific review (Member 5) of the wording and of whether a non-replicated result
is shown; the decisions listed in the decision record.
