import os
import time
import machine
import ota_state


RESET_DELAY_MS = 1000


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def _remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _cleanup_new_files(files):
    for file_entry in files:
        name = file_entry.get("name")
        if isinstance(name, str):
            _remove_if_present(name + ".new")


def _restore_marker_files(files):
    restored = True
    for file_entry in reversed(files):
        name = file_entry.get("name")
        if not isinstance(name, str):
            restored = False
            continue
        backup_path = file_entry.get("backup", name + ".bak")
        if not isinstance(backup_path, str):
            restored = False
            print("OTA rollback : sauvegarde invalide pour " + name)
            _remove_if_present(name)
            continue

        had_previous_file = file_entry.get("had_previous_file")
        print("OTA rollback : restauration de " + name)
        _remove_if_present(name)

        if had_previous_file:
            if not _exists(backup_path):
                print(
                    "OTA rollback : backup manquant pour "
                    + name
                )
                restored = False
                continue
            try:
                os.rename(backup_path, name)
            except OSError as error:
                print("OTA rollback : echec restauration de " + name + " : " + str(error))
                restored = False
        else:
            _remove_if_present(name)
    return restored


def _restart():
    time.sleep_ms(RESET_DELAY_MS)
    machine.reset()


def run():
    print("OTA rollback : demarrage")
    marker = ota_state.load_boot_pending()
    if marker is None:
        print("OTA rollback : marqueur absent")
        ota_state.remove_boot_pending()
        _restart()
        return False

    files = marker["files"]
    restored_ok = True
    try:
        restored_ok = _restore_marker_files(files)
        _cleanup_new_files(files)
        ota_state.remove_boot_pending()
        ota_state.remove_update_confirmed()
        ota_state.remove_install_ready()
        ota_state.remove_install_pending()
        ota_state.remove_ready()
        if not restored_ok:
            ota_state.create_rollback_done(
                marker["remote_version"],
                "restauration incomplete",
            )
        print("OTA rollback : restauration terminee")
        print("OTA rollback : redemarrage vers l'ancienne version")
        _restart()
        return restored_ok
    except Exception as error:
        print("OTA rollback : erreur : " + str(error))
        ota_state.remove_boot_pending()
        ota_state.remove_update_confirmed()
        _restart()
        return False
