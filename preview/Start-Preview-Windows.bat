@echo off
REM Double-click to start the FlameGuard-SI development preview on Windows.
REM If port 8790 is busy (an older preview), it uses the next free port and opens that address.
cd /d "%~dp0.."
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.11 or newer is not installed. See preview\README.md.
  pause
  exit /b 1
)
py -3 preview\run.py --auto-port --open
pause
