NIGHT_PROFILE_NAME = "NUIT"
NIGHT_PROFILE_DELAY_MINUTES = 30
NIGHT_END_MINUTES = 6 * 60


_state = {
    "initialized": False,
    "active": False,
    "active_start_date": None,
    "active_end_date": None,
    "sunset": None,
    "previous_sunset": None,
    "diagnostic_sunset": None,
    "diagnostic_local_time": None,
}


def initialize():
    _state["initialized"] = True
    _state["active"] = False
    _state["active_start_date"] = None
    _state["active_end_date"] = None
    _state["sunset"] = None
    _state["previous_sunset"] = None
    _state["diagnostic_sunset"] = None
    _state["diagnostic_local_time"] = None


def _is_leap_year(year):
    return (year % 4) == 0 and ((year % 100) != 0 or (year % 400) == 0)


def _days_in_month(year, month):
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    return 29 if _is_leap_year(year) else 28


def _next_date(date_value):
    year, month, day = date_value
    day += 1
    if day > _days_in_month(year, month):
        day = 1
        month += 1
        if month > 12:
            month = 1
            year += 1
    return (year, month, day)


def _valid_date(date_value):
    if not isinstance(date_value, tuple) or len(date_value) != 3:
        return False
    year, month, day = date_value
    if not all(isinstance(value, int) for value in date_value):
        return False
    if year < 2024 or month < 1 or month > 12:
        return False
    return 1 <= day <= _days_in_month(year, month)


def _valid_sunset(sunset):
    if not isinstance(sunset, dict):
        return False
    date_value = sunset.get("date")
    hour = sunset.get("hour")
    minute = sunset.get("minute")
    return (
        _valid_date(date_value)
        and isinstance(hour, int)
        and isinstance(minute, int)
        and 0 <= hour <= 23
        and 0 <= minute <= 59
    )


def _remember_sunset(sunset):
    if not _valid_sunset(sunset) or sunset == _state["sunset"]:
        return

    if (
        _state["sunset"] is not None
        and _state["sunset"]["date"] != sunset["date"]
    ):
        _state["previous_sunset"] = _state["sunset"]

    _state["sunset"] = {
        "date": sunset["date"],
        "hour": sunset["hour"],
        "minute": sunset["minute"],
    }
    start_total = sunset["hour"] * 60 + sunset["minute"] + NIGHT_PROFILE_DELAY_MINUTES
    start_minutes = start_total % (24 * 60)
    print("Profil nuit : coucher du soleil %02d:%02d" % (sunset["hour"], sunset["minute"]))
    print("Profil nuit : activation prevue a %02d:%02d" % (start_minutes // 60, start_minutes % 60))


def _get_start_window(sunset):
    start_total = sunset["hour"] * 60 + sunset["minute"] + NIGHT_PROFILE_DELAY_MINUTES
    if start_total < 24 * 60:
        return sunset["date"], start_total
    return _next_date(sunset["date"]), start_total % (24 * 60)


def update(local_time, sunset=None):
    if _state["diagnostic_local_time"] is not None:
        local_time = _state["diagnostic_local_time"]

    if not _state["initialized"] or local_time is None or len(local_time) < 5:
        return None

    local_date = tuple(local_time[:3])
    if not _valid_date(local_date):
        return None
    hour = local_time[3]
    minute = local_time[4]
    if not isinstance(hour, int) or not isinstance(minute, int):
        return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    current_minutes = hour * 60 + minute
    selected_sunset = _state["diagnostic_sunset"]
    if selected_sunset is None:
        selected_sunset = sunset
    _remember_sunset(selected_sunset)

    if _state["active"]:
        active_end_date = _state["active_end_date"]
        if active_end_date is None:
            return None
        if local_date > active_end_date or (
            local_date == active_end_date and current_minutes >= NIGHT_END_MINUTES
        ):
            _state["active"] = False
            _state["active_start_date"] = None
            _state["active_end_date"] = None
            print("Profil nuit : mode NUIT automatique termine a 06:00")
            return "ended"
        return None

    matching_window = None
    for known_sunset in (_state["sunset"], _state["previous_sunset"]):
        if not _valid_sunset(known_sunset):
            continue
        start_date, start_minutes = _get_start_window(known_sunset)
        if local_date != start_date or current_minutes < start_minutes:
            continue
        if start_minutes < NIGHT_END_MINUTES and current_minutes >= NIGHT_END_MINUTES:
            continue
        matching_window = (start_date, start_minutes)
        break

    if matching_window is None:
        return None

    start_date, start_minutes = matching_window

    _state["active"] = True
    _state["active_start_date"] = start_date
    _state["active_end_date"] = (
        start_date if start_minutes < NIGHT_END_MINUTES else _next_date(start_date)
    )
    print("Profil nuit : mode NUIT automatique active")
    return "started"


def is_auto_night_active():
    return bool(_state["active"])


def get_effective_profile(user_profile):
    if _state["active"]:
        return NIGHT_PROFILE_NAME
    return user_profile


def set_diagnostic_sunset(date_value, hour, minute):
    sunset = {"date": date_value, "hour": hour, "minute": minute}
    if not _valid_sunset(sunset):
        return False
    _state["diagnostic_sunset"] = sunset
    _state["sunset"] = None
    _state["previous_sunset"] = None
    return True


def clear_diagnostic_sunset():
    _state["diagnostic_sunset"] = None
    _state["sunset"] = None
    _state["previous_sunset"] = None


def set_diagnostic_local_time(local_time):
    if local_time is None or len(local_time) < 5:
        return False
    date_value = tuple(local_time[:3])
    hour = local_time[3]
    minute = local_time[4]
    if not _valid_date(date_value):
        return False
    if not isinstance(hour, int) or not isinstance(minute, int):
        return False
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return False
    _state["diagnostic_local_time"] = local_time
    return True


def clear_diagnostic_local_time():
    _state["diagnostic_local_time"] = None


def force_auto_night(active, start_date=None):
    if active:
        if not _valid_date(start_date):
            return False
        _state["active"] = True
        _state["active_start_date"] = start_date
        _state["active_end_date"] = _next_date(start_date)
    else:
        _state["active"] = False
        _state["active_start_date"] = None
        _state["active_end_date"] = None
    return True


def get_diagnostic_state():
    return {
        "active": _state["active"],
        "active_start_date": _state["active_start_date"],
        "active_end_date": _state["active_end_date"],
        "sunset": _state["sunset"],
        "previous_sunset": _state["previous_sunset"],
        "diagnostic_sunset": _state["diagnostic_sunset"],
        "diagnostic_local_time": _state["diagnostic_local_time"],
    }
