def analyze_heatmap(features):
    """
    Analyze FortyGuard GeoJSON temperature tiles
    and identify heat hotspots.
    """

    tiles = []

    # -------------------------------------------------------
    # Extract temperature information from every tile
    # -------------------------------------------------------

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

    # -------------------------------------------------------
    # No usable data
    # -------------------------------------------------------

    if not tiles:
        return {
            "tiles_analyzed": 0,
            "hotspots": [],
            "overall_risk": "UNKNOWN"
        }

    # -------------------------------------------------------
    # Calculate overall statistics
    # -------------------------------------------------------

    temperatures = [
        tile["temperature"]
        for tile in tiles
    ]

    average_temperature = (
        sum(temperatures) / len(temperatures)
    )

    maximum_temperature = max(temperatures)

    minimum_temperature = min(temperatures)

    # -------------------------------------------------------
    # Identify hotspots
    #
    # A hotspot is a tile that is:
    #   1. At least 1.5°C hotter than the area average
    #   OR
    #   2. 33°C or hotter
    # -------------------------------------------------------

    hotspots = []

    for tile in tiles:

        temperature = tile["temperature"]

        if (
            temperature >= 33
            or temperature >= average_temperature + 1.5
        ):

            if temperature >= 35:
                risk = "EXTREME"

            elif temperature >= 33:
                risk = "HIGH"

            else:
                risk = "MODERATE"

            hotspots.append({
                "tile_id": tile["tile_id"],
                "temperature": round(
                    temperature,
                    2
                ),
                "risk_level": risk,
                "geometry": tile["geometry"]
            })

    # -------------------------------------------------------
    # Sort hottest tiles first
    # -------------------------------------------------------

    hotspots.sort(
        key=lambda hotspot: hotspot["temperature"],
        reverse=True
    )

    # -------------------------------------------------------
    # Determine overall area risk
    # -------------------------------------------------------

    if maximum_temperature >= 35:
        overall_risk = "EXTREME"

    elif maximum_temperature >= 33:
        overall_risk = "HIGH"

    elif average_temperature >= 30:
        overall_risk = "MODERATE"

    else:
        overall_risk = "LOW"

    # -------------------------------------------------------
    # Return analysis
    # -------------------------------------------------------

    return {
        "tiles_analyzed": len(tiles),

        "temperature": {
            "minimum": round(
                minimum_temperature,
                2
            ),
            "maximum": round(
                maximum_temperature,
                2
            ),
            "average": round(
                average_temperature,
                2
            ),
            "unit": "Celsius"
        },

        "overall_risk": overall_risk,

        "hotspot_count": len(hotspots),

        "hotspots": hotspots
    }