import time

try:
    import urequests as requests
except ImportError:
    try:
        import requests
    except ImportError:
        requests = None


# Remplacer ce domaine par l'URL reelle du site Netlify avant le deploiement.
VERSION_MANIFEST_URL = "https://votre-site.netlify.app/version.json"

UPDATE_INITIAL_DELAY_MS = 15 * 1000
UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000
UPDATE_RETRY_DELAY_MS = 60 * 60 * 1000
SUPPORTED_MANIFEST_VERSION = 1


_state = {
    "initialized": False,
    "local_version": None,
    "remote_version": None,
    "update_available": False,
    "wifi_connected": False,
    "next_check_ms": None,
    "in_progress": False,
    "last_error": None,
    "check_completed": False,
}


def _parse_version(version):
    if not isinstance(version, str):
        return None

    parts = version.split(".")
    if len(parts) != 3:
        return None

    numbers = []
    for part in parts:
        if not part or not all("0" <= character <= "9" for character in part):
            return None
        numbers.append(int(part))

    return tuple(numbers)


def compare_versions(first_version, second_version):
    first = _parse_version(first_version)
    second = _parse_version(second_version)
    if first is None or second is None:
        return None
    if first > second:
        return 1
    if first < second:
        return -1
    return 0


def initialize(local_version):
    _state["initialized"] = True
    _state["local_version"] = local_version
    _state["remote_version"] = None
    _state["update_available"] = False
    _state["wifi_connected"] = False
    _state["next_check_ms"] = None
    _state["in_progress"] = False
    _state["last_error"] = None
    _state["check_completed"] = False

    if _parse_version(local_version) is None:
        _state["last_error"] = "version locale invalide"
        print("Mise a jour : version locale invalide")


def _validate_manifest(data):
    if not isinstance(data, dict):
        return None
    if data.get("manifest_version") != SUPPORTED_MANIFEST_VERSION:
        return None

    remote_version = data.get("version")
    if _parse_version(remote_version) is None:
        return None

    files = data.get("files", [])
    if not isinstance(files, list):
        return None
    for file_entry in files:
        if not isinstance(file_entry, dict):
            return None

    return remote_version


def _schedule_retry(now_ms):
    _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_RETRY_DELAY_MS)
    print("Mise a jour : nouvelle tentative dans 1 heure")


def _check_manifest(now_ms):
    response = None
    _state["in_progress"] = True
    _state["check_completed"] = False
    _state["last_error"] = None
    print("Mise a jour : verification du manifeste")

    try:
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")

        response = requests.get(VERSION_MANIFEST_URL)
        if response is None:
            raise RuntimeError("aucune reponse HTTP")

        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            _state["last_error"] = "HTTP " + str(status_code)
            print("Mise a jour : erreur HTTP : " + str(status_code))
            _schedule_retry(now_ms)
            return False

        remote_version = _validate_manifest(response.json())
        if remote_version is None:
            _state["last_error"] = "manifeste invalide"
            print("Mise a jour : manifeste invalide")
            _schedule_retry(now_ms)
            return False

        comparison = compare_versions(remote_version, _state["local_version"])
        if comparison is None:
            _state["last_error"] = "version mal formee"
            print("Mise a jour : version mal formee")
            _schedule_retry(now_ms)
            return False

        _state["remote_version"] = remote_version
        _state["update_available"] = comparison > 0
        _state["check_completed"] = True
        _state["next_check_ms"] = time.ticks_add(
            now_ms, UPDATE_CHECK_INTERVAL_MS
        )

        print("Mise a jour : version locale " + _state["local_version"])
        print("Mise a jour : version distante " + remote_version)
        if _state["update_available"]:
            print("Mise a jour : nouvelle version " + remote_version + " disponible")
        else:
            print("Mise a jour : aucune mise a jour disponible")
        return True
    except Exception as error:
        _state["last_error"] = str(error)
        print("Mise a jour : echec : " + str(error))
        _schedule_retry(now_ms)
        return False
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        _state["in_progress"] = False


def update(now_ms, wifi_connected):
    if not _state["initialized"] or _state["in_progress"]:
        return False

    wifi_connected = bool(wifi_connected)
    newly_connected = wifi_connected and not _state["wifi_connected"]
    _state["wifi_connected"] = wifi_connected

    if not wifi_connected:
        _state["next_check_ms"] = None
        return False

    if newly_connected or _state["next_check_ms"] is None:
        _state["next_check_ms"] = time.ticks_add(
            now_ms, UPDATE_INITIAL_DELAY_MS
        )

    if time.ticks_diff(now_ms, _state["next_check_ms"]) < 0:
        return False

    _state["next_check_ms"] = None
    return _check_manifest(now_ms)


def is_update_available():
    return bool(_state["update_available"])


def get_remote_version():
    return _state["remote_version"]


def force_check(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()
    _state["next_check_ms"] = now_ms


def get_state():
    return {
        "local_version": _state["local_version"],
        "remote_version": _state["remote_version"],
        "update_available": _state["update_available"],
        "next_check_ms": _state["next_check_ms"],
        "last_error": _state["last_error"],
        "in_progress": _state["in_progress"],
        "check_completed": _state["check_completed"],
    }
