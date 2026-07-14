import gc
import time
import ota_state
import network_request_lock

try:
    import urequests as requests
except ImportError:
    try:
        import requests
    except ImportError:
        requests = None


VERSION_MANIFEST_URL = "https://tube-vintage-jfb.netlify.app/version.json"
UPDATE_INITIAL_DELAY_MS = 60 * 1000
UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000
UPDATE_RETRY_DELAY_MS = 60 * 60 * 1000
UPDATE_LOCK_RETRY_DELAY_MS = 5 * 1000
UPDATE_DELAY_AFTER_SUN_MS = 30 * 1000
SUPPORTED_MANIFEST_VERSION = 1

FORBIDDEN_FILENAMES = (
    "wifi_secrets.py",
    "time_state.json",
    "runtime_state.json",
    "runtime_state.tmp",
    "ota_download_pending.json",
    "ota_download_pending.tmp",
    "ota_download_ready.json",
    "ota_download_ready.tmp",
    "time_state.tmp",
    ".gitignore",
    "package.json",
    "package-lock.json",
    "pyrightconfig.json",
    "netlify.toml",
)


_state = {
    "initialized": False,
    "local_version": None,
    "remote_version": None,
    "manifest_files": [],
    "update_available": False,
    "ota_preparation_requested": False,
    "ota_preparation_attempted": False,
    "wifi_connected": False,
    "next_check_ms": None,
    "in_progress": False,
    "last_error": None,
    "check_completed": False,
    "first_attempt_started": False,
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
    _state["manifest_files"] = []
    _state["update_available"] = False
    _state["ota_preparation_requested"] = False
    _state["ota_preparation_attempted"] = False
    _state["wifi_connected"] = False
    _state["next_check_ms"] = None
    _state["in_progress"] = False
    _state["last_error"] = None
    _state["check_completed"] = False
    _state["first_attempt_started"] = False


def _is_safe_filename(name):
    if not isinstance(name, str) or not name:
        return False
    lower_name = name.lower()
    if name.startswith("/") or "/" in name or "\\" in name or ".." in name:
        return False
    if lower_name.startswith(".") or lower_name.endswith((".new", ".bak")):
        return False
    if lower_name in FORBIDDEN_FILENAMES:
        return False
    if lower_name.startswith(("npm-", "git-", "vscode-", "update_marker")):
        return False
    return True


def _is_valid_sha256(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character.lower() in "0123456789abcdef" for character in value)


def _validate_manifest(data):
    if not isinstance(data, dict):
        return None
    if data.get("manifest_version") != SUPPORTED_MANIFEST_VERSION:
        return None
    remote_version = data.get("version")
    if _parse_version(remote_version) is None:
        return None
    files = data.get("files")
    if not isinstance(files, list) or not files:
        return None

    normalized_files = []
    seen_names = []
    for file_entry in files:
        if not isinstance(file_entry, dict):
            return None
        name = file_entry.get("name")
        url = file_entry.get("url")
        size = file_entry.get("size")
        sha256 = file_entry.get("sha256")
        if not isinstance(name, str) or not _is_safe_filename(name):
            return None
        if name.lower() in seen_names:
            return None
        if not isinstance(url, str) or not url.startswith("https://"):
            return None
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            return None
        if not isinstance(sha256, str) or not _is_valid_sha256(sha256):
            return None
        seen_names.append(name.lower())
        normalized_files.append(
            {"name": name, "url": url, "size": size, "sha256": sha256.lower()}
        )
    return {"version": remote_version, "files": normalized_files}


def _schedule_retry(now_ms):
    _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_RETRY_DELAY_MS)
    print("Mise a jour : nouvelle tentative dans 1 heure")


