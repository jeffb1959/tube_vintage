import time

try:
    import network
except Exception as import_error:
    network = None
    _IMPORT_ERROR = import_error
else:
    _IMPORT_ERROR = None


# Nombre de tentatives rapides à effectuer après un échec initial.
WIFI_FAST_RETRY_COUNT = 5

# Délai entre deux tentatives rapides (en ms).
WIFI_FAST_RETRY_DELAY_MS = 60000

# Délai entre deux tentatives longues (en ms).
WIFI_LONG_RETRY_DELAY_MS = 21600000

# Durée max d'une tentative de connexion (en ms).
WIFI_CONNECT_TIMEOUT_MS = 15000


_state = {
    "enabled": False,
    "initialized": False,
    "wlan": None,
    "ssid": None,
    "password": None,
    "connected": False,
    "last_connected_state": False,
    "attempt_in_progress": False,
    "attempt_start_ms": 0,
    "attempt_timeout_ms": 0,
    "attempt_number": 0,
    "fast_attempts_done": 0,
    "next_attempt_ms": None,
}


def _safe_int_value(value):
    if value is None:
        return None
    return str(value).strip()


def _load_credentials():
    try:
        import wifi_secrets
    except Exception:
        return None, None

    ssid = _safe_int_value(getattr(wifi_secrets, "WIFI_SSID", None))
    password = _safe_int_value(getattr(wifi_secrets, "WIFI_PASSWORD", None))

    if not ssid or not password:
        return None, None

    return ssid, password


def _print_if_needed(message):
    print(message)


def initialize():
    if _state["initialized"]:
        return

    _state["initialized"] = True

    if network is None:
        _print_if_needed(
            "Wi-Fi désactivé : module réseau indisponible ("
            + str(_IMPORT_ERROR)
            + ")"
        )
        return

    ssid, password = _load_credentials()
    if ssid is None or password is None:
        _print_if_needed(
            "Wi-Fi désactivé : fichier wifi_secrets.py manquant ou invalide."
        )
        return

    _state["ssid"] = ssid
    _state["password"] = password
    _state["enabled"] = True

    try:
        _state["wlan"] = network.WLAN(network.STA_IF)
        _state["wlan"].active(True)
    except Exception as error:
        _state["enabled"] = False
        _print_if_needed("Wi-Fi désactivé : " + str(error))
        return

    # Démarrage de la première tentative immédiatement.
    _state["next_attempt_ms"] = time.ticks_ms()


def _start_attempt(now_ms):
    if not _state["enabled"] or _state["attempt_in_progress"]:
        return

    if _state["wlan"] is None:
        _state["enabled"] = False
        return

    _state["attempt_in_progress"] = True
    _state["attempt_start_ms"] = now_ms
    _state["attempt_timeout_ms"] = time.ticks_add(now_ms, WIFI_CONNECT_TIMEOUT_MS)
    _state["attempt_number"] += 1

    attempt_number = _state["attempt_number"]
    if attempt_number <= WIFI_FAST_RETRY_COUNT + 1:
        _print_if_needed("Wi-Fi : tentative de connexion %d/6" % attempt_number)
    else:
        _print_if_needed("Wi-Fi : tentative de reconnexion")

    try:
        _state["wlan"].disconnect()
        _state["wlan"].connect(_state["ssid"], _state["password"])
    except Exception as error:
        _state["attempt_in_progress"] = False
        _print_if_needed("Erreur connexion Wi-Fi : " + str(error))
        _schedule_retry(now_ms, was_connected_lost=False)


def _schedule_retry(now_ms, was_connected_lost):
    if _state["fast_attempts_done"] < WIFI_FAST_RETRY_COUNT:
        _state["fast_attempts_done"] += 1
        _state["next_attempt_ms"] = time.ticks_add(
            now_ms,
            WIFI_FAST_RETRY_DELAY_MS,
        )
        _print_if_needed(
            "Wi-Fi : prochaine tentative rapide dans %d secondes"
            % (WIFI_FAST_RETRY_DELAY_MS // 1000)
        )
    else:
        _state["next_attempt_ms"] = time.ticks_add(
            now_ms,
            WIFI_LONG_RETRY_DELAY_MS,
        )
        if was_connected_lost:
            _print_if_needed(
                "Wi-Fi : mode de reconnexion longue, "
                "prochaine tentative dans %d heures"
                % (WIFI_LONG_RETRY_DELAY_MS // 3600000)
            )
        else:
            _print_if_needed(
                "Wi-Fi : mode de reconnexion longue, "
                "prochaine tentative dans 6 heures"
            )


def _handle_disconnect():
    was_connected = _state["connected"]

    if was_connected:
        _print_if_needed("Wi-Fi perdu")

    _state["connected"] = False
    _state["last_connected_state"] = True
    _state["attempt_in_progress"] = False
    _state["fast_attempts_done"] = 0
    _state["attempt_number"] = 0
    _state["next_attempt_ms"] = time.ticks_ms()


def _handle_connected():
    _state["connected"] = True
    _state["attempt_in_progress"] = False
    _state["fast_attempts_done"] = 0
    _state["attempt_number"] = 0
    _state["next_attempt_ms"] = None
    _print_if_needed("Wi-Fi connecté")
    ip = get_ip_address()
    if ip:
        _print_if_needed("Adresse IP : " + ip)
    _state["last_connected_state"] = False


def _check_attempt_status(now_ms):
    if not _state["attempt_in_progress"]:
        return

    try:
        if _state["wlan"] is None:
            _state["attempt_in_progress"] = False
            _schedule_retry(now_ms, was_connected_lost=False)
            return

        if _state["wlan"].isconnected():
            _handle_connected()
            return

        if time.ticks_diff(now_ms, _state["attempt_timeout_ms"]) >= 0:
            _state["attempt_in_progress"] = False
            _print_if_needed("Wi-Fi : tentative échouée (délai dépassé)")
            _state["wlan"].disconnect()
            _schedule_retry(now_ms, was_connected_lost=False)
    except Exception as error:
        _state["attempt_in_progress"] = False
        _print_if_needed("Erreur Wi-Fi : " + str(error))
        _schedule_retry(now_ms, was_connected_lost=False)


def update(now_ms=None):
    if not _state["initialized"]:
        return

    if not _state["enabled"] or _state["wlan"] is None:
        return

    if now_ms is None:
        now_ms = time.ticks_ms()

    try:
        is_connected = _state["wlan"].isconnected()
    except Exception as error:
        _print_if_needed("Erreur Wi-Fi : " + str(error))
        return

    if _state["connected"]:
        if not is_connected:
            _handle_disconnect()
        return

    if _state["attempt_in_progress"]:
        _check_attempt_status(now_ms)
        return

    if (
        _state["next_attempt_ms"] is not None
        and time.ticks_diff(now_ms, _state["next_attempt_ms"]) >= 0
    ):
        _state["next_attempt_ms"] = None
        _start_attempt(now_ms)


def is_connected():
    return bool(_state["connected"])


def get_ip_address():
    try:
        if _state["wlan"] is None:
            return None

        config = _state["wlan"].ifconfig()
        return config[0] if config else None
    except Exception:
        return None

