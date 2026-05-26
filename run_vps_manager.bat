@echo off
REM VPS Manager — Windows launcher
cd /d "%~dp0"
echo ^=^=^> Installing / verifying dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo.
echo ^=^=^> Starting VPS Manager...
python main.py
if errorlevel 1 (
    echo ERROR: Application exited with error.
    pause
)
