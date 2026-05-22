from custom.profile.store import load_profile


def get_macros(target_calories: int, goal: str) -> dict:
    ratios = {
        "fat_loss":    (0.35, 0.35, 0.30),
        "performance": (0.20, 0.55, 0.25),
        "muscle_gain": (0.30, 0.45, 0.25),
        "maintenance": (0.25, 0.45, 0.30),
    }
    p, c, f = ratios.get(goal, ratios["maintenance"])
    return {
        "protein_g": round((target_calories * p) / 4),
        "carbs_g":   round((target_calories * c) / 4),
        "fat_g":     round((target_calories * f) / 9),
    }


def build_note(goal: str, active_calories: int) -> str:
    notes = {
        "fat_loss":    "Moderate deficit. Keep protein high to protect muscle while running.",
        "performance": "Small surplus to fuel training. Prioritize carbs around workouts.",
        "muscle_gain": "Lean bulk surplus. Strength train consistently to use the extra calories.",
        "maintenance": "Eating at maintenance. Adjust if your weight or training load changes.",
    }
    base = notes.get(goal, "")
    if active_calories < 200:
        base += " Today is a low activity day so the number is on the lower side."
    elif active_calories > 800:
        base += " High activity day — make sure you are eating enough to recover."
    return base


async def recommend_daily_calories(
    goal: str = None,
    custom_adjustment: int = None
) -> dict:
    """
    Recommends daily calorie intake based on Garmin data and user goal.
    Reads bmrKilocalories and activeKilocalories from the user's Garmin stats.
    Falls back to stored profile preferences if no goal is passed in.
    """
    from garmin_mcp.tools.health import get_stats
    from datetime import date

    profile = load_profile()

    # Use stored values if not passed in directly
    goal = goal or profile.get("calorie_goal", "maintenance")
    custom_adjustment = custom_adjustment or profile.get("calorie_adjustment", None)
    sex = profile.get("sex", "male")

    # Pull live Garmin data
    today = date.today().isoformat()
    stats = await get_stats(today)

    bmr = stats.get("bmrKilocalories", 0)
    active = stats.get("activeKilocalories", 0)

    # Fall back to formula if Garmin BMR is missing
    if not bmr:
        weight_kg = profile.get("weight_kg", 70)
        height_cm = profile.get("height_cm", 170)
        age = profile.get("age", 30)
        if sex == "female":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

    tdee = bmr + active

    # Apply adjustment
    presets = {
        "maintenance":  0,
        "fat_loss":    -400,
        "performance": +200,
        "muscle_gain": +300,
    }
    adjustment = custom_adjustment if custom_adjustment is not None else presets.get(goal, 0)
    target = tdee + adjustment

    # Safety minimums
    min_calories = 1600 if sex == "female" else 1800
    target = max(target, min_calories)

    return {
        "date":             today,
        "bmr_calories":     round(bmr),
        "active_calories":  round(active),
        "tdee":             round(tdee),
        "goal":             goal,
        "adjustment":       adjustment,
        "target_calories":  round(target),
        "macros":           get_macros(round(target), goal),
        "note":             build_note(goal, active),
        "custom_override":  custom_adjustment is not None
    }