import gc
import os
import time
import wifi_manager

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


TEST_URL = "https://tube-vintage-jfb.netlify.app/firmware/update_test_large.txt"
EXPECTED_SIZE = 65536
TEMP_FILE = "speed_test_download.tmp"
BLOCK_SIZES = (1024, 2048, 4096)
TEST_MODES = ("A", "B", "C", "D")
WIFI_TIMEOUT_MS = 60 * 1000
STREAM_TIMEOUT_SECONDS = 30
INTER_TEST_DELAY_MS = 2000

REQUEST_HEADERS = {
    "Accept-Encoding": "identity",
    "Connection": "close",
}

MODE_OPTIONS = {
    "A": {"sha256": False, "flash": False, "label": "reseau seulement"},
    "B": {"sha256": True, "flash": False, "label": "reseau + SHA-256"},
    "C": {"sha256": False, "flash": True, "label": "reseau + flash"},
    "D": {"sha256": True, "flash": True, "label": "complet"},
}


def _memory_free():
    mem_free = getattr(gc, "mem_free", None)
    if callable(mem_free):
        return mem_free()
    return None


def _remove_temp_file():
    try:
        os.remove(TEMP_FILE)
    except OSError:
        pass


def _get_header(response, header_name):
    headers = getattr(response, "headers", None)
    if not isinstance(headers, dict):
        return None

    expected_name = header_name.lower()
    for name, value in headers.items():
        if isinstance(name, str) and name.lower() == expected_name:
            return str(value).strip()
    return None


def _format_memory(value):
    if value is None:
        return "indisponible"
    return str(value)


def _sha256_hex(hasher):
    return binascii.hexlify(hasher.digest()).decode().lower()


def _wait_for_wifi():
    wifi_manager.initialize()
    start_ms = time.ticks_ms()
    deadline_ms = time.ticks_add(start_ms, WIFI_TIMEOUT_MS)

    while not wifi_manager.is_connected():
        now_ms = time.ticks_ms()
        wifi_manager.update(now_ms)
        if time.ticks_diff(now_ms, deadline_ms) >= 0:
            raise RuntimeError("connexion Wi-Fi impossible")
        time.sleep_ms(50)


def _print_summary(result):
    print("=== Test %s | bloc %d ===" % (result["mode"], result["block_size"]))
    print("Mode : " + result["label"])
    print("Memoire avant : " + _format_memory(result["memory_before"]))
    print("Ouverture HTTPS : %.2f s" % (result["open_ms"] / 1000))
    print("Lecture : %.2f s" % (result["read_ms"] / 1000))
    print("Duree totale : %.2f s" % (result["total_ms"] / 1000))
    print("Octets recus : %d" % result["received_bytes"])
    print("Vitesse moyenne : %.2f Ko/s" % result["speed_kib_s"])
    if result["sha256"] is not None:
        print("SHA-256 : " + result["sha256"])
    print("Memoire apres : " + _format_memory(result["memory_after"]))
    if result["error"] is None:
        print("Resultat : OK")
    else:
        print("Resultat : ECHEC - " + result["error"])
    print("")


