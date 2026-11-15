@echo off
REM Double-click to start the FlameGuard-SI development preview on Windows.
cd /d "%~dp0.."
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 or newer is not installed. See preview\README.md.
  pause
  exit /b 1
)
start "" /min cmd /c "timeout /t 12 >nul & start http://127.0.0.1:8790/"
py -3 preview\run.py
pause
