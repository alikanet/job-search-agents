#!/bin/bash
# Double-click to start Claude Code in the interview prep folder, ready for /prep and /debrief.
cd "$(dirname "$0")/../interview-prep-agent" || exit 1
export PATH="$HOME/.local/bin:$PATH"  # where the Claude Code installer puts it
if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code is not installed yet."
  echo "Follow steps 3 and 4 of docs/01-install-prerequisites.md, then try again."
  read -r -p "Press Enter to close this window." _
  exit 1
fi
claude
