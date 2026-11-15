# Decision record: reuse of pre-event FFT/STFT work for Combustion Signal Analysis

Status: PENDING

This file is a request and an audit. It is **not** a ruling and records no approval. Until the
status line above reads `APPROVED` with both sign-offs below filled in, nothing from the earlier
repository is copied here (master spec §2.5), and `tests/test_pre_event_gate.py` fails any branch
that adds the feature's code.

| Required by §2.5 | State | Recorded by |
| --- | --- | --- |
| (a) Organizer ruling on pre-event work | PENDING (spec §8, open decision 1) | nobody yet |
| (b) Content and license audit | Drafted below by Member 1; needs an independent check | nobody yet |

## What is proposed for reuse

Source: private repository `AlphaCenturian3/FlameGuard-SI`, branch `stage-4-physics-modules`,
commit `0013a77e8d91ceb8e964c89ee3f6fbca1eec1295`. Sole commit author of every file listed:
the project owner (Member 1), per `git log`. The files pre-date this repository.

| Item | Path in the source repository | SHA-256 (first 16) | Proposed use |
| --- | --- | --- | --- |
| Temporal spectral measures (detrend, Hann periodogram, band share, peak frequency) | `research/bass2/bassrepro/spectral.py` (last changed in `0b38973`, 2026-11-06) | `12385a997f1a2679` | Port, with an attribution header |
| Short-time Fourier transform settings | one call in `research/bass2/scripts/04_o4_reproduce.py` | not hashed: one line | Port the settings |
| Frozen method parameters | `research/bass2/config/frozen_method_v2.json` | `f75978eb6160798e` | Reference, unchanged |
| Recorded results | `research/bass2/outputs/o4_stats.json`, `confirmatory.json` | `61f36fc5f37df7a6`, `68860ce3caaed370` | Display, unchanged, with limits |
| Reconstructed time series | `research/bass2/outputs/series/*_ticks.csv` | not copied | **Not proposed** until rights are settled (below) |

Not proposed: the 2D imaging spectrum module (spatial analysis stays separate, spec §2.4), the
surrogate and autoregressive statistics, and any NASA video, frame or PDF.

## Content audit

- **Authorship.** The work is the project owner's own, written before the event. Any port must
  say so in the file header (source repository, commit, original date) and must not present it
  as written during the event or by the team.
- **Nature of the data.** The series were reconstructed from numbers burned into NASA video.
  The source README states: "They are not original sensor data, and RAD is uncalibrated."
  They are not contract `Finding` objects and are not registered NASA evidence in this
  repository.
- **What the results say.** The source records one target test. Its own verdicts are: O4,
  "positive control, not a confirmatory test"; O15a and O15b, "NOT REPLICATED"; the remaining
  recordings carry no verdict. The README states: "Nothing here measures predictive skill or a
  false-alarm rate. Not for operational fire safety decisions."
- **Reproducibility check (2026-11-15, read-only, nothing copied).** Recomputing the O4
  final-window values from the stored series with the stored code returned exactly the values
  recorded in `o4_stats.json`, and the short-time transform ran with the recorded settings.
- **History.** The source repository and its outputs were not modified.

## License and rights audit

| Question | Finding |
| --- | --- |
| License of the source repository | None. No LICENSE file; private. The owner can license their own code, but must say so in writing. |
| License of this repository | None yet (spec §8, open decision 2). |
| Third-party code inside the files proposed | None found. `spectral.py` imports only NumPy and SciPy. |
| New runtime dependencies | NumPy and SciPy (both BSD-3-Clause). Neither is a dependency here today; adding them changes `pyproject.toml` and needs team agreement. |
| NASA video and anything derived frame-by-frame from it | Rights review still open (spec §2.4). The reconstructed series are derived from NASA video, so they are held back with it. |
| Published method or citation the code depends on | None cited in the source README. |

## Decisions needed (not made here)

1. Organizer ruling: may pre-event work by a team member be reused, and with what disclosure?
2. Written statement from the owner licensing the listed files to this project.
3. Independent check of this audit by a teammate other than Member 1.
4. Team agreement to add NumPy and SciPy.
5. Rights decision on the reconstructed series. Until then the feature could only show the
   recorded summary values, not plots of the series.
6. Member 5 (independent scientific review): whether, and with what wording, a result that did
   not replicate should be shown at all.

## Sign-off

- Organizer ruling: PENDING
- Content and license audit checked by: PENDING
