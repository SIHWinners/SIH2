-- PostgreSQL Initialization Script for Oil India Digital Twin (SIH26120)
-- Schema creation for Well-to-Surface Optimization (CSS & SRP)

CREATE TABLE IF NOT EXISTS well_metadata (
    well_id VARCHAR(64) PRIMARY KEY,
    well_name VARCHAR(128) NOT NULL,
    well_type VARCHAR(16) NOT NULL DEFAULT 'SRP', -- 'SRP' or 'CSS'
    field_name VARCHAR(64) NOT NULL DEFAULT 'Oil India - Baghewala Asset',
    depth_m DOUBLE PRECISION NOT NULL DEFAULT 1200.0,
    oil_gravity_api DOUBLE PRECISION NOT NULL DEFAULT 18.0,
    pump_depth_m DOUBLE PRECISION NOT NULL DEFAULT 1050.0,
    stroke_length_in DOUBLE PRECISION NOT NULL DEFAULT 120.0,
    plunger_diameter_in DOUBLE PRECISION NOT NULL DEFAULT 1.75,
    target_production_bpd DOUBLE PRECISION NOT NULL DEFAULT 125.0,
    css_cycle_number INTEGER NOT NULL DEFAULT 1,
    css_phase VARCHAR(32) NOT NULL DEFAULT 'PRODUCTION',
    status VARCHAR(16) NOT NULL DEFAULT 'healthy'
);

CREATE TABLE IF NOT EXISTS sensor_telemetry (
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    well_id VARCHAR(64) NOT NULL,
    well_type VARCHAR(16) NOT NULL DEFAULT 'SRP',
    casing_pressure DOUBLE PRECISION NOT NULL,
    tubing_pressure DOUBLE PRECISION NOT NULL,
    polished_rod_load DOUBLE PRECISION NOT NULL,
    stroke_speed DOUBLE PRECISION NOT NULL,
    motor_temp DOUBLE PRECISION NOT NULL,
    flow_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    water_cut DOUBLE PRECISION NOT NULL DEFAULT 15.0,
    power_consumption DOUBLE PRECISION NOT NULL DEFAULT 12.5,
    vibration_rms DOUBLE PRECISION NOT NULL DEFAULT 1.8,
    dyno_card_type VARCHAR(32) NOT NULL DEFAULT 'Normal',
    css_phase VARCHAR(32) NOT NULL DEFAULT 'NONE',
    steam_temp DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    steam_pressure DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    steam_quality DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    predicted_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    optimal_speed DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    anomaly_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    PRIMARY KEY (timestamp, well_id)
);

CREATE INDEX IF NOT EXISTS ix_sensor_telemetry_well_id_timestamp 
ON sensor_telemetry (well_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    well_id VARCHAR(64) NOT NULL,
    severity VARCHAR(16) DEFAULT 'CRITICAL',
    anomaly_type VARCHAR(64) NOT NULL,
    description VARCHAR(255) NOT NULL,
    root_cause VARCHAR(255) NOT NULL,
    recommended_action VARCHAR(255) NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_anomaly_alerts_well_id 
ON anomaly_alerts (well_id);

CREATE INDEX IF NOT EXISTS ix_anomaly_alerts_timestamp 
ON anomaly_alerts (timestamp DESC);
