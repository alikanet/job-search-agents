#!/bin/bash
# Double-click to run the CV and cover letter agent.
cd "$(dirname "$0")/../cv-cover-letter-agent" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "The CV and cover letter agent is not set up yet."
  echo "Follow step 5 of docs/01-install-prerequisites.md, then try again."
  read -r -p "Press Enter to close this window." _
  exit 1
fi
.venv/bin/python tailor_application.py
echo
read -r -p "Press Enter to close this window." _
