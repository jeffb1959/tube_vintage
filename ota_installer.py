import os
import time
import machine
import ota_state


RESET_DELAY_MS = 1000

# Diagnostic manuel de la phase 3.0.2. Utiliser 1 pour provoquer une erreur
# avant l'installation du deuxieme fichier, puis remettre None.
INSTALL_TEST_FAIL_ON_INDEX = None


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
        _remove_if_present(file_entry["name"] + ".new")


def _verify_new_files(files):
    print("OTA installateur : verification des fichiers .new")
    for file_entry in files:
        name = file_entry["name"]
        if not ota_state.is_installable_name(name):
            raise RuntimeError("nom interdit : " + name)
        if not _exists(name + ".new"):
            raise RuntimeError("fichier .new absent : " + name)


def _restore(operations, files):
    print("OTA installateur : restauration en cours")
    restoration_ok = True
    for operation in reversed(operations):
        name = operation["name"]
        backup_path = name + ".bak"
        try:
            if operation["new_installed"]:
                _remove_if_present(name)
            if operation["backup_created"] and _exists(backup_path):
                os.rename(backup_path, name)
        except OSError as error:
            restoration_ok = False
            print("OTA installateur : restauration impossible : " + str(error))
    _cleanup_new_files(files)
    if restoration_ok:
        print("OTA installateur : restauration terminee")
    else:
        print("OTA installateur : restauration incomplete")
    return restoration_ok


def _restart():
    time.sleep_ms(RESET_DELAY_MS)
    machine.reset()


def run():
    print("OTA installateur : demarrage")
    marker = ota_state.load_install_pending()
    if marker is None:
        print("OTA installateur : marqueur invalide")
        ota_state.remove_install_pending()
        _restart()
        return False

    files = marker["files"]
    operations = []
    current_name = "fichier inconnu"
    ota_state.remove_install_ready()

    try:
        _verify_new_files(files)
        for index, file_entry in enumerate(files):
            current_name = file_entry["name"]
            if INSTALL_TEST_FAIL_ON_INDEX == index:
                raise RuntimeError("echec de test simule")

            backup_path = current_name + ".bak"
            new_path = current_name + ".new"
            if _exists(backup_path):
                _remove_if_present(backup_path)

            had_original = _exists(current_name)
            if had_original:
                print("OTA installateur : sauvegarde de " + current_name)
                os.rename(current_name, backup_path)

            operation = {
                "name": current_name,
                "had_original": had_original,
                "backup_created": False,
                "new_installed": False,
            }
            operations.append(operation)
            print("OTA installateur : installation de " + current_name)
            os.rename(new_path, current_name)
            operation["backup_created"] = had_original
            operation["new_installed"] = True

        installed_files = [file_entry["name"] for file_entry in files]
        if not ota_state.create_install_ready(
            marker["remote_version"], installed_files
        ):
            raise RuntimeError("creation du statut d'installation impossible")

        ota_state.remove_install_pending()
        ota_state.remove_ready()
        print("OTA installateur : installation terminee")
        print("OTA installateur : redemarrage vers l'application")
        _restart()
        return True
    except Exception as error:
        print("OTA installateur : erreur sur " + current_name)
        print("OTA installateur : " + str(error))
        _restore(operations, files)
        ota_state.remove_install_pending()
        ota_state.remove_ready()
        ota_state.remove_install_ready()
        print("OTA installateur : retour a l'application")
        _restart()
        return False
