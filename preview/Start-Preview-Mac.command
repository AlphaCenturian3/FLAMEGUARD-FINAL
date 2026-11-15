#!/bin/bash
# Double-click to start the FlameGuard-SI development preview on a Mac.
# If port 8790 is busy (an older preview), it uses the next free port and opens that address.
cd "$(dirname "$0")/.." || exit 1
PY=$(command -v python3.12 || command -v python3.11 || command -v python3)
if [ -z "$PY" ]; then echo "Python 3.11 or newer is not installed. See preview/README.md."; read -r -p "Press Enter to close"; exit 1; fi
"$PY" preview/run.py --auto-port --open
read -r -p "Preview stopped. Press Enter to close"
