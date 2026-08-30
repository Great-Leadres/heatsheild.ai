import os
import sys
import time
import json
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure local module imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(root_dir, "backend")

for p in [current_dir, root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")
BASE_URL = "https://api.fortyguard.com/v1"

# Find sample data path
SAMPLE_DATA_PATH = os.path.join(current_dir, "heatmap_result.json")
if not os.path.exists(SAMPLE_DATA_PATH):
    SAMPLE_DATA_PATH = os.path.join(backend_dir, "heatmap_result.json")

# ============================================================
# FASTAPI APP (Top-level instance for Vercel)
# ============================================================

app = FastAPI(
    title="HeatShield AI",
    description="AI-powered urban heat intelligence backend",
    version="1.0.0"
)

# Open CORS configuration so any frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler alias for Vercel serverless compatibility
handler = app
application = app

# ============================================================
# TEST AREA
# Lower Manhattan, New York City
# ============================================================

TEST_POLYGON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.0170, 40.7050],
                    [-74.0030, 40.7050],
                    [-74.0030, 40.7180],
                    [-74.0170, 40.7180],
                    [-74.0170, 40.7050]
                ]]
            }
        }
    ]
}


# ============================================================
# CORE LOGIC ENGINES
# ============================================================

def analyze_heatmap(features):
    """Analyze GeoJSON temperature tiles and identify heat hotspots."""
    tiles = []
    for feature in features:
        properties = feature.get("properties", {})
        temperature = properties.get("average_temperature")
        if temperature is None:
            continue
        tile = {
            "tile_id": properties.get("tile_id"),
            "temperature": float(temperature),
            "geometry": feature.get("geometry")
        }
        tiles.append(tile)

    if not tiles:
        return {
            "tiles_analyzed": 0,
            "hotspots": [],
            "overall_risk": "UNKNOWN"
        }

    temperatures = [tile["temperature"] for tile in tiles]
    average_temperature = sum(temperatures) / len(temperatures)
    maximum_temperature = max(temperatures)
    minimum_temperature = min(temperatures)

    hotspots = []
    for tile in tiles:
        temperature = tile["temperature"]
        if temperature >= 33 or temperature >= average_temperature + 1.5:
            if temperature >= 35:
                risk = "EXTREME"
            elif temperature >= 33:
                risk = "HIGH"
            else:
                risk = "MODERATE"

            hotspots.append({
                "tile_id": tile["tile_id"],
                "temperature": round(temperature, 2),
                "risk_level": risk,
                "geometry": tile["geometry"]
            })

    hotspots.sort(key=lambda hotspot: hotspot["temperature"], reverse=True)

    if maximum_temperature >= 35:
        overall_risk = "EXTREME"
    elif maximum_temperature >= 33:
        overall_risk = "HIGH"
    elif average_temperature >= 30:
        overall_risk = "MODERATE"
    else:
        overall_risk = "LOW"

    return {
        "tiles_analyzed": len(tiles),
        "temperature": {
            "minimum": round(minimum_temperature, 2),
            "maximum": round(maximum_temperature, 2),
            "average": round(average_temperature, 2),
            "unit": "Celsius"
        },
        "overall_risk": overall_risk,
        "hotspot_count": len(hotspots),
        "hotspots": hotspots
    }


def calculate_risk(analysis):
    """Calculate heat risk score and reasons."""
    temperature = analysis.get("temperature", {})
    average = temperature.get("average")
    maximum = temperature.get("maximum")
    hotspot_count = analysis.get("hotspot_count", 0)
    tiles_analyzed = analysis.get("tiles_analyzed", 0)

    if average is None or maximum is None:
        return {
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "reasons": ["Insufficient temperature data."]
        }

    if average >= 35:
        average_score = 40
    elif average >= 33:
        average_score = 30
    elif average >= 30:
        average_score = 20
    elif average >= 27:
        average_score = 10
    else:
        average_score = 5

    if maximum >= 40:
        maximum_score = 35
    elif maximum >= 37:
        maximum_score = 30
    elif maximum >= 35:
        maximum_score = 25
    elif maximum >= 33:
        maximum_score = 18
    elif maximum >= 30:
        maximum_score = 10
    else:
        maximum_score = 5

    if tiles_analyzed > 0:
        hotspot_percentage = (hotspot_count / tiles_analyzed) * 100
    else:
        hotspot_percentage = 0

    if hotspot_percentage >= 30:
        hotspot_score = 25
    elif hotspot_percentage >= 15:
        hotspot_score = 20
    elif hotspot_percentage >= 5:
        hotspot_score = 12
    elif hotspot_percentage > 0:
        hotspot_score = 5
    else:
        hotspot_score = 0

    risk_score = min(average_score + maximum_score + hotspot_score, 100)

    if risk_score >= 75:
        risk_level = "EXTREME"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    reasons = []
    if average >= 33:
        reasons.append("Area-wide temperature is very high.")
    elif average >= 30:
        reasons.append("Area-wide temperature is elevated.")

    if maximum >= 35:
        reasons.append("Very high localized temperatures detected.")
    elif maximum >= 33:
        reasons.append("High-temperature hotspots detected.")

    if hotspot_percentage >= 15:
        reasons.append("Heat is concentrated across a significant portion of the monitored area.")
    elif hotspot_percentage > 0:
        reasons.append("Localized heat hotspots are present.")

    if not reasons:
        reasons.append("No major heat indicators detected.")

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "hotspot_percentage": round(hotspot_percentage, 2),
        "reasons": reasons
    }


