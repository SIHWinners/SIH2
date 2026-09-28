from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class WellMetadataSchema(BaseModel):
    well_id: str
    well_name: str
    well_type: str = "SRP"
    field_name: str = "Oil India - Baghewala Asset"
    depth_m: float = 1200.0
    oil_gravity_api: float = 18.0
    pump_depth_m: float = 1050.0
    stroke_length_in: float = 120.0
    plunger_diameter_in: float = 1.75
    target_production_bpd: float = 125.0
    css_cycle_number: int = 1
    css_phase: str = "PRODUCTION"
    status: str = "healthy"


class TelemetryCreate(BaseModel):
    timestamp: datetime | None = None
    well_id: str = Field(..., min_length=1, max_length=64)
    well_type: str = Field(default="SRP")
    casing_pressure: float = Field(..., gt=0)
    tubing_pressure: float = Field(..., gt=0)
    polished_rod_load: float = Field(..., gt=0)
    stroke_speed: float = Field(..., gt=0)
    motor_temp: float = Field(..., gt=0)
    flow_rate: float | None = Field(default=None)
    water_cut: float | None = Field(default=None)
    power_consumption: float | None = Field(default=None)
    vibration_rms: float | None = Field(default=None)
    dyno_card_type: str | None = Field(default="Normal")
    css_phase: str | None = Field(default="NONE")
    steam_temp: float | None = Field(default=0.0)
    steam_pressure: float | None = Field(default=0.0)
    steam_quality: float | None = Field(default=0.0)


class TelemetryResponse(TelemetryCreate):
    flow_rate: float
    water_cut: float
    power_consumption: float
    vibration_rms: float
    dyno_card_type: str
    css_phase: str
    steam_temp: float
    steam_pressure: float
    steam_quality: float
    predicted_anomaly: bool
    optimal_speed: float
    anomaly_score: float


class PredictRequest(BaseModel):
    well_id: str = Field(..., min_length=1, max_length=64)
    casing_pressure: float = Field(..., gt=0)
    tubing_pressure: float = Field(..., gt=0)
    polished_rod_load: float = Field(..., gt=0)
    stroke_speed: float = Field(..., gt=0)
    motor_temp: float = Field(..., gt=0)
    steam_temp: float | None = Field(default=0.0)
    water_cut: float | None = Field(default=15.0)


class PredictResponse(BaseModel):
    well_id: str
    timestamp: datetime
    predicted_anomaly: bool
    anomaly_score: float
    optimal_speed: float
    expected_flow_rate: float
    energy_savings_pct: float
    explanation: str
    shap_contributions: dict[str, float]
    scada_action_recommendation: str


class WellStatus(BaseModel):
    well_id: str
    well_name: str = ""
    well_type: str = "SRP"
    last_timestamp: str | None = None
    status: str
    anomaly_count: int = 0
    average_optimal_speed: float = 0.0
    latest_casing_pressure: float = 0.0
    latest_rod_load: float = 0.0
    latest_stroke_speed: float = 0.0
    latest_flow_rate: float = 0.0
    latest_motor_temp: float = 0.0
    css_phase: str = "NONE"


class AlertSchema(BaseModel):
    id: int
    timestamp: datetime
    well_id: str
    severity: str
    anomaly_type: str
    description: str
    root_cause: str
    recommended_action: str
    acknowledged: bool


class DynoCardPoint(BaseModel):
    position_in: float
    surface_load_lbs: float
    downhole_load_lbs: float


class DynoCardResponse(BaseModel):
    well_id: str
    timestamp: datetime
    card_type: str  # Normal, Fluid Pound, Gas Interference, Parted Rod
    pprl_lbs: float  # Peak Polished Rod Load
    mprl_lbs: float  # Minimum Polished Rod Load
    stroke_length_in: float
    indicated_pump_hp: float
    pump_fillage_pct: float
    diagnostic_message: str
    points: list[DynoCardPoint]


class CssCycleMetrics(BaseModel):
    well_id: str
    cycle_number: int
    current_phase: str  # INJECTION, SOAKING, PRODUCTION
    phase_day: int
    total_phase_days: int
    steam_temp_c: float
    steam_pressure_psi: float
    steam_quality_pct: float
    cumulative_steam_injected_tons: float
    current_sor: float  # Steam-Oil Ratio (m3 steam / m3 oil)
    reservoir_viscosity_cp: float
    casing_thermal_stress_psi: float
    next_transition_estimate_days: int
    operational_recommendation: str


class ShapFeatureDriver(BaseModel):
    feature: str
    label: str
    value: float
    baseline: float
    shap_value: float
    impact: str  # "increases_anomaly_risk" or "decreases_anomaly_risk"


class ShapExplanationResponse(BaseModel):
    well_id: str
    timestamp: datetime
    predicted_anomaly: bool
    anomaly_score: float
    base_value: float
    top_drivers: list[ShapFeatureDriver]
    natural_language_summary: str


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class CopilotResponse(BaseModel):
    query: str
    answer: str
    category: str
    suggested_actions: list[str]
