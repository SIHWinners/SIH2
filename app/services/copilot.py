from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.models import AlertRecord, TelemetryRecord, WellMetadata
from app.services.predictor import infer_and_score

logger = logging.getLogger(__name__)


def generate_copilot_response(query: str, db: Session) -> dict[str, Any]:
    """Process natural language queries using real-time field context, ML inferences, and petroleum engineering logic."""
    q = query.lower().strip()
    wells = db.query(WellMetadata).all()
    alerts = db.query(AlertRecord).filter(AlertRecord.acknowledged == False).all()

    # Identify if a specific well was mentioned
    target_well = None
    for w in wells:
        if w.well_id.lower() in q or w.well_id.lower().replace("-", "") in q:
            target_well = w.well_id
            break

    # 1. FIELD STATUS & SUMMARY
    if any(k in q for k in ["summary", "overview", "field status", "how is the field", "healthy", "overall"]):
        total = len(wells)
        critical = [w.well_id for w in wells if w.status == "critical"]
        warning = [w.well_id for w in wells if w.status == "warning"]
        healthy = [w.well_id for w in wells if w.status == "healthy"]

        answer = (
            f"**Oil India Field Operations Summary (Baghewala Asset):**\n\n"
            f"- **Total Monitored Units:** {total} Wells (4 Sucker Rod Pump units, 3 Cyclic Steam Stimulation thermal units).\n"
            f"- **Healthy Units ({len(healthy)}):** {', '.join(healthy)} — operating within nominal mechanical and thermal limits.\n"
            f"- **Warning Units ({len(warning)}):** {', '.join(warning) if warning else 'None'} — showing early sensor drift or underfillage.\n"
            f"- **Critical Units ({len(critical)}):** {', '.join(critical) if critical else 'None'} — requires immediate SCADA intervention.\n\n"
            f"**Active SCADA Alarms ({len(alerts)} unacknowledged):**\n"
        )
        for a in alerts[:3]:
            answer += f"- **{a.well_id} [{a.severity}]**: {a.anomaly_type} — *{a.recommended_action}*\n"
        return {
            "query": query,
            "answer": answer,
            "category": "field_summary",
            "suggested_actions": ["Inspect Critical Units", "Run Anomaly Simulation", "Review Dyno Cards"],
        }

    # 2. SPECIFIC WELL INQUIRY
    if target_well:
        latest = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.well_id == target_well)
            .order_by(TelemetryRecord.timestamp.desc())
            .first()
        )
        meta = db.query(WellMetadata).filter(WellMetadata.well_id == target_well).first()
        is_css = target_well.startswith("CSS")

        if not latest:
            return {
                "query": query,
                "answer": f"Well {target_well} is configured in asset registry, but no sensor telemetry has been ingested yet.",
                "category": "well_diagnostic",
                "suggested_actions": ["Trigger SCADA Tick", "Check Sensor RTU"],
            }

        if is_css:
            phase = meta.css_phase if meta else latest.css_phase
            answer = (
                f"### Thermal Diagnostic Report: {target_well} (Cyclic Steam Stimulation)\n\n"
                f"- **Current Cycle & Phase:** Cycle {meta.css_cycle_number if meta else 2}, **{phase} Phase**.\n"
                f"- **Downhole Steam Temperature:** `{latest.steam_temp:.1f} °C` (Operating Pressure: `{latest.steam_pressure:.0f} psi`).\n"
                f"- **Steam Quality:** `{latest.steam_quality:.1f} %`.\n"
                f"- **Heavy Oil Viscosity Estimate:** `{max(6.0, 15000.0 * 2.718 ** (-0.028 * latest.steam_temp)):.1f} cP` (Baghewala 18° API crude).\n\n"
            )
            if phase == "INJECTION":
                answer += (
                    f"**Engineering Recommendation:** Maintain continuous high-quality steam injection to reach target cumulative "
                    f"heat front. Monitor offset casing annulus pressures for premature steam breakthrough."
                )
            elif phase == "SOAKING":
                answer += (
                    f"**Engineering Recommendation:** Well is shut-in to allow conductive thermal dissipation into matrix. "
                    f"Prepare surface rod pump for workover reconnection upon completion of soak period."
                )
            else:
                answer += (
                    f"**Engineering Recommendation:** Production phase active. Heavy crude is flowing at `{latest.flow_rate:.1f} BPD`. "
                    f"Adjust beam pump speed to match declining thermal profile as fluid cools."
                )
        else:
            is_anomaly = latest.predicted_anomaly
            status_tag = '[STATUS: CRITICAL ANOMALY]' if (is_anomaly and latest.anomaly_score > 0.8) else ('[STATUS: WARNING THRESHOLD]' if is_anomaly else '[STATUS: NOMINAL OPERATING]')
            answer = (
                f"### Engineering Diagnostic Report: {target_well} (Sucker Rod Pumping Unit)\n\n"
                f"- **Operating Health Status:** `{status_tag}`\n"
                f"- **Current Speed:** `{latest.stroke_speed:.1f} SPM` (AI Recommended Optimal: `{latest.optimal_speed:.1f} SPM`)\n"
                f"- **Polished Rod Load:** `{latest.polished_rod_load:.1f} kN` (Depth: `{meta.depth_m if meta else 1200} m`)\n"
                f"- **Wellbore Pressures:** Casing `{latest.casing_pressure:.0f} psi` • Tubing `{latest.tubing_pressure:.0f} psi`\n"
                f"- **Motor Temperature:** `{latest.motor_temp:.1f} °C` (Vibration: `{latest.vibration_rms:.1f} mm/s`)\n"
                f"- **Dyno Card Classification:** **{latest.dyno_card_type}**\n\n"
            )
            if latest.dyno_card_type == "Fluid Pound":
                answer += (
                    f"**Root Cause Analysis:** Plunger strikes liquid level on downstroke due to low pump fillage (casing pressure `{latest.casing_pressure:.0f} psi`).\n"
                    f"**SCADA Action:** Reduce VFD frequency to `{latest.optimal_speed:.1f} SPM` to allow pump barrel full fluid replenishment."
                )
            elif latest.dyno_card_type == "Worn Barrel" or latest.motor_temp > 80:
                answer += (
                    f"**Root Cause Analysis:** High mechanical drag and elevated motor temperature (`{latest.motor_temp:.1f} °C`). High rod stress (`{latest.polished_rod_load:.1f} kN`).\n"
                    f"**SCADA Action:** Dispatch crew for hot water wax flush and decelerate pump to `{latest.optimal_speed:.1f} SPM` to prevent rod string fatigue parting."
                )
            else:
                answer += (
                    f"**Root Cause Analysis:** Mechanical and hydrodynamic parameters align with optimal production envelope.\n"
                    f"**SCADA Action:** Maintain current VFD setpoint; no manual intervention required."
                )

        return {
            "query": query,
            "answer": answer,
            "category": "well_diagnostic",
            "suggested_actions": [f"View Dyno Card for {target_well}", f"Optimize {target_well}", "Back to Overview"],
        }

    # 3. DYNAMOMETER CARD QUESTIONS
    if any(k in q for k in ["dyno", "dynamometer", "card", "fluid pound", "gas lock"]):
        answer = (
            f"**Understanding Sucker Rod Pump Dynamometer Cards in Oilfield Operations:**\n\n"
            f"A **Dynamometer Card** plots Polished Rod Load (lbs) against Stroke Position (inches) throughout a complete pumping cycle:\n\n"
            f"1. **Surface Card**: Measured at the surface polished rod using a load cell and position transducer. Includes rod stretch and fluid inertia.\n"
            f"2. **Downhole Pump Card**: Calculated using the Gibbs wave equation to isolate the exact behavior of the traveling and standing valves downhole.\n\n"
            f"**Common Failure Shapes Detected by our ML Engine:**\n"
            f"- **Normal Card**: Full rectangular parallelogram showing complete liquid fillage (90%+ volumetric efficiency).\n"
            f"- **Fluid Pound**: Sudden vertical load drop halfway down the downstroke when plunger impacts liquid surface (inflow starvation).\n"
            f"- **Gas Interference**: Rounded, banana-like compression shape due to gas compressibility delaying valve opening.\n"
            f"- **Parted Rod**: Flat, very low load representing only the buoyant weight of broken upper rod segment.\n"
            f"- **Worn Barrel / Traveling Valve Leak**: Sloping top and bottom boundaries caused by continuous fluid slippage."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "technical_knowledge",
            "suggested_actions": ["View SRP-002 Dyno Card", "View SRP-004 Dyno Card", "Test What-If Sandbox"],
        }

    # 4. CSS / THERMAL RECOVERY QUESTIONS
    if any(k in q for k in ["css", "cyclic steam", "steam", "huff and puff", "thermal", "viscosity"]):
        answer = (
            f"**Cyclic Steam Stimulation (CSS / 'Huff-and-Puff') in Heavy Oil Fields:**\n\n"
            f"CSS is the primary thermal enhanced oil recovery (EOR) method utilized by Oil India in heavy crude assets like **Baghewala (Rajasthan)**:\n\n"
            f"1. **Phase 1: Steam Huff (Injection)**: High-pressure, high-temperature steam ($260-310^\\circ\\text{{C}}$, 75-80% quality) is injected downhole for 10-14 days.\n"
            f"2. **Phase 2: Thermal Soaking**: Well is shut-in for 5-8 days. Conductive heat transfer diffuses heat through reservoir sand to dramatically reduce heavy oil viscosity.\n"
            f"3. **Phase 3: Production Puff**: The well is connected to a Sucker Rod Pump (SRP). Hot, mobilized heavy crude flows at high rates before gradually cooling.\n\n"
            f"**Viscosity Physics (ASTM D341):**\n"
            f"At reservoir temperature ($25^\\circ\\text{{C}}$), Baghewala crude has a tar-like viscosity of $\\sim 15,000\\text{{ cP}}$. When heated to $120^\\circ\\text{{C}}$ during CSS production, "
            f"viscosity collapses to $< 45\\text{{ cP}}$, unlocking economic recovery without solvent additives."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "technical_knowledge",
            "suggested_actions": ["View CSS-101 Thermal Twin", "Check Viscosity Curves", "Review SOR Ratios"],
        }

    # 5. CAPABILITIES / WHAT CAN YOU DO
    if any(k in q for k in ["what can you do", "what can u do", "capabilities", "features", "help me", "how to use", "who are you"]):
        answer = (
            f"### OIL INDIA OPERATIONS COPILOT: CAPABILITY MATRIX\n\n"
            f"Grounding Architecture: Live SCADA Telemetry, Thermodynamic Multi-Phase Physics, and Scikit-Learn Predictive Models for Baghewala Field Assets:\n\n"
            f"1. **Real-Time Well Diagnostics**: Query any wellhead (e.g., 'Diagnose SRP-004' or 'Check CSS-001') to retrieve telemetry vectors, motor thermal curves, polished rod loadings, and casing/tubing gradients.\n"
            f"2. **Dynamometer Card Interpretation**: Query 'Explain dyno card' for diagnostic decomposition of surface polished rod and downhole pump stroke cycles.\n"
            f"3. **Thermal EOR & Viscosity Kinetics**: Query 'What is CSS thermal recovery' to review steam breakthrough margins and ASTM D341 heavy oil viscosity collapse.\n"
            f"4. **VFD Stroke Rate Optimization**: Query 'How does AI calculate optimal SPM' to inspect Random Forest Regressor target speeds for maximum lift efficiency.\n"
            f"5. **Field-Wide Operational Briefing**: Query 'Field summary' or 'Show active alarms' for supervisory control indices.\n"
            f"6. **Environmental Impact Tracking**: Query 'Current weather' for ambient Thar Desert solar irradiation, ambient temperatures, and surface gathering line heat loss."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "capabilities",
            "suggested_actions": ["Field Summary", "Diagnose SRP-004", "How does AI calculate SPM?", "Current Weather"],
        }

    # 6. AI & MACHINE LEARNING EXPLANATION
    if any(k in q for k in ["ai", "ml", "machine learning", "model", "algorithm", "random forest", "isolation forest", "shap", "spm", "optimize"]):
        answer = (
            f"### MACHINE LEARNING & PHYSICS-INFORMED ARCHITECTURE\n\n"
            f"Our platform integrates four production mathematical and ML pipelines:\n\n"
            f"1. **Anomaly Detection (IsolationForest)**: Unsupervised high-dimensional isolation forest evaluating multi-sensor vectors (pressures, thermal trends, loads, vibration RMS, stroke frequencies) to compute anomaly contamination scores.\n"
            f"2. **Production Optimization (RandomForestRegressor)**: Non-linear regression pipeline calibrating VFD speed targets to maximize reservoir inflow while attenuating rod fatigue limits.\n"
            f"3. **Explainable AI (SHAP TreeExplainer)**: Computes exact Shapley contribution values for each telemetry feature, transparently attributing risk factors for operator verification.\n"
            f"4. **Gibbs Wave Equation Simulation**: Solves the damped 1D wave equation u_tt = a^2 u_xx - v u_t to convert surface polished rod dynamometer cards into downhole pump stroke loops."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "ai_explanation",
            "suggested_actions": ["Diagnose SRP-001", "Field Summary", "Explain Dyno Card"],
        }

    # 7. WEATHER & ENVIRONMENTAL CONDITIONS
    if any(k in q for k in ["weather", "temperature", "desert", "ambient", "thar", "climate"]):
        from app.services.weather import get_thar_desert_weather
        w = get_thar_desert_weather()
        answer = (
            f"### THAR DESERT METEOROLOGICAL TELEMETRY (BAGHEWALA FIELD)\n\n"
            f"- **Field Coordinates:** 27.50°N, 71.50°E (Jaisalmer Basin, Rajasthan)\n"
            f"- **Ambient Temperature:** `{w.get('temperature_c', 38.0)} °C` ({w.get('weather_condition', 'Arid Desert Conditions')})\n"
            f"- **Relative Humidity:** `{w.get('humidity_percent', 18)} %` • **Wind Speed:** `{w.get('wind_speed_kmh', 14)} km/h`\n"
            f"- **Solar Irradiance:** `{w.get('solar_radiation_w_m2', 820)} W/m²`\n\n"
            f"**Thermodynamic Impact on Heavy Crude:**\n"
            f"High ambient solar heat reduces surface flowline heat loss, mitigating paraffin deposition. However, elevated ambient conditions diminish natural motor convection cooling. "
            f"The digital twin automatically compensates motor overheat alarm thresholds based on ambient weather vectors."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "weather_feed",
            "suggested_actions": ["Field Summary", "Check Motor Temps", "CSS Thermal Recovery"],
        }

    # 8. BAGHEWALA FIELD GEOLOGY
    if any(k in q for k in ["baghewala", "reservoir", "geology", "oil india", "asset", "heavy oil"]):
        answer = (
            f"### ASSET SPECIFICATION: OIL INDIA LIMITED (BAGHEWALA FIELD)\n\n"
            f"- **Basin Designation:** Bikaner-Nagaur Basin, Thar Desert, Rajasthan, India\n"
            f"- **Pay Zone Formation:** Jodhpur Sandstone & Bilara Carbonate (1,100 m – 1,300 m True Vertical Depth)\n"
            f"- **Fluid Classification:** Ultra-Heavy Crude (16°–19° API gravity) with high downhole viscosity (~15,000 cP at initial reservoir temperature of 25°C)\n"
            f"- **Primary Recovery Methodology:** Cyclic Steam Stimulation (CSS) thermal dissipation coupled with Sucker Rod Pumping (SRP) units to achieve commercial production rates."
        )
        return {
            "query": query,
            "answer": answer,
            "category": "geology_knowledge",
            "suggested_actions": ["Field Summary", "What is CSS?", "Diagnose SRP-001"],
        }

    # 9. DEFAULT HELPFUL FALLBACK
    return {
        "query": query,
        "answer": (
            f"I am the **Oil India Digital Twin Operations Copilot**. I analyze live telemetry, SCADA streams, and machine learning models "
            f"across our Baghewala SRP and CSS wells.\n\n"
            f"You can ask me:\n"
            f"- *'How is the field operating today?'*\n"
            f"- *'Why is well SRP-004 in critical state?'*\n"
            f"- *'Explain the dynamometer card for SRP-002.'*\n"
            f"- *'What is the current thermal phase of CSS-001?'*\n"
            f"- *'How does AI calculate optimal pump stroke speed?'*\n"
            f"- *'What is the current weather in Thar Desert?'*"
        ),
        "category": "general_guidance",
        "suggested_actions": ["Field Summary", "Diagnose SRP-004", "Explain Dyno Card", "CSS Thermal Recovery"],
    }
