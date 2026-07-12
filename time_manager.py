import time
import ntptime


# Délai court après une connexion Wi-Fi avant la première synchronisation NTP.
NTP_POST_CONNECT_DELAY_MS = 3000

# Intervalle de resynchronisation après une synchronisation réussie.
NTP_RESYNC_INTERVAL_MS = 6 * 60 * 60 * 1000

# Délai entre deux tentatives de synchronisation en cas d'échec.
NTP_RETRY_DELAY_MS = 60000

# Année minimale pour considérer une date synchronisée comme plausible.
NTP_MIN_VALID_YEAR = 2024


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
    if _state["initialized"]:
        return
    _state["initialized"] = True


def is_time_valid():
    return bool(_state["time_valid"])


def get_last_sync_ms():
    return _state["last_sync_ms"]


def get_utc_time():
    if not _state["time_valid"]:
        return None
    return time.localtime()


def _format_utc(time_tuple):
    year, month, day, hour, minute, second, _, _ = time_tuple
    return "%04d-%02d-%02d %02d:%02d:%02d UTC" % (
        year,
        month,
        day,
        hour,
        minute,
        second,
    )


def _is_reasonable_time(time_tuple):
    return time_tuple[0] >= NTP_MIN_VALID_YEAR


def _print(message):
    print(message)


def _schedule_next(now_ms, delay_ms):
    _state["next_attempt_ms"] = time.ticks_add(now_ms, delay_ms)


def _mark_time_invalid():
    _state["time_valid"] = False
    _state["last_sync_ms"] = None


def _attempt_sync(now_ms):
    _state["in_progress"] = True
    _print("NTP : synchronisation demandee")

    try:
        ntptime.settime()
        now_tuple = time.localtime()

        if not _is_reasonable_time(now_tuple):
            raise RuntimeError("Date non plausible")

        _state["time_valid"] = True
        _state["last_sync_ms"] = now_ms
        _schedule_next(now_ms, NTP_RESYNC_INTERVAL_MS)
        _print("NTP : synchronisation reussie")
        _print("Heure UTC : " + _format_utc(now_tuple))
    except Exception as error:
        _mark_time_invalid()
        _schedule_next(now_ms, NTP_RETRY_DELAY_MS)
        _print("NTP : echec de synchronisation : " + str(error))
        _print(
            "NTP : nouvelle tentative dans %d secondes" % (NTP_RETRY_DELAY_MS // 1000)
        )
    finally:
        _state["in_progress"] = False


def _handle_wifi_connected(now_ms):
    _state["wifi_connected"] = True

    if _state["time_valid"]:
        _schedule_next(now_ms, NTP_RESYNC_INTERVAL_MS)
    else:
        _schedule_next(now_ms, NTP_POST_CONNECT_DELAY_MS)


def update(now_ms=None, wifi_connected=False):
    if not _state["initialized"]:
        return

    if now_ms is None:
        now_ms = time.ticks_ms()

    if not _state["enabled"]:
        return

    if _state["in_progress"]:
        return

    if not wifi_connected:
        _state["wifi_connected"] = False
        _state["next_attempt_ms"] = None
        return

    if not _state["wifi_connected"]:
        _handle_wifi_connected(now_ms)

    if _state["next_attempt_ms"] is None and not _state["time_valid"]:
        _schedule_next(now_ms, NTP_RETRY_DELAY_MS)

    if (
        _state["next_attempt_ms"] is not None
        and time.ticks_diff(now_ms, _state["next_attempt_ms"]) >= 0
    ):
        _state["next_attempt_ms"] = None
        _attempt_sync(now_ms)
