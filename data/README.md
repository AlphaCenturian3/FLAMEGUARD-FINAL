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

The manifest is empty at initialization. **No NASA data has been ingested yet.**

Never fabricate, estimate, or gap-fill experimental values. A missing value stays `null`.
