#!/bin/bash
# Double-click to open your job search dashboard in your web browser.
# Keep this window open while you use the dashboard. Close it to stop.
cd "$(dirname "$0")/.." || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python is not installed yet. Follow step 2 of docs/01-install-prerequisites.md, then try again."
  read -r -p "Press Enter to close this window." _
  exit 1
fi
if ! python3 tracker/dashboard.py "$@"; then
  echo
  echo "Something went wrong. Read the message above, or see docs/05-use-the-dashboard.md."
  read -r -p "Press Enter to close this window." _
fi
