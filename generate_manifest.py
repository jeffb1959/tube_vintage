from pathlib import Path
import runpy


def main():
    script_path = Path(__file__).resolve().parent / "tools" / "generate_manifest.py"
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    main()
