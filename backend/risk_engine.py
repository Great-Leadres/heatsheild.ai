def calculate_risk(analysis):

    temperature = analysis.get("temperature", {})

    average = temperature.get("average")
    maximum = temperature.get("maximum")

    hotspot_count = analysis.get(
        "hotspot_count",
        0
    )

    tiles_analyzed = analysis.get(
        "tiles_analyzed",
        0
    )

    if average is None or maximum is None:

        return {
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "reasons": [
                "Insufficient temperature data."
            ]
        }

    # Average temperature component
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

    # Maximum temperature component
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

    # Hotspot concentration
    if tiles_analyzed > 0:
        hotspot_percentage = (
            hotspot_count / tiles_analyzed
        ) * 100
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

    risk_score = min(
        average_score +
        maximum_score +
        hotspot_score,
        100
    )

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
        reasons.append(
            "Area-wide temperature is very high."
        )
    elif average >= 30:
        reasons.append(
            "Area-wide temperature is elevated."
        )

    if maximum >= 35:
        reasons.append(
            "Very high localized temperatures detected."
        )
    elif maximum >= 33:
        reasons.append(
            "High-temperature hotspots detected."
        )

    if hotspot_percentage >= 15:
        reasons.append(
            "Heat is concentrated across a significant "
            "portion of the monitored area."
        )
    elif hotspot_percentage > 0:
        reasons.append(
            "Localized heat hotspots are present."
        )

    if not reasons:
        reasons.append(
            "No major heat indicators detected."
        )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "hotspot_percentage": round(
            hotspot_percentage,
            2
        ),
        "reasons": reasons
    }