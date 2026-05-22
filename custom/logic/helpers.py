def format_time(total_seconds: float) -> str:
    """Converts seconds into H:MM:SS string. Example: 12600 -> '3:30:00'"""
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def seconds_to_pace(seconds_per_meter: float) -> str:
    """Converts Garmin's seconds-per-meter pace to MM:SS per mile string."""
    seconds_per_mile = seconds_per_meter * 1609.34
    minutes = int(seconds_per_mile // 60)
    seconds = int(seconds_per_mile % 60)
    return f"{minutes}:{seconds:02d}"


def meters_to_miles(meters: float) -> float:
    """Converts meters to miles rounded to 2 decimal places."""
    return round(meters / 1609.34, 2)


def meters_to_km(meters: float) -> float:
    return round(meters / 1000, 2)


def safe_get(data: dict, *keys, default=None):
    """Safely retrieves a nested key from a dict without crashing."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
    return data