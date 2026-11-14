import pytest
from fastapi.testclient import TestClient

from flameguard import CONTRACT_VERSION
from flameguard.api.app import PLANNED_ENDPOINTS, app

client = TestClient(app)


def test_health_matches_contract(validator_for):
    r = client.get("/api/health")
    assert r.status_code == 200
    validator_for("health.schema.json").validate(r.json())
    assert r.json()["contract_version"] == CONTRACT_VERSION


@pytest.mark.parametrize(("method", "path"), PLANNED_ENDPOINTS)
def test_planned_endpoints_return_501(validator_for, method, path):
    concrete = path.replace("{investigation_id}", "x").replace("{simulation_id}", "x")
    r = client.request(method, concrete)
    assert r.status_code == 501
    validator_for("error.schema.json").validate(r.json())
    assert r.json()["error"]["code"] == "not_implemented"
