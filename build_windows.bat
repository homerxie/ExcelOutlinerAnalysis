@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==> Excel Data Analysis Windows build

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo Virtual environment not found. Running setup first...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
  if errorlevel 1 (
    echo.
    echo Setup failed. Build stopped.
    pause
    exit /b 1
  )
)

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
  echo.
  echo Could not find virtual environment Python:
  echo   %VENV_PYTHON%
  pause
  exit /b 1
)

echo.
echo ==> Upgrading build tools
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo.
  echo Failed to upgrade build tools.
  pause
  exit /b 1
)

echo.
echo ==> Installing build dependencies
"%VENV_PYTHON%" -m pip install -r requirements-build.txt
if errorlevel 1 (
  echo.
  echo Failed to install build dependencies.
  pause
  exit /b 1
)

echo.
echo ==> Building GUI package
"%VENV_PYTHON%" -m PyInstaller --clean --noconfirm excel-data-analysis-gui.spec
if errorlevel 1 (
  echo.
  echo GUI build failed.
  pause
  exit /b 1
)

echo.
echo ==> Building CLI package
"%VENV_PYTHON%" -m PyInstaller --clean --noconfirm excel-data-analysis-cli.spec
if errorlevel 1 (
  echo.
  echo CLI build failed.
  pause
  exit /b 1
)

echo.
echo Build completed successfully.
echo GUI output: dist\ExcelDataAnalysis
echo CLI output: dist\excel-data-analysis
pause
