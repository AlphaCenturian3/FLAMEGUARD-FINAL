"""Output read from Chrome, Node or a child server is UTF-8 whatever the user's locale.

Found in the db916a1 integration run: with `text=True` and no encoding, Python decodes child output
with the locale's encoding. Under a C locale that crashed the browser tests (UnicodeDecodeError on
"·" and "—" in the dashboard), and on Windows (cp1252) it would turn them into mojibake, so text
checks such as "Excluded by FlameGuard-SI — value not shown" would fail. Every text-mode subprocess
in these files must name its encoding.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "tests" / "test_full_application.py",
    ROOT / "tests" / "backend" / "test_b7_frontend.py",
]


def calls_without_encoding(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"subprocess\.(?:run|Popen)\((?:[^()]|\([^()]*\))*\)", text, re.S):
        call = m.group(0)
        if "text=True" in call and "encoding=" not in call:
            out.append(call.splitlines()[0])
    return out


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_text_mode_subprocess_names_utf8(path):
    assert calls_without_encoding(path.read_text(encoding="utf-8")) == []


def test_the_checker_itself_notices_a_missing_encoding():
    assert calls_without_encoding("subprocess.run(cmd, capture_output=True, text=True)")
    assert not calls_without_encoding('subprocess.run(cmd, text=True, encoding="utf-8")')


@pytest.mark.skipif(
    not (ROOT / "frontend" / "index.html").is_file(),
    reason="NOT VERIFIED: frontend/ is not present in this tree",
)
def test_the_browser_tests_pass_under_a_non_utf8_locale():
    env = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONIOENCODING": ""}
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(FILES[0])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=ROOT,
        timeout=600,
        check=False,
    )
    tail = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-300:]
    assert done.returncode in (0, 5) and "UnicodeDecodeError" not in done.stdout, tail
