@echo off
rem Double-click to open your job search dashboard in your web browser.
rem Keep this window open while you use the dashboard. Close it to stop.
cd /d "%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 (
  py tracker\dashboard.py %*
) else (
  python tracker\dashboard.py %*
)
if errorlevel 1 (
  echo.
  echo Something went wrong. Read the message above, or see docs\05-use-the-dashboard.md.
  echo If it says Python was not found, install Python first: docs\01-install-prerequisites.md, step 2.
  pause
)
