from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import numpy as np
from app.database import SessionLocal, init_db
from app.models import AlertRecord, TelemetryRecord, WellMetadata
from app.services.predictor import infer_and_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELLS_CONFIG = [
    {
        "well_id": "SRP-001",
        "well_name": "Baghewala SRP-01 (Main Producer)",
        "well_type": "SRP",
        "depth_m": 1180.0,
        "oil_gravity_api": 19.2,
        "pump_depth_m": 1050.0,
        "stroke_length_in": 120.0,
        "plunger_diameter_in": 1.75,
        "target_production_bpd": 140.0,
        "status": "healthy",
        "base_casing": 205.0,
        "base_tubing": 145.0,
        "base_load": 225.0,
        "base_speed": 10.5,
        "base_temp": 64.0,
    },
    {
        "well_id": "SRP-002",
        "well_name": "Baghewala SRP-02 (South Flank)",
        "well_type": "SRP",
        "depth_m": 1240.0,
        "oil_gravity_api": 18.0,
        "pump_depth_m": 1100.0,
        "stroke_length_in": 144.0,
        "plunger_diameter_in": 2.00,
        "target_production_bpd": 165.0,
        "status": "warning",  # Has fluid pound
        "base_casing": 160.0,
        "base_tubing": 110.0,
        "base_load": 250.0,
        "base_speed": 11.0,
        "base_temp": 68.0,
    },
    {
        "well_id": "SRP-003",
        "well_name": "Baghewala SRP-03 (Central Block)",
        "well_type": "SRP",
        "depth_m": 1150.0,
        "oil_gravity_api": 19.5,
        "pump_depth_m": 1020.0,
        "stroke_length_in": 120.0,
        "plunger_diameter_in": 1.75,
        "target_production_bpd": 130.0,
        "status": "healthy",
        "base_casing": 195.0,
        "base_tubing": 138.0,
        "base_load": 215.0,
        "base_speed": 9.8,
        "base_temp": 62.0,
    },
    {
        "well_id": "SRP-004",
        "well_name": "Baghewala SRP-04 (North Crest)",
        "well_type": "SRP",
        "depth_m": 1300.0,
        "oil_gravity_api": 17.2,
        "pump_depth_m": 1180.0,
        "stroke_length_in": 144.0,
        "plunger_diameter_in": 2.25,
        "target_production_bpd": 180.0,
        "status": "critical",  # High rod load / motor overheat
        "base_casing": 230.0,
        "base_tubing": 170.0,
        "base_load": 320.0,
        "base_speed": 12.5,
        "base_temp": 86.0,
    },
    {
        "well_id": "CSS-101",
        "well_name": "Baghewala CSS-01 (Thermal Cycle 2)",
        "well_type": "CSS",
        "depth_m": 1100.0,
        "oil_gravity_api": 16.5,
        "pump_depth_m": 980.0,
        "stroke_length_in": 100.0,
        "plunger_diameter_in": 1.75,
        "target_production_bpd": 210.0,
        "css_cycle_number": 2,
        "css_phase": "PRODUCTION",
        "status": "healthy",
        "base_casing": 220.0,
        "base_tubing": 150.0,
        "base_load": 260.0,
        "base_speed": 9.2,
        "base_temp": 115.0,
    },
    {
        "well_id": "CSS-102",
        "well_name": "Baghewala CSS-02 (Steam Huff-Puff)",
        "well_type": "CSS",
        "depth_m": 1120.0,
        "oil_gravity_api": 16.0,
        "pump_depth_m": 1000.0,
        "stroke_length_in": 0.0,
        "plunger_diameter_in": 0.0,
        "target_production_bpd": 0.0,
        "css_cycle_number": 3,
        "css_phase": "INJECTION",
        "status": "warning",
        "base_casing": 340.0,
        "base_tubing": 1320.0,
        "base_load": 40.0,
        "base_speed": 0.0,
        "base_temp": 48.0,
    },
    {
        "well_id": "CSS-103",
        "well_name": "Baghewala CSS-03 (Thermal Soak Phase)",
        "well_type": "CSS",
        "depth_m": 1080.0,
        "oil_gravity_api": 16.8,
        "pump_depth_m": 960.0,
        "stroke_length_in": 0.0,
        "plunger_diameter_in": 0.0,
        "target_production_bpd": 0.0,
        "css_cycle_number": 1,
        "css_phase": "SOAKING",
        "status": "healthy",
        "base_casing": 230.0,
        "base_tubing": 410.0,
        "base_load": 38.0,
        "base_speed": 0.0,
        "base_temp": 42.0,
    },
]


