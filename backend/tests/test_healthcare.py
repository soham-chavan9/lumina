"""HIPAA workflow tests for backend.routes.healthcare_route (deterministic shells). No prior unit tests."""

def test_breach_clock(client):
    res = client.post(
        "/api/breach-clock",
        json={
            "description": "Lost unencrypted laptop containing ePHI for 120 patients",
            "discovered_at": "2026-11-01",
            "phi_involved": True,
            "individuals_affected": 120,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["notification_deadline"] == "2026-12-31"
    assert body["likely_reportable"] is True
    assert len(body["four_factor"]) == 4
    assert body["days_remaining"] is not None


def test_access_request(client):
    res = client.post(
        "/api/access-request",
        json={
            "request_type": "access",
            "received_at": "2026-11-01",
            "channel": "patient portal",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["statutory_deadline"] == "2026-12-01"
    assert len(body["checklist"]) >= 3


def test_baa_screen(client):
    res = client.post(
        "/api/baa-screen",
        json={
            "vendor_name": "CloudFax Co",
            "services": "fax transmission of clinical notes",
            "creates_receives_maintains_or_transmits_phi": True,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ba_likely_required"] is True
    assert body["risk_level"] == "High"
    assert len(body["required_clauses"]) >= 3


def test_access_request_validation(client):
    res = client.post(
        "/api/access-request",
        json={"request_type": "invalid", "received_at": "2026-11-01"},
    )
    assert res.status_code == 422

