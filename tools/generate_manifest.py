import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIRMWARE_DIR = PROJECT_ROOT / "netlify" / "firmware"
MANIFEST_PATH = PROJECT_ROOT / "netlify" / "version.json"
BASE_URL = "https://tube-vintage-jeff.netlify.app/firmware"
MANIFEST_VERSION = 1
REMOTE_VERSION = "3.0.1"
TEST_FILES = (
    "update_test_small.txt",
    "update_test_large.txt",
)


def ensure_test_files():
    FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
    small_path = FIRMWARE_DIR / TEST_FILES[0]
    small_path.write_bytes(b"Tube Vintage - petit fichier de test OTA 3.0.1\n")

    large_path = FIRMWARE_DIR / TEST_FILES[1]
    line = b"Tube Vintage OTA 3.0.1 - bloc de test pour telechargement en flux.\n"
    target_size = 64 * 1024
    content = (line * ((target_size // len(line)) + 1))[:target_size]
    large_path.write_bytes(content)


def build_entry(filename):
    path = FIRMWARE_DIR / filename
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while True:
            block = source.read(64 * 1024)
            if not block:
                break
            size += len(block)
            digest.update(block)
    return {
        "name": filename,
        "url": BASE_URL + "/" + filename,
        "size": size,
        "sha256": digest.hexdigest(),
    }


def main():
    ensure_test_files()
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "version": REMOTE_VERSION,
        "files": [build_entry(filename) for filename in TEST_FILES],
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    for entry in manifest["files"]:
        print(entry["name"], entry["size"], entry["sha256"])


if __name__ == "__main__":
    main()
