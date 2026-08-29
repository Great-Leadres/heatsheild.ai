def generate_agent_decision(risk, analysis):

    risk_level = risk.get(
        "risk_level",
        "UNKNOWN"
    )

    score = risk.get(
        "risk_score",
        0
    )

    hotspot_count = analysis.get(
        "hotspot_count",
        0
    )

    maximum = analysis.get(
        "temperature",
        {}
    ).get("maximum")

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

        actions = [
            "Continue monitoring the area."
        ]

    return {
        "agent_status": "ANALYZED",

        "priority": priority,

        "assessment": (
            f"HeatShield detected {hotspot_count} "
            f"hotspot(s), with a maximum temperature "
            f"of {maximum}°C and a risk score of {score}/100."
        ),

        "recommended_actions": actions,

        "automation_ready": risk_level in [
            "HIGH",
            "EXTREME"
        ]
    }