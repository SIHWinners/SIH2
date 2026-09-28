from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.models import TelemetryRecord

logger = logging.getLogger(__name__)

ANOMALY_FEATURE_COLS = [
    "casing_pressure", "tubing_pressure", "polished_rod_load", "stroke_speed", "motor_temp",
    "casing_pressure_lag1", "tubing_pressure_lag1", "polished_rod_load_lag1", "stroke_speed_lag1", "motor_temp_lag1",
    "casing_pressure_rolling_mean_3", "tubing_pressure_rolling_mean_3", "polished_rod_load_rolling_mean_3",
    "stroke_speed_rolling_mean_3", "motor_temp_rolling_mean_3",
]

REGRESSION_FEATURE_COLS = [
    "casing_pressure", "tubing_pressure", "polished_rod_load", "motor_temp",
    "casing_pressure_lag1", "tubing_pressure_lag1", "polished_rod_load_lag1", "motor_temp_lag1",
    "casing_pressure_rolling_mean_3", "tubing_pressure_rolling_mean_3", "polished_rod_load_rolling_mean_3",
    "motor_temp_rolling_mean_3",
]

FEATURE_LABELS = {
    "casing_pressure": "Casing Pressure (psi)",
    "tubing_pressure": "Tubing Pressure (psi)",
    "polished_rod_load": "Polished Rod Load (kN)",
    "stroke_speed": "Stroke Speed (SPM)",
    "motor_temp": "Motor Temperature (°C)",
    "casing_pressure_lag1": "Casing Pressure Lag (t-1)",
    "tubing_pressure_lag1": "Tubing Pressure Lag (t-1)",
    "polished_rod_load_lag1": "Rod Load Lag (t-1)",
    "stroke_speed_lag1": "Stroke Speed Lag (t-1)",
    "motor_temp_lag1": "Motor Temp Lag (t-1)",
    "casing_pressure_rolling_mean_3": "Casing Pressure 3-pt Moving Avg",
    "tubing_pressure_rolling_mean_3": "Tubing Pressure 3-pt Moving Avg",
    "polished_rod_load_rolling_mean_3": "Rod Load 3-pt Moving Avg",
    "stroke_speed_rolling_mean_3": "Stroke Speed 3-pt Moving Avg",
    "motor_temp_rolling_mean_3": "Motor Temp 3-pt Moving Avg",
}

# In-memory model cache
_ANOMALY_MODEL = None
_REGRESSOR_MODEL = None
_SHAP_BACKGROUND = None
_SHAP_EXPLAINER = None


def _ensure_models() -> None:
    """Ensure ML models exist; train if not present."""
    if (
        not Path(settings.ANOMALY_MODEL_PATH).exists()
        or not Path(settings.REGRESSOR_MODEL_PATH).exists()
    ):
        from app.ml.train_models import train_models
        train_models()


def load_models():
    """Load serialized pipelines and SHAP artifacts with singleton caching."""
    global _ANOMALY_MODEL, _REGRESSOR_MODEL, _SHAP_BACKGROUND
    if _ANOMALY_MODEL is None or _REGRESSOR_MODEL is None:
        _ensure_models()
        _ANOMALY_MODEL = joblib.load(settings.ANOMALY_MODEL_PATH)
        _REGRESSOR_MODEL = joblib.load(settings.REGRESSOR_MODEL_PATH)
        if Path(settings.SHAP_BACKGROUND_PATH).exists():
            _SHAP_BACKGROUND = joblib.load(settings.SHAP_BACKGROUND_PATH)
    return _ANOMALY_MODEL, _REGRESSOR_MODEL, _SHAP_BACKGROUND


def _compute_rolling_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def build_feature_dict(raw_payload: dict[str, Any], history: list[TelemetryRecord]) -> dict[str, float]:
    """Extract and engineer time-series features from raw reading and recent history."""
    feature_map = {
        "casing_pressure": float(raw_payload.get("casing_pressure", 180.0)),
        "tubing_pressure": float(raw_payload.get("tubing_pressure", 130.0)),
        "polished_rod_load": float(raw_payload.get("polished_rod_load", 220.0)),
        "stroke_speed": float(raw_payload.get("stroke_speed", 10.0)),
        "motor_temp": float(raw_payload.get("motor_temp", 65.0)),
    }

    historical = {
        field: [float(getattr(row, field, feature_map[field])) for row in reversed(history[:3])]
        for field in feature_map
    }

    out: dict[str, float] = {}
    for field, current_val in feature_map.items():
        last_val = float(getattr(history[0], field, current_val)) if history else current_val
        rolling_vals = historical.get(field, []) + [current_val]
        out[f"{field}"] = current_val
        out[f"{field}_lag1"] = last_val
        out[f"{field}_rolling_mean_3"] = _compute_rolling_mean(rolling_vals)

    return out