def run_test(mode, block_size):
    options = MODE_OPTIONS[mode]
    response = None
    output_file = None
    stream = None
    chunk = None
    read_buffer = bytearray(block_size)
    buffer_view = memoryview(read_buffer)
    data_view = None
    hasher = hashlib.sha256() if options["sha256"] else None
    received_bytes = 0
    open_ms = 0
    read_ms = 0
    calculated_sha256 = None
    error_message = None
    open_start_ms = None
    read_start_ms = None

    _remove_temp_file()
    gc.collect()
    memory_before = _memory_free()
    total_start_ms = time.ticks_ms()

    try:
        if requests is None:
            raise RuntimeError("bibliotheque HTTP indisponible")

        open_start_ms = time.ticks_ms()
        response = requests.get(TEST_URL, headers=REQUEST_HEADERS, stream=True)
        open_ms = time.ticks_diff(time.ticks_ms(), open_start_ms)
        if response is None:
            raise RuntimeError("aucune reponse HTTP")

        status_code = getattr(response, "status_code", None)
        if status_code is not None and not 200 <= status_code < 300:
            raise RuntimeError("HTTP " + str(status_code))

        content_length = _get_header(response, "Content-Length")
        if content_length is None or not content_length.isdigit():
            raise RuntimeError("Content-Length absent ou invalide")
        if int(content_length) != EXPECTED_SIZE:
            raise RuntimeError("Content-Length incorrect")

        content_encoding = _get_header(response, "Content-Encoding")
        if content_encoding is not None and content_encoding.lower() not in (
            "",
            "identity",
        ):
            raise RuntimeError("contenu compresse non pris en charge")

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

        if options["flash"]:
            output_file = open(TEMP_FILE, "wb")

        read_start_ms = time.ticks_ms()
        while received_bytes < EXPECTED_SIZE:
            remaining_bytes = EXPECTED_SIZE - received_bytes
            read_size = min(block_size, remaining_bytes)

            if callable(read_into):
                target_view = buffer_view[:read_size]
                bytes_read = read_into(target_view)
                if not isinstance(bytes_read, int) or bytes_read <= 0:
                    raise RuntimeError("flux tronque")
                if bytes_read > read_size:
                    raise RuntimeError("bloc trop grand")
                data_view = buffer_view[:bytes_read]
                if output_file is not None:
                    output_file.write(data_view)
                if hasher is not None:
                    hasher.update(data_view)
                received_bytes += bytes_read
            else:
                if not callable(read_chunk):
                    raise RuntimeError("lecture HTTP en flux indisponible")
                chunk = read_chunk(read_size)
                if not isinstance(chunk, (bytes, bytearray)) or not chunk:
                    raise RuntimeError("flux tronque")
                if len(chunk) > read_size:
                    raise RuntimeError("bloc trop grand")
                if output_file is not None:
                    output_file.write(chunk)
                if hasher is not None:
                    hasher.update(chunk)
                received_bytes += len(chunk)

        read_ms = time.ticks_diff(time.ticks_ms(), read_start_ms)
        if received_bytes != EXPECTED_SIZE:
            raise RuntimeError("taille invalide")
        if hasher is not None:
            calculated_sha256 = _sha256_hex(hasher)
    except KeyboardInterrupt:
        raise
    except Exception as error:
        if read_start_ms is not None:
            read_ms = time.ticks_diff(time.ticks_ms(), read_start_ms)
        elif open_start_ms is not None:
            open_ms = time.ticks_diff(time.ticks_ms(), open_start_ms)
        error_message = str(error)
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
        read_buffer = None
        buffer_view = None
        data_view = None
        _remove_temp_file()
        gc.collect()

    total_ms = time.ticks_diff(time.ticks_ms(), total_start_ms)
    memory_after = _memory_free()
    read_seconds = read_ms / 1000
    speed_kib_s = 0
    if read_seconds > 0:
        speed_kib_s = received_bytes / 1024 / read_seconds

    result = {
        "mode": mode,
        "label": options["label"],
        "block_size": block_size,
        "memory_before": memory_before,
        "memory_after": memory_after,
        "open_ms": open_ms,
        "read_ms": read_ms,
        "total_ms": total_ms,
        "received_bytes": received_bytes,
        "speed_kib_s": speed_kib_s,
        "sha256": calculated_sha256,
        "error": error_message,
    }
    _print_summary(result)
    return result


def connect_wifi():
    _wait_for_wifi()
    print("Wi-Fi connecte")


def run_single_test(mode, block_size):
    return run_test(mode, block_size)


def run_speed_tests():
    print("Diagnostic temporaire HTTPS/flash")
    print("URL : " + TEST_URL)
    connect_wifi()
    print("")

    for mode in TEST_MODES:
        for block_size in BLOCK_SIZES:
            run_test(mode, block_size)
            time.sleep_ms(INTER_TEST_DELAY_MS)
