"""FLEX Table IX -> measured Finding JSON. STAGING ONLY, NOT REGISTERED, NOT EVIDENCE YET.

A deterministic, fail-closed transformation of the NASA-as-printed Table IX rows FLEX-001..010
(`data/curated/flex_tp2015216046_table_ix_001_010.csv`) and their quality flags into contract
Findings, following docs/proposals/flex-finding-derivation-design.md (PR #15).

    python tools/derive_flex_findings.py --stage /tmp/flex-staging

What it does NOT do, by construction (each is tested):
- it never writes under the repository's data/ folder, never edits data/manifest.json, the source
  CSV or the flags CSV, and never registers anything. Output goes to a new, empty staging folder
  with a STAGING_REPORT.json whose `registrable` is false until every gate in
  tools/flex_derivation_gates.json is closed by its owners;
- it does not enable comparisons, rankings or TARS conclusions; nothing reads the staging folder;
- it never guesses: a blank cell without a `not_available` flag, a flag that matches nothing, an
  unknown outcome, an unreadable number, or a note without a verifiable source passage is an
  error or a withheld Finding, never a default.

The original measurements and exclusions are preserved: values come from the exact source cell by
strict decimal parsing (a printed 0 stays 0, nothing is rounded, interpolated or converted except
mmHg -> kPa with the exact factor), and an excluded value (FLEX-010 burning rate, flag F042) is
emitted as null with an exclusion note, with its printed number appearing nowhere in the output.

Test identity and outcome (contract v0.2.2, rule S11): every Finding carries `test_id` (the
printed FLEX identifier, ASCII-normalised) and `test_outcome` (the printed `Test end` label),
checked against contracts/outcomes.json, which must be CONFIRMED. Nothing is inferred from other
values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("s10_sources", ROOT / "tools" / "s10_sources.py")
s10 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = s10
_spec.loader.exec_module(s10)

CSV_ID = "nasa-tp-2015-216046.table-ix.flex-001-010"
FLAGS_ID = CSV_ID + ".flags"
FINDINGS_ID = "nasa-tp-2015-216046.flex.findings"  # proposed manifest id; not registered here
INVESTIGATIONS_ID = "nasa-tp-2015-216046.flex.investigations"
INVESTIGATION_ID = "flex"
GATES_PATH = ROOT / "tools" / "flex_derivation_gates.json"
OUTCOMES_PATH = ROOT / "contracts" / "outcomes.json"
VOCABULARY_PATH = ROOT / "contracts" / "vocabulary.json"

# 1 mmHg = 133.322387415 Pa exactly (conventional definition); NOT the torr approximation.
KPA_PER_MMHG = Decimal("0.133322387415")

# (csv field, quantity, label used in statements), in the fixed output order.
QUANTITIES = [
    ("initial_droplet_diameter_mm", "initial_droplet_diameter", "initial droplet diameter"),
    (
        "visible_flame_extinction_diameter_mm",
        "visible_flame_extinction_diameter",
        "visible flame extinction diameter",
    ),
    ("burning_rate_constant_mm2_per_s", "burning_rate_constant", "burning rate constant"),
    ("burn_time_s", "burn_time", "burn time"),
]
EXPECTED_COLUMNS = [
    "flex_test",
    "flex_identifier",
    "test_date_as_printed",
    "test_date_iso",
    "test_time_gmt",
    "fuel",
    "ambient_pressure_mmhg",
    "o2_mole_fraction",
    "n2_mole_fraction",
    "co2_mole_fraction",
    "he_mole_fraction",
    "initial_droplet_diameter_mm",
    "visible_flame_extinction_diameter_mm",
    "burning_rate_constant_mm2_per_s",
    "burn_time_s",
    "test_end",
    "source_dash_fields",
    "source_printed_page",
    "source_pdf_page",
]
EXPECTED_TESTS = [f"FLEX-{n:03d}" for n in range(1, 11)]
# Flag fields that are not a mapped quantity. A `test_end` flag is about the printed outcome that
# every Finding of that test carries (outcomes.json conditions_of_use 6), so it attaches to all of
# them. `test_time_gmt` is metadata and never becomes a Finding.
OUTCOME_FIELD = "test_end"
METADATA_FIELDS = {"test_time_gmt"}
GAS_ORDER = [("CO2", "co2_mole_fraction"), ("He", "he_mole_fraction"), ("N2", "n2_mole_fraction")]


class DerivationError(ValueError):
    """The inputs cannot be derived from safely. Never swallowed, never defaulted."""


# --- strict parsing ----------------------------------------------------------------------------


def number(text: str, where: str):
    """A JSON number equal to the exact decimal in `text`, or DerivationError."""
    try:
        d = Decimal(text)
    except InvalidOperation as exc:
        raise DerivationError(f"{where}: {text!r} is not a number") from exc
    if not d.is_finite():
        raise DerivationError(f"{where}: {text!r} is not finite")
    if re.fullmatch(r"-?\d+", text):
        return int(d)
    value = float(d)
    if Decimal(repr(value)) != d:
        raise DerivationError(f"{where}: {text!r} is not exactly representable as a JSON number")
    return value


def pressure_kpa(mmhg: str, where: str):
    d = Decimal(mmhg) * KPA_PER_MMHG
    value = float(d)
    if Decimal(repr(value)) != d:
        raise DerivationError(f"{where}: converted pressure {d} is not exactly representable")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- inputs ------------------------------------------------------------------------------------


def load_manifest(root: Path) -> dict:
    return json.loads((root / "data" / "manifest.json").read_text(encoding="utf-8"))


def verified_input(root: Path, manifest: dict, entry_id: str, evidence_class: str) -> Path:
    """The registered, hash-verified file for a manifest id."""
    matches = [d for d in manifest.get("datasets", []) if d.get("id") == entry_id]
    if len(matches) != 1:
        raise DerivationError(f"manifest must have exactly one entry {entry_id!r}")
    entry = matches[0]
    if entry.get("evidence_class") != evidence_class:
        raise DerivationError(f"{entry_id}: evidence_class must be {evidence_class!r}")
    path = root / entry["path"]
    if not path.is_file():
        raise DerivationError(f"{entry_id}: file {entry['path']} is missing")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise DerivationError(f"{entry_id}: sha256 differs from the manifest; refusing to derive")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DerivationError(f"{entry_id}: not UTF-8") from exc
    if b"\r" in data:
        raise DerivationError(f"{entry_id}: contains CR; expected LF line endings")
    return path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise DerivationError(f"unexpected CSV columns: {reader.fieldnames}")
        rows = list(reader)
    tests = [r["flex_test"] for r in rows]
    if tests != EXPECTED_TESTS:
        raise DerivationError(f"expected exactly {EXPECTED_TESTS}, got {tests}")
    for r in rows:
        if any(v is None for v in r.values()):
            raise DerivationError(f"{r['flex_test']}: short row")
    return rows


def load_outcomes(path: Path = OUTCOMES_PATH) -> list[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("status") != "CONFIRMED":
        raise DerivationError(
            "contracts/outcomes.json is not CONFIRMED; test_outcome cannot be set"
        )
    outcomes = doc.get("outcomes")
    if not outcomes or not all(isinstance(o, str) and o for o in outcomes):
        raise DerivationError("contracts/outcomes.json has no usable outcome list")
    return outcomes


def load_gates(path: Path = GATES_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def registrable(gates: dict) -> bool:
    """True only when every gate is closed and every condition decision approved."""
    open_gates = [g for g in gates["gates"] if g["status"] != "closed"]
    unapproved = [c for c in gates["conditions"].values() if c["status"] != "approved"]
    return not open_gates and not unapproved


# --- conditions --------------------------------------------------------------------------------


def diluent_text(row: dict[str, str]) -> str | None:
    """Proposed (G7, unapproved) format: non-zero gases from the printed fractions, as printed."""
    parts = []
    for symbol, column in GAS_ORDER:
        text = row[column]
        if number(text, f"{row['flex_test']}.{column}") != 0:
            parts.append(f"{symbol} {text}")
    return "; ".join(parts) or None


def conditions(row: dict[str, str], gates: dict) -> dict:
    t = row["flex_test"]
    decisions = gates["conditions"]
    if set(decisions) != {"diluent", "fuel_or_material", "sample_geometry"}:
        raise DerivationError(
            "gates file must decide exactly diluent, fuel_or_material, sample_geometry"
        )
    fuel = row["fuel"].strip()
    return {
        "gravity_environment": "microgravity",  # ISS experiment; not partial gravity
        "oxygen_mole_fraction": number(row["o2_mole_fraction"], f"{t}.o2_mole_fraction"),
        "pressure_kpa": pressure_kpa(row["ambient_pressure_mmhg"], f"{t}.ambient_pressure_mmhg"),
        "flow_velocity_mm_s": None,  # no experimental velocity is reported
        "flow_configuration": None,  # no approved classification; free-floating is not "quiescent"
        "diluent": diluent_text(row) if decisions["diluent"]["use"] == "proposed" else None,
        "fuel_or_material": fuel if decisions["fuel_or_material"]["use"] == "as_printed" else None,
        "sample_geometry": None,  # needs an owner-approved source-grounded label
    }


# --- flags and notes ---------------------------------------------------------------------------


def applicable_flags(flags: list[dict[str, str]], test: str, field: str) -> list[dict[str, str]]:
    return [
        f for f in flags if f["flex_test"] == test and f["field"] in (field, "*", OUTCOME_FIELD)
    ]


def check_flag_accounting(flags: list[dict[str, str]], rows: list[dict[str, str]]) -> None:
    ids = [f["flag_id"] for f in flags]
    if len(ids) != len(set(ids)):
        raise DerivationError("duplicate flag ids")
    tests = {r["flex_test"] for r in rows}
    fields = {q[0] for q in QUANTITIES} | {"*", OUTCOME_FIELD} | METADATA_FIELDS
    for f in flags:
        if f["flex_test"] not in tests:
            raise DerivationError(f"{f['flag_id']}: unknown test {f['flex_test']}")
        if f["field"] not in fields:
            raise DerivationError(f"{f['flag_id']}: flag field {f['field']!r} maps to nothing")
        if f["field"] in METADATA_FIELDS and f["ranking_use"] != "not_available":
            raise DerivationError(f"{f['flag_id']}: only a dash may be flagged on metadata")


def note_source(flag: dict, sources: list[dict], proposals: dict) -> tuple[dict | None, str]:
    """(Source for a note, status). The note records the flag's own verbatim quote."""
    page = int(flag["source_printed_page"])
    quote = flag["source_quote"]
    key = (page, s10.normalize_text(quote))
    for src in sources:
        if (
            int(src["page"]) == page
            and src.get("quote")
            and key[1] in s10.normalize_text(src["quote"])
        ):
            return {**src, "quote": quote}, "registered"
    if key in proposals:
        return dict(proposals[key]), "proposed_unregistered"
    return None, "unavailable"