def seed_database(hours: int = 48) -> None:
    """Populate database with rich metadata, historical telemetry, and operational alerts."""
    init_db()
    db = SessionLocal()

    logger.info("Seeding Well Metadata...")
    for cfg in WELLS_CONFIG:
        existing = db.query(WellMetadata).filter(WellMetadata.well_id == cfg["well_id"]).first()
        if not existing:
            meta = WellMetadata(
                well_id=cfg["well_id"],
                well_name=cfg["well_name"],
                well_type=cfg["well_type"],
                field_name="Oil India - Baghewala Asset",
                depth_m=cfg["depth_m"],
                oil_gravity_api=cfg["oil_gravity_api"],
                pump_depth_m=cfg["pump_depth_m"],
                stroke_length_in=cfg["stroke_length_in"],
                plunger_diameter_in=cfg["plunger_diameter_in"],
                target_production_bpd=cfg["target_production_bpd"],
                css_cycle_number=cfg.get("css_cycle_number", 1),
                css_phase=cfg.get("css_phase", "PRODUCTION"),
                status=cfg["status"],
            )
            db.add(meta)
        else:
            existing.status = cfg["status"]
            existing.css_phase = cfg.get("css_phase", "PRODUCTION")

    db.commit()

    logger.info("Generating %d hours of historical telemetry (15-min intervals)...", hours)
    now = datetime.utcnow()
    periods = hours * 4  # 4 readings per hour
    rng = np.random.default_rng(123)

    records_to_insert: list[TelemetryRecord] = []

    for cfg in WELLS_CONFIG:
        well_id = cfg["well_id"]
        well_type = cfg["well_type"]
        is_css = (well_type == "CSS")
        css_phase = cfg.get("css_phase", "NONE")

        for i in range(periods):
            ts = now - timedelta(minutes=(periods - i) * 15)
            minute = ts.hour * 60 + ts.minute
            cycle = np.sin((minute / 1440) * 2 * np.pi)

            casing = cfg["base_casing"] + 8 * cycle + rng.normal(0, 4)
            tubing = cfg["base_tubing"] + 5 * cycle + rng.normal(0, 3)
            load = cfg["base_load"] + 15 * cycle + rng.normal(0, 6)
            speed = max(0.0, cfg["base_speed"] + 1.2 * np.sin((minute / 60) / 12) + rng.normal(0, 0.4))
            temp = cfg["base_temp"] + 3 * cycle + rng.normal(0, 1.2)

            # Specific anomaly behavior
            dyno_card = "Normal"
            pred_anomaly = False
            anomaly_score = 0.08
            opt_speed = speed

            if well_id == "SRP-002" and i > periods - 12:  # Last 3 hours
                dyno_card = "Fluid Pound"
                casing -= 45.0
                load -= 35.0
                pred_anomaly = True
                anomaly_score = 0.88
                opt_speed = 6.0
            elif well_id == "SRP-004" and i > periods - 16:  # Last 4 hours
                dyno_card = "Worn Barrel"
                load += 65.0
                temp += 24.0
                pred_anomaly = True
                anomaly_score = 0.94
                opt_speed = 7.5
            elif well_id == "CSS-102":
                dyno_card = "Normal"
                steam_temp = 288.0 + rng.normal(0, 5)
                steam_press = 1340.0 + rng.normal(0, 20)
                steam_qual = 78.5 + rng.normal(0, 1.5)
                if i > periods - 8:
                    pred_anomaly = True
                    anomaly_score = 0.79
            else:
                opt_speed = max(6.0, speed * 1.05)

            steam_t = 285.0 if css_phase == "INJECTION" else (180.0 if css_phase == "SOAKING" else (temp if is_css else 0.0))
            steam_p = 1320.0 if css_phase == "INJECTION" else (450.0 if css_phase == "SOAKING" else 0.0)
            steam_q = 78.0 if css_phase == "INJECTION" else 0.0

            flow_rate = max(0.0, speed * 13.8 - tubing * 0.08 + rng.normal(0, 3)) if (speed > 1.0) else 0.0
            power_kw = 12.0 + 0.03 * load + 0.25 * speed if speed > 1.0 else 2.5
            vibration = 1.4 + 0.06 * speed if not pred_anomaly else 3.8

            record = TelemetryRecord(
                timestamp=ts,
                well_id=well_id,
                well_type=well_type,
                casing_pressure=round(float(casing), 2),
                tubing_pressure=round(float(tubing), 2),
                polished_rod_load=round(float(load), 2),
                stroke_speed=round(float(speed), 2),
                motor_temp=round(float(temp), 2),
                flow_rate=round(float(flow_rate), 2),
                water_cut=round(float(16.5 + rng.normal(0, 1.0)), 1),
                power_consumption=round(float(power_kw), 2),
                vibration_rms=round(float(vibration), 2),
                dyno_card_type=dyno_card,
                css_phase=css_phase,
                steam_temp=round(float(steam_t), 1),
                steam_pressure=round(float(steam_p), 1),
                steam_quality=round(float(steam_q), 1),
                predicted_anomaly=pred_anomaly,
                optimal_speed=round(float(opt_speed), 2),
                anomaly_score=round(float(anomaly_score), 4),
            )
            records_to_insert.append(record)

    db.query(TelemetryRecord).delete()
    db.bulk_save_objects(records_to_insert)
    db.commit()

    logger.info("Seeding initial Anomaly Alerts...")
    db.query(AlertRecord).delete()
    alerts = [
        AlertRecord(
            timestamp=now - timedelta(minutes=45),
            well_id="SRP-004",
            severity="CRITICAL",
            anomaly_type="Motor Thermal Surge & Overload",
            description="Surface drive motor temperature exceeded 86°C threshold with 320 kN rod load.",
            root_cause="Heavy crude slugging combined with severe mechanical friction in tubing string.",
            recommended_action="Reduce VFD frequency from 12.5 SPM to 7.5 SPM and schedule hot water flush.",
            acknowledged=False,
        ),
        AlertRecord(
            timestamp=now - timedelta(minutes=110),
            well_id="SRP-002",
            severity="WARNING",
            anomaly_type="Fluid Pound / Underfilled Barrel",
            description="Dyno card shows delayed fluid contact at 45% downstroke; casing pressure dropped to 115 psi.",
            root_cause="Pump displacement exceeds reservoir inflow replenishment rate.",
            recommended_action="Trim stroke speed to 6.0 SPM to allow pump barrel full liquid fillage.",
            acknowledged=False,
        ),
        AlertRecord(
            timestamp=now - timedelta(hours=3),
            well_id="CSS-102",
            severity="WARNING",
            anomaly_type="Steam Breakthrough Early Indicator",
            description="Injection manifold pressure fluctuating; casing temperature spike detected.",
            root_cause="High permeability streak channel in upper sand zone.",
            recommended_action="Throttle steam injection rate by 15% and increase monitoring of offset well CSS-103.",
            acknowledged=True,
        ),
    ]
    db.bulk_save_objects(alerts)
    db.commit()
    db.close()
    logger.info("Database seeding complete. Seeded %d telemetry records and %d alerts across %d wells.",
                len(records_to_insert), len(alerts), len(WELLS_CONFIG))


if __name__ == "__main__":
    seed_database()
