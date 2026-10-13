#!/bin/bash
# Finish routing with Freerouting: the PathFinder result (ROUTES json) minus the nets still in conflict (DROP, comma list) is
# applied and locked; Freerouting then routes only the dropped nets and the GND pads that are not yet tied to the In1 plane.
# Usage: ROUTES=/path/route_all.json DROP=NET1,NET2 bash gen/fr_finish.sh [passes]
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - "$ROUTES" "$DROP" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); drop = set(sys.argv[2].split(",")) | {"GND"}
r["tracks"] = [t for t in r["tracks"] if t["net"] not in drop]
r["vias"] = [v for v in r["vias"] if v["net"] not in drop]
json.dump(r, open("kicad/route_fr_base.json", "w"))
print("fr_finish: base routes", len(r["tracks"]), "tracks", len(r["vias"]), "vias; dropped", sorted(drop))
PY
kc 'python3 gen/build_pcb.py --fresh >/dev/null 2>&1
python3 gen/critical.py >/dev/null
FANOUT=mcu python3 gen/gndfan.py >/dev/null
F405_ROUTES=route_fr_base.json python3 gen/rapply.py >/dev/null
python3 gen/gndfan.py | tail -1
python3 gen/route.py --stage zones >/dev/null
python3 gen/route.py --stage lockall
python3 gen/route.py --stage dsn
rm -f /work/kicad/F405FC.ses
/opt/jdk/bin/java -Djava.awt.headless=true -jar /opt/fr/freerouting-2.5.0.jar -de /work/kicad/F405FC.dsn -do /work/kicad/F405FC.ses -mp '"${1:-30}"' -mt 3 > /tmp/fr_finish.log 2>&1 || echo "freerouting exit $?"
tail -3 /tmp/fr_finish.log
python3 gen/route.py --stage ses
python3 gen/route.py --stage minwidth >/dev/null
python3 gen/route.py --stage pours >/dev/null
python3 gen/route.py --stage fill >/dev/null
python3 gen/drc_summary.py >/dev/null' 2>&1 | grep -v Debug
python3 gen/prune.py
kc 'python3 gen/route.py --stage fill >/dev/null; python3 gen/drc_summary.py | grep -E "^violations|^unconn"' 2>&1 | grep -v Debug
