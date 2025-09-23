@echo off
echo Installing B2 Sync Local...
echo.

REM Change to the script directory to ensure we're in the right location
cd /d "%~dp0"
echo Working directory: %CD%

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found in current directory.
    echo Current directory: %CD%
    dir
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

REM Install the application
echo Installing B2 Sync Local...
pip install -e .
if errorlevel 1 (
    echo Error: Failed to install application.
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\B2 Sync Local.lnk
set TARGET_PATH=%CD%\venv\Scripts\b2-sync-local-gui.exe
set WORKING_DIR=%CD%

powershell -ExecutionPolicy Bypass -File "%CD%\create_shortcut.ps1" -ShortcutPath "%SHORTCUT_PATH%" -TargetPath "%TARGET_PATH%" -WorkingDirectory "%WORKING_DIR%"

REM Add to startup (optional)
echo.
set /p ADD_STARTUP="Add B2 Sync to Windows startup? (y/n): "
if /i "%ADD_STARTUP%"=="y" (
    set STARTUP_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
    set STARTUP_SHORTCUT=%STARTUP_PATH%\B2 Sync Local.lnk
    powershell -ExecutionPolicy Bypass -File "%CD%\create_shortcut.ps1" -ShortcutPath "%STARTUP_SHORTCUT%" -TargetPath "%TARGET_PATH%" -WorkingDirectory "%WORKING_DIR%" -WindowStyle 7
    echo Added to Windows startup.
)

echo.
echo Installation completed successfully!
echo.
echo You can now:
echo 1. Run B2 Sync Local from the desktop shortcut
echo 2. Configure your B2 credentials in the settings
echo 3. Start syncing your files
echo.
pause