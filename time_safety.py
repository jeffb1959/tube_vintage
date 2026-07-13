import json
import os
import time


MAX_TIME_WITHOUT_SYNC_SECONDS = 72 * 60 * 60
STATE_FILE = "time_state.json"
TEMP_STATE_FILE = "time_state.tmp"
STATE_VERSION = 1
MIN_VALID_YEAR = 2024
MAX_VALID_YEAR = 2100


_state = {
    "initialized": False,
    "initial_grace_active": False,
    "initial_grace_deadline_ms": None,
    "session_sync_received": False,
    "last_ntp_sync_utc": None,
    "persisted_last_ntp_sync_utc": None,
    "locked": True,
    "reported_threshold_hours": 0,
}


def _is_plausible_timestamp(timestamp):
    if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
        return False

    try:
        year = time.localtime(int(timestamp))[0]
    except (OverflowError, OSError, ValueError, TypeError):
        return False

    return MIN_VALID_YEAR <= year <= MAX_VALID_YEAR


def _load_persisted_state():
    try:
        with open(STATE_FILE, "r") as state_file:
            data = json.load(state_file)

        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            return None

        timestamp = data.get("last_ntp_sync_utc")
        if not _is_plausible_timestamp(timestamp):
            return None
        if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
            return None

        return int(timestamp)
    except (OSError, ValueError, TypeError):
        return None


def initialize(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()

    _state["initialized"] = True
    _state["persisted_last_ntp_sync_utc"] = _load_persisted_state()
    _state["session_sync_received"] = False
    _state["last_ntp_sync_utc"] = None
    _state["initial_grace_active"] = True
    _state["initial_grace_deadline_ms"] = time.ticks_add(
        now_ms, MAX_TIME_WITHOUT_SYNC_SECONDS * 1000
    )
    _state["locked"] = False
    _state["reported_threshold_hours"] = 0

    if _state["persisted_last_ntp_sync_utc"] is None:
        print("Securite temps : aucun etat persistant valide")
    else:
        print("Securite temps : derniere synchronisation enregistree trouvee")

    print(
        "Securite temps : aucune heure valide, periode de grace de 72 heures demarree"
    )
    print("Securite temps : fonctionnement manuel autorise sans Wi-Fi")


def _remove_file_if_present(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def _save_state(timestamp):
    data = {
        "version": STATE_VERSION,
        "last_ntp_sync_utc": int(timestamp),
    }

    try:
        with open(TEMP_STATE_FILE, "w") as temp_file:
            json.dump(data, temp_file)

        _remove_file_if_present(STATE_FILE)
        os.rename(TEMP_STATE_FILE, STATE_FILE)
        return True
    except (OSError, ValueError, TypeError) as error:
        print("Securite temps : sauvegarde impossible : " + str(error))
        _remove_file_if_present(TEMP_STATE_FILE)
        return False


def record_ntp_sync(timestamp_utc):
    if not _is_plausible_timestamp(timestamp_utc):
        print("Securite temps : synchronisation invalide ignoree")
        return False

    was_locked = _state["locked"]
    first_session_sync = not _state["session_sync_received"]
    timestamp_utc = int(timestamp_utc)
    _state["session_sync_received"] = True
    _state["initial_grace_active"] = False
    _state["initial_grace_deadline_ms"] = None
    _state["last_ntp_sync_utc"] = timestamp_utc
    _state["persisted_last_ntp_sync_utc"] = timestamp_utc
    _state["locked"] = False
    _state["reported_threshold_hours"] = 0

    if first_session_sync:
        print("Securite temps : premiere synchronisation recue")
    else:
        print("Securite temps : nouvelle synchronisation recue")
    if _save_state(timestamp_utc):
        print("Securite temps : synchronisation enregistree")

    if was_locked:
        print("Securite temps : verrouillage leve")

    return True


def get_sync_age_seconds(current_utc):
    if not _state["session_sync_received"]:
        return None

    last_sync = _state["last_ntp_sync_utc"]
    if last_sync is None or not _is_plausible_timestamp(current_utc):
        return None

    return max(0, int(current_utc) - last_sync)


def update(now_ms, current_utc=None):
    if not _state["initialized"] or _state["locked"]:
        return False

    if not _state["session_sync_received"]:
        grace_deadline = _state["initial_grace_deadline_ms"]
        if (
            _state["initial_grace_active"]
            and grace_deadline is not None
            and time.ticks_diff(now_ms, grace_deadline) >= 0
        ):
            _state["initial_grace_active"] = False
            _state["locked"] = True
            print("Securite temps : periode de grace expiree")
            print("Securite temps : LED verrouillees")
            return True

        return False

    age_seconds = get_sync_age_seconds(current_utc)
    if age_seconds is None:
        return False

    age_hours = age_seconds // 3600
    for threshold in (24, 48):
        if age_hours >= threshold and _state["reported_threshold_hours"] < threshold:
            _state["reported_threshold_hours"] = threshold
            print(
                "Securite temps : derniere synchronisation agee de %d heures"
                % threshold
            )

    if age_seconds < MAX_TIME_WITHOUT_SYNC_SECONDS or _state["locked"]:
        return False

    _state["locked"] = True
    _state["reported_threshold_hours"] = 72
    print("Securite temps : limite de 72 heures atteinte")
    print("Securite temps : LED verrouillees")
    return True


def is_locked():
    return bool(_state["locked"])


def has_session_sync():
    return bool(_state["session_sync_received"])


def is_initial_grace_active():
    return bool(_state["initial_grace_active"])


def get_initial_grace_remaining_seconds(now_ms=None):
    if not _state["initial_grace_active"]:
        return 0
    if now_ms is None:
        now_ms = time.ticks_ms()

    grace_deadline = _state["initial_grace_deadline_ms"]
    if grace_deadline is None:
        return 0

    remaining_ms = time.ticks_diff(grace_deadline, now_ms)
    return max(0, remaining_ms // 1000)


def get_last_ntp_sync_utc():
    return _state["last_ntp_sync_utc"]


def get_persisted_last_ntp_sync_utc():
    return _state["persisted_last_ntp_sync_utc"]


def simulate_sync_age_seconds(age_seconds, current_utc):
    """Diagnostic RAM-only; the next NTP sync restores the production state."""
    if not _state["session_sync_received"]:
        return False
    if age_seconds < 0 or not _is_plausible_timestamp(current_utc):
        return False

    _state["last_ntp_sync_utc"] = int(current_utc) - int(age_seconds)
    _state["reported_threshold_hours"] = 0
    return True


def expire_initial_grace_for_diagnostic(now_ms=None):
    """Expire only the RAM grace period; production remains configured for 72 h."""
    if not _state["initial_grace_active"]:
        return False
    if now_ms is None:
        now_ms = time.ticks_ms()

    _state["initial_grace_deadline_ms"] = now_ms
    return True
