from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.database import SessionLocal
from app.services.copilot import generate_copilot_response
from app.services.predictor import (
    calculate_astm_d341_viscosity,
    calculate_goodman_stress_ratio,
    calculate_rod_fall_limit_spm,
    calculate_vogel_inflow,
    compute_css_cycle_metrics,
    generate_dynamometer_card,
)

client = TestClient(app)


def test_astm_d341_viscosity_accuracy():
    """Verify ASTM D341 logarithmic standard accurately models Baghewala heavy crude."""
    # At 25°C (Reservoir initial temp), crude should be ultra-viscous bitumen (~15,000 cP)
    visc_25 = calculate_astm_d341_viscosity(25.0)
    assert 13000.0 <= visc_25 <= 16000.0, f"Expected ~15000 cP at 25°C, got {visc_25}"

    # At 60°C, early thermal mobilization occurs
    visc_60 = calculate_astm_d341_viscosity(60.0)
    assert 400.0 <= visc_60 <= 900.0, f"Expected 400-900 cP at 60°C, got {visc_60}"

    # At 120°C (Target CSS production lift temperature), crude collapses to pumpable level (~45 cP)
    visc_120 = calculate_astm_d341_viscosity(120.0)
    assert 35.0 <= visc_120 <= 60.0, f"Expected ~45 cP at 120°C, got {visc_120}"

    # At 280°C (Steam injection front), viscosity collapses to single digits
    visc_280 = calculate_astm_d341_viscosity(280.0)
    assert 5.0 <= visc_280 <= 15.0, f"Expected 5-15 cP at 280°C, got {visc_280}"

    # Monotonicity test: viscosity must strictly decrease as temperature increases
    assert visc_25 > visc_60 > visc_120 > visc_280


def test_goodman_stress_ratio():
    """Verify API RP 11L modified Goodman diagram fatigue stress calculations."""
    # Moderate load: 22,000 lbs peak, 8,000 lbs min on 1" rod (Area = 0.785 sq.in)
    ratio, eval_text = calculate_goodman_stress_ratio(pprl_lbs=22000.0, mprl_lbs=8000.0)
    assert 0.0 < ratio < 100.0
    assert "fatigue" in eval_text.lower() or "allowable" in eval_text.lower()

    # Extreme overload: 45,000 lbs peak load exceeds allowable endurance limit
    ratio_overload, eval_overload = calculate_goodman_stress_ratio(pprl_lbs=45000.0, mprl_lbs=4000.0)
    assert ratio_overload > 100.0
    assert "critical" in eval_overload.lower() or "overload" in eval_overload.lower()


def test_vogel_inflow_deliverability():
    """Verify Vogel's Inflow Performance Relationship deliverability equation."""
    # Lower casing pressure (lower bottom-hole pressure) yields higher reservoir inflow
    inflow_low_pwf = calculate_vogel_inflow(casing_pressure_psi=120.0)
    inflow_high_pwf = calculate_vogel_inflow(casing_pressure_psi=350.0)
    assert inflow_low_pwf > inflow_high_pwf
    assert inflow_low_pwf > 0.0


def test_rod_fall_velocity_limit():
    """Verify Stokes viscous drag correctly limits maximum SPM in cold vs hot crude."""
    # In cold heavy crude (15,000 cP), rod falls slowly, limiting maximum downstroke SPM
    spm_limit_cold = calculate_rod_fall_limit_spm(15000.0)
    # In hot mobile crude (45 cP), rod falls much faster, allowing higher SPM
    spm_limit_hot = calculate_rod_fall_limit_spm(45.0)

    assert spm_limit_cold < spm_limit_hot
    assert 4.0 <= spm_limit_cold <= 10.0
    assert spm_limit_hot >= 12.0


