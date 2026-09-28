from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


SRP_WELLS = ["SRP-001", "SRP-002", "SRP-003", "SRP-004"]
CSS_WELLS = ["CSS-101", "CSS-102", "CSS-103"]
ALL_WELLS = SRP_WELLS + CSS_WELLS


def generate_mock_dataset(
    output_path: str | Path,
    wells: list[str] | None = None,
    days: int = 120,
) -> pd.DataFrame:
    """Create a realistic synthetic time-series dataset for Oil India SRP and CSS well monitoring.

    Generates both normal operating envelopes and realistic anomalous operating states
    (fluid pound, gas interference, motor overheating, rod overload, and steam breakthrough).
    """
    if wells is None:
        wells = ALL_WELLS

    rng = np.random.default_rng(42)
    timestamps = pd.date_range("2024-01-01", periods=days * 24 * 4, freq="15min")
    rows: list[dict[str, float | str]] = []

    for well in wells:
        is_css = well.startswith("CSS")
        well_type = "CSS" if is_css else "SRP"

        baseline_pressure = 195 + rng.normal(0, 15)
        baseline_temp = 64 + rng.normal(0, 6)
        baseline_load = 220 + rng.normal(0, 20)

        for ts in timestamps:
            day_of_year = ts.dayofyear
            minute = ts.hour * 60 + ts.minute
            daily_cycle = np.sin((minute / 1440) * 2 * np.pi)
            seasonal_trend = 1 + (day_of_year / 365) * 0.15

            # CSS Phase Calculation (60-day cycle: 12 days Injection, 6 days Soaking, 42 days Production)
            css_phase = "NONE"
            steam_temp = 0.0
            steam_pressure = 0.0
            steam_quality = 0.0

            if is_css:
                cycle_day = day_of_year % 60
                if cycle_day < 12:
                    css_phase = "INJECTION"
                    steam_temp = 285 + rng.normal(0, 8)
                    steam_pressure = 1350 + rng.normal(0, 40)
                    steam_quality = 78 + rng.normal(0, 3)
                    stroke_speed = 0.0
                    polished_rod_load = 40.0 + rng.normal(0, 5)
                    casing_pressure = 320 + rng.normal(0, 15)
                    tubing_pressure = 1250 + rng.normal(0, 30)
                    motor_temp = 42 + rng.normal(0, 3)
                    flow_rate = 0.0
                    water_cut = 0.0
                    power_consumption = 3.0
                    vibration_rms = 0.5
                    dyno_type = "Normal"
                elif cycle_day < 18:
                    css_phase = "SOAKING"
                    steam_temp = 210 - (cycle_day - 12) * 12 + rng.normal(0, 5)
                    steam_pressure = 850 - (cycle_day - 12) * 70 + rng.normal(0, 25)
                    steam_quality = 0.0
                    stroke_speed = 0.0
                    polished_rod_load = 40.0 + rng.normal(0, 4)
                    casing_pressure = 240 - (cycle_day - 12) * 10 + rng.normal(0, 8)
                    tubing_pressure = 380 - (cycle_day - 12) * 25 + rng.normal(0, 12)
                    motor_temp = 38 + rng.normal(0, 2)
                    flow_rate = 0.0
                    water_cut = 0.0
                    power_consumption = 1.0
                    vibration_rms = 0.3
                    dyno_type = "Normal"
                else:
                    css_phase = "PRODUCTION"
                    prod_day = cycle_day - 18
                    # Thermal decay as heavy oil produces and cools
                    fluid_temp = 140 - prod_day * 1.6 + rng.normal(0, 4)
                    steam_temp = max(55.0, float(fluid_temp))
                    casing_pressure = baseline_pressure * 1.2 * seasonal_trend - prod_day * 0.8 + 10 * daily_cycle + rng.normal(0, 7)
                    tubing_pressure = (casing_pressure * 0.74) + rng.normal(0, 5)
                    polished_rod_load = baseline_load * 1.15 * seasonal_trend + 30 * daily_cycle + prod_day * 0.5 + rng.normal(0, 10)
                    stroke_speed = 9.5 + 2.5 * np.sin((minute / 60) / 12) + rng.normal(0, 0.8)
                    motor_temp = baseline_temp + 0.03 * (casing_pressure - 150) + 0.12 * (polished_rod_load / 10) + rng.normal(0, 2.0)
                    flow_rate = max(10.0, 210.0 - prod_day * 2.8 + rng.normal(0, 8))
                    water_cut = min(85.0, 18.0 + prod_day * 0.75 + rng.normal(0, 2))
                    power_consumption = 14.0 + 0.03 * polished_rod_load + rng.normal(0, 0.5)
                    vibration_rms = 1.6 + 0.05 * stroke_speed + rng.normal(0, 0.2)
                    dyno_type = "Normal"
            else:
                # SRP Well Standard Physics
                casing_pressure = baseline_pressure * seasonal_trend + 14 * daily_cycle + rng.normal(0, 6)
                tubing_pressure = (casing_pressure * 0.70) + rng.normal(0, 5)
                polished_rod_load = baseline_load * seasonal_trend + 34 * daily_cycle + rng.normal(0, 10)
                stroke_speed = 8.5 + 3.8 * np.sin((minute / 60) / 12) + rng.normal(0, 0.9)
                motor_temp = baseline_temp + 0.04 * (casing_pressure - 150) + 0.15 * (polished_rod_load / 10) + rng.normal(0, 2.2)
                flow_rate = max(15.0, stroke_speed * 14.2 - (tubing_pressure * 0.12) + rng.normal(0, 5))
                water_cut = 18.0 + 4.0 * np.sin((day_of_year / 30) * np.pi) + rng.normal(0, 1.5)
                power_consumption = 12.0 + 0.04 * polished_rod_load + 0.2 * stroke_speed + rng.normal(0, 0.6)
                vibration_rms = 1.4 + 0.08 * stroke_speed + rng.normal(0, 0.15)
                dyno_type = "Normal"

            # Inject Realistic Failure / Anomaly Scenarios (3% rate overall, elevated during specific fatigue windows)
            is_anomaly_window = (day_of_year % 38 == 0) and (ts.hour in range(11, 17))
            anomaly_prob = 0.50 if is_anomaly_window else 0.012

            if rng.random() < anomaly_prob:
                fault_selector = rng.choice(["fluid_pound", "motor_overheat", "rod_overload", "gas_lock"])
                if fault_selector == "fluid_pound":
                    casing_pressure = max(40.0, casing_pressure - 65)
                    tubing_pressure = max(30.0, tubing_pressure - 40)
                    polished_rod_load += rng.normal(60, 15)
                    vibration_rms += 2.8 + rng.normal(0, 0.5)
                    dyno_type = "Fluid Pound"
                elif fault_selector == "motor_overheat":
                    motor_temp += 32 + rng.normal(0, 5)
                    power_consumption += 8.5 + rng.normal(0, 1.5)
                    vibration_rms += 1.9 + rng.normal(0, 0.3)
                    dyno_type = "Normal"
                elif fault_selector == "rod_overload":
                    polished_rod_load += 140 + rng.normal(0, 25)
                    motor_temp += 18 + rng.normal(0, 4)
                    power_consumption += 6.0 + rng.normal(0, 1.2)
                    dyno_type = "Worn Barrel"
                elif fault_selector == "gas_lock":
                    casing_pressure += 80 + rng.normal(0, 18)
                    tubing_pressure = max(30.0, tubing_pressure - 35)
                    flow_rate = max(2.0, flow_rate * 0.25)
                    dyno_type = "Gas Interference"

            rows.append({
                "timestamp": ts,
                "well_id": well,
                "well_type": well_type,
                "casing_pressure": round(float(casing_pressure), 3),
                "tubing_pressure": round(float(tubing_pressure), 3),
                "polished_rod_load": round(float(polished_rod_load), 3),
                "stroke_speed": round(float(stroke_speed), 3),
                "motor_temp": round(float(motor_temp), 3),
                "flow_rate": round(float(max(0.0, flow_rate)), 2),
                "water_cut": round(float(max(0.0, min(100.0, water_cut))), 2),
                "power_consumption": round(float(max(0.0, power_consumption)), 2),
                "vibration_rms": round(float(max(0.1, vibration_rms)), 2),
                "dyno_card_type": dyno_type,
                "css_phase": css_phase,
                "steam_temp": round(float(steam_temp), 2),
                "steam_pressure": round(float(steam_pressure), 2),
                "steam_quality": round(float(steam_quality), 2),
            })

    df = pd.DataFrame(rows)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df
