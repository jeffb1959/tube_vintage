import json
import os


STATE_VERSION = 1
MAX_OTA_ATTEMPTS = 3
PENDING_FILE = "ota_download_pending.json"
PENDING_TEMP_FILE = "ota_download_pending.tmp"
READY_FILE = "ota_download_ready.json"
READY_TEMP_FILE = "ota_download_ready.tmp"

FORBIDDEN_FILENAMES = (
    "wifi_secrets.py",
    "time_state.json",
    "time_state.tmp",
    "runtime_state.json",
    "runtime_state.tmp",
    PENDING_FILE,
    PENDING_TEMP_FILE,
    READY_FILE,
    READY_TEMP_FILE,
)


def _remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _write_atomic(final_path, temp_path, data):
    try:
        with open(temp_path, "w") as temp_file:
            json.dump(data, temp_file)
        _remove_if_present(final_path)
        os.rename(temp_path, final_path)
        return True
    except (OSError, TypeError, ValueError):
        _remove_if_present(temp_path)
        return False


def pending_exists():
    try:
        os.stat(PENDING_FILE)
        return True
    except OSError:
        return False


def create_pending(remote_version, files):
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": files,
        "attempts": 0,
    }
    return _write_atomic(PENDING_FILE, PENDING_TEMP_FILE, data)


def _valid_file_entry(file_entry):
    if not isinstance(file_entry, dict):
        return False
    name = file_entry.get("name")
    url = file_entry.get("url")
    size = file_entry.get("size")
    sha256 = file_entry.get("sha256")
    if not isinstance(name, str) or not name:
        return False
    lower_name = name.lower()
    if name.startswith("/") or "/" in name or "\\" in name or ".." in name:
        return False
    if lower_name.startswith(".") or lower_name.endswith((".new", ".bak")):
        return False
    if lower_name in FORBIDDEN_FILENAMES:
        return False
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        return False
    if not isinstance(sha256, str) or len(sha256) != 64:
        return False
    return all(character.lower() in "0123456789abcdef" for character in sha256)


def load_pending():
    try:
        with open(PENDING_FILE, "r") as marker_file:
            data = json.load(marker_file)
        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            return None
        if not isinstance(data.get("remote_version"), str):
            return None
        files = data.get("files")
        attempts = data.get("attempts")
        if not isinstance(files, list) or not files:
            return None
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
            return None
        seen_names = []
        for file_entry in files:
            if not _valid_file_entry(file_entry):
                return None
            name = file_entry["name"].lower()
            if name in seen_names:
                return None
            seen_names.append(name)
        return data
    except (OSError, TypeError, ValueError):
        return None


def begin_attempt(marker):
    marker["attempts"] += 1
    marker.pop("last_error", None)
    if not _write_atomic(PENDING_FILE, PENDING_TEMP_FILE, marker):
        return False
    return True


def record_failure(marker, error):
    marker["last_error"] = str(error)[:120]
    if marker["attempts"] >= MAX_OTA_ATTEMPTS:
        remove_pending()
        return False
    return _write_atomic(PENDING_FILE, PENDING_TEMP_FILE, marker)


def create_ready(remote_version, new_files):
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": new_files,
    }
    return _write_atomic(READY_FILE, READY_TEMP_FILE, data)


def remove_pending():
    _remove_if_present(PENDING_FILE)
    _remove_if_present(PENDING_TEMP_FILE)
