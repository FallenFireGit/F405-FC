"""Run kicad-cli DRC (with schematic parity) and summarise violations by type. Usage: kc 'python3 gen/drc_summary.py [filter]'"""
import json
import subprocess
import sys

PCB = "/work/kicad/F405FC.kicad_pcb"
subprocess.run(["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
                "-o", "/tmp/drc.json", PCB], stdout=subprocess.DEVNULL)
d = json.load(open("/tmp/drc.json"))
from collections import Counter
cnt = Counter(v["type"] for v in d["violations"])
print("violations:", dict(cnt))
print("unconnected:", len(d.get("unconnected_items", [])), "parity:", len(d.get("schematic_parity", [])))
flt = sys.argv[1] if len(sys.argv) > 1 else None
for v in d["violations"]:
    if flt and flt not in v["type"]:
        continue
    print(v["type"], "|", v["description"][:60], "|", "; ".join(i["description"][:50] for i in v["items"]))
if "--parity" in sys.argv:
    for v in d.get("schematic_parity", []):
        print("PARITY", v["description"], [i["description"] for i in v["items"]])
