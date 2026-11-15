"""The demo documents must not drift from the launcher or the demo contract (preview/doc_check.py).

Each test damages a throwaway copy of the preview documentation in one way a careless edit could,
and requires `doc_check.check` to report it. The browser half of the contract (does the interface
still show these phrases?) runs in `python preview/run.py --smoke`.
"""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("doc_check", ROOT / "preview" / "doc_check.py")
dc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = dc
_spec.loader.exec_module(dc)


@pytest.fixture
def repo(tmp_path):
    out = tmp_path / "repo"
    shutil.copytree(ROOT / "preview", out / "preview", ignore=shutil.ignore_patterns("__pycache__"))
    return out


def edit(repo, rel, fn):
    path = repo / rel
    text = path.read_text(encoding="utf-8")
    new = fn(text)
    assert new != text, "the edit changed nothing"
    path.write_text(new, encoding="utf-8")


def problems(repo):
    return dc.check(repo=repo)


def test_the_shipped_documents_match_the_launcher_and_the_contract():
    assert dc.check() == []


def test_a_missing_document_or_launcher_is_reported(repo):
    (repo / "preview/PRESENTATION_SCRIPT.md").unlink()
    assert any("missing document" in p for p in problems(repo))
    (repo / "preview/Start-Preview-Mac.command").unlink()
    assert any(
        "launcher preview/Start-Preview-Mac.command does not exist" in p for p in problems(repo)
    )


@pytest.mark.parametrize(
    "old",
    ["http://127.0.0.1:8790/?fixtures=1", "Start-Preview-Windows.bat", "--port 8791"],
)
def test_the_launch_card_must_keep_its_addresses_launchers_and_alternate_port(repo, old):
    edit(repo, "preview/LAUNCH_CARD.md", lambda t: t.replace(old, "REMOVED"))
    assert problems(repo), old


def test_a_documented_flag_that_the_launcher_does_not_have_is_reported(repo):
    edit(
        repo,
        "preview/DEMO.md",
        lambda t: t.replace(
            "python preview/run.py --port 8791 --smoke", "python preview/run.py --port 8791 --turbo"
        ),
    )
    assert any("--turbo" in p for p in problems(repo))


def test_a_renamed_launcher_flag_breaks_the_documented_commands(repo):
    edit(repo, "preview/run.py", lambda t: t.replace('"--smoke"', '"--selftest"'))
    assert any("--smoke" in p for p in problems(repo))


def test_a_changed_default_port_breaks_the_documented_live_address(repo):
    edit(repo, "preview/run.py", lambda t: t.replace("default=8790", "default=9000"))
    assert any("default port" in p for p in problems(repo))


@pytest.mark.parametrize(
    "phrase",
    [
        "FIXTURE DATA. NOT NASA DATA.",
        "No investigations available",
        "Start 90-second demo",
        "value not shown",
        "HTTP 501",
    ],
)
def test_every_critical_phrase_must_be_documented_somewhere(repo, phrase):
    for doc in ("LAUNCH_CARD", "PRESENTATION_SCRIPT", "DEMO"):
        edit_if = (repo / f"preview/{doc}.md").read_text(encoding="utf-8")
        if phrase in edit_if:
            (repo / f"preview/{doc}.md").write_text(
                edit_if.replace(phrase, "REDACTED"), encoding="utf-8"
            )
    assert any(repr(phrase) in p for p in problems(repo)), phrase


def test_both_audience_documents_must_carry_the_blender_disclaimer_and_a_never_section(repo):
    disclaimer = "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data."
    edit(repo, "preview/PRESENTATION_SCRIPT.md", lambda t: t.replace(disclaimer, "illustration"))
    assert any("PRESENTATION_SCRIPT.md: must contain" in p for p in problems(repo))
    edit(
        repo,
        "preview/LAUNCH_CARD.md",
        lambda t: t.replace("## Never claim", "## Claims").replace("Never", "Do not"),
    )
    assert any("LAUNCH_CARD.md: must contain 'Never'" in p for p in problems(repo))


def test_the_script_keeps_six_ordered_segments_and_a_word_budget(repo):
    edit(repo, "preview/PRESENTATION_SCRIPT.md", lambda t: t.replace("## 1:15 to 2:15", "## 9:99"))
    assert any("six timed segments" in p for p in problems(repo))
    contract = json.loads((repo / "preview/demo_contract.json").read_text(encoding="utf-8"))
    contract["script"]["max_words"] = 50
    assert any("exceeds 50 words" in p for p in dc.check(contract, repo))


def test_no_document_may_cite_a_specific_flex_test(repo):
    edit(repo, "preview/DEMO.md", lambda t: t + "\nFLEX-004 showed it.\n")
    assert any("cites a specific FLEX test" in p for p in problems(repo))
    edit(repo, "preview/LAUNCH_CARD.md", lambda t: t + "\nFLEX–010 too.\n")
    assert sum("cites a specific FLEX test" in p for p in problems(repo)) == 2


def test_forbidden_claims_are_caught_outside_a_negation_but_allowed_inside_one(repo):
    edit(repo, "preview/DEMO.md", lambda t: t + "\nNASA data shows the flame is smaller.\n")
    assert any("forbidden claim 'NASA data shows'" in p for p in problems(repo))
    clean = repo / "preview/DEMO.md"
    clean.write_text(
        clean.read_text(encoding="utf-8").replace(
            "NASA data shows the flame is smaller.", "Never say NASA data shows anything."
        ),
        encoding="utf-8",
    )
    assert not any("forbidden claim" in p for p in problems(repo))


def test_an_interface_label_that_disappears_from_every_document_is_reported(repo):
    contract = json.loads((repo / "preview/demo_contract.json").read_text(encoding="utf-8"))
    contract["ui"]["nav_labels"].append("Quantum Dashboard")
    assert any("Quantum Dashboard" in p for p in dc.check(contract, repo))


def test_the_contract_lists_the_same_demo_steps_as_the_smoke_walkthrough():
    contract = dc.load_contract()
    assert contract["ui"]["demo_steps"] == [
        "Discover",
        "Compare",
        "Rank",
        "Interpret",
        "Safety Insight",
    ]
    smoke = (ROOT / "preview" / "smoke.py").read_text(encoding="utf-8")
    assert 'DEMO["ui"]["demo_steps"]' in smoke, (
        "the walkthrough check reads the contract, not a copy"
    )


def test_a_contract_command_with_an_unknown_flag_is_reported(repo):
    contract = json.loads((repo / "preview/demo_contract.json").read_text(encoding="utf-8"))
    contract["launch"]["commands"].append("python preview/run.py --bogus")
    assert any("--bogus" in p for p in dc.check(contract, repo))


def test_the_launch_card_screenshot_must_exist_be_a_png_and_be_referenced(repo):
    (repo / "preview/screenshots/fixture-excluded-finding.png").write_bytes(b"not a png")
    assert any("not a PNG" in p for p in problems(repo))
    (repo / "preview/screenshots/fixture-excluded-finding.png").unlink()
    assert any("missing or not a PNG" in p for p in problems(repo))
    edit(
        repo,
        "preview/LAUNCH_CARD.md",
        lambda t: t.replace("preview/screenshots/fixture-excluded-finding.png", "REMOVED"),
    )
    assert any("does not reference its screenshot" in p for p in problems(repo))
