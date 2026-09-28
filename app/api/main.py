from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import AlertRecord, TelemetryRecord, WellMetadata
from app.schemas import (
    AlertSchema,
    CssCycleMetrics,
    DynoCardResponse,
    PredictRequest,
    PredictResponse,
    ShapExplanationResponse,
    ShapFeatureDriver,
    TelemetryCreate,
    TelemetryResponse,
    WellMetadataSchema,
    WellStatus,
    CopilotRequest,
    CopilotResponse,
)
from app.services.predictor import (
    FEATURE_LABELS,
    build_feature_dict,
    compute_css_cycle_metrics,
    compute_shap_feature_importance,
    generate_dynamometer_card,
    infer_and_score,
)
from app.services.copilot import generate_copilot_response
from app.services.weather import fetch_field_weather

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed demo data if database is empty."""
    init_db()
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        well_count = db.query(WellMetadata).count()
        telemetry_count = db.query(TelemetryRecord).count()
        if well_count == 0 or telemetry_count == 0:
            logger.info("Database empty on startup; seeding demo assets and telemetry...")
            from scripts.seed_demo_data import seed_database
            seed_database(hours=48)
    except Exception as e:
        logger.warning("Auto-seed check encountered exception: %s", e)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Oil India SIH26120 Digital Twin API for Well-to-Surface Optimization (CSS & SRP)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check() -> dict[str, object]:
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "asset_field": settings.FIELD_NAME,
        "database": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/wells", response_model=list[str])
def list_wells(db: Session = Depends(get_db)) -> list[str]:
    """Return all active well IDs."""
    rows = db.query(WellMetadata.well_id).all()
    if rows:
        return [row[0] for row in rows]
    # Fallback to distinct wells in telemetry
    telemetry_wells = db.query(TelemetryRecord.well_id).distinct().all()
    return [row[0] for row in telemetry_wells] or ["SRP-001"]


@app.get("/api/v1/wells/details", response_model=list[WellMetadataSchema])
def list_wells_detailed(db: Session = Depends(get_db)) -> list[WellMetadataSchema]:
    """Return detailed metadata and technical specs for all monitored wells."""
    wells = db.query(WellMetadata).all()
    return [
        WellMetadataSchema(
            well_id=w.well_id,
            well_name=w.well_name,
            well_type=w.well_type,
            field_name=w.field_name,
            depth_m=w.depth_m,
            oil_gravity_api=w.oil_gravity_api,
            pump_depth_m=w.pump_depth_m,
            stroke_length_in=w.stroke_length_in,
            plunger_diameter_in=w.plunger_diameter_in,
            target_production_bpd=w.target_production_bpd,
            css_cycle_number=w.css_cycle_number,
            css_phase=w.css_phase,
            status=w.status,
        )
        for w in wells
    ]


@app.post("/api/v1/telemetry", response_model=TelemetryResponse)
def ingest_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)) -> TelemetryResponse:
    """Ingest live sensor reading, evaluate ML models, detect anomalies, and persist."""
    timestamp = payload.timestamp or datetime.utcnow()
    history = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == payload.well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(6)
        .all()
    )
    result = infer_and_score(payload.model_dump(), payload.well_id, history)

    flow_rate = payload.flow_rate if payload.flow_rate is not None else result["expected_flow_rate"]
    water_cut = payload.water_cut if payload.water_cut is not None else 16.0
    power_kw = payload.power_consumption if payload.power_consumption is not None else (12.0 + 0.03 * payload.polished_rod_load)
    vibration = payload.vibration_rms if payload.vibration_rms is not None else (1.5 if not result["predicted_anomaly"] else 3.5)
    dyno_card = payload.dyno_card_type or ("Fluid Pound" if payload.casing_pressure < 110 else "Normal")
    css_phase = payload.css_phase or "NONE"

    record = TelemetryRecord(
        timestamp=timestamp,
        well_id=payload.well_id,
        well_type=payload.well_type,
        casing_pressure=payload.casing_pressure,
        tubing_pressure=payload.tubing_pressure,
        polished_rod_load=payload.polished_rod_load,
        stroke_speed=payload.stroke_speed,
        motor_temp=payload.motor_temp,
        flow_rate=flow_rate,
        water_cut=water_cut,
        power_consumption=power_kw,
        vibration_rms=vibration,
        dyno_card_type=dyno_card,
        css_phase=css_phase,
        steam_temp=payload.steam_temp or 0.0,
        steam_pressure=payload.steam_pressure or 0.0,
        steam_quality=payload.steam_quality or 0.0,
        predicted_anomaly=result["predicted_anomaly"],
        optimal_speed=result["optimal_speed"],
        anomaly_score=result["anomaly_score"],
    )
    db.merge(record)

    # Log critical alert if anomaly detected
    if result["predicted_anomaly"] and result["anomaly_score"] > 0.65:
        alert = AlertRecord(
            timestamp=timestamp,
            well_id=payload.well_id,
            severity="CRITICAL" if result["anomaly_score"] > 0.80 else "WARNING",
            anomaly_type="Anomaly Flagged by IsolationForest",
            description=result["explanation"],
            root_cause="Operating state deviation from historical baseline",
            recommended_action=result["scada_action_recommendation"],
            acknowledged=False,
        )
        db.add(alert)

    # Update well status
    well_meta = db.query(WellMetadata).filter(WellMetadata.well_id == payload.well_id).first()
    if well_meta:
        if result["predicted_anomaly"]:
            well_meta.status = "critical" if result["anomaly_score"] > 0.80 else "warning"
        else:
            well_meta.status = "healthy"

    db.commit()

    return TelemetryResponse(
        timestamp=timestamp,
        well_id=payload.well_id,
        well_type=payload.well_type,
        casing_pressure=payload.casing_pressure,
        tubing_pressure=payload.tubing_pressure,
        polished_rod_load=payload.polished_rod_load,
        stroke_speed=payload.stroke_speed,
        motor_temp=payload.motor_temp,
        flow_rate=flow_rate,
        water_cut=water_cut,
        power_consumption=power_kw,
        vibration_rms=vibration,
        dyno_card_type=dyno_card,
        css_phase=css_phase,
        steam_temp=payload.steam_temp or 0.0,
        steam_pressure=payload.steam_pressure or 0.0,
        steam_quality=payload.steam_quality or 0.0,
        predicted_anomaly=result["predicted_anomaly"],
        optimal_speed=result["optimal_speed"],
        anomaly_score=result["anomaly_score"],
    )


@app.get("/api/v1/telemetry/{well_id}")
def get_telemetry(
    well_id: str,
    minutes: int = Query(default=180, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Fetch time-series telemetry for a specific well over the requested time horizon."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    rows = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .filter(TelemetryRecord.timestamp >= since)
        .order_by(TelemetryRecord.timestamp.asc())
        .all()
    )
    if not rows:
        # Fallback to last 100 rows regardless of time
        rows = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.well_id == well_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(100)
            .all()
        )
        rows.reverse()

    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "well_id": row.well_id,
            "well_type": row.well_type,
            "casing_pressure": row.casing_pressure,
            "tubing_pressure": row.tubing_pressure,
            "polished_rod_load": row.polished_rod_load,
            "stroke_speed": row.stroke_speed,
            "motor_temp": row.motor_temp,
            "flow_rate": row.flow_rate,
            "water_cut": row.water_cut,
            "power_consumption": row.power_consumption,
            "vibration_rms": row.vibration_rms,
            "dyno_card_type": row.dyno_card_type,
            "css_phase": row.css_phase,
            "steam_temp": row.steam_temp,
            "steam_pressure": row.steam_pressure,
            "steam_quality": row.steam_quality,
            "predicted_anomaly": row.predicted_anomaly,
            "optimal_speed": row.optimal_speed,
            "anomaly_score": row.anomaly_score,
        }
        for row in rows
    ]


@app.get("/api/v1/dashboard", response_model=list[WellStatus])
def dashboard_status(db: Session = Depends(get_db)) -> list[WellStatus]:
    """Return live status cards and KPIs for all wells in the asset field."""
    wells = db.query(WellMetadata).all()
    statuses: list[WellStatus] = []

    for w in wells:
        latest = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.well_id == w.well_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .first()
        )
        anomalies_count = (
            db.query(func.count(TelemetryRecord.timestamp))
            .filter(TelemetryRecord.well_id == w.well_id)
            .filter(TelemetryRecord.predicted_anomaly == True)
            .scalar()
            or 0
        )
        avg_speed = (
            db.query(func.avg(TelemetryRecord.optimal_speed))
            .filter(TelemetryRecord.well_id == w.well_id)
            .scalar()
            or 0.0
        )

        status = w.status
        if latest:
            if latest.predicted_anomaly:
                status = "critical" if latest.anomaly_score > 0.80 else "warning"
            else:
                status = "healthy"

        statuses.append(
            WellStatus(
                well_id=w.well_id,
                well_name=w.well_name,
                well_type=w.well_type,
                last_timestamp=latest.timestamp.isoformat() if latest else None,
                status=status,
                anomaly_count=int(anomalies_count),
                average_optimal_speed=round(float(avg_speed), 2),
                latest_casing_pressure=round(float(latest.casing_pressure), 1) if latest else 0.0,
                latest_rod_load=round(float(latest.polished_rod_load), 1) if latest else 0.0,
                latest_stroke_speed=round(float(latest.stroke_speed), 1) if latest else 0.0,
                latest_flow_rate=round(float(latest.flow_rate), 1) if latest else 0.0,
                latest_motor_temp=round(float(latest.motor_temp), 1) if latest else 0.0,
                css_phase=w.css_phase,
            )
        )
    return statuses


@app.post("/api/v1/predict/simulate", response_model=PredictResponse)
def simulate_prediction(payload: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    """Run interactive 'what-if' digital twin optimization sandbox."""
    history = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == payload.well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(6)
        .all()
    )
    result = infer_and_score(payload.model_dump(), payload.well_id, history)
    return PredictResponse(
        well_id=payload.well_id,
        timestamp=datetime.utcnow(),
        predicted_anomaly=result["predicted_anomaly"],
        anomaly_score=result["anomaly_score"],
        optimal_speed=result["optimal_speed"],
        expected_flow_rate=result["expected_flow_rate"],
        energy_savings_pct=result["energy_savings_pct"],
        explanation=result["explanation"],
        shap_contributions=result["shap_contributions"],
        scada_action_recommendation=result["scada_action_recommendation"],
    )


@app.get("/api/v1/explain/{well_id}", response_model=ShapExplanationResponse)
def explain_well(well_id: str, db: Session = Depends(get_db)) -> ShapExplanationResponse:
    """Generate SHAP local feature attribution and waterfall breakdown for latest well state."""
    latest = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail=f"No telemetry found for well {well_id}")

    history = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .offset(1)
        .limit(5)
        .all()
    )

    raw_dict = {
        "casing_pressure": latest.casing_pressure,
        "tubing_pressure": latest.tubing_pressure,
        "polished_rod_load": latest.polished_rod_load,
        "stroke_speed": latest.stroke_speed,
        "motor_temp": latest.motor_temp,
    }
    feature_vals = build_feature_dict(raw_dict, history)
    anomaly_vector = [feature_vals[col] for col in FEATURE_LABELS.keys() if col in feature_vals]

    shap_vals = compute_shap_feature_importance(anomaly_vector)

    drivers: list[ShapFeatureDriver] = []
    for k, v in shap_vals.items():
        base_k = k.split("_lag1")[0].split("_rolling_mean_3")[0]
        drivers.append(
            ShapFeatureDriver(
                feature=k,
                label=FEATURE_LABELS.get(k, k),
                value=round(feature_vals.get(k, 0.0), 2),
                baseline=200.0,
                shap_value=v,
                impact="increases_anomaly_risk" if v > 0 else "decreases_anomaly_risk",
            )
        )
    # Sort by absolute SHAP impact
    drivers.sort(key=lambda d: abs(d.shap_value), reverse=True)

    summary = (
        f"Top driver is '{drivers[0].label}' (SHAP attribution: {drivers[0].shap_value:+.3f}). "
        f"Joint contribution of top 3 features accounts for {sum(abs(d.shap_value) for d in drivers[:3]):.2f} "
        f"of total anomaly score."
    )

    return ShapExplanationResponse(
        well_id=well_id,
        timestamp=latest.timestamp,
        predicted_anomaly=latest.predicted_anomaly,
        anomaly_score=latest.anomaly_score,
        base_value=0.035,
        top_drivers=drivers[:8],
        natural_language_summary=summary,
    )


@app.get("/api/v1/dyno-card/{well_id}", response_model=DynoCardResponse)
def get_dyno_card(well_id: str, db: Session = Depends(get_db)) -> DynoCardResponse:
    """Generate high-resolution Dynamometer Card (Polished Rod Load vs Stroke Position) for SRP pump diagnosis."""
    latest = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )
    meta = db.query(WellMetadata).filter(WellMetadata.well_id == well_id).first()
    stroke_length = meta.stroke_length_in if meta else 120.0
    load_kn = latest.polished_rod_load if latest else 230.0
    spm = latest.stroke_speed if latest else 10.0
    card_type = latest.dyno_card_type if latest else "Normal"

    card_data = generate_dynamometer_card(
        well_id=well_id,
        stroke_length_in=stroke_length,
        current_load_kn=load_kn,
        stroke_speed_spm=spm,
        card_type=card_type,
    )

    return DynoCardResponse(
        well_id=well_id,
        timestamp=latest.timestamp if latest else datetime.utcnow(),
        card_type=card_data["card_type"],
        pprl_lbs=card_data["pprl_lbs"],
        mprl_lbs=card_data["mprl_lbs"],
        stroke_length_in=card_data["stroke_length_in"],
        indicated_pump_hp=card_data["indicated_pump_hp"],
        pump_fillage_pct=card_data["pump_fillage_pct"],
        diagnostic_message=card_data["diagnostic_message"],
        points=card_data["points"],
    )


@app.get("/api/v1/css-status/{well_id}", response_model=CssCycleMetrics)
def get_css_status(well_id: str, db: Session = Depends(get_db)) -> CssCycleMetrics:
    """Get Cyclic Steam Stimulation (CSS) thermal metrics, steam-oil ratio, and viscosity curves."""
    latest = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )
    meta = db.query(WellMetadata).filter(WellMetadata.well_id == well_id).first()

    phase = meta.css_phase if meta else (latest.css_phase if latest else "PRODUCTION")
    steam_temp = latest.steam_temp if latest else 280.0
    steam_press = latest.steam_pressure if latest else 1300.0
    steam_qual = latest.steam_quality if latest else 75.0

    metrics = compute_css_cycle_metrics(
        well_id=well_id,
        steam_temp_c=steam_temp,
        steam_pressure_psi=steam_press,
        steam_quality_pct=steam_qual,
        day_in_phase=8,
        phase=phase,
    )
    return CssCycleMetrics(**metrics)


@app.get("/api/v1/alerts", response_model=list[AlertSchema])
def list_alerts(limit: int = 50, db: Session = Depends(get_db)) -> list[AlertSchema]:
    """Retrieve recent field anomaly alerts and diagnostic audit logs."""
    alerts = (
        db.query(AlertRecord)
        .order_by(AlertRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        AlertSchema(
            id=a.id,
            timestamp=a.timestamp,
            well_id=a.well_id,
            severity=a.severity,
            anomaly_type=a.anomaly_type,
            description=a.description,
            root_cause=a.root_cause,
            recommended_action=a.recommended_action,
            acknowledged=a.acknowledged,
        )
        for a in alerts
    ]


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Acknowledge an alert by a field operator."""
    alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"status": "success", "message": f"Alert {alert_id} acknowledged."}


