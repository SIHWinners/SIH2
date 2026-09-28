from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_list_wells():
    response = client.get("/api/v1/wells")
    assert response.status_code == 200
    wells = response.json()
    assert isinstance(wells, list)
    assert len(wells) >= 7
    assert "SRP-001" in wells
    assert "CSS-101" in wells


def test_wells_detailed():
    response = client.get("/api/v1/wells/details")
    assert response.status_code == 200
    wells = response.json()
    assert len(wells) >= 7
    srp1 = next(w for w in wells if w["well_id"] == "SRP-001")
    assert srp1["well_type"] == "SRP"
    assert srp1["stroke_length_in"] > 0


def test_dashboard_status():
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 7
    for item in items:
        assert "well_id" in item
        assert item["status"] in ("healthy", "warning", "critical")


def test_dyno_card_endpoint():
    response = client.get("/api/v1/dyno-card/SRP-001")
    assert response.status_code == 200
    card = response.json()
    assert card["well_id"] == "SRP-001"
    assert "points" in card
    assert len(card["points"]) == 36
    assert card["pprl_lbs"] > card["mprl_lbs"]


def test_css_status_endpoint():
    response = client.get("/api/v1/css-status/CSS-101")
    assert response.status_code == 200
    css = response.json()
    assert css["well_id"] == "CSS-101"
    assert css["current_phase"] in ("INJECTION", "SOAKING", "PRODUCTION")
    assert css["reservoir_viscosity_cp"] > 0


def test_explain_endpoint():
    response = client.get("/api/v1/explain/SRP-001")
    assert response.status_code == 200
    explain = response.json()
    assert explain["well_id"] == "SRP-001"
    assert len(explain["top_drivers"]) > 0


def test_simulate_prediction():
    payload = {
        "well_id": "SRP-001",
        "casing_pressure": 210.0,
        "tubing_pressure": 140.0,
        "polished_rod_load": 225.0,
        "stroke_speed": 10.5,
        "motor_temp": 65.0,
    }
    response = client.post("/api/v1/predict/simulate", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert "optimal_speed" in res
    assert 4.0 <= res["optimal_speed"] <= 20.0
    assert "anomaly_score" in res
    assert "explanation" in res


def test_telemetry_ingestion():
    payload = {
        "well_id": "SRP-001",
        "casing_pressure": 205.0,
        "tubing_pressure": 142.0,
        "polished_rod_load": 228.0,
        "stroke_speed": 10.2,
        "motor_temp": 64.5,
    }
    response = client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["well_id"] == "SRP-001"
    assert "optimal_speed" in res


def test_weather_endpoint():
    response = client.get("/api/v1/weather")
    assert response.status_code == 200
    data = response.json()
    assert "ambient_temperature_c" in data
    assert "field_thermal_impact_advisory" in data


def test_copilot_chat_endpoint():
    payload = {"message": "Why is well SRP-004 in critical state?"}
    response = client.post("/api/v1/copilot/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 50
    assert "suggested_actions" in data


def test_well_report_endpoint():
    response = client.get("/api/v1/report/SRP-001")
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "mechanical_specs" in data
    assert data["well_id"] == "SRP-001"
