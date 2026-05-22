import json
import os

PROFILE_FILE = os.path.join(os.path.dirname(__file__), "user_profile.json")

def load_profile() -> dict:
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profile(profile: dict):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=2)