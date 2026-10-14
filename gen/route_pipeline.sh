#!/bin/bash
# Full routing pipeline (reproducible), 6-layer rev D: pre-route board -> reachability check -> PathFinder on F/In2/In3/B
# (In1/In4 solid GND, never routed) -> PathFinder resume at 0.025 mm with the GND plane ties -> board rebuild, pours, fill, DRC.
set -euo pipefail
cd "$(dirname "$0")/.."
kc 'python3 gen/build_pcb.py --fresh >/dev/null 2>&1; python3 gen/critical.py; FANOUT=mcu python3 gen/gndfan.py; python3 gen/gndfan.py; python3 gen/route.py --stage zones; python3 gen/rexport.py' 2>&1 | grep -v Debug
/usr/bin/python3.13 gen/reachcheck.py
GND=0 /usr/bin/python3.13 gen/pathfinder.py "${PF_PASSES:-40}"
RESUME=1 PRES="${PF_PRES:-500}" ROUTE_RES="${PF_RES:-0.025}" /usr/bin/python3.13 gen/pathfinder.py "${PF_RESUME:-15}"
bash gen/route_finish.sh
