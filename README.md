# Digital Twin for Well-to-Surface Optimization (CSS & SRP)
**Problem Statement ID: SIH26120 (Oil India Limited)**  
**Asset Focus:** Baghewala Heavy Oil Asset (Western Asset / Assam-Arakan Basin)

---

## 📌 Executive Summary

This enterprise-grade Digital Twin delivers real-time time-series monitoring, machine learning anomaly detection, stroke speed optimization, and explainable AI (XAI) for both **Sucker Rod Pumping (SRP)** systems and **Cyclic Steam Stimulation (CSS)** heavy oil thermal recovery operations.

Built for **Oil India Limited** under Smart India Hackathon (SIH26120), this solution bridges downhole wellbore physics with surface production facilities to eliminate equipment failures, prevent rod parting, optimize strokes per minute (SPM), and maximize heavy oil lift efficiency.

---

## 🌟 Key Technical Features

### 1. Dual Operational Mode Modeling (CSS & SRP)
- **Sucker Rod Pump (SRP) Digital Twin**:
  - Mechanical stress monitoring: Polished Rod Load (PRL), Peak/Minimum Rod Loads (PPRL/MPRL).
  - Downhole-to-surface pressure dynamics: Casing Pressure, Tubing Backpressure, Motor Temperature, Electrical Power Draw, and Vibration RMS.
  - **High-Resolution Dynamometer Card Engine**: 36-point Surface & Downhole pump cards with automated pattern recognition for **Normal Operation**, **Fluid Pound**, **Gas Interference**, **Parted Sucker Rod**, and **Worn Barrel / Traveling Valve Leakage**.
- **Cyclic Steam Stimulation (CSS) Thermal Recovery Twin**:
  - 3-Phase Cycle Tracking: **Steam Injection (Huff)** $\rightarrow$ **Thermal Soaking** $\rightarrow$ **Production (Puff)**.
  - Thermal metrics: Downhole steam temperature ($250-310^\circ\text{C}$), injection pressure, steam quality (%), and Cumulative Steam Injected (CSI).
  - Heavy Oil Viscosity Reduction Curve: Powered by the ASTM D341 heavy crude viscosity equation for Baghewala heavy crude ($18^\circ \text{API}$).
  - Steam-Oil Ratio (SOR) calculation and thermal breakthrough early warnings.

### 2. Machine Learning & Explainable AI (XAI)
- **Unsupervised Anomaly Detection**:
  - `IsolationForest` pipeline with StandardScaler and median imputation, trained on multi-sensor lag features ($t-1$) and rolling moving averages ($3\text{-pt}$).
  - Calibrated 0–100% anomaly risk score.
- **Supervised Speed Optimization**:
  - `RandomForestRegressor` predicting optimal strokes per minute (SPM) based on current well inflow, backpressure, and fluid viscosity to prevent fluid pound and maximize BPD flow rate.
- **Explainable AI (SHAP Engine)**:
  - Powered by `shap.TreeExplainer` on a curated background dataset.
  - Computes exact local Shapley feature attributions, explaining *why* an anomaly was flagged (e.g., $+0.34$ from motor thermal surge, $+0.21$ from rod overload).
- **Automated SCADA Control Rule Engine**:
  - Automatically recommends actionable VFD motor frequency trim or shut-in actions (e.g., *"Reduce VFD frequency to target 7.5 SPM and initiate hot-water wax flush protocol"*).

### 3. Industrial Data Architecture
- **FastAPI REST API**: High-throughput endpoints for telemetry ingestion, historical query, what-if simulation, dyno card retrieval, CSS tracking, and alert management.
- **Hybrid Database Layer**: Seamless zero-configuration SQLite for instant local development, with automatic connection pooling (`psycopg2`) for enterprise PostgreSQL deployments.
- **Live SCADA Simulator**: Generates realistic time-series with noise, daily cyclic trends, and intermittent faults for both SRP and CSS wells.

---

## 🏗️ System Architecture