def test_gibbs_dynamometer_card_diagnostics():
    """Verify Gibbs wave equation dynamometer card profiles and indicated horsepower."""
    # Test Normal card
    card_normal = generate_dynamometer_card("SRP-001", card_type="Normal")
    assert card_normal["card_type"] == "Normal"
    assert card_normal["pump_fillage_pct"] >= 90.0
    assert card_normal["pprl_lbs"] > card_normal["mprl_lbs"]
    assert card_normal["indicated_pump_hp"] > 0.5
    assert "goodman_stress_ratio_pct" in card_normal

    # Test Fluid Pound card
    card_pound = generate_dynamometer_card("SRP-002", card_type="Fluid Pound")
    assert card_pound["card_type"] == "Fluid Pound"
    assert card_pound["pump_fillage_pct"] < 65.0
    assert "impact" in card_pound["diagnostic_message"].lower() or "underfillage" in card_pound["diagnostic_message"].lower()

    # Test Parted Rod card
    card_parted = generate_dynamometer_card("SRP-003", card_type="Parted Rod")
    assert card_parted["card_type"] == "Parted Rod"
    assert card_parted["pump_fillage_pct"] < 15.0
    assert card_parted["pprl_lbs"] < card_normal["pprl_lbs"] * 0.70


def test_copilot_well_reasoning_srp():
    """Verify Copilot produces deep Chain-of-Thought reasoning for SRP wellhead inquiry."""
    db = SessionLocal()
    try:
        resp = generate_copilot_response("Why is well SRP-004 in critical state?", db)
        assert resp["category"] == "well_diagnostic"
        answer = resp["answer"]
        # Verify 5 structured sections are present
        assert "1. Executive Findings" in answer
        assert "2. Step-by-Step Petro-Mechanical Reasoning" in answer
        assert "3. Explicit Engineering Assumptions" in answer
        assert "4. Predictive Projections" in answer
        assert "5. Prescriptive SCADA Dispatch" in answer
        # Verify specific technical constants are included
        assert "API Grade D" in answer or "18.0° API" in answer
        assert len(resp["suggested_actions"]) >= 2
    finally:
        db.close()


def test_copilot_well_reasoning_css():
    """Verify Copilot produces deep thermal twin reasoning for CSS wellhead inquiry."""
    db = SessionLocal()
    try:
        resp = generate_copilot_response("Diagnose CSS-101 thermal recovery", db)
        assert resp["category"] in ("well_diagnostic", "thermal_diagnostic")
        answer = resp["answer"]
        assert "Cyclic Steam Stimulation" in answer or "CSS" in answer
        assert "ASTM D341" in answer
        assert "Viscosity" in answer
        assert len(resp["suggested_actions"]) >= 2
    finally:
        db.close()


def test_copilot_cross_well_comparison():
    """Verify Copilot compares two wells side-by-side with mechanical divergence analysis."""
    db = SessionLocal()
    try:
        resp = generate_copilot_response("Compare SRP-001 and SRP-004", db)
        assert resp["category"] == "well_comparison"
        answer = resp["answer"]
        assert "SRP-001" in answer and "SRP-004" in answer
        assert "Operational Telemetry Comparison" in answer
        assert "Mechanical Loading Divergence" in answer or "Prescriptive Setpoint" in answer
    finally:
        db.close()


def test_copilot_what_if_simulation():
    """Verify Copilot evaluates hypothetical simulation scenarios with physical impacts."""
    db = SessionLocal()
    try:
        resp = generate_copilot_response("What if we increase stroke speed to 15 SPM on SRP-002?", db)
        assert resp["category"] == "simulation_sandbox"
        answer = resp["answer"]
        assert "15.0 SPM" in answer
        assert "Reservoir Inflow" in answer or "Vogel" in answer
        assert "Goodman" in answer or "Fluid Pound" in answer
    finally:
        db.close()


def test_copilot_physics_foundations():
    """Verify Copilot explains the Gibbs wave equation and ASTM D341 formulas accurately."""
    db = SessionLocal()
    try:
        resp_gibbs = generate_copilot_response("How does the Gibbs wave equation work for dynamometer cards?", db)
        assert "Gibbs" in resp_gibbs["answer"]
        assert "4,900" in resp_gibbs["answer"] or "wave equation" in resp_gibbs["answer"].lower()

        resp_astm = generate_copilot_response("Explain ASTM D341 viscosity equation in heavy oil", db)
        assert "ASTM D341" in resp_astm["answer"]
        assert "15,000" in resp_astm["answer"]
    finally:
        db.close()
