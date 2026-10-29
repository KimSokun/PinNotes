@echo off
title Building PinNotes Setup Program
cd /d "%~dp0\.."
echo ===================================================
echo  Starting PinNotes Enterprise Build Process
echo ===================================================
python scripts\build_release.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo [SUCCESS] Build completed! Your setup.exe is ready in the dist folder.
pause
