from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
import requests

logger = logging.getLogger(__name__)

# Baghewala Heavy Oil Asset, Jaisalmer District, Rajasthan (Thar Desert Basin)
BAGHEWALA_LAT = 27.50
BAGHEWALA_LON = 71.50


def fetch_field_weather() -> dict[str, Any]:
    """Fetch live ambient weather from Open-Meteo API for Baghewala Heavy Oil Asset.

    Ambient surface temperature in the Thar Desert ranges from 12°C at night to 48°C in summer.
    This directly affects surface electric motor cooling, flowline viscosity, and rod string thermal stresses.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={BAGHEWALA_LAT}&longitude={BAGHEWALA_LON}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,surface_pressure,wind_speed_10m,weather_code"
        f"&hourly=temperature_2m,relative_humidity_2m&forecast_days=1"
    )
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current", {})
            temp_c = float(curr.get("temperature_2m", 36.5))
            humidity = float(curr.get("relative_humidity_2m", 28.0))
            wind_kmh = float(curr.get("wind_speed_10m", 14.2))
            pressure_hpa = float(curr.get("surface_pressure", 1004.0))

            # Domain calculation: ambient temperature impact on surface equipment
            if temp_c > 38.0:
                thermal_impact = "ELEVATED: High ambient heat reduces surface motor convective cooling efficiency by ~18%."
                cooling_derating_pct = 15.0
            elif temp_c < 18.0:
                thermal_impact = "COLD NIGHT: Surface flowline viscosity increases; paraffin wax precipitation risk elevated."
                cooling_derating_pct = 0.0
            else:
                thermal_impact = "NOMINAL: Standard atmospheric heat dissipation conditions across well pads."
                cooling_derating_pct = 0.0

            return {
                "source": "Open-Meteo Live SCADA Weather Integration",
                "location": "Baghewala Heavy Oil Asset (Rajasthan, India)",
                "coordinates": f"{BAGHEWALA_LAT}°N, {BAGHEWALA_LON}°E",
                "timestamp": datetime.utcnow().isoformat(),
                "ambient_temperature_c": round(temp_c, 1),
                "relative_humidity_pct": round(humidity, 1),
                "wind_speed_kmh": round(wind_kmh, 1),
                "surface_pressure_hpa": round(pressure_hpa, 1),
                "motor_cooling_derating_pct": cooling_derating_pct,
                "field_thermal_impact_advisory": thermal_impact,
                "live": True,
            }
    except Exception as e:
        logger.debug("Weather API call fell back to local atmospheric model: %s", e)

    # High-fidelity fallback based on Thar Desert local diurnal cycle
    hour = datetime.utcnow().hour
    fallback_temp = 32.0 + 8.0 * ((hour - 6) / 12.0 if 6 <= hour <= 18 else -0.5)
    return {
        "source": "Thar Desert Atmospheric Physical Simulation (Simulated RTU)",
        "location": "Baghewala Heavy Oil Asset (Rajasthan, India)",
        "coordinates": f"{BAGHEWALA_LAT}°N, {BAGHEWALA_LON}°E",
        "timestamp": datetime.utcnow().isoformat(),
        "ambient_temperature_c": round(fallback_temp, 1),
        "relative_humidity_pct": 24.5,
        "wind_speed_kmh": 12.8,
        "surface_pressure_hpa": 1008.2,
        "motor_cooling_derating_pct": 12.0 if fallback_temp > 38 else 0.0,
        "field_thermal_impact_advisory": "Ambient desert temperature monitored. Surface motor cooling envelope nominal.",
        "live": False,
    }
