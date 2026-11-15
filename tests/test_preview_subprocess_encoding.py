"""The preview reads Chrome, Node and pip output as UTF-8 whatever the user's locale.

With `text=True` and no encoding Python decodes with the locale's encoding: a C locale crashes on
the dashboard's "·" and "—", and Windows (cp1252) turns them into mojibake, so the smoke check
"Excluded by FlameGuard-SI — value not shown" would fail on the owner's Windows machine. Found in
the db916a1 integration run.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "preview").glob("*.py"))


def calls_without_encoding(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"subprocess\.(?:run|Popen)\((?:[^()]|\([^()]*\))*\)", text, re.S):
        call = m.group(0)
        if "text=True" in call and "encoding=" not in call:
            out.append(call.splitlines()[0])
    return out


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_text_mode_subprocess_in_the_preview_names_utf8(path):
    assert calls_without_encoding(path.read_text(encoding="utf-8")) == []


def test_the_checker_notices_a_missing_encoding():
    assert calls_without_encoding("subprocess.run(cmd, capture_output=True, text=True)")
    assert not calls_without_encoding('subprocess.run(cmd, text=True, encoding="utf-8")')
