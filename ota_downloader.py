import gc
import os
import time
import machine
import network
import ota_state
import wifi_secrets

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


DOWNLOAD_BLOCK_SIZE = 1024
PROGRESS_INTERVAL_BYTES = 16 * 1024
WIFI_TIMEOUT_MS = 60 * 1000
STREAM_TIMEOUT_SECONDS = 30
RESET_DELAY_MS = 1000
REQUEST_HEADERS = {
    "Accept-Encoding": "identity",
    "Connection": "close",
}


def _memory_free():
    mem_free = getattr(gc, "mem_free", None)
    if callable(mem_free):
        return mem_free()
    return None


def _remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _cleanup_new_files(files):
    for file_entry in files:
        if isinstance(file_entry, dict):
            name = file_entry.get("name")
            if isinstance(name, str):
                _remove_if_present(name + ".new")


def _get_header(response, header_name):
    headers = getattr(response, "headers", None)
    if not isinstance(headers, dict):
        return None
    expected_name = header_name.lower()
    for name, value in headers.items():
        if isinstance(name, str) and name.lower() == expected_name:
            return str(value).strip()
    return None


def _sha256_hex(hasher):
    return binascii.hexlify(hasher.digest()).decode().lower()


def _connect_wifi():
    print("OTA minimal : connexion Wi-Fi")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(wifi_secrets.WIFI_SSID, wifi_secrets.WIFI_PASSWORD)
    deadline_ms = time.ticks_add(time.ticks_ms(), WIFI_TIMEOUT_MS)
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), deadline_ms) >= 0:
            raise RuntimeError("connexion Wi-Fi impossible")
        time.sleep_ms(100)
    return wlan


def _download_file(file_entry):
    filename = file_entry["name"]
    expected_size = file_entry["size"]
    target_path = filename + ".new"
    response = None
    output_file = None
    stream = None
    print("OTA minimal : telechargement de " + filename)

    try:
        gc.collect()
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")
        response = requests.get(
            file_entry["url"], headers=REQUEST_HEADERS, stream=True
        )
        if response is None:
            raise RuntimeError("aucune reponse HTTP")
        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            raise RuntimeError("HTTP " + str(status_code))

        content_length = _get_header(response, "Content-Length")
        if content_length is not None and content_length.isdigit():
            if int(content_length) != expected_size:
                raise RuntimeError("taille HTTP invalide")
        content_encoding = _get_header(response, "Content-Encoding")
        if content_encoding is not None and content_encoding.lower() not in (
            "",
            "identity",
        ):
            raise RuntimeError("encodage HTTP non pris en charge")

        stream = getattr(response, "raw", None)
        read_into = getattr(stream, "readinto", None)
        read_chunk = getattr(stream, "read", None)
        if not callable(read_into) and not callable(read_chunk):
            raise RuntimeError("lecture HTTP en flux indisponible")
        set_timeout = getattr(stream, "settimeout", None)
        if callable(set_timeout):
            try:
                set_timeout(STREAM_TIMEOUT_SECONDS)
            except Exception:
                pass

        read_buffer = bytearray(DOWNLOAD_BLOCK_SIZE)
        buffer_view = memoryview(read_buffer)
        hasher = hashlib.sha256()
        received_bytes = 0
        next_progress = PROGRESS_INTERVAL_BYTES
        output_file = open(target_path, "wb")

        while received_bytes < expected_size:
            read_size = min(DOWNLOAD_BLOCK_SIZE, expected_size - received_bytes)
            if callable(read_into):
                target_view = buffer_view[:read_size]
                bytes_read = read_into(target_view)
                if not isinstance(bytes_read, int) or bytes_read <= 0:
                    raise RuntimeError("flux tronque")
                if bytes_read > read_size:
                    raise RuntimeError("taille invalide")
                data_view = buffer_view[:bytes_read]
                output_file.write(data_view)
                hasher.update(data_view)
                received_bytes += bytes_read
            else:
                if not callable(read_chunk):
                    raise RuntimeError("lecture HTTP en flux indisponible")
                chunk = read_chunk(read_size)
                if not isinstance(chunk, (bytes, bytearray)) or not chunk:
                    raise RuntimeError("flux tronque")
                if len(chunk) > read_size:
                    raise RuntimeError("taille invalide")
                output_file.write(chunk)
                hasher.update(chunk)
                received_bytes += len(chunk)

            while received_bytes >= next_progress:
                print(
                    "OTA minimal : %d / %d octets"
                    % (next_progress, expected_size)
                )
                next_progress += PROGRESS_INTERVAL_BYTES

        output_file.close()
        output_file = None
        if received_bytes != expected_size:
            raise RuntimeError("taille invalide")
        if _sha256_hex(hasher) != file_entry["sha256"].lower():
            raise RuntimeError("SHA-256 invalide")
        print("OTA minimal : fichier valide")
        return target_path
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
        gc.collect()


def _restart():
    time.sleep_ms(RESET_DELAY_MS)
    machine.reset()


def run():
    print("OTA minimal : demarrage")
    memory_free = _memory_free()
    if memory_free is not None:
        print("OTA minimal : memoire libre : " + str(memory_free))

    marker = ota_state.load_pending()
    if marker is None:
        print("OTA minimal : marqueur invalide, abandon")
        ota_state.remove_pending()
        return False
    files = marker["files"]
    if marker["attempts"] >= ota_state.MAX_OTA_ATTEMPTS:
        print("OTA minimal : limite d'echecs atteinte")
        _cleanup_new_files(files)
        ota_state.remove_pending()
        return False
    if not ota_state.begin_attempt(marker):
        print("OTA minimal : impossible de mettre a jour le marqueur")
        ota_state.remove_pending()
        return False

    try:
        _cleanup_new_files(files)
        _connect_wifi()
        new_files = []
        for file_entry in files:
            new_files.append(_download_file(file_entry))

        if not ota_state.create_ready(marker["remote_version"], new_files):
            raise RuntimeError("creation du marqueur pret impossible")
        ota_state.remove_pending()
        print("OTA minimal : tous les fichiers telecharges et valides")
        print("OTA minimal : redemarrage vers l'application")
        _restart()
        return True
    except Exception as error:
        print("OTA minimal : echec : " + str(error))
        _cleanup_new_files(files)
        retry_allowed = ota_state.record_failure(marker, error)
        if not retry_allowed:
            print("OTA minimal : trois echecs, retour a l'application")
        else:
            print("OTA minimal : nouvelle tentative au redemarrage")
        _restart()
        return False
