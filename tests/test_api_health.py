from src.config import AppConfig
from src.extract_311 import fetch_incremental_data


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_api_health_request_shape(monkeypatch):
    seen = {"calls": 0, "params": None, "headers": None, "json": None}

    def fake_post(url, params=None, headers=None, json=None, timeout=0):
        seen["calls"] += 1
        seen["params"] = params
        seen["headers"] = headers
        seen["json"] = json
        return DummyResponse({"results": []})

    monkeypatch.setattr("src.extract_311.requests.post", fake_post)

    cfg = AppConfig(page_size=100, max_pages=1, app_token="demo_token")
    rows = fetch_incremental_data(cfg, "2026-05-04T00:00:00+00:00")

    assert rows == []
    assert seen["calls"] == 1
    assert seen["params"]["pageNumber"] == 1
    assert seen["params"]["pageSize"] == 100
    assert seen["params"]["app_token"] == "demo_token"
    assert seen["headers"]["X-App-Token"] == "demo_token"
    assert "created_date >" in seen["json"]["query"]
    assert "LIMIT 100 OFFSET 0" in seen["json"]["query"]