def make_note(flag: dict, source: dict, kinds: dict[str, str]) -> dict:
    return {
        "kind": kinds[flag["ranking_use"]],
        "note": flag["reason"],
        "generated_by": "FlameGuard-SI",
        "flag_ref": {"manifest_id": FLAGS_ID, "flag_id": flag["flag_id"]},
        "source": source,
    }


# --- findings ----------------------------------------------------------------------------------

_PREFIX = "NASA/TP-2015-216046 Table IX (printed p. 20)"


def statement(status: str, label: str, test: str, value, unit: str) -> str:
    if status == "reported":
        return f"{_PREFIX} reports a {label} of {value} {unit} for {test}, as printed."
    if status == "not_reported":
        return f"{_PREFIX} prints a dash (no value reported) for the {label} of {test}."
    return (
        f"{_PREFIX} lists a {label} for {test} that FlameGuard-SI excludes from use; "
        "see the exclusion note. No value is stated."
    )


def derive(root: Path = ROOT) -> dict:
    """Everything derivable from the registered inputs, plus what had to be withheld."""
    manifest = load_manifest(root)
    csv_path = verified_input(root, manifest, CSV_ID, "measured")
    flags_path = verified_input(root, manifest, FLAGS_ID, "interpretation")
    rows = read_rows(csv_path)
    flags = s10.load_flags(flags_path)
    check_flag_accounting(flags, rows)
    outcomes = load_outcomes(root / "contracts" / "outcomes.json")
    gates = load_gates(root / "tools" / "flex_derivation_gates.json")
    vocabulary = json.loads((root / "contracts" / "vocabulary.json").read_text(encoding="utf-8"))

    entry = next(d for d in manifest["datasets"] if d["id"] == CSV_ID)
    sources = list(entry["sources"])
    numeric_sources, _ = s10.split_sources(sources)
    if len(numeric_sources) != 1:
        raise DerivationError("expected exactly one numeric (Table IX) source")

    kinds = s10.note_kinds(root / "contracts" / "schemas" / "common.schema.json")
    passages = s10.passages(flags, kinds)
    status_by_key = s10.coverage(passages, sources)
    props = {}
    proposed_list, unproposable = [], []
    pdf_titles = gates.get("proposed_note_sources", {})
    for p in passages:
        if status_by_key[p.key] == "registered_quote":
            continue
        entry_key = f"{p.page}|{s10.normalize_text(p.quote)}"
        if entry_key in pdf_titles:
            proposal = {**pdf_titles[entry_key], "quote": p.quote}
            props[p.key] = proposal
            proposed_list.append(proposal)
        else:
            unproposable.append(p)

    findings, withheld, note_status = [], [], {"registered": 0, "proposed_unregistered": 0}
    accounted: set[str] = set()
    for line, row in enumerate(rows, start=2):  # physical CSV line numbers (header is line 1)
        test = row["flex_test"]
        dash_fields = set(filter(None, row["source_dash_fields"].split(";")))
        outcome = row["test_end"]
        if outcome not in outcomes:
            raise DerivationError(f"{test}: printed outcome {outcome!r} is not in outcomes.json")
        for field, quantity, label in QUANTITIES:
            unit = vocabulary["quantities"][quantity]["unit"]
            applicable = applicable_flags(flags, test, field)
            accounted.update(f["flag_id"] for f in applicable)
            uses = {f["ranking_use"] for f in applicable}
            cell = row[field]
            is_dash = field in dash_fields
            if is_dash != (cell == ""):
                raise DerivationError(f"{test}.{field}: blank cell and source_dash_fields disagree")
            flagged_dash = any(
                f["field"] == field and f["ranking_use"] == "not_available" for f in applicable
            )
            if flagged_dash != is_dash:
                raise DerivationError(
                    f"{test}.{field}: a dash needs its not_available flag, and only a dash"
                )
            if is_dash and "exclude" in uses:
                raise DerivationError(f"{test}.{field}: a dash cannot also be excluded")
            if "exclude" in uses:
                value_status, value = "excluded", None
            elif is_dash:
                value_status, value = "not_reported", None
            else:
                value_status, value = "reported", number(cell, f"{test}.{field}")

            notes, missing = [], []
            for f in sorted(applicable, key=lambda x: x["flag_id"]):
                if f["ranking_use"] == "not_available":
                    continue  # S10(c): no note; the finding is not_reported
                src, st = note_source(f, sources, props)
                if src is None:
                    missing.append(f["flag_id"])
                    continue
                note_status[st] += 1
                notes.append(make_note(f, src, kinds))
            fid = f"{INVESTIGATION_ID}.{test.lower()}.{quantity}"
            if missing:
                withheld.append(
                    {
                        "id": fid,
                        "reason": "a required note has no verifiable source passage",
                        "flags": missing,
                    }
                )
                continue
            finding = {
                "id": fid,
                "investigation_id": INVESTIGATION_ID,
                "evidence_class": "measured",
                "statement": statement(value_status, label, test, value, unit),
                "quantity": quantity,
                "value": value,
                "unit": unit,
                "value_status": value_status,
                "uncertainty": None,
                "conditions": conditions(row, gates),
                "provenance": {
                    "manifest_id": FINDINGS_ID,
                    "locator": (
                        f"NASA/TP-2015-216046, Table IX, printed p. 20 (PDF p. 26), {test}, "
                        f"field {field}, CSV line {line}"
                    ),
                    "sources": [dict(numeric_sources[0])],
                },
                "test_id": test,
                "test_outcome": outcome,
            }
            if notes:
                finding["curation_notes"] = notes
            findings.append(finding)

    unaccounted = sorted(
        {f["flag_id"] for f in flags}
        - accounted
        - {f["flag_id"] for f in flags if f["field"] in METADATA_FIELDS}
    )
    if unaccounted:
        raise DerivationError(f"flags that match no emitted quantity: {unaccounted}")

    investigation = {
        "id": INVESTIGATION_ID,
        "name": "Flame Extinguishment Experiment (FLEX)",
        "acronym": "FLEX",
        "platform": "ISS Combustion Integrated Rack / MDCA",
        "objectives": [],
        "relevant_environments": [],
        "datasets": [FINDINGS_ID],
        "sources": [dict(numeric_sources[0])],
    }
    return {
        "investigation": investigation,
        "findings": findings,
        "withheld": withheld,
        "note_sources": {
            "registered": note_status["registered"],
            "proposed_unregistered": note_status["proposed_unregistered"],
            "proposed": proposed_list,
            "unproposable": [
                {"page": p.page, "flags": list(p.flag_ids), "quote": p.quote} for p in unproposable
            ],
        },
        "inputs": {
            CSV_ID: sha256_file(csv_path),
            FLAGS_ID: sha256_file(flags_path),
            "manifest": sha256_file(root / "data" / "manifest.json"),
        },
        "gates": gates,
    }


