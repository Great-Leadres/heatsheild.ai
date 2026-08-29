import os
import time
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.heat_analysis import analyze_heatmap
from backend.risk_engine import calculate_risk
from backend.agent import generate_agent_decision


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

BASE_URL = "https://api.fortyguard.com/v1"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="HeatShield AI",
    description="AI-powered urban heat intelligence backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
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


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def home():
    return {
        "name": "HeatShield AI",
        "status": "online",
        "message": "HeatShield backend is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# FORTYGUARD HEATMAP
# ============================================================

@app.get("/api/heatmap")
def get_heatmap():

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="FORTYGUARD_API_KEY is not configured."
        )

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

    # --------------------------------------------------------
    # Submit heatmap request
    # --------------------------------------------------------

    try:

        response = requests.post(
            f"{BASE_URL}/heatmap",
            headers=headers,
            json=payload,
            timeout=60
        )

    except requests.RequestException as error:

        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to FortyGuard: {error}"
        )

    if not response.ok:

        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    submission = response.json()

    try:

        activity_id = submission["data"]["activity_id"]

    except (KeyError, TypeError):

        raise HTTPException(
            status_code=502,
            detail="FortyGuard returned an unexpected response."
        )

    # --------------------------------------------------------
    # Poll for completed result
    # --------------------------------------------------------

    status_url = f"{BASE_URL}/status/{activity_id}"

    for _ in range(60):

        try:

            status_response = requests.get(
                status_url,
                headers={
                    "api-key": API_KEY
                },
                timeout=60
            )

        except requests.RequestException as error:

            raise HTTPException(
                status_code=502,
                detail=f"Could not check FortyGuard status: {error}"
            )

        if not status_response.ok:

            raise HTTPException(
                status_code=status_response.status_code,
                detail=status_response.text
            )

        status_json = status_response.json()

        data = status_json.get(
            "data",
            {}
        )

        status = str(
            data.get("status", "")
        ).lower()

        # ----------------------------------------------------
        # Completed
        # ----------------------------------------------------

        if status in (
            "completed",
            "succeeded"
        ):

            result = data.get(
                "result",
                {}
            )

            map_data = result.get(
                "map_data",
                {}
            )

            features = map_data.get(
                "features",
                []
            )

            # ------------------------------------------------
            # Extract temperatures
            # ------------------------------------------------

            temperatures = []

            for feature in features:

                properties = feature.get(
                    "properties",
                    {}
                )

                temperature = properties.get(
                    "average_temperature"
                )

                if temperature is not None:

                    temperatures.append(
                        float(temperature)
                    )

            # ------------------------------------------------
            # Calculate statistics
            # ------------------------------------------------

            if temperatures:

                minimum_temperature = min(
                    temperatures
                )

                maximum_temperature = max(
                    temperatures
                )

                average_temperature = (
                    sum(temperatures)
                    / len(temperatures)
                )

            else:

                minimum_temperature = None
                maximum_temperature = None
                average_temperature = None

            # ------------------------------------------------
            # Return HeatShield response
            # ------------------------------------------------

            return {
                "success": True,

                "activity_id": activity_id,

                "location": {
                    "city": "New York City",
                    "state": "New York",
                    "country": "USA"
                },

                "temperature": {
                    "minimum": minimum_temperature,
                    "maximum": maximum_temperature,
                    "average": average_temperature,
                    "unit": "Celsius"
                },

                "tiles_analyzed": len(
                    temperatures
                ),

                "heatmap": map_data
            }

        # ----------------------------------------------------
        # Failed
        # ----------------------------------------------------

        elif status in (
            "failed",
            "error"
        ):

            raise HTTPException(
                status_code=502,
                detail="FortyGuard heatmap processing failed."
            )

        # ----------------------------------------------------
        # Still processing
        # ----------------------------------------------------

        time.sleep(5)

    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    raise HTTPException(
        status_code=504,
        detail="FortyGuard heatmap processing timed out."
    )


# ============================================================
# STEP 8 — HEAT ANALYSIS
# ============================================================

@app.get("/api/analysis")
def get_analysis():

    # Get FortyGuard heatmap
    heatmap_response = get_heatmap()

    heatmap = heatmap_response.get(
        "heatmap",
        {}
    )

    features = heatmap.get(
        "features",
        []
    )

    # Analyze temperature tiles
    analysis = analyze_heatmap(
        features
    )

    return {
        "success": True,

        "location": heatmap_response.get(
            "location"
        ),

        "analysis": analysis
    }


# ============================================================
# STEP 9 — RISK ENGINE
# ============================================================

@app.get("/api/risk")
def get_risk():

    # Get FortyGuard heatmap
    heatmap_response = get_heatmap()

    heatmap = heatmap_response.get(
        "heatmap",
        {}
    )

    features = heatmap.get(
        "features",
        []
    )

    # Analyze heatmap
    analysis = analyze_heatmap(
        features
    )

    # Calculate HeatShield risk
    risk = calculate_risk(
        analysis
    )

    return {
        "success": True,

        "location": heatmap_response.get(
            "location"
        ),

        "risk": risk,

        "analysis": analysis
    }


# ============================================================
# STEP 10 — HEATSHIELD AGENT
# ============================================================

@app.get("/api/agent")
def get_agent_decision():

    # Get FortyGuard heatmap
    heatmap_response = get_heatmap()

    heatmap = heatmap_response.get(
        "heatmap",
        {}
    )

    features = heatmap.get(
        "features",
        []
    )

    # Analyze heat
    analysis = analyze_heatmap(
        features
    )

    # Calculate risk
    risk = calculate_risk(
        analysis
    )

    # Generate agent decision
    decision = generate_agent_decision(
        risk,
        analysis
    )

    return {
        "success": True,

        "location": heatmap_response.get(
            "location"
        ),

        "risk": risk,

        "analysis": analysis,

        "agent": decision
    }