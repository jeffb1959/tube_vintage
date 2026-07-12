SCHEDULE_START_HOUR = 6
SCHEDULE_END_HOUR = 0
SCHEDULE_START_MINUTE = 0
SCHEDULE_END_MINUTE = 0

PERIOD_DAY = "JOUR"
PERIOD_NIGHT = "NUIT"

_state = {
    "initialized": False,
    "current_period": None,
    "manual_override_active": False,
    "manual_override_state": False,
    "last_requested_state": None,
}


def initialize():
    if _state["initialized"]:
        return

    _state["initialized"] = True
    _state["current_period"] = None
    _state["manual_override_active"] = False
    _state["manual_override_state"] = False
    _state["last_requested_state"] = None


def get_current_period():
    return _state["current_period"]


def is_manual_override_active():
    return bool(_state["manual_override_active"])


def get_manual_override_state():
    return bool(_state["manual_override_state"])


def set_manual_override(state_is_on):
    _state["manual_override_active"] = True
    _state["manual_override_state"] = bool(state_is_on)


def clear_manual_override():
    if not _state["manual_override_active"]:
        return False

    _state["manual_override_active"] = False
    return True


def _normalize_hour(hour):
    if hour < 0:
        return 0
    if hour > 23:
        return 23
    return hour


def _normalize_minute(minute):
    if minute < 0:
        return 0
    if minute > 59:
        return 59
    return minute


def _time_to_minutes(hour, minute):
    hour = _normalize_hour(hour)
    minute = _normalize_minute(minute)
    return hour * 60 + minute


def _get_period(current_minutes):
    start_minutes = _time_to_minutes(SCHEDULE_START_HOUR, SCHEDULE_START_MINUTE)
    end_minutes = _time_to_minutes(SCHEDULE_END_HOUR, SCHEDULE_END_MINUTE)

    if start_minutes == end_minutes:
        return PERIOD_DAY

    if start_minutes < end_minutes:
        if current_minutes >= start_minutes and current_minutes < end_minutes:
            return PERIOD_DAY
        return PERIOD_NIGHT

    if current_minutes >= start_minutes or current_minutes < end_minutes:
        return PERIOD_DAY

    return PERIOD_NIGHT


def _period_to_state(period):
    return period == PERIOD_DAY


def get_requested_state_from_time(local_time):
    if local_time is None:
        return False

    return _period_to_state(
        _get_period(_time_to_minutes(local_time[3], local_time[4]))
    )


def _build_event(state_on, period, message=None, manual_cleared=False):
    return {
        "changed": True,
        "state_on": state_on,
        "period": period,
        "mode": "ON" if state_on else "OFF",
        "message": message,
        "manual_override_cleared": bool(manual_cleared),
        "show_indicator": bool(state_on),
    }


def update(local_time, time_valid, current_leds_on):
    if not _state["initialized"]:
        return None

    if not time_valid or local_time is None:
        return None

    current_period = _get_period(_time_to_minutes(local_time[3], local_time[4]))
    requested_state = _period_to_state(current_period)
    _state["last_requested_state"] = requested_state

    if _state["current_period"] is None:
        _state["current_period"] = current_period
        if _state["manual_override_active"]:
            return None

        if current_leds_on == requested_state:
            return None

        if requested_state:
            return _build_event(
                True,
                current_period,
                "Horaire : periode JOUR",
                manual_cleared=False,
            )

        return _build_event(
            False,
            current_period,
            "Horaire : periode NUIT",
            manual_cleared=False,
        )

    if current_period == _state["current_period"]:
        return None

    previous_period = _state["current_period"]
    _state["current_period"] = current_period

    manual_cleared = clear_manual_override()

    if previous_period == PERIOD_NIGHT and current_period == PERIOD_DAY:
        return _build_event(
            True,
            current_period,
            "Horaire : periode JOUR",
            manual_cleared=manual_cleared,
        )

    if previous_period == PERIOD_DAY and current_period == PERIOD_NIGHT:
        return _build_event(
            False,
            current_period,
            "Horaire : periode NUIT",
            manual_cleared=manual_cleared,
        )

    return _build_event(requested_state, current_period, manual_cleared=manual_cleared)
