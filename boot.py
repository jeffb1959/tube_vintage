# tube_vintage - demarrage et selection du mode OTA minimal

print("tube_vintage : demarrage")

try:
    import ota_state

    if ota_state.install_pending_exists():
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
