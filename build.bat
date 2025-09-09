@echo off
echo Building WinTelemetryService.exe...

pyinstaller --noconfirm --onefile --windowed --name WinTelemetryService --icon=NONE main.py

echo.
echo Done. The executable is in the 'dist' folder.
pause