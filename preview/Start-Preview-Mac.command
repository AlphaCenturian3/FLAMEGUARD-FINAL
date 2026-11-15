#!/bin/bash
# Double-click to start the FlameGuard-SI development preview on a Mac.
cd "$(dirname "$0")/.." || exit 1
PY=$(command -v python3.12 || command -v python3.11 || command -v python3)
if [ -z "$PY" ]; then echo "Python 3.11 or newer is not installed. See preview/README.md."; read -r -p "Press Enter to close"; exit 1; fi
( sleep 12; open "http://127.0.0.1:8790/" ) &
"$PY" preview/run.py
read -r -p "Preview stopped. Press Enter to close"
