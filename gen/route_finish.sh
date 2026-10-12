#!/bin/bash
# Final board assembly from the routing result (see gen/ripup.py):
#   fresh placement build -> critical routes -> MCU inward fanout -> all router tracks/vias (kicad/route_all.json) -> GND planes/pours -> fill -> DRC
# Usage: bash gen/route_finish.sh   (expects kicad/route_all.json, produced from a Freerouting + ripup run)
set -euo pipefail
cd "$(dirname "$0")/.."
kc 'python3 gen/build_pcb.py --fresh >/dev/null 2>&1
python3 gen/critical.py
FANOUT=mcu python3 gen/gndfan.py
F405_ROUTES=route_all.json python3 gen/rapply.py
python3 gen/route.py --stage zones
python3 gen/route.py --stage pours
python3 gen/route.py --stage minwidth
python3 gen/route.py --stage fill
python3 gen/drc_summary.py' 2>&1 | grep -v Debug
