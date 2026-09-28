from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WellMetadata(Base):
    """Stores static engineering configuration and metadata for SRP and CSS wells."""

    __tablename__ = "well_metadata"

    well_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    well_name: Mapped[str] = mapped_column(String(128), nullable=False)
    well_type: Mapped[str] = mapped_column(String(16), nullable=False, default="SRP")  # "SRP" or "CSS"
    field_name: Mapped[str] = mapped_column(String(64), nullable=False, default="Oil India - Baghewala Asset")
    depth_m: Mapped[float] = mapped_column(Float, nullable=False, default=1200.0)
    oil_gravity_api: Mapped[float] = mapped_column(Float, nullable=False, default=18.0)
    pump_depth_m: Mapped[float] = mapped_column(Float, nullable=False, default=1050.0)
    stroke_length_in: Mapped[float] = mapped_column(Float, nullable=False, default=120.0)
    plunger_diameter_in: Mapped[float] = mapped_column(Float, nullable=False, default=1.75)
    target_production_bpd: Mapped[float] = mapped_column(Float, nullable=False, default=125.0)
    css_cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    css_phase: Mapped[str] = mapped_column(String(32), nullable=False, default="PRODUCTION")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="healthy")

    def __repr__(self) -> str:
        return f"<WellMetadata {self.well_id} ({self.well_type})>"


class TelemetryRecord(Base):
    """Stores the sensor snapshot and the model decision for one well at one timestamp."""

    __tablename__ = "sensor_telemetry"
    __table_args__ = (
        Index("ix_sensor_telemetry_well_id_timestamp", "well_id", "timestamp"),
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True, index=True)
    well_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False, index=True)
    well_type: Mapped[str] = mapped_column(String(16), nullable=False, default="SRP")
    casing_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    tubing_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    polished_rod_load: Mapped[float] = mapped_column(Float, nullable=False)
    stroke_speed: Mapped[float] = mapped_column(Float, nullable=False)
    motor_temp: Mapped[float] = mapped_column(Float, nullable=False)
    flow_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    water_cut: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)
    power_consumption: Mapped[float] = mapped_column(Float, nullable=False, default=12.5)
    vibration_rms: Mapped[float] = mapped_column(Float, nullable=False, default=1.8)
    dyno_card_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Normal")
    css_phase: Mapped[str] = mapped_column(String(32), nullable=False, default="NONE")
    steam_temp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    steam_pressure: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    steam_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    predicted_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    optimal_speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return (
            f"TelemetryRecord(timestamp={self.timestamp!r}, well_id={self.well_id!r}, "
            f"predicted_anomaly={self.predicted_anomaly!r}, optimal_speed={self.optimal_speed!r})"
        )


class AlertRecord(Base):
    """Stores logged anomalies and operational alert history for field monitoring."""

    __tablename__ = "anomaly_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    well_id: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="CRITICAL")  # "WARNING", "CRITICAL"
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    root_cause: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(255), nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<AlertRecord {self.id} {self.well_id} {self.anomaly_type}>"
