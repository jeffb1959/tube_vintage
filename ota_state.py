import json
import os


STATE_VERSION = 1
MAX_OTA_ATTEMPTS = 3
PENDING_FILE = "ota_download_pending.json"
PENDING_TEMP_FILE = "ota_download_pending.tmp"
READY_FILE = "ota_download_ready.json"
READY_TEMP_FILE = "ota_download_ready.tmp"
INSTALL_PENDING_FILE = "ota_install_pending.json"
INSTALL_PENDING_TEMP_FILE = "ota_install_pending.tmp"
INSTALL_READY_FILE = "ota_install_ready.json"
INSTALL_READY_TEMP_FILE = "ota_install_ready.tmp"
BOOT_PENDING_FILE = "ota_boot_pending.json"
BOOT_PENDING_TEMP_FILE = "ota_boot_pending.tmp"
OTA_BOOT_CONFIRM_MAX_ATTEMPTS = 3
UPDATE_CONFIRMED_FILE = "ota_update_confirmed.json"
UPDATE_CONFIRMED_TEMP_FILE = "ota_update_confirmed.tmp"
ROLLBACK_DONE_FILE = "ota_rollback_done.json"
ROLLBACK_DONE_TEMP_FILE = "ota_rollback_done.tmp"

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
    INSTALL_PENDING_FILE,
    INSTALL_PENDING_TEMP_FILE,
    INSTALL_READY_FILE,
    INSTALL_READY_TEMP_FILE,
    BOOT_PENDING_FILE,
    BOOT_PENDING_TEMP_FILE,
    UPDATE_CONFIRMED_FILE,
    UPDATE_CONFIRMED_TEMP_FILE,
    ROLLBACK_DONE_FILE,
    ROLLBACK_DONE_TEMP_FILE,
    "main.py",
    "config.py",
    "boot.py",
    ".gitignore",
    "package.json",
    "package-lock.json",
    "pyrightconfig.json",
    "netlify.toml",
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


def install_pending_exists():
    try:
        os.stat(INSTALL_PENDING_FILE)
        return True
    except OSError:
        return False


def boot_pending_exists():
    try:
        os.stat(BOOT_PENDING_FILE)
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


def is_installable_name(name):
    if not isinstance(name, str) or not name:
        return False
    lower_name = name.lower()
    if name.startswith("/") or "/" in name or "\\" in name or ".." in name:
        return False
    if lower_name.startswith(".") or lower_name.endswith((".new", ".bak")):
        return False
    if lower_name in FORBIDDEN_FILENAMES:
        return False
    if lower_name.startswith("ota_") or lower_name.endswith(".py"):
        return False
    if lower_name.startswith(("npm-", "git-", "vscode-", "update_marker")):
        return False
    return True


def _valid_file_entry(file_entry):
    if not isinstance(file_entry, dict):
        return False
    name = file_entry.get("name")
    url = file_entry.get("url")
    size = file_entry.get("size")
    sha256 = file_entry.get("sha256")
    if not is_installable_name(name):
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


def create_install_pending(remote_version, files):
    install_files = []
    for file_entry in files:
        if not _valid_file_entry(file_entry):
            return False
        install_files.append({"name": file_entry["name"]})
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": install_files,
    }
    return _write_atomic(
        INSTALL_PENDING_FILE, INSTALL_PENDING_TEMP_FILE, data
    )


def load_install_pending():
    try:
        with open(INSTALL_PENDING_FILE, "r") as marker_file:
            data = json.load(marker_file)
        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            return None
        if not isinstance(data.get("remote_version"), str):
            return None
        files = data.get("files")
        if not isinstance(files, list) or not files:
            return None
        seen_names = []
        for file_entry in files:
            if not isinstance(file_entry, dict):
                return None
            name = file_entry.get("name")
            if not isinstance(name, str) or not is_installable_name(name):
                return None
            lower_name = name.lower()
            if lower_name in seen_names:
                return None
            seen_names.append(lower_name)
        return data
    except (OSError, TypeError, ValueError):
        return None


def create_install_ready(remote_version, files):
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": files,
    }
    return _write_atomic(INSTALL_READY_FILE, INSTALL_READY_TEMP_FILE, data)


