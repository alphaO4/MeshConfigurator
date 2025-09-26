import sys
from pathlib import Path

def resource_path(rel: str) -> str:
    """Return absolute path to resource for both dev and PyInstaller-frozen builds."""
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / rel)  # PyInstaller temp dir
    # repo root / same dir as app.py
    return str(Path(__file__).resolve().parent / rel)