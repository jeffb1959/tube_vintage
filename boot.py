# tube_vintage - demarrage et selection du mode OTA minimal

print("tube_vintage : demarrage")

try:
    import ota_state

    if ota_state.pending_exists():
        try:
            import ota_downloader

            ota_downloader.run()
        except Exception as ota_error:
            print("OTA minimal : erreur de demarrage : " + str(ota_error))
            marker = ota_state.load_pending()
            if marker is None:
                ota_state.remove_pending()
            elif ota_state.begin_attempt(marker):
                retry_allowed = ota_state.record_failure(marker, ota_error)
                if retry_allowed:
                    import machine
                    import time

                    time.sleep_ms(1000)
                    machine.reset()
                else:
                    print("OTA minimal : abandon apres trois echecs")
except Exception as boot_error:
    print("OTA minimal : verification impossible : " + str(boot_error))
