@echo off
REM VPS Manager — Windows launcher (uv)
cd /d "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: 'uv' not found. Install it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo ^=^=^> Syncing dependencies with uv...
uv sync --quiet
if errorlevel 1 (
    echo ERROR: uv sync failed.
    pause
    exit /b 1
)

echo.
echo ^=^=^> Starting VPS Manager...
uv run python main.py
if errorlevel 1 (
    echo ERROR: Application exited with error.
    pause
)
