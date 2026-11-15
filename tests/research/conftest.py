import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESEARCH_DOCS = ROOT / "docs" / "research" / "member5"
CRITERIA_FILE = ROOT / "config" / "research_relevance_criteria_v1.proposed.json"
FIXTURE_FILE = ROOT / "tests" / "fixtures" / "research" / "fixture_evidence.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def real_evidence() -> list[dict]:
    return _load(RESEARCH_DOCS / "evidence_reported.json")["records"]


@pytest.fixture
def real_cards() -> list[dict]:
    return _load(RESEARCH_DOCS / "insight_cards.json")["cards"]


@pytest.fixture
def register() -> list[dict]:
    return _load(RESEARCH_DOCS / "investigations.json")["investigations"]


@pytest.fixture
def criteria() -> dict:
    return _load(CRITERIA_FILE)


@pytest.fixture
def fixtures() -> list[dict]:
    return _load(FIXTURE_FILE)["records"]


@pytest.fixture
def fx(fixtures):
    """Deep copy of one fixture record by id, safe to mutate."""
    by_id = {r["id"]: r for r in fixtures}
    return lambda rid: copy.deepcopy(by_id[rid])
