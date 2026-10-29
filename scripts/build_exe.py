"""Build standalone Windows executable for PinNotes using PyInstaller."""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build():
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    assets_dir = PROJECT_ROOT / "assets"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PinNotes",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--icon={str(icon_path)}",
        f"--add-data={str(assets_dir)};assets",
        str(PROJECT_ROOT / "app.py"),
    ]

    print(f"Building PinNotes from: {PROJECT_ROOT}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode == 0:
        print("\nBuild successful! Output is in dist/PinNotes/")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
