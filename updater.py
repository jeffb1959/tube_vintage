import gc
import os
import time
import network_request_lock

try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import urequests as requests
except ImportError:
    try:
        import requests
    except ImportError:
        requests = None


# Remplacer ce domaine par l'URL reelle du site Netlify avant le deploiement.
VERSION_MANIFEST_URL = "https://tube-vintage-jeff.netlify.app/version.json"

UPDATE_INITIAL_DELAY_MS = 60 * 1000
UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000
UPDATE_RETRY_DELAY_MS = 60 * 60 * 1000
UPDATE_LOCK_RETRY_DELAY_MS = 5 * 1000
UPDATE_DELAY_AFTER_SUN_MS = 30 * 1000
DOWNLOAD_FILE_GAP_MS = 10 * 1000
DOWNLOAD_BLOCK_SIZE = 1024
DOWNLOAD_PROGRESS_INTERVAL_BYTES = 16 * 1024
DOWNLOAD_SOCKET_TIMEOUT_SECONDS = 20
DOWNLOAD_SPACE_MARGIN_BYTES = 4096
SUPPORTED_MANIFEST_VERSION = 1

DOWNLOAD_REQUEST_HEADERS = {
    "Accept-Encoding": "identity",
    "Connection": "close",
}

FORBIDDEN_FILENAMES = (
    "wifi_secrets.py",
    "time_state.json",
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
    "wifi_connected": False,
    "next_check_ms": None,
    "in_progress": False,
    "last_error": None,
    "check_completed": False,
    "first_attempt_started": False,
    "download_requested": False,
    "download_in_progress": False,
    "download_current_file": None,
    "download_files_completed": 0,
    "download_files_total": 0,
    "download_complete": False,
    "download_new_files": [],
    "download_next_attempt_ms": None,
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
    _state["wifi_connected"] = False
    _state["next_check_ms"] = None
    _state["in_progress"] = False
    _state["last_error"] = None
    _state["check_completed"] = False
    _state["first_attempt_started"] = False
    _reset_download_state()

    if _parse_version(local_version) is None:
        _state["last_error"] = "version locale invalide"
        print("Mise a jour : version locale invalide")


def _reset_download_state():
    _state["download_requested"] = False
    _state["download_in_progress"] = False
    _state["download_current_file"] = None
    _state["download_files_completed"] = 0
    _state["download_files_total"] = 0
    _state["download_complete"] = False
    _state["download_new_files"] = []
    _state["download_next_attempt_ms"] = None


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
    if lower_name in ("update_state.json", "update_pending", "update_marker"):
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
            {
                "name": name,
                "url": url,
                "size": size,
                "sha256": sha256.lower(),
            }
        )

    return {"version": remote_version, "files": normalized_files}


def _schedule_check_retry(now_ms):
    _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_RETRY_DELAY_MS)
    print("Mise a jour : nouvelle tentative dans 1 heure")


def _print_free_memory(label):
    mem_free = getattr(gc, "mem_free", None)
    if callable(mem_free):
        print("Memoire libre " + label + " : " + str(mem_free()))


def _check_manifest(now_ms):
    if not _state["first_attempt_started"]:
        last_sun_release_ms = network_request_lock.get_last_release_ms("sun")
        if last_sun_release_ms is None:
            _state["next_check_ms"] = time.ticks_add(
                now_ms, UPDATE_LOCK_RETRY_DELAY_MS
            )
            return False
        earliest_check_ms = time.ticks_add(
            last_sun_release_ms, UPDATE_DELAY_AFTER_SUN_MS
        )
        if time.ticks_diff(now_ms, earliest_check_ms) < 0:
            _state["next_check_ms"] = earliest_check_ms
            return False

    if not network_request_lock.try_acquire("updater", now_ms):
        _state["next_check_ms"] = time.ticks_add(
            now_ms, UPDATE_LOCK_RETRY_DELAY_MS
        )
        return False

    _state["first_attempt_started"] = True
    response = None
    payload = None
    _state["in_progress"] = True
    _state["check_completed"] = False
    _state["last_error"] = None
    print("Mise a jour : verification du manifeste")

    try:
        gc.collect()
        _print_free_memory("avant Mise a jour")
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

        remote_version = manifest["version"]
        comparison = compare_versions(remote_version, _state["local_version"])
        if comparison is None:
            raise RuntimeError("version mal formee")

        previous_remote_version = _state["remote_version"]
        if (
            previous_remote_version is not None
            and previous_remote_version != remote_version
        ):
            _cleanup_download_attempt()
            _reset_download_state()

        _state["remote_version"] = remote_version
        _state["manifest_files"] = manifest["files"]
        _state["update_available"] = comparison > 0
        _state["check_completed"] = True
        _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_CHECK_INTERVAL_MS)

        print("Mise a jour : version locale " + _state["local_version"])
        print("Mise a jour : version distante " + remote_version)
        if _state["update_available"]:
            print("Mise a jour : nouvelle version " + remote_version + " disponible")
            if not _state["download_complete"]:
                start_download(now_ms)
        else:
            print("Mise a jour : aucune mise a jour disponible")
        return True
    except Exception as error:
        _state["last_error"] = str(error)
        print("Mise a jour : echec : " + str(error))
        _schedule_check_retry(now_ms)
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
        _print_free_memory("apres Mise a jour")


