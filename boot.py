# tube_vintage - demarrage et selection du mode OTA minimal

print("tube_vintage : demarrage")

try:
    import ota_state

    if ota_state.boot_pending_exists():
        try:
            marker = ota_state.load_boot_pending()
            print("OTA : demarrage de la nouvelle version a confirmer")
            if marker is None:
                ota_state.remove_boot_pending()
            else:
                updated_marker = ota_state.increment_boot_attempt(marker)
                if updated_marker is None:
                    ota_state.remove_boot_pending()
                else:
                    attempts = updated_marker.get("boot_attempts")
                    max_attempts = updated_marker.get("max_boot_attempts")
                    if isinstance(attempts, int) and isinstance(max_attempts, int):
                        print(
                            "OTA : tentative de demarrage "
                            + str(attempts)
                            + " / "
                            + str(max_attempts)
                        )
                        if attempts > max_attempts:
                            import ota_rollback

                            ota_rollback.run()
        except Exception as boot_error:
            print("OTA rollback : erreur de demarrage : " + str(boot_error))
    elif ota_state.install_pending_exists():
        try:
            import ota_installer

            ota_installer.run()
        except Exception as ota_error:
            print("OTA installateur : erreur de demarrage : " + str(ota_error))
            ota_state.remove_install_pending()
    elif ota_state.pending_exists():
        try:
            import ota_downloader

            ota_downloader.run()
        except Exception as ota_error:
            print("OTA minimal : erreur de demarrage : " + str(ota_error))
            marker = ota_state.load_pending()
            if marker is None:
                ota_state.remove_pending()
except Exception as boot_error:
    print("OTA minimal : verification impossible : " + str(boot_error))
