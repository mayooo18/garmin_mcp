from custom.profile.store import load_profile, save_profile


async def get_user_profile() -> dict:
    """
    Returns all stored user preferences.
    Claude should call this at the start of any fitness question
    to know the user's goals, stats, and custom settings.
    """
    profile = load_profile()

    return {
        "calorie_goal":        profile.get("calorie_goal", "maintenance"),
        "calorie_adjustment":  profile.get("calorie_adjustment", None),
        "marathon_target":     profile.get("marathon_target", "3:30"),
        "target_pace_seconds": profile.get("target_pace_seconds", 480),
        "age":                 profile.get("age", None),
        "weight_kg":           profile.get("weight_kg", None),
        "height_cm":           profile.get("height_cm", None),
        "sex":                 profile.get("sex", None),
        "low_carb":            profile.get("low_carb", False),
        "rest_day_threshold":  profile.get("rest_day_threshold", 40),
        "preferences_set":     len(profile) > 0
    }


async def save_user_preference(key: str, value: str) -> dict:
    """
    Saves a single user preference by key and value.
    Call this whenever the user states a preference in conversation.
    Examples:
      key="calorie_adjustment", value="-250"
      key="marathon_target", value="3:45"
      key="low_carb", value="true"
      key="age", value="28"
    """
    profile = load_profile()

    if value.lower() in ("true", "false"):
        profile[key] = value.lower() == "true"
    elif value.lstrip("-").isdigit():
        profile[key] = int(value)
    else:
        try:
            profile[key] = float(value)
        except ValueError:
            profile[key] = value

    save_profile(profile)
    return {"saved": True, "key": key, "value": profile[key]}


async def reset_user_profile() -> dict:
    """
    Clears all stored user preferences and resets to defaults.
    Use when the user wants to start fresh with new goals.
    """
    save_profile({})
    return {"reset": True, "message": "All preferences cleared. Starting fresh."}