# --- staging output ----------------------------------------------------------------------------


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def count_status(findings: list[dict]) -> dict:
    out: dict[str, int] = {}
    for f in findings:
        out[f["value_status"]] = out.get(f["value_status"], 0) + 1
    return out


def stage(out_dir: Path, root: Path = ROOT) -> dict:
    """Write the derivation into an empty folder outside data/. Registers nothing."""
    out_dir = out_dir.resolve()
    root = root.resolve()
    inside = [
        root / "data",
        root / "contracts",
        root / "tools",
        root / "backend",
        root / "frontend",
    ]
    if out_dir == root or any(out_dir == p or p in out_dir.parents for p in inside):
        raise DerivationError(
            "staging output must not be inside the repository's data/ or code folders"
        )
    if out_dir.exists() and any(out_dir.iterdir()):
        raise DerivationError(f"{out_dir} is not empty; refusing to overwrite")
    result = derive(root)
    (out_dir / "findings").mkdir(parents=True, exist_ok=True)
    investigations_text = dumps([result["investigation"]])
    findings_text = dumps(result["findings"])
    (out_dir / "investigations.json").write_text(
        investigations_text, encoding="utf-8", newline="\n"
    )
    (out_dir / "findings" / "flex.json").write_text(findings_text, encoding="utf-8", newline="\n")
    gates = result["gates"]
    open_gates = [g["id"] for g in gates["gates"] if g["status"] != "closed"]
    unapproved = sorted(k for k, c in gates["conditions"].items() if c["status"] != "approved")
    is_registrable = (
        registrable(gates)
        and not result["withheld"]
        and not result["note_sources"]["proposed_unregistered"]
        and not result["note_sources"]["unproposable"]
    )
    report = {
        "status": "STAGING ONLY. NOT REGISTERED. NOT EVIDENCE.",
        "registrable": is_registrable,
        "open_gates": open_gates,
        "unapproved_condition_decisions": unapproved,
        "counts": {
            "findings": len(result["findings"]),
            "by_value_status": count_status(result["findings"]),
        },
        "withheld": result["withheld"],
        "note_sources": result["note_sources"],
        "inputs_sha256": result["inputs"],
        "outputs_sha256": {
            "investigations.json": hashlib.sha256(investigations_text.encode("utf-8")).hexdigest(),
            "findings/flex.json": hashlib.sha256(findings_text.encode("utf-8")).hexdigest(),
        },
        "proposed_manifest_entries_not_applied": [
            {
                "id": INVESTIGATIONS_ID,
                "path": "data/curated/investigations.json",
                "evidence_class": "measured",
            },
            {
                "id": FINDINGS_ID,
                "path": "data/curated/findings/flex.json",
                "evidence_class": "measured",
            },
        ],
    }
    report_text = dumps(report)
    (out_dir / "STAGING_REPORT.json").write_text(report_text, encoding="utf-8", newline="\n")
    (out_dir / "NOT_REGISTERED.txt").write_text(
        "These files are a derivation preview. They are not registered in data/manifest.json, are "
        "not served by the API, and must not be shown or cited as NASA evidence until every gate "
        "in STAGING_REPORT.json is closed and the required scientific approvals exist.\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--stage", type=Path, required=True, help="new, empty folder outside data/")
    args = ap.parse_args(argv)
    try:
        report = stage(args.stage)
    except DerivationError as exc:
        print(f"derivation refused: {exc}")
        return 1
    print(
        json.dumps(
            {k: report[k] for k in ("status", "registrable", "counts", "open_gates")}, indent=2
        )
    )
    print(f"withheld findings: {len(report['withheld'])}; staged in {args.stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
