# Data

Owner: `feat/nasa-data-tars`. Rules: master spec §2.

| Folder | Contents | In git? |
|---|---|---|
| `raw/` | Original NASA downloads (PSI, NTRS, images, video) | **No**, git-ignored until rights are reviewed |
| `curated/` | `measured` and `interpretation` files used by the app | Yes, once registered and checked |
| `simulated/` | `illustrative_simulation` outputs, always labelled | Yes |

Every file in `curated/` or `simulated/` must have an entry in `manifest.json` (schema: `contracts/schemas/data_manifest.schema.json`). Run:

```bash
python tools/check_data_provenance.py
```

## Registered datasets

| Manifest id | What | Docs |
|---|---|---|
| `nasa-tp-2015-216046.table-ix.flex-001-010` | FLEX Table IX, tests FLEX-001 to FLEX-010, transcribed from NASA/TP-2015-216046 (`measured`) | [`docs/flex_table_ix.md`](docs/flex_table_ix.md) |
| `nasa-tp-2015-216046.table-ix.flex-001-010.flags` | Per-cell exclusion and caution flags for the rows above, each with a verbatim source quote (`interpretation`) | [`docs/flex_table_ix.md`](docs/flex_table_ix.md#exclusion-and-caution-flags) |

To re-verify the FLEX extract against the original PDF (local only, needs PyMuPDF), see `tools/verify_flex_table_ix.py`.

Curated and simulated files are stored byte-for-byte (`data/.gitattributes`) so their SHA-256 matches on every platform.

Never fabricate, estimate, or gap-fill experimental values. A missing value stays `null`.
