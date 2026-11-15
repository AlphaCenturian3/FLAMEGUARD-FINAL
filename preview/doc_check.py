"""Static checks that the demo documents match the launcher and the demo contract.

    python preview/doc_check.py          # exit 1 on any drift

No browser needed. It checks durable facts rather than incidental wording:
- every document named in preview/demo_contract.json exists;
- the launch card names the real launchers (which exist), the two real addresses, the alternate
  port and the commands it promises, and every `--flag` used in a documented command exists in
  preview/run.py;
- every critical phrase of the contract appears in at least one document, and both audience
  documents carry a "Never" section and the exact Blender disclaimer;
- the script has its six timed segments, stays within the word budget, and cites no specific FLEX
  test or number (no NASA measurement may appear in the demo documents).
`smoke.py` then checks that the running interface still shows the same phrases.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "preview" / "demo_contract.json"


def load_contract(repo: Path = REPO) -> dict:
    return json.loads((repo / "preview" / "demo_contract.json").read_text(encoding="utf-8"))


def read_docs(contract: dict, repo: Path = REPO) -> tuple[dict[str, str], list[str]]:
    docs, problems = {}, []
    for rel in contract["docs"]:
        path = repo / rel
        if path.is_file():
            docs[rel] = path.read_text(encoding="utf-8")
        else:
            problems.append(f"missing document {rel}")
    return docs, problems


def run_py_flags(repo: Path = REPO) -> set[str]:
    src = (repo / "preview" / "run.py").read_text(encoding="utf-8")
    return set(re.findall(r'add_argument\(\s*"(--[a-z][a-z-]*)"', src))


def check(contract: dict | None = None, repo: Path = REPO) -> list[str]:
    contract = contract or load_contract(repo)
    docs, problems = read_docs(contract, repo)
    everything = "\n".join(docs.values())
    launch = contract["launch"]
    card = docs.get("preview/LAUNCH_CARD.md", "")

    for rel in launch["launchers"]:
        if not (repo / rel).is_file():
            problems.append(f"launcher {rel} does not exist")
        if Path(rel).name not in card:
            problems.append(f"the launch card does not name {Path(rel).name}")
    for key in ("live_url", "fixture_url", "illustrations_url"):
        if launch[key] not in card:
            problems.append(f"the launch card is missing the address {launch[key]}")
    if (
        f"--port {launch['alternate_port']}" not in card
        or str(launch["alternate_port"]) not in card
    ):
        problems.append("the launch card does not explain the alternate port")
    if "8790" not in launch["live_url"] or "?fixtures=1" not in launch["fixture_url"]:
        problems.append("contract addresses no longer match the documented defaults")

    shot = launch.get("screenshot")
    if shot:
        shot_path = repo / shot
        if not shot_path.is_file() or shot_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            problems.append(f"screenshot {shot} is missing or not a PNG")
        if shot not in card:
            problems.append("the launch card does not reference its screenshot")

    flags = run_py_flags(repo)
    for cmd in launch["commands"]:
        for flag in re.findall(r"--[a-z][a-z-]*", cmd):
            if flag not in flags:
                problems.append(
                    f"contract command uses {flag}, which preview/run.py does not define"
                )
    for rel, text in docs.items():
        for line in text.splitlines():
            if "preview/run.py" in line or "preview\\run.py" in line:
                for flag in re.findall(r"(?<![\w-])--[a-z][a-z-]*", line):
                    if flag not in flags:
                        problems.append(
                            f"{rel}: documents {flag}, which preview/run.py does not define"
                        )
    port_default = re.search(
        r'"--port",\s*type=int,\s*default=(\d+)',
        (repo / "preview" / "run.py").read_text(encoding="utf-8"),
    )
    if not port_default or f":{port_default.group(1)}/" not in launch["live_url"]:
        problems.append("the documented live address does not use run.py's default port")

    for phrase in contract["documented_somewhere"]:
        if phrase not in everything:
            problems.append(f"no document mentions {phrase!r}")
    audience = contract["documented_in_every_audience_doc"]
    for rel in audience["docs"]:
        for phrase in audience["must_contain"]:
            if phrase not in docs.get(rel, ""):
                problems.append(f"{rel}: must contain {phrase!r}")
    for label in contract["ui"]["nav_labels"] + [contract["ui"]["demo_button"]]:
        if label.replace("&", "and") not in everything and label not in everything:
            problems.append(f"no document mentions the interface label {label!r}")

    script = docs.get("preview/PRESENTATION_SCRIPT.md", "")
    positions = [script.find(seg) for seg in contract["script"]["segments"]]
    if -1 in positions or positions != sorted(positions):
        problems.append("the script's six timed segments are missing or out of order")
    if len(script.split()) > contract["script"]["max_words"]:
        problems.append(f"the script exceeds {contract['script']['max_words']} words")
    for rel, text in docs.items():
        if re.search(r"FLEX\s*[-–]\s*\d{3}", text):
            problems.append(
                f"{rel}: cites a specific FLEX test; no NASA measurement may appear in the demo"
            )
        for forbidden in (
            "is a validated simulation",
            "validated physics shows",
            "NASA data shows",
            "according to NASA",
        ):
            for m in re.finditer(re.escape(forbidden), text, re.I):
                before = text[max(0, m.start() - 60) : m.start()].lower()
                if not re.search(r"never|not |no |don't|do not", before):
                    problems.append(f"{rel}: forbidden claim {forbidden!r} outside a negation")
    return problems


def main() -> int:
    problems = check()
    for p in problems:
        print(f"DOC DRIFT: {p}")
    if not problems:
        print("demo documents match the launcher and the demo contract")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
