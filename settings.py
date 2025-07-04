import json
import os

SETTINGS_FILE = "user_settings.json"

DEFAULT_SETTINGS = {
    "volume": 0.5,
    "screen_width": 800,
    "screen_height": 600,
    "fullscreen": False,
    "key_bindings": {
        "move_left": "a",
        "move_right": "d",
        "move_up": "w",
        "move_down": "s",
        "dash": "space"
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                settings = json.load(f)
                merged = DEFAULT_SETTINGS.copy()
                merged.update(settings)
                if "key_bindings" in settings:
                    merged["key_bindings"].update(settings["key_bindings"])
                return merged
            except Exception:
                return DEFAULT_SETTINGS.copy()
    else:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)