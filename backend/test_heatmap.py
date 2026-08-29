import os
import time
import json
import requests
from dotenv import load_dotenv

# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv()

API_KEY = os.getenv("FORTYGUARD_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "FORTYGUARD_API_KEY was not found. Check your .env file."
    )

BASE_URL = "https://api.fortyguard.com/v1"

HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json",
}


# ============================================================
# TEST AREA
# Lower Manhattan, New York City
# ============================================================

polygon = {
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
# HEATMAP REQUEST
# ============================================================

payload = {
    "polygon_aoi": polygon,
    "date_time": {
        "start_date": "2024-07-15",
        "start_time": "14:00",
        "filter_type": 1
    },
    "granularity": 100
}


# ============================================================
# SUBMIT REQUEST
# ============================================================

print("=" * 60)
print("HEATSHIELD AI - FORTYGUARD API TEST")
print("=" * 60)

print("\n1. Submitting heatmap request...")

response = requests.post(
    f"{BASE_URL}/heatmap",
    headers=HEADERS,
    json=payload,
    timeout=60
)

print("HTTP Status:", response.status_code)

if not response.ok:
    print("\nFortyGuard returned an error:")
    print(response.text)
    response.raise_for_status()

submission = response.json()

print("\nSubmission response:")
print(json.dumps(submission, indent=2))

activity_id = submission["data"]["activity_id"]

print("\n2. Request submitted successfully!")
print("Activity ID:", activity_id)


# ============================================================
# POLL FOR RESULT
# ============================================================

print("\n3. Waiting for FortyGuard to process the request...")

status_url = f"{BASE_URL}/status/{activity_id}"

for attempt in range(60):

    status_response = requests.get(
        status_url,
        headers={
            "api-key": API_KEY
        },
        timeout=60
    )

    if not status_response.ok:
        print("\nStatus request failed:")
        print(status_response.text)
        status_response.raise_for_status()

    status_json = status_response.json()

    data = status_json.get("data", {})
    status = str(data.get("status", "")).lower()

    print(f"Attempt {attempt + 1}: {status}")

    # ========================================================
    # SUCCESS
    # ========================================================

    if status in ("completed", "succeeded"):

        print("\n" + "=" * 60)
        print("HEATMAP COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        result = data.get("result", {})

        # ----------------------------------------------------
        # SAVE COMPLETE RESULT
        # ----------------------------------------------------

        output_file = "backend/heatmap_result.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        print(f"\nComplete result saved to: {output_file}")

        # ----------------------------------------------------
        # GET GEOJSON FEATURES
        # ----------------------------------------------------

        map_data = result.get("map_data", {})
        features = map_data.get("features", [])

        # ----------------------------------------------------
        # EXTRACT TEMPERATURES
        # ----------------------------------------------------

        temperatures = []

        for feature in features:

            properties = feature.get("properties", {})

            temperature = properties.get("average_temperature")

            if temperature is not None:
                temperatures.append(float(temperature))

        # ----------------------------------------------------
        # TEMPERATURE STATISTICS
        # ----------------------------------------------------

        print("\nTEMPERATURE STATISTICS")
        print("-" * 40)

        if temperatures:

            minimum_temperature = min(temperatures)
            maximum_temperature = max(temperatures)
            average_temperature = sum(temperatures) / len(temperatures)

            print(
                "Tiles analyzed:",
                len(temperatures)
            )

            print(
                "Minimum:",
                round(minimum_temperature, 2),
                "°C"
            )

            print(
                "Maximum:",
                round(maximum_temperature, 2),
                "°C"
            )

            print(
                "Average:",
                round(average_temperature, 2),
                "°C"
            )

            print(
                "Temperature range:",
                round(
                    maximum_temperature - minimum_temperature,
                    2
                ),
                "°C"
            )

        else:

            print("No temperature data found.")

        # ----------------------------------------------------
        # GEOJSON CHECK
        # ----------------------------------------------------

        print("\nHEATMAP DATA")

        if features:

            print("GeoJSON received: YES")

            print(
                "Number of geographic tiles:",
                len(features)
            )

        else:

            print("GeoJSON received: NO")

        print("\nDay 1 API test completed!")

        break

    # ========================================================
    # FAILURE
    # ========================================================

    elif status in ("failed", "error"):

        print("\nFortyGuard task failed.")

        print(
            json.dumps(
                status_json,
                indent=2
            )
        )

        raise RuntimeError(
            "FortyGuard heatmap task failed."
        )

    # ========================================================
    # STILL PROCESSING
    # ========================================================

    else:

        time.sleep(5)

else:

    raise TimeoutError(
        "FortyGuard task did not complete within the expected time."
    )