def create_boot_pending(remote_version, files, max_boot_attempts=OTA_BOOT_CONFIRM_MAX_ATTEMPTS):
    boot_files = []
    for file_entry in files:
        if not isinstance(file_entry, dict):
            return False
        name = file_entry.get("name")
        backup = file_entry.get("backup")
        had_previous_file = file_entry.get("had_previous_file")
        if not isinstance(name, str) or not is_installable_name(name):
            return False
        if not isinstance(backup, str):
            return False
        if not backup.endswith(".bak"):
            return False
        if backup.lower() != (name + ".bak").lower():
            return False
        if not isinstance(had_previous_file, bool):
            return False
        if "/" in backup or "\\" in backup or ".." in backup:
            return False
        if backup.startswith("."):
            return False
        boot_files.append(
            {
                "name": name,
                "backup": backup,
                "had_previous_file": had_previous_file,
            }
        )

    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": boot_files,
        "boot_attempts": 0,
        "max_boot_attempts": max_boot_attempts,
    }
    return _write_atomic(BOOT_PENDING_FILE, BOOT_PENDING_TEMP_FILE, data)


def load_boot_pending():
    try:
        with open(BOOT_PENDING_FILE, "r") as marker_file:
            data = json.load(marker_file)
        if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
            return None
        if not isinstance(data.get("remote_version"), str):
            return None
        files = data.get("files")
        if not isinstance(files, list) or not files:
            return None
        boot_attempts = data.get("boot_attempts")
        max_boot_attempts = data.get("max_boot_attempts")
        if (
            not isinstance(boot_attempts, int)
            or isinstance(boot_attempts, bool)
            or boot_attempts < 0
        ):
            return None
        if (
            not isinstance(max_boot_attempts, int)
            or isinstance(max_boot_attempts, bool)
            or max_boot_attempts <= 0
        ):
            return None

        seen_names = []
        for file_entry in files:
            if not isinstance(file_entry, dict):
                return None
            name = file_entry.get("name")
            backup = file_entry.get("backup")
            had_previous_file = file_entry.get("had_previous_file")
            if not isinstance(name, str) or not is_installable_name(name):
                return None
            if not isinstance(backup, str):
                return None
            if not isinstance(had_previous_file, bool):
                return None
            lower_name = name.lower()
            if lower_name in seen_names:
                return None
            if not backup.lower() == (lower_name + ".bak"):
                return None
            if backup.startswith(".") or backup.startswith("/") or ".." in backup:
                return None
            seen_names.append(lower_name)

        return data
    except (OSError, TypeError, ValueError):
        return None


def confirm_boot_success():
    marker = load_boot_pending()
    if marker is None:
        return False

    print("OTA : demarrage confirme")
    files = marker["files"]
    for file_entry in files:
        backup = file_entry.get("backup")
        if isinstance(backup, str):
            _remove_if_present(backup)
            print("OTA : suppression du backup " + backup)

    remove_boot_pending()
    remove_update_confirmed()
    remove_install_ready()
    remove_install_pending()
    remove_ready()
    create_update_confirmed(
        marker["remote_version"],
        marker["files"],
    )
    print("OTA : suppression des sauvegardes .bak terminee")
    return True


def increment_boot_attempt(marker):
    marker["boot_attempts"] += 1
    if not _write_atomic(BOOT_PENDING_FILE, BOOT_PENDING_TEMP_FILE, marker):
        return None
    return marker


def create_update_confirmed(remote_version, files):
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "files": files,
    }
    return _write_atomic(UPDATE_CONFIRMED_FILE, UPDATE_CONFIRMED_TEMP_FILE, data)


def remove_pending():
    _remove_if_present(PENDING_FILE)
    _remove_if_present(PENDING_TEMP_FILE)


def remove_ready():
    _remove_if_present(READY_FILE)
    _remove_if_present(READY_TEMP_FILE)


def remove_install_pending():
    _remove_if_present(INSTALL_PENDING_FILE)
    _remove_if_present(INSTALL_PENDING_TEMP_FILE)


def remove_install_ready():
    _remove_if_present(INSTALL_READY_FILE)
    _remove_if_present(INSTALL_READY_TEMP_FILE)


def remove_boot_pending():
    _remove_if_present(BOOT_PENDING_FILE)
    _remove_if_present(BOOT_PENDING_TEMP_FILE)


def remove_update_confirmed():
    _remove_if_present(UPDATE_CONFIRMED_FILE)
    _remove_if_present(UPDATE_CONFIRMED_TEMP_FILE)


def remove_rollback_done():
    _remove_if_present(ROLLBACK_DONE_FILE)
    _remove_if_present(ROLLBACK_DONE_TEMP_FILE)


def create_rollback_done(remote_version, error):
    data = {
        "version": STATE_VERSION,
        "remote_version": remote_version,
        "error": error,
    }
    return _write_atomic(ROLLBACK_DONE_FILE, ROLLBACK_DONE_TEMP_FILE, data)
