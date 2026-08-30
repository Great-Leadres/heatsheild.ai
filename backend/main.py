import os
import sys
import time
import json
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure local module imports work seamlessly regardless of how the file is run
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.heat_analysis import analyze_heatmap
    from backend.risk_engine import calculate_risk
    from backend.agent import generate_agent_decision
except ImportError:
    from heat_analysis import analyze_heatmap
    from risk_engine import calculate_risk
    from agent import generate_agent_decision

# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")
BASE_URL = "https://api.fortyguard.com/v1"
SAMPLE_DATA_PATH = os.path.join(current_dir, "heatmap_result.json")

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="HeatShield AI",
    description="AI-powered urban heat intelligence backend",
    version="1.0.0"
)

# Open CORS configuration so any frontend (local, preview, production) can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def load_fallback_heatmap():
    """Load local cached/sample heatmap data if FortyGuard API is unavailable."""
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
            print(f"Error loading fallback heatmap from {SAMPLE_DATA_PATH}: {e}")

    # Default fallback if file is missing
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


# In-memory cache for live result to avoid repeated slow polling on serverless
_HEATMAP_CACHE = None
_HEATMAP_CACHE_TIME = 0
CACHE_DURATION_SECONDS = 300  # 5 minutes cache


def fetch_heatmap_data():
    global _HEATMAP_CACHE, _HEATMAP_CACHE_TIME

    # Return in-memory cached response if fresh
    if _HEATMAP_CACHE and (time.time() - _HEATMAP_CACHE_TIME < CACHE_DURATION_SECONDS):
        return _HEATMAP_CACHE

    if not API_KEY or API_KEY == "your_fortyguard_api_key_here":
        fallback = load_fallback_heatmap()
        _HEATMAP_CACHE = fallback
        _HEATMAP_CACHE_TIME = time.time()
        return fallback

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "polygon_aoi": TEST_POLYGON,
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1
        },
        "granularity": 100
    }

    try:
        response = requests.post(
            f"{BASE_URL}/heatmap",
            headers=headers,
            json=payload,
            timeout=10
        )
        if not response.ok:
            print(f"FortyGuard submission returned {response.status_code}: {response.text}")
            fallback = load_fallback_heatmap()
            _HEATMAP_CACHE = fallback
            _HEATMAP_CACHE_TIME = time.time()
            return fallback

        submission = response.json()
        activity_id = submission.get("data", {}).get("activity_id")
        if not activity_id:
            fallback = load_fallback_heatmap()
            _HEATMAP_CACHE = fallback
            _HEATMAP_CACHE_TIME = time.time()
            return fallback

        # Poll with short timeout (suitable for serverless function execution)
        status_url = f"{BASE_URL}/status/{activity_id}"
        for _ in range(6):  # Poll max 6 times (~12s total)
            time.sleep(2)
            try:
                status_response = requests.get(
                    status_url,
                    headers={"api-key": API_KEY},
                    timeout=10
                )
            except Exception:
                continue

            if not status_response.ok:
                continue

            status_json = status_response.json()
            data = status_json.get("data", {})
            status = str(data.get("status", "")).lower()

            if status in ("completed", "succeeded"):
                result = data.get("result", {})
                map_data = result.get("map_data", {})
                features = map_data.get("features", [])

                temperatures = []
                for feature in features:
                    properties = feature.get("properties", {})
                    temperature = properties.get("average_temperature")
                    if temperature is not None:
                        temperatures.append(float(temperature))

                min_temp = min(temperatures) if temperatures else None
                max_temp = max(temperatures) if temperatures else None
                avg_temp = (sum(temperatures) / len(temperatures)) if temperatures else None

                res = {
                    "success": True,
                    "activity_id": activity_id,
                    "location": {
                        "city": "New York City",
                        "state": "New York",
                        "country": "USA"
                    },
                    "temperature": {
                        "minimum": min_temp,
                        "maximum": max_temp,
                        "average": avg_temp,
                        "unit": "Celsius"
                    },
                    "tiles_analyzed": len(temperatures),
                    "heatmap": map_data
                }
                _HEATMAP_CACHE = res
                _HEATMAP_CACHE_TIME = time.time()
                return res
            elif status in ("failed", "error"):
                break

    except Exception as e:
        print(f"FortyGuard request exception: {e}")

    fallback = load_fallback_heatmap()
    _HEATMAP_CACHE = fallback
    _HEATMAP_CACHE_TIME = time.time()
    return fallback


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
@app.get("/api")
def home():
    return {
        "name": "HeatShield AI",
        "status": "online",
        "message": "HeatShield backend is running!"
    }


@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# FORTYGUARD HEATMAP
# ============================================================

@app.get("/heatmap")
@app.get("/api/heatmap")
def get_heatmap():
    return fetch_heatmap_data()


# ============================================================
# STEP 8 — HEAT ANALYSIS
# ============================================================

@app.get("/analysis")
@app.get("/api/analysis")
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


# ============================================================
# STEP 9 — RISK ENGINE
# ============================================================

@app.get("/risk")
@app.get("/api/risk")
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


# ============================================================
# STEP 10 — HEATSHIELD AGENT
# ============================================================

@app.get("/agent")
@app.get("/api/agent")
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