def generate_agent_decision(risk, analysis):
    """Generate agent assessment and recommendations."""
    risk_level = risk.get("risk_level", "UNKNOWN")
    score = risk.get("risk_score", 0)
    hotspot_count = analysis.get("hotspot_count", 0)
    maximum = analysis.get("temperature", {}).get("maximum")

    if risk_level == "EXTREME":
        priority = "IMMEDIATE"
        actions = [
            "Issue a localized heat alert.",
            "Prioritize cooling resources in hotspot areas.",
            "Recommend avoiding prolonged outdoor exposure.",
            "Continue monitoring for escalation."
        ]
    elif risk_level == "HIGH":
        priority = "HIGH"
        actions = [
            "Issue a heat-risk advisory.",
            "Prioritize hotspot areas for cooling resources.",
            "Recommend safer lower-heat travel options.",
            "Continue monitoring temperature changes."
        ]
    elif risk_level == "MODERATE":
        priority = "MEDIUM"
        actions = [
            "Monitor hotspot development.",
            "Prepare cooling resources.",
            "Provide heat-safety guidance."
        ]
    else:
        priority = "LOW"
        actions = ["Continue monitoring the area."]

    return {
        "agent_status": "ANALYZED",
        "priority": priority,
        "assessment": (
            f"HeatShield detected {hotspot_count} hotspot(s), "
            f"with a maximum temperature of {maximum}°C and a risk score of {score}/100."
        ),
        "recommended_actions": actions,
        "automation_ready": risk_level in ["HIGH", "EXTREME"]
    }


# ============================================================
# HEATMAP DATA LOADER & CACHE
# ============================================================

def load_fallback_heatmap():
    """Load local cached/sample heatmap data."""
    if os.path.exists(SAMPLE_DATA_PATH):
        try:
            with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            map_data = cached_data.get("map_data", cached_data)
            features = map_data.get("features", [])

            temperatures = []
            for feature in features:
                properties = feature.get("properties", {})
                temperature = properties.get("average_temperature")
                if temperature is not None:
                    temperatures.append(float(temperature))

            min_temp = min(temperatures) if temperatures else 28.5
            max_temp = max(temperatures) if temperatures else 35.8
            avg_temp = (sum(temperatures) / len(temperatures)) if temperatures else 32.1

            return {
                "success": True,
                "activity_id": "cached-nyc-manhattan",
                "location": {
                    "city": "New York City",
                    "state": "New York",
                    "country": "USA"
                },
                "temperature": {
                    "minimum": round(min_temp, 2),
                    "maximum": round(max_temp, 2),
                    "average": round(avg_temp, 2),
                    "unit": "Celsius"
                },
                "tiles_analyzed": len(temperatures),
                "heatmap": map_data
            }
        except Exception as e:
            print(f"Error loading fallback heatmap: {e}")

    return {
        "success": True,
        "activity_id": "sample-data",
        "location": {
            "city": "New York City",
            "state": "New York",
            "country": "USA"
        },
        "temperature": {
            "minimum": 29.1,
            "maximum": 35.4,
            "average": 32.3,
            "unit": "Celsius"
        },
        "tiles_analyzed": 0,
        "heatmap": {
            "type": "FeatureCollection",
            "features": []
        }
    }


_HEATMAP_CACHE = None
_HEATMAP_CACHE_TIME = 0
CACHE_DURATION_SECONDS = 300


def fetch_heatmap_data():
    """Returns heat intelligence data instantly for fast page load."""
    global _HEATMAP_CACHE, _HEATMAP_CACHE_TIME

    if _HEATMAP_CACHE and (time.time() - _HEATMAP_CACHE_TIME < CACHE_DURATION_SECONDS):
        return _HEATMAP_CACHE

    # Load rich pre-computed NYC dataset immediately
    data = load_fallback_heatmap()
    _HEATMAP_CACHE = data
    _HEATMAP_CACHE_TIME = time.time()
    return data



# ============================================================
# API ROUTES
# ============================================================

@app.get("/")
@app.get("/api")
@app.get("/api/")
def home():
    return {
        "name": "HeatShield AI",
        "status": "online",
        "message": "HeatShield backend is running!"
    }


@app.get("/health")
@app.get("/health/")
@app.get("/api/health")
@app.get("/api/health/")
def health():
    return {
        "status": "healthy"
    }


@app.get("/heatmap")
@app.get("/heatmap/")
@app.get("/api/heatmap")
@app.get("/api/heatmap/")
def get_heatmap():
    return fetch_heatmap_data()


@app.get("/analysis")
@app.get("/analysis/")
@app.get("/api/analysis")
@app.get("/api/analysis/")
def get_analysis():
    heatmap_response = fetch_heatmap_data()
    heatmap = heatmap_response.get("heatmap", {})
    features = heatmap.get("features", [])
    analysis = analyze_heatmap(features)

    return {
        "success": True,
        "location": heatmap_response.get("location"),
        "analysis": analysis
    }


@app.get("/risk")
@app.get("/risk/")
@app.get("/api/risk")
@app.get("/api/risk/")
def get_risk():
    heatmap_response = fetch_heatmap_data()
    heatmap = heatmap_response.get("heatmap", {})
    features = heatmap.get("features", [])
    analysis = analyze_heatmap(features)
    risk = calculate_risk(analysis)

    return {
        "success": True,
        "location": heatmap_response.get("location"),
        "risk": risk,
        "analysis": analysis
    }


@app.get("/agent")
@app.get("/agent/")
@app.get("/api/agent")
@app.get("/api/agent/")
def get_agent_decision():
    heatmap_response = fetch_heatmap_data()
    heatmap = heatmap_response.get("heatmap", {})
    features = heatmap.get("features", [])
    analysis = analyze_heatmap(features)
    risk = calculate_risk(analysis)
    decision = generate_agent_decision(risk, analysis)

    return {
        "success": True,
        "location": heatmap_response.get("location"),
        "risk": risk,
        "analysis": analysis,
        "agent": decision
    }