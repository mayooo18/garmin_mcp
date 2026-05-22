from custom.profile.store import load_profile
from custom.logic.helpers import meters_to_miles, format_time
from datetime import date, timedelta


def mileage_score(peak_weekly_miles: float) -> int:
    if peak_weekly_miles >= 50:   return 100
    elif peak_weekly_miles >= 40: return 85
    elif peak_weekly_miles >= 30: return 65
    elif peak_weekly_miles >= 20: return 40
    else:                         return 15


def long_run_score(longest_miles: float) -> int:
    if longest_miles >= 20:   return 100
    elif longest_miles >= 18: return 80
    elif longest_miles >= 16: return 60
    elif longest_miles >= 14: return 40
    else:                     return 15


def pace_score(avg_pace_seconds: float, target_pace: int = 480) -> int:
    gap = avg_pace_seconds - target_pace
    if gap <= 0:    return 100
    elif gap <= 15: return 85
    elif gap <= 30: return 65
    elif gap <= 60: return 40
    else:           return 15


def vo2_score(vo2max: float) -> int:
    if vo2max >= 55:   return 100
    elif vo2max >= 50: return 85
    elif vo2max >= 45: return 65
    elif vo2max >= 40: return 40
    else:              return 20


def consistency_score(weeks_active: int) -> int:
    if weeks_active >= 11:  return 100
    elif weeks_active >= 9: return 80
    elif weeks_active >= 7: return 55
    elif weeks_active >= 5: return 30
    else:                   return 10


def recovery_score(training_status: str) -> int:
    status_map = {
        "PRODUCTIVE":    100,
        "PEAKING":       100,
        "MAINTAINING":   80,
        "UNPRODUCTIVE":  50,
        "OVERREACHING":  20,
    }
    return status_map.get(str(training_status).upper(), 60)


def get_verdict(score: float) -> str:
    if score >= 85:
        return "You are on track. A 3:30 is very realistic if you stay healthy."
    elif score >= 70:
        return "Close but not quite. A few more long runs would make a big difference."
    elif score >= 50:
        return "You could finish the marathon but 3:30 may be a stretch. Consider targeting 3:45 to 4:00."
    else:
        return "Your training base is not ready for a 3:30 marathon right now. Build up gradually."


def find_top_gap(scores: dict) -> str:
    worst_key = min(scores, key=scores.get)
    labels = {
        "mileage":     "weekly mileage",
        "long_run":    "longest run distance",
        "pace":        "recent running pace",
        "vo2max":      "VO2 max fitness level",
        "consistency": "training consistency",
        "recovery":    "recovery and training load",
    }
    return f"Your biggest gap right now is {labels.get(worst_key, worst_key)}."


def project_finish_time(
    readiness_score: float,
    recent_pace_seconds: float,
    vo2max: float
) -> dict:
    base = recent_pace_seconds * 26.2

    if recent_pace_seconds < 480:   fatigue = 1.05
    elif recent_pace_seconds < 540: fatigue = 1.08
    else:                           fatigue = 1.12

    projected = base * fatigue

    if readiness_score >= 80:   margin = 300
    elif readiness_score >= 60: margin = 600
    else:                       margin = 900

    return {
        "best_case":  format_time(projected - margin),
        "projected":  format_time(projected),
        "worst_case": format_time(projected + margin),
    }


async def get_marathon_readiness() -> dict:
    """
    Analyzes marathon readiness using 6 pillars:
    weekly mileage, longest run, recent pace, VO2 max,
    consistency, and recovery status.
    Returns a readiness score and projected finish time range.
    """
    from garmin_mcp.tools.activities import get_activities
    from garmin_mcp.tools.health import get_training_status, get_max_metrics

    profile = load_profile()
    target_pace = profile.get("target_pace_seconds", 480)
    marathon_target = profile.get("marathon_target", "3:30")

    today = date.today()
    twelve_weeks_ago = today - timedelta(weeks=12)

    # Fetch data
    activities      = await get_activities(start=0, limit=100)
    training_status = await get_training_status(today.isoformat())
    max_metrics     = await get_max_metrics(today.isoformat())

    # Filter to running activities in past 12 weeks
    runs = [
        a for a in (activities or [])
        if a.get("activityType", {}).get("typeKey") == "running"
        and a.get("startTimeLocal", "") >= twelve_weeks_ago.isoformat()
    ]

    # Weekly mileage — group runs by week
    weekly_miles = {}
    for run in runs:
        run_date = date.fromisoformat(run["startTimeLocal"][:10])
        week = run_date.isocalendar()[1]
        miles = meters_to_miles(run.get("distance", 0))
        weekly_miles[week] = weekly_miles.get(week, 0) + miles

    peak_weekly = max(weekly_miles.values()) if weekly_miles else 0
    weeks_active = len(weekly_miles)

    # Longest run
    longest = max(
        (meters_to_miles(r.get("distance", 0)) for r in runs),
        default=0
    )

    # Recent pace — average of last 5 runs
    recent_runs = sorted(runs, key=lambda r: r.get("startTimeLocal", ""), reverse=True)[:5]
    paces = []
    for r in recent_runs:
        dist = r.get("distance", 0)
        dur = r.get("duration", 0)
        if dist > 0 and dur > 0:
            paces.append((dur / dist) * 1609.34)  # seconds per mile
    avg_pace = sum(paces) / len(paces) if paces else target_pace + 60

    # VO2 max
    vo2max = (max_metrics or {}).get("vo2MaxValue", 0) or 0

    # Training status
    status = (training_status or {}).get("trainingStatus", {}).get("latestTrainingStatusPhase", "UNKNOWN")

    # Score each pillar
    scores = {
        "mileage":     mileage_score(peak_weekly),
        "long_run":    long_run_score(longest),
        "pace":        pace_score(avg_pace, target_pace),
        "vo2max":      vo2_score(vo2max),
        "consistency": consistency_score(weeks_active),
        "recovery":    recovery_score(status),
    }

    weights = {
        "mileage":     0.25,
        "long_run":    0.25,
        "pace":        0.20,
        "vo2max":      0.15,
        "consistency": 0.10,
        "recovery":    0.05,
    }

    total = sum(scores[k] * weights[k] for k in scores)

    return {
        "marathon_target":    marathon_target,
        "readiness_score":    round(total),
        "pillar_scores":      scores,
        "peak_weekly_miles":  round(peak_weekly, 1),
        "longest_run_miles":  round(longest, 1),
        "weeks_active":       weeks_active,
        "avg_recent_pace":    format_time(avg_pace) + " /mile" if avg_pace else "no data",
        "vo2max":             vo2max,
        "training_status":    status,
        "projected_finish":   project_finish_time(total, avg_pace, vo2max),
        "verdict":            get_verdict(total),
        "top_gap":            find_top_gap(scores),
    }