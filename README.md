# PinNotes

A fast, lightweight, Obsidian-compatible pinnable desktop notes application built with Python and PySide6 (Qt).

**Developed by kun**

## Features

- **Pinnable Floating Window:** Stay on top of other windows with one click on the pushpin icon (`Ctrl+Shift+P`).
- **Obsidian Compatible:** Notes are saved as plain Markdown files (`.md`) with YAML frontmatter in standard folders.
- **Clean Distraction-Free UI:** Vector SVG icons, borderless draggable window frame, and customizable tabs.
- **Search & Filter:** Instant note search (`Ctrl+F`) across titles and content.
- **Autosave & Backup:** Fast asynchronous background autosave to prevent data loss.
- **Light & Dark Themes:** Seamless one-click theme switcher.

## Quick Start

### 1. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python app.py
```

### 3. Build Standalone Executables & Installer
To compile the standalone `PinNotes.exe`, `Setup.exe` wizard, and `Uninstall.exe`:
```bash
python scripts/build_release.py
```
Output files will be generated in `dist/`.

## Project Structure

```text
PinNotes/
├── app.py                     # Main application entry point
├── custom.json                # User interface customization
├── requirements.txt           # Python package dependencies
├── assets/                    # Icons and application graphics (.ico, .png, .svg)
├── PinNotes/                  # User notes vault and configurations
│   ├── config/                # Application settings (settings.json)
│   └── notes/                 # Markdown notes store
├── scripts/                   # Automated build and release scripts
│   └── build_release.py       # Enterprise PyInstaller release builder
└── src/                       # Application core package
    ├── core/                  # Business logic, note models, and settings
    ├── installer/             # Windows setup and uninstaller wizards
    ├── storage/               # File system and Markdown storage engine
    └── ui/                    # PySide6 windows, widgets, and SVG icons
```

## License
MIT License.
