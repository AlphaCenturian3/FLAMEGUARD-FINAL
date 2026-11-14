"""Generate the test_outcome rules from contracts/outcomes.json (the single source of truth).

    python contracts/build_outcome_rules.py            # rewrite the two schema files
    python contracts/build_outcome_rules.py --check    # exit 1 if they are out of date

It rewrites exactly two things, and nothing else:
  common.schema.json      $defs.test_outcome        the closed enum: [*outcomes, null]
  comparison.schema.json  the `comparable: true`    one rule per outcome value v:
                          allOf entry tagged        "no row with outcome v together with a row
                          x-generated-from-outcomes  whose outcome is a different string"

With an empty `outcomes` list the enum is [null] and no per-value rule is generated.
A test fails if the committed schemas differ from this script's output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE / "schemas"
TAG = "x-generated-from-outcomes"


def test_outcome_def(outcomes: list[str]) -> dict:
    return {
        "description": (
            "Closed vocabulary from contracts/outcomes.json, as printed by the source "
            "for the test. "
            "null means not reported. While that list is empty (status UNCONFIRMED) only null is "
            "valid. Never free text."
        ),
        "enum": [*outcomes, None],
    }


def per_value_rule(value: str) -> dict:
    """comparable:true must not mix `value` with any different reported outcome."""
    has = {"required": ["test_outcome"], "properties": {"test_outcome": {"const": value}}}
    other = {
        "required": ["test_outcome"],
        "properties": {"test_outcome": {"type": "string", "not": {"const": value}}},
    }
    return {
        TAG: value,
        "not": {
            "allOf": [
                {"properties": {"rows": {"contains": has}}},
                {"properties": {"rows": {"contains": other}}},
            ]
        },
    }


def generate(outcomes: list[str]) -> tuple[dict, list[dict]]:
    return test_outcome_def(outcomes), [per_value_rule(v) for v in outcomes]


def _dump(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def build() -> dict[Path, str]:
    registry = json.loads((HERE / "outcomes.json").read_text(encoding="utf-8"))
    outcomes = registry["outcomes"]
    if len(outcomes) != len(set(outcomes)) or any(
        not isinstance(o, str) or not o for o in outcomes
    ):
        raise SystemExit("outcomes.json: values must be unique, non-empty strings")
    enum_def, rules = generate(outcomes)

    common_path = SCHEMAS / "common.schema.json"
    common = json.loads(common_path.read_text(encoding="utf-8"))
    common["$defs"]["test_outcome"] = enum_def

    cmp_path = SCHEMAS / "comparison.schema.json"
    cmp = json.loads(cmp_path.read_text(encoding="utf-8"))
    comparable_true = next(
        r
        for r in cmp["allOf"]
        if r.get("if", {}).get("properties", {}).get("comparable", {}).get("const") is True
    )
    kept = [r for r in comparable_true["then"].get("allOf", []) if TAG not in r]
    comparable_true["then"]["allOf"] = [*kept, *rules]
    if not comparable_true["then"]["allOf"]:
        del comparable_true["then"]["allOf"]
    return {common_path: _dump(common), cmp_path: _dump(cmp)}


def main(argv: list[str]) -> int:
    out = build()
    stale = [p.name for p, text in out.items() if p.read_text(encoding="utf-8") != text]
    if "--check" in argv:
        if stale:
            print("out of date (run python contracts/build_outcome_rules.py):", ", ".join(stale))
            return 1
        print("outcome rules are up to date")
        return 0
    for path, text in out.items():
        path.write_text(text, encoding="utf-8")
    print("rewrote:", ", ".join(stale) or "nothing (already up to date)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
