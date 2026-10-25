@echo off
rem Double-click to run the CV and cover letter agent.
cd /d "%~dp0..\cv-cover-letter-agent"
if not exist .venv\Scripts\python.exe (
  echo The CV and cover letter agent is not set up yet.
  echo Follow step 5 of docs\01-install-prerequisites.md, then try again.
  pause
  exit /b 1
)
.venv\Scripts\python tailor_application.py
echo.
pause