@app.post("/api/v1/simulator/step")
def simulator_step(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Generate one live telemetry tick across all wells and score models."""
    from scripts.simulate_telemetry import generate_telemetry_tick
    updated = generate_telemetry_tick(db)
    return {"status": "ok", "wells_updated": updated, "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/weather")
def get_weather() -> dict[str, Any]:
    """Return live ambient weather metrics for the Baghewala oilfield asset."""
    return fetch_field_weather()


@app.post("/api/v1/copilot/chat", response_model=CopilotResponse)
def copilot_chat(payload: CopilotRequest, db: Session = Depends(get_db)) -> CopilotResponse:
    """Process natural language query with real-time field context and ML insights."""
    res = generate_copilot_response(payload.message, db)
    return CopilotResponse(
        query=res["query"],
        answer=res["answer"],
        category=res["category"],
        suggested_actions=res["suggested_actions"],
    )


@app.get("/api/v1/report/{well_id}")
def generate_well_report(well_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Generate executive technical audit and compliance health report for a well."""
    meta = db.query(WellMetadata).filter(WellMetadata.well_id == well_id).first()
    latest = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.well_id == well_id)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )
    alerts = (
        db.query(AlertRecord)
        .filter(AlertRecord.well_id == well_id)
        .order_by(AlertRecord.timestamp.desc())
        .limit(5)
        .all()
    )
    if not meta or not latest:
        raise HTTPException(status_code=404, detail=f"Well {well_id} not found or has no telemetry")

    return {
        "report_id": f"OIL-AUDIT-{well_id}-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
        "generated_at": datetime.utcnow().isoformat(),
        "asset": settings.FIELD_NAME,
        "well_id": well_id,
        "well_name": meta.well_name,
        "well_type": meta.well_type,
        "current_status": meta.status.upper(),
        "mechanical_specs": {
            "depth_m": meta.depth_m,
            "pump_depth_m": meta.pump_depth_m,
            "stroke_length_in": meta.stroke_length_in,
            "plunger_diameter_in": meta.plunger_diameter_in,
            "oil_gravity_api": meta.oil_gravity_api,
            "target_production_bpd": meta.target_production_bpd,
        },
        "operating_snapshot": {
            "casing_pressure_psi": latest.casing_pressure,
            "tubing_pressure_psi": latest.tubing_pressure,
            "rod_load_kn": latest.polished_rod_load,
            "stroke_speed_spm": latest.stroke_speed,
            "optimal_speed_spm": latest.optimal_speed,
            "motor_temp_c": latest.motor_temp,
            "vibration_rms": latest.vibration_rms,
            "flow_rate_bpd": latest.flow_rate,
            "dyno_card_type": latest.dyno_card_type,
            "anomaly_detected": latest.predicted_anomaly,
            "anomaly_score": latest.anomaly_score,
        },
        "recent_alerts": [
            {
                "timestamp": a.timestamp.isoformat(),
                "severity": a.severity,
                "type": a.anomaly_type,
                "action": a.recommended_action,
            }
            for a in alerts
        ],
        "compliance_signoff": "Approved for SCADA optimization under SIH26120 protocol.",
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Oil India SIH26120 Digital Twin API is running",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "weather_url": "/api/v1/weather",
    }
