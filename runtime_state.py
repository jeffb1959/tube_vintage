import json
import os


STATE_VERSION = 1
STATE_FILE = "runtime_state.json"
TEMP_STATE_FILE = "runtime_state.tmp"


def _remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass


def save_user_profile(user_profile):
    data = {"version": STATE_VERSION, "user_profile": user_profile}
    try:
        with open(TEMP_STATE_FILE, "w") as temp_file:
            json.dump(data, temp_file)
        _remove_if_present(STATE_FILE)
        os.rename(TEMP_STATE_FILE, STATE_FILE)
        return True
    except (OSError, TypeError, ValueError) as error:
        print("Etat execution : sauvegarde impossible : " + str(error))
        _remove_if_present(TEMP_STATE_FILE)
        return False


def load_user_profile(valid_profiles):
    try:
        with open(STATE_FILE, "r") as state_file:
            data = json.load(state_file)
        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            return None
        user_profile = data.get("user_profile")
        if not isinstance(user_profile, str) or user_profile not in valid_profiles:
            return None
        return user_profile
    except (OSError, TypeError, ValueError):
        return None
