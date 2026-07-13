import time

try:
    import urequests as requests
except ImportError:
    try:
        import requests
    except ImportError:
        requests = None


LATITUDE = "46.851"
LONGITUDE = "-71.36"
TIMEZONE = "America%2FToronto"
FORECAST_DAYS = "1"
OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude="
    + LATITUDE
    + "&longitude="
    + LONGITUDE
    + "&daily=sunset&timezone="
    + TIMEZONE
    + "&forecast_days="
    + FORECAST_DAYS
)

SUN_REQUEST_DELAY_MS = 7 * 1000
SUN_RETRY_DELAY_MS = 15 * 60 * 1000
MIN_VALID_YEAR = 2024
MAX_VALID_YEAR = 2100


_state = {
    "initialized": False,
    "wifi_connected": False,
    "time_valid": False,
    "pending_date": None,
    "fetched_date": None,
    "sunset": None,
    "next_attempt_ms": None,
    "in_progress": False,
    "force_requested": False,
    "last_error": None,
}


def initialize():
    _state["initialized"] = True
    _state["wifi_connected"] = False
    _state["time_valid"] = False
    _state["pending_date"] = None
    _state["fetched_date"] = None
    _state["sunset"] = None
    _state["next_attempt_ms"] = None
    _state["in_progress"] = False
    _state["force_requested"] = False
    _state["last_error"] = None


def _days_in_month(year, month):
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if (year % 4) == 0 and ((year % 100) != 0 or (year % 400) == 0):
        return 29
    return 28


def _is_valid_date(date_value):
    if not isinstance(date_value, tuple) or len(date_value) != 3:
        return False

    year, month, day = date_value
    if not all(isinstance(value, int) for value in date_value):
        return False
    if year < MIN_VALID_YEAR or year > MAX_VALID_YEAR:
        return False
    if month < 1 or month > 12:
        return False
    return 1 <= day <= _days_in_month(year, month)


def _parse_date(date_text):
    if not isinstance(date_text, str) or len(date_text) != 10:
        return None
    if date_text[4] != "-" or date_text[7] != "-":
        return None

    try:
        parsed_date = (
            int(date_text[0:4]),
            int(date_text[5:7]),
            int(date_text[8:10]),
        )
    except (TypeError, ValueError):
        return None

    if not _is_valid_date(parsed_date):
        return None
    return parsed_date


def _parse_response(data, expected_date):
    if not isinstance(data, dict):
        return None

    daily = data.get("daily")
    if not isinstance(daily, dict):
        return None

    dates = daily.get("time")
    sunsets = daily.get("sunset")
    if not isinstance(dates, list) or not dates:
        return None
    if not isinstance(sunsets, list) or not sunsets:
        return None

    response_date = _parse_date(dates[0])
    sunset_text = sunsets[0]
    if response_date != expected_date:
        return None
    if not isinstance(sunset_text, str) or len(sunset_text) < 16:
        return None
    if sunset_text[10] != "T" or _parse_date(sunset_text[0:10]) != response_date:
        return None
    if sunset_text[13] != ":":
        return None

    try:
        hour = int(sunset_text[11:13])
        minute = int(sunset_text[14:16])
    except (TypeError, ValueError):
        return None

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return {
        "date": response_date,
        "hour": hour,
        "minute": minute,
    }


def _schedule_retry(now_ms):
    _state["next_attempt_ms"] = time.ticks_add(now_ms, SUN_RETRY_DELAY_MS)
    print("Soleil : nouvelle tentative dans 15 minutes")


def _request_sunset(expected_date, now_ms):
    response = None
    _state["in_progress"] = True
    _state["last_error"] = None
    print("Soleil : recuperation du coucher demandee")

    try:
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")

        response = requests.get(OPEN_METEO_URL)
        if response is None:
            raise RuntimeError("aucune reponse HTTP")

        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            _state["last_error"] = "HTTP " + str(status_code)
            print("Soleil : reponse HTTP invalide : " + str(status_code))
            _schedule_retry(now_ms)
            return False

        sunset = _parse_response(response.json(), expected_date)
        if sunset is None:
            _state["last_error"] = "reponse JSON invalide"
            print("Soleil : reponse JSON invalide")
            _schedule_retry(now_ms)
            return False

        _state["sunset"] = sunset
        _state["fetched_date"] = expected_date
        _state["next_attempt_ms"] = None
        return True
    except Exception as error:
        _state["last_error"] = str(error)
        print("Soleil : echec de la requete : " + str(error))
        _schedule_retry(now_ms)
        return False
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        _state["in_progress"] = False


def update(now_ms, wifi_connected, time_valid, local_date):
    if not _state["initialized"] or _state["in_progress"]:
        return False

    wifi_connected = bool(wifi_connected)
    time_valid = bool(time_valid)
    conditions_became_ready = (
        (wifi_connected and not _state["wifi_connected"])
        or (time_valid and not _state["time_valid"])
    )
    _state["wifi_connected"] = wifi_connected
    _state["time_valid"] = time_valid

    if not wifi_connected or not time_valid or not _is_valid_date(local_date):
        _state["next_attempt_ms"] = None
        return False

    if _state["fetched_date"] == local_date and not _state["force_requested"]:
        _state["next_attempt_ms"] = None
        return False

    date_changed = _state["pending_date"] != local_date
    if date_changed:
        _state["pending_date"] = local_date

    if _state["next_attempt_ms"] is None or conditions_became_ready or date_changed:
        delay_ms = 0 if _state["force_requested"] else SUN_REQUEST_DELAY_MS
        _state["next_attempt_ms"] = time.ticks_add(now_ms, delay_ms)

    if time.ticks_diff(now_ms, _state["next_attempt_ms"]) < 0:
        return False

    _state["next_attempt_ms"] = None
    _state["force_requested"] = False
    return _request_sunset(local_date, now_ms)


def has_valid_sunset():
    return _state["sunset"] is not None


def get_sunset():
    return _state["sunset"]


def get_sunset_date():
    sunset = _state["sunset"]
    if sunset is None:
        return None
    return sunset["date"]


def get_next_attempt_ms():
    return _state["next_attempt_ms"]


def force_refresh(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()

    _state["fetched_date"] = None
    _state["pending_date"] = None
    _state["next_attempt_ms"] = now_ms
    _state["force_requested"] = True


def get_diagnostic_state():
    return {
        "sunset": _state["sunset"],
        "fetched_date": _state["fetched_date"],
        "next_attempt_ms": _state["next_attempt_ms"],
        "in_progress": _state["in_progress"],
        "last_error": _state["last_error"],
    }
