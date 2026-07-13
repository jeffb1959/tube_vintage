import time
import ntptime


NTP_POST_CONNECT_DELAY_MS = 3000
NTP_RESYNC_INTERVAL_MS = 6 * 60 * 60 * 1000
NTP_RETRY_DELAY_MS = 60000
NTP_MIN_VALID_YEAR = 2024

DST_STANDARD_OFFSET_HOURS = -5
DST_DAYLIGHT_OFFSET_HOURS = -4
DST_START_MONTH = 3
DST_END_MONTH = 11
DST_RULE_WEEKDAY = 6


def _timestamp_to_tuple(timestamp):
    if hasattr(time, "gmtime"):
        return time.gmtime(timestamp)
    return time.localtime(timestamp)


def _tuple_to_timestamp(time_tuple):
    year, month, day, hour, minute, second = time_tuple[:6]
    return time.mktime((year, month, day, hour, minute, second, 0, 0))


def format_time_tuple(time_tuple):
    year, month, day, hour, minute, second = time_tuple[:6]
    return "%04d-%02d-%02d %02d:%02d:%02d" % (
        year,
        month,
        day,
        hour,
        minute,
        second,
    )


_state = {
    "initialized": False,
    "enabled": True,
    "time_valid": False,
    "last_sync_ms": None,
    "next_attempt_ms": None,
    "in_progress": False,
    "wifi_connected": False,
}


def initialize():
    _state["initialized"] = True
    _state["time_valid"] = False
    _state["last_sync_ms"] = None
    _state["next_attempt_ms"] = None
    _state["in_progress"] = False
    _state["wifi_connected"] = False


def is_time_valid():
    return bool(_state["time_valid"])


def get_last_sync_ms():
    return _state["last_sync_ms"]


def get_utc_time():
    if not _state["time_valid"]:
        return None

    return time.localtime()


def get_utc_timestamp():
    utc_time = get_utc_time()
    if utc_time is None:
        return None

    return int(_tuple_to_timestamp(utc_time))


def _days_in_month(year, month):
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31

    if month in (4, 6, 9, 11):
        return 30

    if (year % 4) == 0 and (year % 100) != 0:
        return 29

    if (year % 400) == 0:
        return 29

    return 28


def get_dst_start_day_march(year):
    sunday_index = DST_RULE_WEEKDAY
    month = DST_START_MONTH
    first_day = _first_weekday_of_month(year, month, sunday_index)
    return first_day + 7


def get_dst_end_day_november(year):
    month = DST_END_MONTH
    return _first_weekday_of_month(year, month, DST_RULE_WEEKDAY)


def _first_weekday_of_month(year, month, weekday):
    max_day = _days_in_month(year, month)
    for day in range(1, max_day + 1):
        day_tuple = (year, month, day, 0, 0, 0, 0, 0)
        if _timestamp_to_tuple(_tuple_to_timestamp(day_tuple))[6] == weekday:
            return day

    return 1


def get_dst_start_utc_for_year(year):
    return (year, DST_START_MONTH, get_dst_start_day_march(year), 7, 0, 0)


def get_dst_end_utc_for_year(year):
    return (year, DST_END_MONTH, get_dst_end_day_november(year), 6, 0, 0)


def _is_daylight_active_by_utc_seconds(utc_seconds):
    utc_tuple = _timestamp_to_tuple(utc_seconds)
    year = utc_tuple[0]

    start_utc = get_dst_start_utc_for_year(year)
    end_utc = get_dst_end_utc_for_year(year)
    start_seconds = _tuple_to_timestamp(start_utc)
    end_seconds = _tuple_to_timestamp(end_utc)

    return utc_seconds >= start_seconds and utc_seconds < end_seconds


def is_daylight_saving_active(utc_time=None):
    if utc_time is None:
        utc_time = get_utc_time()

    if utc_time is None:
        return False

    utc_seconds = _tuple_to_timestamp(utc_time)
    return _is_daylight_active_by_utc_seconds(utc_seconds)


def get_utc_offset_hours(utc_time=None):
    if is_daylight_saving_active(utc_time):
        return DST_DAYLIGHT_OFFSET_HOURS

    return DST_STANDARD_OFFSET_HOURS


def get_timezone_mode_label(utc_time=None):
    if is_daylight_saving_active(utc_time):
        return "heure avancee, UTC-4"

    return "heure normale, UTC-5"


def get_local_time(utc_time=None):
    if utc_time is None:
        utc_time = get_utc_time()

    if utc_time is None:
        return None

    utc_seconds = _tuple_to_timestamp(utc_time)
    offset_hours = get_utc_offset_hours(utc_time)
    local_seconds = utc_seconds + (offset_hours * 3600)
    return _timestamp_to_tuple(local_seconds)


def debug_utc_to_local(utc_time):
    utc_tuple = tuple(utc_time)
    local_tuple = get_local_time(utc_tuple)

    print("Heure UTC : " + format_time_tuple(utc_tuple) + " UTC")
    print("Heure locale : " + format_time_tuple(local_tuple))
    print("Mode horaire : " + get_timezone_mode_label(utc_tuple))

    return local_tuple


def _attempt_sync(now_ms):
    _state["in_progress"] = True
    print("NTP : synchronisation demandee")
    sync_ok = False

    try:
        ntptime.settime()
        now_tuple = time.localtime()

        if now_tuple[0] < NTP_MIN_VALID_YEAR:
            raise RuntimeError("Date non plausible")

        _state["time_valid"] = True
        _state["last_sync_ms"] = now_ms
        _state["next_attempt_ms"] = time.ticks_add(now_ms, NTP_RESYNC_INTERVAL_MS)
        sync_ok = True
        print("NTP : synchronisation reussie")
        print("Heure UTC : " + format_time_tuple(now_tuple) + " UTC")
    except Exception as error:
        if not _state["time_valid"]:
            _state["last_sync_ms"] = None
        _state["next_attempt_ms"] = time.ticks_add(now_ms, NTP_RETRY_DELAY_MS)
        print("NTP : echec de synchronisation : " + str(error))
        print(
            "NTP : nouvelle tentative dans %d secondes"
            % (NTP_RETRY_DELAY_MS // 1000)
        )
    finally:
        _state["in_progress"] = False

    return sync_ok


def _schedule_sync_attempt(now_ms, delay_ms):
    _state["next_attempt_ms"] = time.ticks_add(now_ms, delay_ms)


def _handle_wifi_connected(now_ms):
    _state["wifi_connected"] = True
    if _state["time_valid"]:
        _schedule_sync_attempt(now_ms, NTP_RESYNC_INTERVAL_MS)
    else:
        _schedule_sync_attempt(now_ms, NTP_POST_CONNECT_DELAY_MS)


def update(now_ms=None, wifi_connected=False):
    if not _state["initialized"]:
        return False

    if now_ms is None:
        now_ms = time.ticks_ms()

    if not _state["enabled"] or _state["in_progress"]:
        return False

    if not wifi_connected:
        _state["wifi_connected"] = False
        _state["next_attempt_ms"] = None
        return False

    if not _state["wifi_connected"]:
        _handle_wifi_connected(now_ms)

    if _state["next_attempt_ms"] is None and not _state["time_valid"]:
        _schedule_sync_attempt(now_ms, NTP_RETRY_DELAY_MS)

    if (
        _state["next_attempt_ms"] is not None
        and time.ticks_diff(now_ms, _state["next_attempt_ms"]) >= 0
    ):
        _state["next_attempt_ms"] = None
        return _attempt_sync(now_ms)

    return False
