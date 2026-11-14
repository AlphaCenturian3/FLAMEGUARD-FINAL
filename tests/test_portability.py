"""Portability guards.

Python's default text encoding is the platform locale (cp1252 on most Windows
machines), and the spec and schemas contain non-ASCII text. Every text read or
write in repository code must name UTF-8, so tests pass on Windows as well as on
Linux CI.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = ("backend", "tests", "tools")
UNPINNED = re.compile(r"\.(read_text|write_text)\((?![^)]*encoding=)[^)]*\)")
OPEN_TEXT = re.compile(r"(?<![\w.])open\((?![^)]*(encoding=|[\"']\w*b\w*[\"']))[^)]*\)")


def _python_files():
    for d in CODE_DIRS:
        yield from (ROOT / d).rglob("*.py")


def test_text_io_names_utf8():
    offenders = []
    for path in _python_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if UNPINNED.search(line) or OPEN_TEXT.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert offenders == []


def test_shared_docs_really_contain_non_ascii():
    """Keeps the guard above meaningful: these files would fail under cp1252."""
    spec = (ROOT / "FLAMEGUARD_MASTER_SPEC.md").read_bytes()
    assert any(b > 0x7F for b in spec)