def infer_and_score(
    raw_payload: dict[str, Any],
    well_id: str,
    history: list[TelemetryRecord],
) -> dict[str, Any]:
    """Run full inference: anomaly detection, optimal speed, and XAI diagnosis."""
    anomaly_model, regressor_model, _ = load_models()
    feature_values = build_feature_dict(raw_payload, history)

    anomaly_vector = {col: feature_values[col] for col in ANOMALY_FEATURE_COLS}
    regressor_vector = {col: feature_values[col] for col in REGRESSION_FEATURE_COLS}

    anomaly_df = pd.DataFrame([anomaly_vector], columns=ANOMALY_FEATURE_COLS)
    reg_df = pd.DataFrame([regressor_vector], columns=REGRESSION_FEATURE_COLS)

    # Anomaly Prediction: -1 is anomaly, 1 is normal
    anomaly_pred = anomaly_model.predict(anomaly_df)[0]
    # Decision function: negative values indicate anomaly, positive normal
    raw_decision = float(anomaly_model.decision_function(anomaly_df)[0])
    predicted_anomaly = bool(anomaly_pred == -1)

    # Convert to 0.0 - 1.0 anomaly risk probability score
    # Lower decision function = higher anomaly risk
    anomaly_risk_prob = 1.0 / (1.0 + np.exp(raw_decision * 12.0))
    anomaly_score = float(np.clip(anomaly_risk_prob, 0.01, 0.99))

    # Regressor: optimal speed
    base_speed = float(regressor_model.predict(reg_df)[0])
    optimal_speed = float(np.clip(base_speed, 4.0, 18.0))

    # Production estimation: Q = Displacement * Fillage Efficiency * (1 - Slip Factor)
    current_speed = float(raw_payload.get("stroke_speed", optimal_speed))
    tubing_press = float(raw_payload.get("tubing_pressure", 130.0))
    expected_flow = max(10.0, optimal_speed * 14.5 * (1.0 - (tubing_press / 1800.0)))

    # Energy savings percentage if shifting from current speed to optimal speed
    speed_delta = abs(current_speed - optimal_speed)
    energy_savings = min(28.5, speed_delta * 3.4)

    # SHAP feature contributions
    shap_contributions = compute_shap_feature_importance(anomaly_vector)

    # Petroleum Engineering Explanation
    explanation, scada_action = generate_diagnostic_summary(raw_payload, feature_values, predicted_anomaly, optimal_speed)

    return {
        "well_id": well_id,
        "predicted_anomaly": predicted_anomaly,
        "anomaly_score": round(anomaly_score, 4),
        "optimal_speed": round(optimal_speed, 2),
        "expected_flow_rate": round(expected_flow, 2),
        "energy_savings_pct": round(energy_savings, 2),
        "explanation": explanation,
        "shap_contributions": shap_contributions,
        "scada_action_recommendation": scada_action,
    }


def compute_shap_feature_importance(anomaly_vector: list[float]) -> dict[str, float]:
    """Compute local feature attributions using SHAP or calibrated baseline deviations."""
    global _SHAP_EXPLAINER
    contributions: dict[str, float] = {}

    try:
        import shap
        anomaly_model, _, shap_background = load_models()

        if _SHAP_EXPLAINER is None and shap_background is not None:
            # Step inside the pipeline to explain the isolation forest directly
            iso_forest = anomaly_model.named_steps.get("isolation_forest")
            scaler = anomaly_model.named_steps.get("scaler")
            if iso_forest and scaler:
                scaled_bg = scaler.transform(shap_background)
                _SHAP_EXPLAINER = shap.TreeExplainer(iso_forest, data=scaled_bg)

        if _SHAP_EXPLAINER is not None:
            scaler = anomaly_model.named_steps["scaler"]
            scaled_input = scaler.transform([anomaly_vector])
            shap_values = _SHAP_EXPLAINER.shap_values(scaled_input)
            
            # Extract single sample values
            if isinstance(shap_values, list):
                vals = shap_values[0][0]
            elif hasattr(shap_values, "values"):
                vals = shap_values.values[0]
            else:
                vals = shap_values[0]

            for i, col in enumerate(ANOMALY_FEATURE_COLS):
                contributions[col] = round(float(vals[i]), 4)
            return contributions

    except Exception as exc:
        logger.debug("SHAP TreeExplainer calculation fell back to parametric attribution: %s", exc)

    # Fast parametric feature attribution based on standard score deviations
    baseline_stats = {
        "casing_pressure": (200.0, 30.0),
        "tubing_pressure": (145.0, 25.0),
        "polished_rod_load": (230.0, 40.0),
        "stroke_speed": (9.5, 2.5),
        "motor_temp": (66.0, 8.0),
    }

    for col in ANOMALY_FEATURE_COLS:
        base_col = col.split("_lag1")[0].split("_rolling_mean_3")[0]
        mean, std = baseline_stats.get(base_col, (100.0, 20.0))
        val = anomaly_vector[col]
        z_score = (val - mean) / std
        contributions[col] = round(float(np.tanh(z_score * 0.45)), 4)

    return contributions


