def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_sites_endpoint_returns_official_sites(client):
    response = client.get("/sites")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert len(body["data"]["sites"]) == 3
    assert body["meta"]["dataVersion"].startswith("official-")
    assert {site["dataReliability"] for site in body["data"]["sites"]} == {"official"}


def test_commercial_assets_endpoint_returns_issuer_coverage(client):
    response = client.get("/commercial-assets")
    assert response.status_code == 200
    body = response.json()
    assets = body["data"]["assets"]
    assert len(assets) >= 10
    assert body["meta"]["dataVersion"].startswith("official-")
    assert {"CICT", "Keppel REIT", "MPACT", "OUE REIT", "Suntec REIT"}.issubset(
        {asset["issuer"] for asset in assets}
    )


def test_assessment_endpoint_cache_metadata(client):
    first = client.get("/sites/site-queenstown-001/assessment")
    second = client.get("/sites/site-queenstown-001/assessment")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["meta"]["cache"]["hit"] is False
    assert second.json()["meta"]["cache"]["hit"] is True
    assert first.json()["data"]["assessment"]["comparableSummary"]["selectedCount"] >= 5


def test_commercial_assessment_endpoint_cache_metadata(client):
    first = client.get("/commercial-assets/cict-capitaspring/assessment")
    second = client.get("/commercial-assets/cict-capitaspring/assessment")
    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    assessment = first_body["data"]["assessment"]
    assert first_body["meta"]["cache"]["hit"] is False
    assert second.json()["meta"]["cache"]["hit"] is True
    assert assessment["asset"]["issuer"] == "CICT"
    assert assessment["metrics"]["latestValuation"]["valuationAmount"] == 1900000000
    assert assessment["metrics"]["valuationPsf"] is not None
    assert assessment["metrics"]["sameSubmarketEventCount"] >= 1


def test_memo_endpoint_returns_fallback_and_cache_metadata(client):
    first = client.post("/sites/site-queenstown-001/memo", json={"tone": "investment-committee"})
    second = client.post("/sites/site-queenstown-001/memo", json={"tone": "investment-committee"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["generation"]["provider"] == "fallback"
    assert first.json()["meta"]["cache"]["hit"] is False
    assert second.json()["meta"]["cache"]["hit"] is True


def test_commercial_memo_endpoint_returns_fallback_and_cache_metadata(client):
    first = client.post("/commercial-assets/cict-capitaspring/memo", json={"tone": "investment-committee"})
    second = client.post("/commercial-assets/cict-capitaspring/memo", json={"tone": "investment-committee"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["generation"]["provider"] == "fallback"
    assert first.json()["data"]["memo"]["executiveSummary"].startswith("CapitaSpring screens")
    assert first.json()["meta"]["cache"]["hit"] is False
    assert second.json()["meta"]["cache"]["hit"] is True


def test_unknown_site_returns_structured_error(client):
    response = client.get("/sites/unknown-site/assessment")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["requestId"]


def test_unknown_commercial_asset_returns_structured_error(client):
    response = client.get("/commercial-assets/unknown-asset/assessment")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["requestId"]
