@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed.
  pause
  exit /b 1
)
echo.
echo Setup completed successfully.
pause