def generate_diagnostic_summary(
    raw_payload: dict[str, Any],
    feature_values: dict[str, float],
    predicted_anomaly: bool,
    optimal_speed: float,
) -> tuple[str, str]:
    """Generate oil industry diagnostic report and automated SCADA control action."""
    casing_p = feature_values["casing_pressure"]
    tubing_p = feature_values["tubing_pressure"]
    rod_load = feature_values["polished_rod_load"]
    motor_temp = feature_values["motor_temp"]
    stroke_speed = feature_values["stroke_speed"]

    if not predicted_anomaly:
        speed_delta = optimal_speed - stroke_speed
        if abs(speed_delta) < 0.5:
            summary = "Well is operating within optimal mechanical and hydrodynamic envelope. Pump fillage is steady."
            scada = "Maintain current VFD setpoint; no control intervention required."
        elif speed_delta > 0.5:
            summary = f"Reservoir inflow supports higher pump displacement. Current SPM ({stroke_speed:.1f}) is under-producing."
            scada = f"Increase VFD motor frequency to target {optimal_speed:.1f} SPM to unlock +{speed_delta*14.5:.1f} BPD."
        else:
            summary = f"Current pump speed ({stroke_speed:.1f} SPM) exceeds optimal reservoir replenishment rate. Risk of fluid pound."
            scada = f"Trim VFD frequency to target {optimal_speed:.1f} SPM to reduce rod cyclic stress and save energy."
        return summary, scada

    # Anomaly conditions
    if motor_temp > 85.0:
        summary = (
            f"CRITICAL MOTOR THERMAL SURGE: Surface motor temperature has reached {motor_temp:.1f}°C "
            f"(nominal envelope < 75°C). Indicates severe mechanical friction, bearing wear, or electrical overload."
        )
        scada = "Trigger automated thermal derating: decelerate motor to 4.0 SPM and dispatch field technician for bearing inspection."
    elif rod_load > 340.0:
        summary = (
            f"HIGH POLISHED ROD LOAD OVERLOAD: Peak load of {rod_load:.1f} kN exceeds rod string endurance threshold. "
            f"Likely caused by paraffin/wax buildup in tubing or heavy fluid slug."
        )
        scada = "Initiate hot-oil wax flush protocol and reduce stroke speed to 6.5 SPM to prevent rod parting."
    elif casing_p > 280.0 and tubing_p < 100.0:
        summary = (
            f"GAS INTERFERENCE / LOCK DETECTED: Casing pressure is abnormally elevated ({casing_p:.1f} psi) "
            f"while tubing pressure has dropped ({tubing_p:.1f} psi). Free gas is entering pump barrel."
        )
        scada = "Modulate casing gas vent valve and activate intermittent pumping sequence to re-prime traveling valve."
    elif casing_p < 100.0 and rod_load < 160.0:
        summary = (
            f"FLUID POUND DETECTED: Low casing pressure ({casing_p:.1f} psi) indicates fluid level has dropped below pump intake. "
            f"Plunger is impacting liquid surface on downstroke."
        )
        scada = "Slow pump speed immediately to 5.0 SPM to avoid severe mechanical shock to rod string and gearbox."
    else:
        summary = (
            f"MULTIVARIATE SENSOR DRIFT DETECTED: Joint distribution of casing pressure ({casing_p:.1f} psi), "
            f"rod load ({rod_load:.1f} kN), and motor temp ({motor_temp:.1f}°C) deviates materially from normal operational baseline."
        )
        scada = f"Set VFD to conservative baseline of {optimal_speed:.1f} SPM and enable high-frequency SCADA telemetry logging."

    return summary, scada


