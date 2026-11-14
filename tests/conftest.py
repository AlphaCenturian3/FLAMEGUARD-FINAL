import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"

# Tests never use a real AI key.
os.environ["FLAMEGUARD_AI_API_KEY"] = ""


def _registry() -> Registry:
    resources = []
    for p in SCHEMAS.glob("*.schema.json"):
        doc = json.loads(p.read_text())
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


@pytest.fixture(scope="session")
def validator_for():
    registry = _registry()

    def make(schema_name: str) -> Draft202012Validator:
        schema = json.loads((SCHEMAS / schema_name).read_text())
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema, registry=registry)

    return make
