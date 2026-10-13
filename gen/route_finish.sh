#!/bin/bash
# Final board assembly from the routing result (gen/pathfinder.py -> kicad/route_all.json):
#   fresh placement build -> critical routes -> MCU inward fanout -> all router tracks/vias -> GND stitching -> GND planes/pours
#   -> fill -> DRC -> prune too-close GND vias (gen/prune.py) -> neck power tracks with sub-um..5 um clearance misses
#   (gen/drcfix.py, NARROW_ONLY) -> refill -> final DRC
set -euo pipefail
cd "$(dirname "$0")/.."
kc 'python3 gen/build_pcb.py --fresh >/dev/null 2>&1
python3 gen/critical.py
FANOUT=mcu python3 gen/gndfan.py
F405_ROUTES=route_all.json python3 gen/rapply.py
python3 gen/gndfan.py
python3 gen/route.py --stage zones
python3 gen/route.py --stage pours
python3 gen/route.py --stage minwidth
python3 gen/route.py --stage fill
python3 gen/drc_summary.py >/dev/null' 2>&1 | grep -v Debug
python3 gen/prune.py
kc 'NARROW_ONLY=1 python3 gen/drcfix.py 2 | tail -1
python3 gen/route.py --stage fill >/dev/null
python3 gen/drc_summary.py' 2>&1 | grep -v Debug
