"""Check data/manifest.json against the provenance rules in master spec section 2.

Exit code 0 means every entry passes; 1 means at least one violation (printed).
Run from the repository root:  python tools/check_data_provenance.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMULATION_LABEL = "Fluid and thermal transport model. No combustion chemistry."
ALLOWED_DIRS = {
    "measured": ("data/curated/",),
    "interpretation": ("data/curated/",),
    "illustrative_simulation": ("data/simulated/",),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(manifest: dict, root: Path = ROOT) -> list[str]:
    """Return a list of human-readable violations (empty if clean)."""
    errors: list[str] = []
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        return ["manifest: 'datasets' must be a list"]

    ids = [d.get("id") for d in datasets]
    for dup in sorted({i for i in ids if ids.count(i) > 1 and i is not None}):
        errors.append(f"{dup}: duplicate id")
    known = set(ids)

    for d in datasets:
        did = d.get("id", "<missing id>")
        cls = d.get("evidence_class")
        path = d.get("path", "")

        if cls not in ALLOWED_DIRS:
            errors.append(f"{did}: evidence_class must be one of {sorted(ALLOWED_DIRS)}")
            continue
        if d.get("fixture"):
            errors.append(f"{did}: fixtures belong in tests/fixtures, not the manifest")
        if not path.startswith(ALLOWED_DIRS[cls]) or ".." in Path(path).parts:
            errors.append(f"{did}: {cls} data must live under {ALLOWED_DIRS[cls][0]}")

        file = root / path
        if not file.is_file():
            errors.append(f"{did}: file not found: {path}")
        elif _sha256(file) != d.get("sha256"):
            errors.append(f"{did}: sha256 mismatch for {path}")

        if cls == "measured":
            sources = d.get("sources") or []
            if not sources:
                errors.append(f"{did}: measured data needs at least one source")
            for s in sources:
                for key in ("title", "url", "retrieved"):
                    if not s.get(key):
                        errors.append(f"{did}: source missing '{key}'")
            if not d.get("rights_status"):
                errors.append(f"{did}: measured data needs rights_status")
        elif cls == "interpretation":
            parents = d.get("derived_from") or []
            if not parents:
                errors.append(f"{did}: interpretation needs derived_from")
            for p in parents:
                if p not in known:
                    errors.append(f"{did}: derived_from unknown id '{p}'")
            if not d.get("method"):
                errors.append(f"{did}: interpretation needs method")
        elif cls == "illustrative_simulation":
            if d.get("label") != SIMULATION_LABEL:
                errors.append(f"{did}: simulation label must be exactly '{SIMULATION_LABEL}'")
            if not d.get("model") or not d.get("model_version"):
                errors.append(f"{did}: simulation needs model and model_version")
    return errors


def tracked_raw_files(root: Path = ROOT) -> list[str]:
    """Files under data/raw/ that git is tracking (only .gitkeep and README are allowed)."""
    try:
        out = subprocess.run(  # noqa: S603
            ["git", "ls-files", "data/raw"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    allowed = {"data/raw/.gitkeep", "data/raw/README.md"}
    return [f for f in out.splitlines() if f and f not in allowed]


def main() -> int:
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    errors = check_manifest(manifest)
    errors += [f"raw NASA file tracked by git: {f}" for f in tracked_raw_files()]
    if errors:
        print("Provenance check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"Provenance check passed ({len(manifest['datasets'])} datasets registered).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
