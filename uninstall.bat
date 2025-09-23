@echo off
echo Uninstalling B2 Sync Local...
echo.

REM Stop any running instances
echo Stopping B2 Sync Local processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq B2 Sync Local*" >nul 2>&1

REM Remove desktop shortcut
echo Removing desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\B2 Sync Local.lnk
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo Desktop shortcut removed.
)

REM Remove startup shortcut
echo Removing startup shortcut...
set STARTUP_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set STARTUP_SHORTCUT=%STARTUP_PATH%\B2 Sync Local.lnk
if exist "%STARTUP_SHORTCUT%" (
    del "%STARTUP_SHORTCUT%"
    echo Startup shortcut removed.
)

REM Remove virtual environment
echo Removing virtual environment...
if exist "venv" (
    rmdir /s /q venv
    echo Virtual environment removed.
)

REM Ask about configuration and logs
echo.
set /p REMOVE_CONFIG="Remove configuration files and logs? (y/n): "
if /i "%REMOVE_CONFIG%"=="y" (
    echo Removing configuration and logs...
    
    REM Remove config directory
    set CONFIG_DIR=%APPDATA%\B2SyncLocal
    if exist "%CONFIG_DIR%" (
        rmdir /s /q "%CONFIG_DIR%"
        echo Configuration files removed.
    )
    
    REM Remove logs directory
    set LOGS_DIR=%LOCALAPPDATA%\B2SyncLocal\logs
    if exist "%LOGS_DIR%" (
        rmdir /s /q "%LOGS_DIR%"
        echo Log files removed.
    )
)

echo.
echo Uninstallation completed!
echo.
echo Note: The application source files remain in this directory.
echo You can safely delete this entire folder if you no longer need it.
echo.
pause