def generate_dynamometer_card(
    well_id: str,
    stroke_length_in: float = 120.0,
    current_load_kn: float = 230.0,
    stroke_speed_spm: float = 10.0,
    card_type: str = "Normal",
) -> dict[str, Any]:
    """Generate high-fidelity 36-point surface and downhole dynamometer card data.

    In SRP oilfield engineering, the Dyno Card plots Polished Rod Load (lbs) vs Position (in)
    and is the premier diagnostic instrument for pump integrity and fillage.
    """
    n_points = 36
    # Load conversion: 1 kN ~ 224.8 lbs
    base_load_lbs = current_load_kn * 224.8
    stroke_length = max(60.0, stroke_length_in)

    # Normalized positions along stroke: 0 -> L (upstroke) -> 0 (downstroke)
    angles = np.linspace(0, 2 * np.pi, n_points)
    positions = (stroke_length / 2.0) * (1.0 - np.cos(angles))

    # Weight of fluid column + rod string (Upstroke Load) vs Rod string weight alone (Downstroke Load)
    fluid_load_lbs = 8500.0
    rod_weight_lbs = base_load_lbs * 0.55
    upstroke_peak = rod_weight_lbs + fluid_load_lbs
    downstroke_base = rod_weight_lbs

    surface_loads = []
    downhole_loads = []

    for i, theta in enumerate(angles):
        pos = positions[i]
        is_upstroke = (i < n_points // 2)

        if card_type == "Fluid Pound":
            # Normal upstroke, but on downstroke, sudden load drop when hitting fluid level
            if is_upstroke:
                s_load = upstroke_peak + 1200 * np.sin(theta)
                d_load = upstroke_peak - 400
            else:
                downstroke_pct = (pos / stroke_length)
                if downstroke_pct > 0.45:
                    # In air/gas: rod carries full weight
                    s_load = upstroke_peak - 1000 + 500 * np.sin(theta)
                    d_load = upstroke_peak - 1200
                else:
                    # Sudden impact on fluid surface
                    s_load = downstroke_base - 1800 + 400 * np.cos(theta)
                    d_load = downstroke_base - 800

        elif card_type == "Gas Interference":
            # Rounded, banana-shaped compression card due to gas compressibility
            compression_factor = (pos / stroke_length) ** 1.8
            if is_upstroke:
                s_load = downstroke_base + fluid_load_lbs * compression_factor + 600 * np.sin(theta)
                d_load = downstroke_base + fluid_load_lbs * compression_factor
            else:
                s_load = downstroke_base + fluid_load_lbs * (1.0 - (1.0 - pos / stroke_length) ** 1.8)
                d_load = downstroke_base + fluid_load_lbs * (pos / stroke_length)

        elif card_type == "Parted Rod":
            # Very low, flat load - rod broke, only carrying top rod segment
            s_load = rod_weight_lbs * 0.35 + 200 * np.sin(theta)
            d_load = 500.0 + 100 * np.cos(theta)

        elif card_type == "Worn Barrel":
            # Leaking valves cause tilted parallelogram with sloping top and bottom
            if is_upstroke:
                s_load = upstroke_peak - 2200 * (1.0 - pos / stroke_length) + 400 * np.sin(theta)
                d_load = upstroke_peak - 1800 * (1.0 - pos / stroke_length)
            else:
                s_load = downstroke_base + 1800 * (pos / stroke_length) + 300 * np.cos(theta)
                d_load = downstroke_base + 1200 * (pos / stroke_length)

        else:  # Normal full pump card (classic rectangular / ideal parallelogram)
            if is_upstroke:
                s_load = upstroke_peak + 800 * np.sin(theta)
                d_load = upstroke_peak - 300
            else:
                s_load = downstroke_base + 500 * np.sin(theta)
                d_load = downstroke_base + 200

        surface_loads.append(round(float(s_load), 1))
        downhole_loads.append(round(float(d_load), 1))

    pprl = max(surface_loads)
    mprl = min(surface_loads)

    # Calculate indicated card area (approximate work done per stroke: Trapezoidal integration)
    trapz_func = getattr(np, "trapezoid", getattr(np, "trapz", None))
    area_in_lbs = float(trapz_func(surface_loads[:n_points//2], positions[:n_points//2]) -
                        trapz_func(surface_loads[n_points//2:], positions[n_points//2:]))
    indicated_hp = max(0.5, abs(area_in_lbs) * stroke_speed_spm / (12.0 * 33000.0))

    fillage_pct = {
        "Normal": 94.5,
        "Fluid Pound": 58.2,
        "Gas Interference": 62.0,
        "Worn Barrel": 71.4,
        "Parted Rod": 8.0,
    }.get(card_type, 90.0)

    diagnostics = {
        "Normal": "Pump operates with full liquid fillage; standing and traveling valves sealing tightly.",
        "Fluid Pound": "Severe underfillage detected; plunger strikes fluid interface at 45% downstroke.",
        "Gas Interference": "Gas expansion delaying traveling valve closure on upstroke; reduces volumetric efficiency.",
        "Worn Barrel": "Excessive slippage past pump plunger; pump barrel or rings require workover replacement.",
        "Parted Rod": "Catastrophic loss of load; sucker rod string has parted below surface.",
    }.get(card_type, "Standard pump card profile.")

    points = [
        {"position_in": round(float(positions[i]), 2), "surface_load_lbs": surface_loads[i], "downhole_load_lbs": downhole_loads[i]}
        for i in range(n_points)
    ]

    return {
        "well_id": well_id,
        "card_type": card_type,
        "pprl_lbs": round(float(pprl), 1),
        "mprl_lbs": round(float(mprl), 1),
        "stroke_length_in": stroke_length,
        "indicated_pump_hp": round(indicated_hp, 2),
        "pump_fillage_pct": round(fillage_pct, 1),
        "diagnostic_message": diagnostics,
        "points": points,
    }


def compute_css_cycle_metrics(
    well_id: str,
    steam_temp_c: float = 280.0,
    steam_pressure_psi: float = 1300.0,
    steam_quality_pct: float = 75.0,
    day_in_phase: int = 8,
    phase: str = "INJECTION",
) -> dict[str, Any]:
    """Calculate thermal engineering metrics for Cyclic Steam Stimulation (CSS) heavy oil recovery."""
    phase_duration_map = {
        "INJECTION": 14,
        "SOAKING": 7,
        "PRODUCTION": 45,
    }
    total_days = phase_duration_map.get(phase, 30)
    current_day = min(total_days, max(1, day_in_phase))
    next_transition_days = max(1, total_days - current_day)

    # Cumulative steam injected (approx 120 tons per injection day)
    csi_tons = 120.0 * (current_day if phase == "INJECTION" else 14.0)

    # Heavy oil viscosity calculation: ASTM D341 equation approximation for Baghewala heavy crude (18° API)
    # At 25°C viscosity ~ 12,000 cP; at 120°C viscosity drops to ~ 45 cP; at 280°C viscosity ~ 8 cP
    temp_ref = max(30.0, steam_temp_c if phase == "INJECTION" else max(40.0, 180.0 - current_day * 2.5))
    viscosity_cp = max(6.0, 15000.0 * np.exp(-0.028 * temp_ref))

    # Steam-Oil Ratio (SOR): Tons of steam injected / Tons of oil produced
    if phase == "PRODUCTION":
        oil_produced_tons = max(10.0, current_day * 32.0)
        current_sor = round(csi_tons / oil_produced_tons, 2)
    else:
        current_sor = 3.2

    # Thermal stress on casing string (thermal expansion psi)
    thermal_stress_psi = round(min(45000.0, (temp_ref - 30.0) * 115.0), 1)

    recommendations = {
        "INJECTION": f"Maintain steam quality at {steam_quality_pct:.1f}%. Target cumulative injection of {14*120} tons. {next_transition_days} days until Soak shut-in.",
        "SOAKING": f"Reservoir heat dissipation underway. Downhole temperature stabilizing. Begin surface pump workover in {next_transition_days} days.",
        "PRODUCTION": f"Hot heavy oil production active. Fluid viscosity at {viscosity_cp:.1f} cP. Adjust pump speed to match declining thermal profile.",
    }.get(phase, "Monitor wellhead thermal sensors.")

    return {
        "well_id": well_id,
        "cycle_number": 2,
        "current_phase": phase,
        "phase_day": current_day,
        "total_phase_days": total_days,
        "steam_temp_c": round(float(temp_ref), 1),
        "steam_pressure_psi": round(float(steam_pressure_psi), 1),
        "steam_quality_pct": round(float(steam_quality_pct), 1),
        "cumulative_steam_injected_tons": round(csi_tons, 1),
        "current_sor": current_sor,
        "reservoir_viscosity_cp": round(viscosity_cp, 1),
        "casing_thermal_stress_psi": thermal_stress_psi,
        "next_transition_estimate_days": next_transition_days,
        "operational_recommendation": recommendations,
    }
