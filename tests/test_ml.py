from __future__ import annotations

import numpy as np
import pytest

from app.services.predictor import (
    compute_css_cycle_metrics,
    compute_shap_feature_importance,
    generate_dynamometer_card,
    infer_and_score,
    load_models,
)


def test_models_load():
    anomaly_model, regressor_model, background = load_models()
    assert anomaly_model is not None
    assert regressor_model is not None
    assert background is not None


def test_inference_and_scoring():
    raw_payload = {
        "casing_pressure": 200.0,
        "tubing_pressure": 140.0,
        "polished_rod_load": 220.0,
        "stroke_speed": 10.0,
        "motor_temp": 65.0,
    }
    result = infer_and_score(raw_payload, "SRP-001", [])
    assert "predicted_anomaly" in result
    assert "optimal_speed" in result
    assert 4.0 <= result["optimal_speed"] <= 20.0
    assert 0.0 <= result["anomaly_score"] <= 1.0
    assert len(result["explanation"]) > 0


def test_dynamometer_card_physics():
    card = generate_dynamometer_card("SRP-001", stroke_length_in=120.0, current_load_kn=230.0, stroke_speed_spm=10.0)
    assert card["well_id"] == "SRP-001"
    assert card["stroke_length_in"] == 120.0
    assert card["pprl_lbs"] > card["mprl_lbs"]
    assert len(card["points"]) == 36
    assert card["indicated_pump_hp"] > 0


def test_css_viscosity_decay():
    css_hot = compute_css_cycle_metrics("CSS-101", steam_temp_c=250.0, phase="INJECTION")
    css_cold = compute_css_cycle_metrics("CSS-101", steam_temp_c=60.0, phase="PRODUCTION")
    # Viscosity should be much lower at 250°C than at 60°C
    assert css_hot["reservoir_viscosity_cp"] < css_cold["reservoir_viscosity_cp"]
    assert css_hot["cumulative_steam_injected_tons"] > 0


def test_shap_feature_importance():
    sample_vector = [200.0, 140.0, 220.0, 10.0, 65.0] * 3
    shap_vals = compute_shap_feature_importance(sample_vector)
    assert isinstance(shap_vals, dict)
    assert len(shap_vals) > 0
