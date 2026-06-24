@echo off
setlocal enabledelayedexpansion

:: Project Forge v1.0.0 - Codex Plugin Installer (CMD version)
:: Usage: install-codex.cmd

set "VERSION=1.0.0"
set "RELEASE_URL=https://github.com/Haozhenyu123/project-forge/releases/download/v%VERSION%/project-forge-codex-%VERSION%.zip"

if not defined CODEX_HOME set "CODEX_HOME=%USERPROFILE%\.codex"
if not defined AGENTS_HOME set "AGENTS_HOME=%USERPROFILE%\.agents"

set "PLUGIN_DIR=%CODEX_HOME%\plugins\project-forge"
set "MARKET_FILE=%AGENTS_HOME%\plugins\marketplace.json"
set "TEMP_DIR=%TEMP%\project-forge-install"

echo ========================================
echo   Project Forge v%VERSION% - Codex Plugin Installer
echo ========================================
echo.
echo Codex home : %CODEX_HOME%
echo Plugin dir : %PLUGIN_DIR%
echo.

:: Check if already installed
if exist "%PLUGIN_DIR%\.codex-plugin\plugin.json" (
    echo Project Forge is already installed.
    echo To reinstall, delete %PLUGIN_DIR% and run this script again.
    echo.
    pause
    exit /b 1
)

:: Download
echo Downloading Project Forge v%VERSION%...
powershell -Command "Invoke-WebRequest -Uri '%RELEASE_URL%' -OutFile '%TEMP_DIR%.zip' -UseBasicParsing"
if %ERRORLEVEL% neq 0 (
    echo Download failed. Check your internet connection.
    pause
    exit /b 1
)
echo [+] Downloaded

:: Extract
echo Extracting...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
powershell -Command "Expand-Archive -Path '%TEMP_DIR%.zip' -DestinationPath '%TEMP_DIR%' -Force"
if %ERRORLEVEL% neq 0 (
    echo Extraction failed.
    pause
    exit /b 1
)
echo [+] Extracted

:: Find plugin root in extracted archive
for /d %%d in ("%TEMP_DIR%\*") do (
    if exist "%%d\.codex-plugin\plugin.json" (
        set "PLUGIN_ROOT=%%d"
    )
)
if not defined PLUGIN_ROOT (
    echo Could not find plugin root in archive.
    pause
    exit /b 1
)

:: Install
echo Installing to %PLUGIN_DIR%...
if exist "%PLUGIN_DIR%" rmdir /s /q "%PLUGIN_DIR%"
if not exist "%CODEX_HOME%\plugins" mkdir "%CODEX_HOME%\plugins"
xcopy /e /i /q "%PLUGIN_ROOT%" "%PLUGIN_DIR%"
echo [+] Plugin files installed

:: Register in marketplace
echo Registering in Codex marketplace...
if not exist "%AGENTS_HOME%\plugins" mkdir "%AGENTS_HOME%\plugins"
powershell -Command "$d=if(Test-Path '%MARKET_FILE%'){Get-Content '%MARKET_FILE%'|ConvertFrom-Json}else@{name='personal';interface=@{displayName='Personal Plugins'};plugins=@()};$d.plugins=@($d.plugins|?{$_.name -ne 'project-forge'})+@{name='project-forge';path='%PLUGIN_DIR%';version='%VERSION%'};$d|ConvertTo-Json -Depth 4|Set-Content '%MARKET_FILE%'"
echo [+] Marketplace registered

:: Cleanup
del /q "%TEMP_DIR%.zip" 2>nul
rmdir /s /q "%TEMP_DIR%" 2>nul

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo   Restart Codex to see Project Forge in your plugin list.
echo.
pause
