"""Grouped BOM from design/circuit.py -> bom/bom_raw.csv (one line per MPN, DNP and PCB-only items excluded).

Usage: kc 'python3 gen/bom.py'   (needs the KiCad chroot only because circuit.py loads stock symbols)
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, os.path.join(ROOT, "design"))
import circuit  # noqa: E402

rows = {}
dnp = []
for p in circuit.c.parts:
    if p.ref.startswith("#") or p.fields.get("InBOM") == "no":
        continue
    if p.dnp:
        dnp.append(p.ref)
        continue
    k = p.fields["MPN"]
    r = rows.setdefault(k, {"MPN": k, "Manufacturer": p.fields["Manufacturer"], "DigiKey": p.fields["DigiKey"],
                            "Value": p.value, "Footprint": p.footprint.split(":", 1)[1], "Refs": [],
                            "Datasheet": p.fields.get("Datasheet", "")})
    r["Refs"].append(p.ref)
out = os.path.join(ROOT, "bom", "bom_raw.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Qty per board", "Refs", "Value", "MPN", "Manufacturer", "DigiKey PN", "Footprint", "Datasheet"])
    for r in sorted(rows.values(), key=lambda r: (r["Refs"][0][0], -len(r["Refs"]), r["MPN"])):
        w.writerow([len(r["Refs"]), " ".join(r["Refs"]), r["Value"], r["MPN"], r["Manufacturer"], r["DigiKey"],
                    r["Footprint"], r["Datasheet"]])
print(f"{len(rows)} lines, {sum(len(r['Refs']) for r in rows.values())} placements; DNP: {' '.join(dnp)} -> {out}")