def _remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _cleanup_download_attempt():
    paths = list(_state["download_new_files"])
    current_name = _state["download_current_file"]
    if current_name is not None:
        current_path = current_name + ".new"
        if current_path not in paths:
            paths.append(current_path)

    for path in paths:
        _remove_if_present(path)

    _state["download_new_files"] = []
    if paths:
        print("Mise a jour : nettoyage des fichiers .new")


def _has_enough_free_space(files):
    statvfs = getattr(os, "statvfs", None)
    if not callable(statvfs):
        return True
    try:
        filesystem = statvfs(".")
        if not isinstance(filesystem, tuple) or len(filesystem) < 5:
            return True
        free_bytes = filesystem[1] * filesystem[4]
        required_bytes = 0
        for file_entry in files:
            if not isinstance(file_entry, dict):
                return False
            file_size = file_entry.get("size")
            if not isinstance(file_size, int):
                return False
            required_bytes += file_size
        return free_bytes >= required_bytes + DOWNLOAD_SPACE_MARGIN_BYTES
    except (OSError, TypeError, IndexError):
        return True


def _sha256_hex(hasher):
    return binascii.hexlify(hasher.digest()).decode().lower()


def _fail_download(now_ms, error):
    _state["last_error"] = str(error)
    print("Mise a jour : " + str(error))
    _cleanup_download_attempt()
    _state["download_in_progress"] = False
    _state["download_current_file"] = None
    _state["download_files_completed"] = 0
    _state["download_complete"] = False
    _state["download_requested"] = True
    _state["download_next_attempt_ms"] = time.ticks_add(
        now_ms, UPDATE_RETRY_DELAY_MS
    )
    print("Mise a jour : nouvelle tentative planifiee dans 1 heure")


