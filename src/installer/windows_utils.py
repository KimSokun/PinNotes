"""Windows system integration: Shortcuts, Registry, and App Uninstaller registration."""

from __future__ import annotations
import os
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Optional


def get_default_install_dir() -> Path:
    """Return the standard per-user application installation directory."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / "AppData" / "Local"
    return base / "Programs" / "PinNotes"


def get_desktop_dir() -> Path:
    """Return user's Desktop directory."""
    profile = os.environ.get("USERPROFILE")
    if profile:
        return Path(profile) / "Desktop"
    return Path.home() / "Desktop"


def get_start_menu_programs_dir() -> Path:
    """Return user's Start Menu Programs directory."""
    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def create_shortcut(
    target_path: Path | str,
    shortcut_path: Path | str,
    icon_path: Optional[Path | str] = None,
    description: str = "PinNotes - Obsidian-Compatible Coding Notes",
    work_dir: Optional[Path | str] = None,
    arguments: str = "",
) -> bool:
    """Create a Windows shell shortcut (.lnk) with custom icon."""
    target_path = Path(target_path).resolve()
    shortcut_path = Path(shortcut_path).resolve()
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)

    if not icon_path:
        icon_loc = f"{target_path},0"
    else:
        icon_loc = str(Path(icon_path).resolve())

    working_directory = str(Path(work_dir).resolve()) if work_dir else str(target_path.parent)

    ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{str(shortcut_path)}')
$s.TargetPath = '{str(target_path)}'
$s.WorkingDirectory = '{working_directory}'
$s.Description = '{description}'
$s.Arguments = '{arguments}'
$s.IconLocation = '{icon_loc}'
$s.Save()
"""
    try:
        cmd = ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode == 0 and shortcut_path.exists()
    except Exception as e:
        print(f"Warning: could not create shortcut '{shortcut_path}': {e}")
        return False


def remove_shortcut(shortcut_path: Path | str) -> bool:
    """Remove a shortcut file safely."""
    try:
        p = Path(shortcut_path)
        if p.exists():
            p.unlink()
            return True
    except Exception as e:
        print(f"Warning: could not remove shortcut '{shortcut_path}': {e}")
    return False


def register_uninstaller(
    install_dir: Path | str,
    uninstaller_exe: Path | str,
    app_version: str = "1.2.0",
    estimated_kb: int = 95000,
) -> bool:
    """Register PinNotes in Windows Add/Remove Programs (Control Panel & Settings App)."""
    install_dir = Path(install_dir).resolve()
    uninstaller_exe = Path(uninstaller_exe).resolve()
    app_exe = install_dir / "PinNotes.exe"

    sub_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PinNotes"
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "PinNotes")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, app_version)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "kun")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f'"{str(app_exe)}",0')
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{str(uninstaller_exe)}"')
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{str(uninstaller_exe)}" /silent')
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, int(estimated_kb))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://github.com/pinnotes/pinnotes")
            winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, "https://github.com/pinnotes/pinnotes")
        return True
    except Exception as e:
        print(f"Warning: could not write Windows uninstall registry key: {e}")
        return False


def unregister_uninstaller() -> bool:
    """Remove PinNotes from Windows Add/Remove Programs."""
    sub_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PinNotes"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub_key)
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"Warning: could not delete Windows uninstall registry key: {e}")
        return False


def set_autostart(app_exe: Path | str, enable: bool = True) -> bool:
    """Register or unregister PinNotes in Windows Startup Run key."""
    sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, "PinNotes", 0, winreg.REG_SZ, f'"{str(Path(app_exe).resolve())}"')
            else:
                try:
                    winreg.DeleteValue(key, "PinNotes")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"Warning: could not set Windows autostart: {e}")
        return False
