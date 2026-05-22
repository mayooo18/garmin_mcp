from custom.profile.store import load_profile
from custom.logic.helpers import safe_get
from datetime import date


def compute_verdict(
    body_battery: int,
    sleep_hours: float,
    sleep_score: int,
    hrv_status: str,
    stress: int,
    threshold: int
) -> tuple[str, str]:
    """
    Returns a (verdict, reason) tuple.
    verdict is one of: run_hard, run_easy, rest
    """
    score = 0

    # Body battery (0-100)
    if body_battery >= 70:   score += 3
    elif body_battery >= 50: score += 2
    elif body_battery >= 30: score += 1
    else:                    score += 0

    # Sleep hours
    if sleep_hours >= 7.5:   score += 3
    elif sleep_hours >= 6.5: score += 2
    elif sleep_hours >= 5.5: score += 1
    else:                    score += 0

    # Sleep score (0-100)
    if sleep_score >= 75:    score += 2
    elif sleep_score >= 55:  score += 1
    else:                    score += 0

    # HRV status
    if hrv_status == "BALANCED":    score += 2
    elif hrv_status == "LOW":       score += 1
    elif hrv_status == "UNBALANCED": score += 0

    # Stress (lower is better)
    if stress <= 25:   score += 2
    elif stress <= 50: score += 1
    else:              score += 0

    # Max possible score is 12
    if score >= 9:
        return "run_hard", f"Body battery {body_battery}, slept {sleep_hours}h, HRV {hrv_status}. You are well recovered."
    elif score >= 6:
        return "run_easy", f"Body battery {body_battery}, slept {sleep_hours}h. Good enough for an easy run but not a hard effort."
    else:
        return "rest", f"Body battery {body_battery}, slept {sleep_hours}h, stress {stress}. Your body needs recovery today."


async def get_recovery_summary() -> dict:
    """
    Computes a recovery verdict using body battery, sleep, HRV, and stress.
    Returns a plain-English recommendation: run hard, run easy, or rest.
    """
    from garmin_mcp.tools.health import (
        get_body_battery,
        get_sleep_data,
        get_hrv_data,
        get_stats
    )

    profile = load_profile()
    threshold = profile.get("rest_day_threshold", 40)
    today = date.today().isoformat()

    # Fetch all data in parallel sources
    stats        = await get_stats(today)
    sleep        = await get_sleep_data(today)
    body_battery = await get_body_battery(today)
    hrv          = await get_hrv_data(today)

    # Extract values safely
    battery_value = 0
    if isinstance(body_battery, list) and body_battery:
        battery_value = body_battery[-1].get("value", 0) or 0

    sleep_dto   = safe_get(sleep, "dailySleepDTO", default={})
    sleep_hours = round(sleep_dto.get("sleepTimeSeconds", 0) / 3600, 1)
    sleep_score = sleep_dto.get("sleepScore", 0) or 0

    hrv_status  = safe_get(hrv, "lastNight", "hrvStatus", default="UNKNOWN")
    stress      = stats.get("averageStressLevel", 50) or 50

    verdict, reason = compute_verdict(
        body_battery=battery_value,
        sleep_hours=sleep_hours,
        sleep_score=sleep_score,
        hrv_status=hrv_status,
        stress=stress,
        threshold=threshold
    )

    return {
        "date":           today,
        "verdict":        verdict,
        "reason":         reason,
        "body_battery":   battery_value,
        "sleep_hours":    sleep_hours,
        "sleep_score":    sleep_score,
        "hrv_status":     hrv_status,
        "stress":         stress,
        "recommendation": {
            "run_hard":  "Go for it. Do your planned hard workout.",
            "run_easy":  "Keep it easy. Zone 2 or a short comfortable run.",
            "rest":      "Skip the run today. Walk, stretch, or do nothing.",
        }.get(verdict, "")
    }
