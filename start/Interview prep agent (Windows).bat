@echo off
rem Double-click to start Claude Code in the interview prep folder, ready for /prep and /debrief.
cd /d "%~dp0..\interview-prep-agent"
where claude >nul 2>nul
if errorlevel 1 (
  echo Claude Code is not installed yet.
  echo Follow steps 3 and 4 of docs\01-install-prerequisites.md, then try again.
  pause
  exit /b 1
)
claude