def _check_manifest(now_ms):
    if not _state["first_attempt_started"]:
        last_sun_release_ms = network_request_lock.get_last_release_ms("sun")
        if last_sun_release_ms is None:
            _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_LOCK_RETRY_DELAY_MS)
            return False
        earliest_ms = time.ticks_add(last_sun_release_ms, UPDATE_DELAY_AFTER_SUN_MS)
        if time.ticks_diff(now_ms, earliest_ms) < 0:
            _state["next_check_ms"] = earliest_ms
            return False

    if not network_request_lock.try_acquire("updater", now_ms):
        _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_LOCK_RETRY_DELAY_MS)
        return False

    response = None
    payload = None
    _state["first_attempt_started"] = True
    _state["in_progress"] = True
    _state["last_error"] = None
    print("Mise a jour : verification du manifeste")
    try:
        gc.collect()
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")
        response = requests.get(VERSION_MANIFEST_URL)
        if response is None:
            raise RuntimeError("aucune reponse HTTP")
        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            raise RuntimeError("HTTP " + str(status_code))
        payload = response.json()
        manifest = _validate_manifest(payload)
        payload = None
        if manifest is None:
            raise RuntimeError("manifeste invalide")
        comparison = compare_versions(manifest["version"], _state["local_version"])
        if comparison is None:
            raise RuntimeError("version mal formee")

        _state["remote_version"] = manifest["version"]
        _state["manifest_files"] = manifest["files"]
        _state["update_available"] = comparison > 0
        _state["ota_preparation_requested"] = comparison > 0
        _state["ota_preparation_attempted"] = False
        _state["check_completed"] = True
        _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_CHECK_INTERVAL_MS)
        print("Mise a jour : version locale " + _state["local_version"])
        print("Mise a jour : version distante " + manifest["version"])
        if comparison > 0:
            print("Mise a jour : nouvelle version " + manifest["version"] + " disponible")
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
        response = None
        payload = None
        _state["in_progress"] = False
        network_request_lock.release("updater", time.ticks_ms())
        gc.collect()


def update(now_ms, wifi_connected):
    if not _state["initialized"] or _state["in_progress"]:
        return False
    wifi_connected = bool(wifi_connected)
    newly_connected = wifi_connected and not _state["wifi_connected"]
    _state["wifi_connected"] = wifi_connected
    if not wifi_connected:
        _state["next_check_ms"] = None
        return False
    if _state["ota_preparation_requested"]:
        return False
    if newly_connected or _state["next_check_ms"] is None:
        _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_INITIAL_DELAY_MS)
    if time.ticks_diff(now_ms, _state["next_check_ms"]) < 0:
        return False
    _state["next_check_ms"] = None
    return _check_manifest(now_ms)


def is_ota_preparation_requested():
    return bool(
        _state["ota_preparation_requested"]
        and not _state["ota_preparation_attempted"]
    )


def prepare_ota_marker():
    if not _state["ota_preparation_requested"]:
        return False
    _state["ota_preparation_attempted"] = True
    if not ota_state.create_pending(_state["remote_version"], _state["manifest_files"]):
        _state["last_error"] = "creation du marqueur OTA impossible"
        return False
    _state["ota_preparation_requested"] = False
    return True


def is_update_available():
    return bool(_state["update_available"])


def get_remote_version():
    return _state["remote_version"]


def force_check(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()
    _state["next_check_ms"] = now_ms


def start_download(now_ms=None):
    if not _state["update_available"]:
        return False
    _state["ota_preparation_requested"] = True
    _state["ota_preparation_attempted"] = False
    return True


def get_download_state():
    return {
        "in_progress": False,
        "requested": _state["ota_preparation_requested"],
        "current_file": None,
        "files_completed": 0,
        "files_total": len(_state["manifest_files"]),
        "last_error": _state["last_error"],
        "complete": False,
        "validated_new_files": [],
        "next_attempt_ms": None,
    }


def get_state():
    return {
        "local_version": _state["local_version"],
        "remote_version": _state["remote_version"],
        "update_available": _state["update_available"],
        "ota_preparation_requested": _state["ota_preparation_requested"],
        "ota_preparation_attempted": _state["ota_preparation_attempted"],
        "next_check_ms": _state["next_check_ms"],
        "last_error": _state["last_error"],
        "in_progress": _state["in_progress"],
        "check_completed": _state["check_completed"],
    }
