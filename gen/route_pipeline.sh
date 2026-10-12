#!/bin/bash
# Full routing pipeline (reproducible): pre-route board -> reachability check -> PathFinder (F/In2/B) -> PathFinder resume with
# last-resort In1 hops + GND plane ties -> board rebuild with all routes, pours, fill, DRC.
set -euo pipefail
cd "$(dirname "$0")/.."
kc 'python3 gen/build_pcb.py --fresh >/dev/null 2>&1; python3 gen/critical.py; FANOUT=mcu python3 gen/gndfan.py; python3 gen/route.py --stage zones; python3 gen/rexport.py' 2>&1 | grep -v Debug
/usr/bin/python3.13 gen/reachcheck.py
GND=0 /usr/bin/python3.13 gen/pathfinder.py "${PF_PASSES:-40}"
RESUME=1 PRES="${PF_PRES:-500}" IN1=1 IN1_COST="${PF_IN1_COST:-6}" /usr/bin/python3.13 gen/pathfinder.py "${PF_RESUME:-15}"
bash gen/route_finish.sh
