"""Re-check that every quoted source text still appears word-for-word at its URL.

Usage (needs network; not part of the offline test suite)::

    python -m research.verify_sources docs/research/member5/evidence_reported.json \
        docs/research/member5/investigations.json

NTRS citation pages are rendered by JavaScript, so for ``ntrs.nasa.gov/citations/<id>``
the public NTRS API record (title and abstract) is checked instead. The comparison
normalises whitespace and HTML entities only. PDF sources are not parsed (that would need
a new dependency) and are reported as ``MANUAL``; check them by hand and log the result.
Exit code 0 means no quote failed. Nothing is downloaded to the repository.
"""

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

_NTRS = re.compile(r"^https://ntrs\.nasa\.gov/citations/(\d+)$")
_USER_AGENT = "FlameGuard-SI citation check"


def _normalise(text: str) -> str:
    text = html.unescape(text).replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


class ManualCheckRequired(Exception):
    """The source is a format this tool does not parse (PDF); a person must check it."""


def fetch_text(url: str) -> str:
    match = _NTRS.match(url)
    fetch_url = f"https://ntrs.nasa.gov/api/citations/{match.group(1)}" if match else url
    if not fetch_url.startswith("https://"):
        raise ValueError(f"refusing non-https url: {url}")
    if fetch_url.lower().endswith(".pdf"):
        raise ManualCheckRequired("PDF source")
    # S310: the scheme is checked to be https on the line above.
    request = urllib.request.Request(fetch_url, headers={"User-Agent": _USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        if "pdf" in (response.headers.get("Content-Type") or "").lower():
            raise ManualCheckRequired("PDF source")
        raw = response.read().decode("utf-8", errors="replace")
    if match:
        record = json.loads(raw)
        return _normalise(f"{record.get('title') or ''} {record.get('abstract') or ''}")
    raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    return _normalise(re.sub(r"(?s)<[^>]+>", " ", raw))


def verify(path: Path) -> list[tuple[str, str, bool | None, str]]:
    """Return (record id, url, found, note). ``found`` is None when a manual check is needed."""
    document = json.loads(path.read_text(encoding="utf-8"))
    records = document.get("records") or document.get("investigations") or []
    cache: dict[str, str] = {}
    results = []
    for record in records:
        for source in record.get("sources", []):
            quote = source.get("quote")
            if not quote:
                continue
            url = source["url"]
            try:
                if url not in cache:
                    cache[url] = fetch_text(url)
                found = _normalise(quote) in cache[url]
                note = "found" if found else "NOT FOUND"
            except ManualCheckRequired as exc:
                found, note = None, f"MANUAL ({exc})"
            except Exception as exc:  # noqa: BLE001 - report any fetch failure
                found, note = False, f"fetch failed: {exc}"
            results.append((record["id"], url, found, note))
    return results


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    results = [r for arg in argv[1:] for r in verify(Path(arg))]
    for rid, url, _found, note in results:
        print(f"{note:>10}  {rid}  {url}")
    found = sum(1 for r in results if r[2] is True)
    manual = sum(1 for r in results if r[2] is None)
    failed = sum(1 for r in results if r[2] is False)
    print(f"{found}/{len(results)} quotes verified; {manual} need manual check; {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