def _download_next_file(now_ms):
    files = _state["manifest_files"]
    file_index = _state["download_files_completed"]
    if file_index == 0 and not _state["download_new_files"]:
        if not _has_enough_free_space(files):
            _fail_download(now_ms, "espace disque insuffisant")
            return False

    if file_index >= len(files):
        return False
    file_entry = files[file_index]
    filename = file_entry["name"]
    target_path = filename + ".new"

    if not network_request_lock.try_acquire("updater-download", now_ms):
        _state["download_next_attempt_ms"] = time.ticks_add(
            now_ms, UPDATE_LOCK_RETRY_DELAY_MS
        )
        return False

    response = None
    output_file = None
    stream = None
    chunk = None
    _state["download_in_progress"] = True
    _state["download_current_file"] = filename
    print("Mise a jour : telechargement de " + filename)

    try:
        gc.collect()
        _print_free_memory("avant telechargement")
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")

        response = requests.get(
            file_entry["url"],
            headers=DOWNLOAD_REQUEST_HEADERS,
            stream=True,
        )
        if response is None:
            raise RuntimeError("aucune reponse HTTP")
        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            raise RuntimeError("HTTP " + str(status_code))

        stream = getattr(response, "raw", None)
        read_chunk = getattr(stream, "read", None)
        if not callable(read_chunk):
            raise RuntimeError("lecture HTTP en flux indisponible")

        set_timeout = getattr(stream, "settimeout", None)
        if callable(set_timeout):
            try:
                set_timeout(DOWNLOAD_SOCKET_TIMEOUT_SECONDS)
            except Exception:
                pass

        received_bytes = 0
        expected_size = file_entry["size"]
        next_progress_bytes = DOWNLOAD_PROGRESS_INTERVAL_BYTES
        hasher = hashlib.sha256()
        output_file = open(target_path, "wb")
        while received_bytes < expected_size:
            remaining_bytes = expected_size - received_bytes
            read_size = min(DOWNLOAD_BLOCK_SIZE, remaining_bytes)
            chunk = read_chunk(read_size)
            if not chunk:
                raise RuntimeError("taille invalide : flux tronque")
            if not isinstance(chunk, (bytes, bytearray)):
                raise RuntimeError("bloc HTTP invalide")
            if len(chunk) > read_size:
                raise RuntimeError("taille invalide")
            output_file.write(chunk)
            hasher.update(chunk)
            received_bytes += len(chunk)
            while received_bytes >= next_progress_bytes:
                print(
                    "Mise a jour : %d / %d octets"
                    % (next_progress_bytes, expected_size)
                )
                next_progress_bytes += DOWNLOAD_PROGRESS_INTERVAL_BYTES

        output_file.close()
        output_file = None
        calculated_sha256 = _sha256_hex(hasher)
        print("Mise a jour : %d octets recus" % received_bytes)
        if received_bytes != expected_size:
            raise RuntimeError("taille invalide")
        print("Mise a jour : taille valide")
        if calculated_sha256 != file_entry["sha256"]:
            raise RuntimeError("SHA-256 invalide")
        print("Mise a jour : SHA-256 valide")

        _state["download_new_files"].append(target_path)
        _state["download_files_completed"] += 1
        _state["download_current_file"] = None
        print("Mise a jour : fichier conserve sous " + target_path)

        if _state["download_files_completed"] == len(files):
            _state["download_requested"] = False
            _state["download_complete"] = True
            _state["download_next_attempt_ms"] = None
            print("Mise a jour : tous les fichiers telecharges et valides")
            print("Mise a jour : aucune installation effectuee")
        else:
            _state["download_next_attempt_ms"] = time.ticks_add(
                now_ms, DOWNLOAD_FILE_GAP_MS
            )
        return True
    except Exception as error:
        if output_file is not None:
            try:
                output_file.close()
            except Exception:
                pass
            output_file = None
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
            response = None
        _fail_download(now_ms, error)
        return False
    finally:
        if output_file is not None:
            try:
                output_file.close()
            except Exception:
                pass
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        output_file = None
        response = None
        stream = None
        chunk = None
        _state["download_in_progress"] = False
        network_request_lock.release("updater-download", time.ticks_ms())
        gc.collect()
        _print_free_memory("apres telechargement")


def update(now_ms, wifi_connected):
    if not _state["initialized"] or _state["in_progress"]:
        return False

    wifi_connected = bool(wifi_connected)
    newly_connected = wifi_connected and not _state["wifi_connected"]
    _state["wifi_connected"] = wifi_connected
    if not wifi_connected:
        _state["next_check_ms"] = None
        return False

    if _state["download_requested"] and not _state["download_in_progress"]:
        next_download_ms = _state["download_next_attempt_ms"]
        if next_download_ms is None or time.ticks_diff(now_ms, next_download_ms) >= 0:
            return _download_next_file(now_ms)

    if newly_connected or _state["next_check_ms"] is None:
        _state["next_check_ms"] = time.ticks_add(now_ms, UPDATE_INITIAL_DELAY_MS)
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


def start_download(now_ms=None):
    if not _state["update_available"] or not _state["manifest_files"]:
        _state["last_error"] = "aucune mise a jour telechargeable"
        return False
    if _state["download_in_progress"]:
        return False
    if now_ms is None:
        now_ms = time.ticks_ms()

    _cleanup_download_attempt()
    _state["download_requested"] = True
    _state["download_current_file"] = None
    _state["download_files_completed"] = 0
    _state["download_files_total"] = len(_state["manifest_files"])
    _state["download_complete"] = False
    _state["download_next_attempt_ms"] = now_ms
    _state["last_error"] = None
    return True


def get_download_state():
    return {
        "in_progress": _state["download_in_progress"],
        "requested": _state["download_requested"],
        "current_file": _state["download_current_file"],
        "files_completed": _state["download_files_completed"],
        "files_total": _state["download_files_total"],
        "last_error": _state["last_error"],
        "complete": _state["download_complete"],
        "validated_new_files": list(_state["download_new_files"]),
        "next_attempt_ms": _state["download_next_attempt_ms"],
    }


def get_state():
    return {
        "local_version": _state["local_version"],
        "remote_version": _state["remote_version"],
        "update_available": _state["update_available"],
        "next_check_ms": _state["next_check_ms"],
        "last_error": _state["last_error"],
        "in_progress": _state["in_progress"],
        "check_completed": _state["check_completed"],
        "first_attempt_started": _state["first_attempt_started"],
        "download": get_download_state(),
    }