```
+--------------------------------------------------------------------------+
|                     OIL INDIA FIELD WELLHEAD SENSORS                     |
|     [SRP Beam Units: Load / SPM]    [CSS Thermal Units: Steam / Press]   |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                    FASTAPI TELEMETRY INGESTION ENGINE                    |
|              /api/v1/telemetry  •  /api/v1/predict/simulate              |
+--------------------+-------------------------------+---------------------+
                     |                               |
                     v                               v
+-----------------------------------+   +----------------------------------+
|     MACHINE LEARNING PIPELINE     |   |       POSTGRESQL DATABASE        |
| - IsolationForest (Anomaly Detect)|   | - well_metadata                  |
| - RandomForest (Optimal Speed)    |   | - sensor_telemetry (Time-Series) |
| - SHAP Explainability Engine      |   | - anomaly_alerts                 |
| - Dynamometer Card Synthesizer    |   | - Connection Pooling (Psycopg2)  |
+--------------------+--------------+   +------------------+---------------+
                     |                                     |
                     +------------------+------------------+
                                        |
                                        v
+--------------------------------------------------------------------------+
|                     STREAMLIT DIGITAL TWIN DASHBOARD                     |
| - Field Command Center         - CSS Thermal Recovery Cycle Tracker      |
| - SRP Downhole Dyno Card View  - What-If Simulation Sandbox              |
| - Explainable AI SHAP View     - Live SCADA Telemetry Feed               |
+--------------------------------------------------------------------------+
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12 (recommended) or Docker

### 1. Local Setup
```bash
# Clone or navigate to the directory
cd c:\Users\SNEH\Desktop\SIH2

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# Install dependencies (FastAPI, Streamlit, Scikit-learn, SHAP, Plotly, etc.)
pip install -r requirements.txt
```

### 2. Generate Dataset & Train ML Models
```bash
python -m app.ml.train_models
```
*Outputs: `models/isolation_forest.joblib`, `models/random_forest_regressor.joblib`, `models/shap_background.joblib`, and `models/model_metadata.json`.*

### 3. Seed Demo Telemetry Data
```bash
python scripts/seed_demo_data.py
```
*Seeds 48 hours of historical sensor data and operational alerts for 4 SRP wells and 3 CSS wells.*

### 4. Run the Modern React + Vite Web App (Recommended for SIH)
```bash
cd web
npm install
npm run dev
```
- **Modern React Digital Twin UI:** [http://127.0.0.1:5173](http://127.0.0.1:5173)
  - Animated 2D Sucker Rod Pump (Nodding Donkey) synced with motor SPM
  - Animated CSS Thermal Recovery Wellbore & Reservoir Sand Model
  - Interactive Dynamometer Card (Surface vs Downhole Pump Card)
  - SHAP Explainable AI Waterfall Bar Chart
  - Live AI Oilfield Operations Copilot Drawer
  - Live Open-Meteo Thar Desert Weather Integration
  - "What-If" Simulation Sandbox & VFD Setpoint Dispatch

### 5. Run the Backend API
```bash
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- Live Weather: [http://127.0.0.1:8000/api/v1/weather](http://127.0.0.1:8000/api/v1/weather)
- AI Copilot: `POST http://127.0.0.1:8000/api/v1/copilot/chat`
- Compliance Report: [http://127.0.0.1:8000/api/v1/report/SRP-001](http://127.0.0.1:8000/api/v1/report/SRP-001)

### 6. (Optional) Run the Streamlit Dashboard
```bash
python -m streamlit run frontend/app.py --server.port 8501
```
- Streamlit Dashboard: [http://127.0.0.1:8501](http://127.0.0.1:8501)

### 6. (Optional) Run Live Background SCADA Telemetry Streamer
```bash
python scripts/simulate_telemetry.py
```

---

## 🐳 Docker Deployment (Full Production Stack)

To run the complete system (PostgreSQL 16, FastAPI Backend, Streamlit Frontend) in Docker:

```bash
docker-compose up --build
```
- PostgreSQL: Port `5432` (initialized with `scripts/init_postgres.sql`)
- FastAPI Backend: Port `8000`
- Streamlit Dashboard: Port `8501`

---

## 🧪 Automated Test Suite

Run the full unit and integration test suite with `pytest`:

```bash
pytest tests -v
```

All 14 tests cover:
- API health and readiness
- Well list and detailed engineering specifications
- Global dashboard status aggregation
- High-resolution Dynamometer Card physics calculation
- CSS thermal cycle metrics and viscosity decay
- SHAP explainability engine attributions
- Interactive "What-If" simulation endpoint
- Live telemetry ingestion and database merge

---

## 📂 Project Structure

```
SIH2/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI endpoints & lifespan
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── mock_data.py            # Physics-based synthetic generator (SRP & CSS)
│   │   └── train_models.py         # IsolationForest, RandomForest, SHAP pipeline
│   ├── services/
│   │   ├── __init__.py
│   │   └── predictor.py            # Inference, SHAP XAI, Dyno Card, CSS calculations
│   ├── config.py                   # App configuration & environment settings
│   ├── database.py                 # SQLAlchemy session & pooling (Postgres/SQLite)
│   ├── models.py                   # WellMetadata, TelemetryRecord, AlertRecord
│   └── schemas.py                  # Pydantic request/response schemas
├── frontend/
│   └── app.py                      # Streamlit Enterprise Industrial Digital Twin
├── scripts/
│   ├── init_postgres.sql           # Production PostgreSQL DDL & indexes
│   ├── seed_demo_data.py           # Historical telemetry and alert seeding
│   └── simulate_telemetry.py       # Live SCADA telemetry generator
├── tests/
│   ├── test_api.py                 # API integration tests
│   └── test_ml.py                  # Machine learning & physics unit tests
├── data/
│   └── mock_sensor_data.csv        # Historical training dataset
├── models/
│   ├── isolation_forest.joblib     # Serialized anomaly detection pipeline
│   ├── random_forest_regressor.joblib # Serialized speed optimizer pipeline
│   ├── shap_background.joblib     # Representative background for SHAP
│   └── model_metadata.json         # Model parameters and evaluation metrics
├── docker-compose.yml              # Multi-container Docker deployment
├── Dockerfile                      # FastAPI production container
├── Dockerfile.frontend             # Streamlit container
├── requirements.txt                # Pinned production dependencies
└── README.md                       # Project documentation
```

---

## 🏆 Smart India Hackathon Presentation Highlights

When demonstrating this project to the evaluation panel:
1. **Highlight Oil India Domain Alignment**: Specifically point out the distinction between **SRP (Sucker Rod Pumping)** mechanical beam units and **CSS (Cyclic Steam Stimulation)** thermal recovery cycles in heavy oil assets like Baghewala.
2. **Showcase the Dynamometer Card**: Open **Tab 2** to demonstrate the interactive Polished Rod Load vs Stroke Position curve, showing how the digital twin identifies downhole fluid pound and gas lock before surface damage occurs.
3. **Demonstrate Explainable AI (SHAP)**: Walk through the SHAP Waterfall chart showing the exact numerical driver of every anomaly alarm.
4. **Interactive What-If Simulation**: In **Tab 4**, slide Casing Pressure down to $90\text{ psi}$ and Rod Load down to $170\text{ kN}$ to instantly watch the model detect Fluid Pound and command the VFD controller to throttle pump speed.
