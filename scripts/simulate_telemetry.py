from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import numpy as np
import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AlertRecord, TelemetryRecord, WellMetadata
from app.services.predictor import infer_and_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELLS = ["SRP-001", "SRP-002", "SRP-003", "SRP-004", "CSS-101", "CSS-102", "CSS-103"]


def generate_payload(well_id: str, index: int) -> dict[str, Any]:
    """Generate realistic live telemetry payload for SRP or CSS well."""
    is_css = well_id.startswith("CSS")
    well_type = "CSS" if is_css else "SRP"
    rng = np.random.default_rng(index + int(well_id[-1]) * 10)

    # Base operating parameters
    base_profiles = {
        "SRP-001": (210.0, 145.0, 230.0, 65.0, 10.5),
        "SRP-002": (155.0, 105.0, 210.0, 69.0, 11.0),  # Underfillage prone
        "SRP-003": (198.0, 140.0, 220.0, 63.0, 9.8),
        "SRP-004": (235.0, 175.0, 310.0, 85.0, 12.5),  # High load
        "CSS-101": (225.0, 155.0, 265.0, 112.0, 9.2),  # CSS Production phase
        "CSS-102": (340.0, 1310.0, 42.0, 48.0, 0.0),   # CSS Injection phase
        "CSS-103": (230.0, 410.0, 38.0, 42.0, 0.0),    # CSS Soaking phase
    }
    c_p, t_p, rod_l, m_temp, spm = base_profiles.get(well_id, (200.0, 140.0, 220.0, 65.0, 10.0))

    cycle_offset = np.sin((index / 20.0) * 2 * np.pi) * 3.5
    c_p += cycle_offset + rng.normal(0, 2.0)
    t_p += cycle_offset * 0.7 + rng.normal(0, 1.5)
    rod_l += cycle_offset * 1.8 + rng.normal(0, 3.0)
    m_temp += cycle_offset * 0.4 + rng.normal(0, 0.8)
    spm = max(0.0, spm + (0.4 * np.cos(index / 10.0)) + rng.normal(0, 0.15)) if spm > 0 else 0.0

    css_phase = "NONE"
    steam_t = 0.0
    steam_p = 0.0
    steam_q = 0.0
    dyno_card = "Normal"

    if is_css:
        if well_id == "CSS-102":
            css_phase = "INJECTION"
            steam_t = 286.0 + rng.normal(0, 3.0)
            steam_p = 1325.0 + rng.normal(0, 15.0)
            steam_q = 79.0 + rng.normal(0, 1.0)
        elif well_id == "CSS-103":
            css_phase = "SOAKING"
            steam_t = 175.0 - (index % 10) * 1.5
            steam_p = 420.0 - (index % 10) * 4.0
        else:
            css_phase = "PRODUCTION"
            steam_t = max(55.0, 115.0 - (index % 15) * 1.2)
    else:
        if well_id == "SRP-002" and (index % 7 in (0, 1)):
            dyno_card = "Fluid Pound"
            c_p -= 35.0
            rod_l -= 30.0
        elif well_id == "SRP-004":
            dyno_card = "Worn Barrel"

    flow_rate = max(0.0, spm * 14.0 - t_p * 0.07 + rng.normal(0, 2.0)) if spm > 0 else 0.0
    power_kw = 12.0 + 0.03 * rod_l + 0.2 * spm if spm > 0 else 2.5
    vibration = 1.4 + 0.06 * spm + rng.normal(0, 0.1)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "well_id": well_id,
        "well_type": well_type,
        "casing_pressure": round(float(c_p), 2),
        "tubing_pressure": round(float(t_p), 2),
        "polished_rod_load": round(float(rod_l), 2),
        "stroke_speed": round(float(spm), 2),
        "motor_temp": round(float(m_temp), 2),
        "flow_rate": round(float(flow_rate), 2),
        "water_cut": 17.5,
        "power_consumption": round(float(power_kw), 2),
        "vibration_rms": round(float(vibration), 2),
        "dyno_card_type": dyno_card,
        "css_phase": css_phase,
        "steam_temp": round(float(steam_t), 1),
        "steam_pressure": round(float(steam_p), 1),
        "steam_quality": round(float(steam_q), 1),
    }


def generate_telemetry_tick(db: Session) -> list[str]:
    """Direct database insertion for single simulation tick across all wells."""
    now = datetime.utcnow()
    updated = []

    for idx, well_id in enumerate(WELLS):
        payload = generate_payload(well_id, int(now.timestamp()) // 10)
        history = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.well_id == well_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(6)
            .all()
        )
        result = infer_and_score(payload, well_id, history)

        record = TelemetryRecord(
            timestamp=now,
            well_id=well_id,
            well_type=payload["well_type"],
            casing_pressure=payload["casing_pressure"],
            tubing_pressure=payload["tubing_pressure"],
            polished_rod_load=payload["polished_rod_load"],
            stroke_speed=payload["stroke_speed"],
            motor_temp=payload["motor_temp"],
            flow_rate=payload["flow_rate"],
            water_cut=payload["water_cut"],
            power_consumption=payload["power_consumption"],
            vibration_rms=payload["vibration_rms"],
            dyno_card_type=payload["dyno_card_type"],
            css_phase=payload["css_phase"],
            steam_temp=payload["steam_temp"],
            steam_pressure=payload["steam_pressure"],
            steam_quality=payload["steam_quality"],
            predicted_anomaly=result["predicted_anomaly"],
            optimal_speed=result["optimal_speed"],
            anomaly_score=result["anomaly_score"],
        )
        db.merge(record)

        # Update well status
        well_meta = db.query(WellMetadata).filter(WellMetadata.well_id == well_id).first()
        if well_meta:
            well_meta.status = "critical" if result["predicted_anomaly"] else "healthy"

        updated.append(well_id)

    db.commit()
    return updated


def main() -> None:
    api_url = settings.API_BASE_URL
    print(f"Starting real-time SCADA telemetry simulator connecting to {api_url}...")
    iteration = 0
    while True:
        try:
            for well_id in WELLS:
                payload = generate_payload(well_id, iteration)
                resp = requests.post(f"{api_url}/api/v1/telemetry", json=payload, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    status = "ANOMALY" if data.get("predicted_anomaly") else "OK"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {well_id} -> {status} "
                          f"(Speed: {data.get('stroke_speed')} -> Opt: {data.get('optimal_speed')})")
                else:
                    print(f"Failed to post {well_id}: {resp.status_code}")
        except Exception as e:
            print(f"Simulator stream error: {e}")

        iteration += 1
        time.sleep(settings.SIMULATOR_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
