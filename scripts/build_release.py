"""Enterprise Release Builder: Builds PinNotes.exe, Uninstall.exe, and Setup.exe."""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.installer.version_info import generate_version_file


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(f"\n[BUILD STEP] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd))
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def make_zip_payload(source_dir: Path, zip_path: Path) -> None:
    """Create a compressed zip payload of the application directory."""
    print(f"\n[PACKAGE] Archiving {source_dir} -> {zip_path}...")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(source_dir)
                z.write(file_path, str(rel_path))
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[PACKAGE] Successfully created {zip_path.name} ({size_mb:.2f} MB)")


def main():
    print("=" * 70)
    print(" PinNotes Enterprise Setup & Executable Build Pipeline")
    print("=" * 70)

    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"
    assets_dir = PROJECT_ROOT / "assets"
    icon_ico = assets_dir / "icon.ico"

    build_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate PE Version Resource files
    print("\n--- Step 1: Generating Windows PE Version Resources ---")
    ver_pinnotes = generate_version_file(
        output_path=build_dir / "ver_pinnotes.txt",
        original_filename="PinNotes.exe",
        file_description="PinNotes - Obsidian-Compatible Coding Notes",
        version_str="1.2.0.0",
    )
    ver_uninstall = generate_version_file(
        output_path=build_dir / "ver_uninstall.txt",
        original_filename="Uninstall.exe",
        file_description="PinNotes Uninstaller",
        version_str="1.2.0.0",
    )
    ver_setup = generate_version_file(
        output_path=build_dir / "ver_setup.txt",
        original_filename="Setup.exe",
        file_description="PinNotes Setup Wizard",
        version_str="1.2.0.0",
    )

    # 2. Build PinNotes.exe (Onedir mode)
    print("\n--- Step 2: Building PinNotes.exe ---")
    pinnotes_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PinNotes",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--paths={str(PROJECT_ROOT)}",
        f"--icon={str(icon_ico)}",
        f"--version-file={str(ver_pinnotes)}",
        f"--add-data={str(assets_dir)};assets",
        f"--add-data={str(icon_ico)};.",
        f"--add-data={str(assets_dir / 'icon.png')};.",
        str(PROJECT_ROOT / "app.py"),
    ]
    run_cmd(pinnotes_cmd, PROJECT_ROOT)

    # 3. Build Uninstall.exe (Onefile mode)
    print("\n--- Step 3: Building Uninstall.exe ---")
    uninstall_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=Uninstall",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--paths={str(PROJECT_ROOT)}",
        f"--icon={str(icon_ico)}",
        f"--version-file={str(ver_uninstall)}",
        f"--add-data={str(icon_ico)};.",
        f"--add-data={str(assets_dir / 'icon.png')};.",
        f"--add-data={str(assets_dir)};assets",
        str(PROJECT_ROOT / "src" / "installer" / "uninstaller_gui.py"),
    ]
    run_cmd(uninstall_cmd, PROJECT_ROOT)

    # Copy built Uninstall.exe and assets into the PinNotes onedir distribution
    app_dist_dir = dist_dir / "PinNotes"
    compiled_uninstaller = dist_dir / "Uninstall.exe"
    if compiled_uninstaller.exists():
        shutil.copy2(compiled_uninstaller, app_dist_dir / "Uninstall.exe")
        print(f"[PACKAGE] Bundled Uninstall.exe into {app_dist_dir}")

    # Ensure root and assets/ icons exist in portable distribution
    (app_dist_dir / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(icon_ico, app_dist_dir / "assets" / "icon.ico")
    shutil.copy2(assets_dir / "icon.png", app_dist_dir / "assets" / "icon.png")
    shutil.copy2(icon_ico, app_dist_dir / "icon.ico")
    shutil.copy2(assets_dir / "icon.png", app_dist_dir / "icon.png")

    # Bundle PinNotes notes vault and configuration template into distribution
    app_notes_dir = app_dist_dir / "PinNotes" / "notes"
    app_notes_dir.mkdir(parents=True, exist_ok=True)
    src_notes_dir = PROJECT_ROOT / "PinNotes" / "notes"
    if src_notes_dir.exists():
        shutil.copytree(src_notes_dir, app_notes_dir, dirs_exist_ok=True)
        print(f"[PACKAGE] Bundled user notes vault into {app_notes_dir}")

    app_config_dir = app_dist_dir / "PinNotes" / "config"
    app_config_dir.mkdir(parents=True, exist_ok=True)
    src_config_dir = PROJECT_ROOT / "PinNotes" / "config"
    if src_config_dir.exists():
        shutil.copytree(src_config_dir, app_config_dir, dirs_exist_ok=True)
        print(f"[PACKAGE] Bundled settings into {app_config_dir}")

    # Copy WebView2Loader.dll if present
    web_dll = PROJECT_ROOT / "WebView2Loader.dll"
    if web_dll.exists():
        shutil.copy2(web_dll, app_dist_dir / "WebView2Loader.dll")

    # 4. Create payload.zip archive of PinNotes directory
    print("\n--- Step 4: Compressing Application Payload Archive ---")
    payload_zip = dist_dir / "payload.zip"
    make_zip_payload(app_dist_dir, payload_zip)

    # 5. Build Setup.exe (Onefile installer with embedded payload)
    print("\n--- Step 5: Building PinNotes-Setup.exe ---")
    setup_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PinNotes-Setup",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--paths={str(PROJECT_ROOT)}",
        f"--icon={str(icon_ico)}",
        f"--version-file={str(ver_setup)}",
        f"--add-data={str(payload_zip)};.",
        f"--add-data={str(icon_ico)};.",
        f"--add-data={str(assets_dir / 'icon.png')};.",
        f"--add-data={str(assets_dir)};assets",
        str(PROJECT_ROOT / "src" / "installer" / "installer_gui.py"),
    ]
    run_cmd(setup_cmd, PROJECT_ROOT)

    # Create alias Setup.exe
    setup_exe = dist_dir / "PinNotes-Setup.exe"
    alias_setup = dist_dir / "Setup.exe"
    if setup_exe.exists():
        shutil.copy2(setup_exe, alias_setup)
        print(f"[PACKAGE] Created {alias_setup.name} alias")

    # 6. Build Standalone PinNotes.exe (Single-file executable directly from app.py)
    print("\n--- Step 6: Building Standalone PinNotes.exe (Onefile) ---")
    pinnotes_standalone_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PinNotes-App",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--paths={str(PROJECT_ROOT)}",
        f"--icon={str(icon_ico)}",
        f"--version-file={str(ver_pinnotes)}",
        f"--add-data={str(assets_dir)};assets",
        f"--add-data={str(icon_ico)};.",
        f"--add-data={str(assets_dir / 'icon.png')};.",
        str(PROJECT_ROOT / "app.py"),
    ]
    run_cmd(pinnotes_standalone_cmd, PROJECT_ROOT)

    built_standalone = dist_dir / "PinNotes-App.exe"
    standalone_pinnotes = dist_dir / "PinNotes.exe"
    if built_standalone.exists():
        if standalone_pinnotes.exists():
            standalone_pinnotes.unlink()
        shutil.move(built_standalone, standalone_pinnotes)
        print(f"[PACKAGE] Created standalone executable: {standalone_pinnotes.name}")

    print("\n" + "=" * 70)
    print(" BUILD COMPLETE!")
    print(f" Standalone Executable (from app.py): {standalone_pinnotes} ({(standalone_pinnotes.stat().st_size / (1024*1024)):.2f} MB)")
    print(f" Standalone Setup Program:           {alias_setup} ({(alias_setup.stat().st_size / (1024*1024)):.2f} MB)")
    print(f" Standalone Named Installer:         {setup_exe}")
    print(f" Portable Application Dir:           {app_dist_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
