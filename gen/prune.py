"""Post-route cleanup of the board file from the last DRC report (host python; text edit, no pcbnew: KiCad 10.0.6 SWIG
segfaults on board.Remove).

  python3 gen/prune.py [drc.json]      then refill zones and re-run DRC (gen/route_finish.sh does this)

- via_dangling (only with PRUNE_DANGLING=1; off by default because the router often attaches to a fanout stub's knee, so trimming
  can cut a used stub; the unused vias are left as DRC warnings): an MCU fanout via the router did not use. The via is deleted together with its stub (a same-net segment ending
  on the via) when no other same-net segment ends anywhere along that stub away from its pad end.
- hole_to_hole between two GND vias: the unlocked one (else the second) is deleted; GND stays tied through the other via and
  the pours. The DRC run that follows checks that nothing became unconnected.
"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "kicad", "F405FC.kicad_pcb")
DRC = sys.argv[1] if len(sys.argv) > 1 else "/opt/kroot/tmp/drc.json"
OX = OY = 100.0
BLOCK = re.compile(r"\t\((via|segment)\n.*?\n\t\)\n", re.S)


def num(blk, key):
    m = re.search(r"\(" + key + r" ([-0-9.]+) ([-0-9.]+)\)", blk)
    return (float(m.group(1)), float(m.group(2))) if m else None


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def main():
    txt = open(PCB).read()
    d = json.load(open(DRC))
    items = []
    for m in BLOCK.finditer(txt):
        blk = m.group(0)
        net = re.search(r'\(net "([^"]*)"\)', blk).group(1)
        if m.group(1) == "via":
            items.append({"k": "v", "span": m.span(), "at": num(blk, "at"), "net": net, "locked": "(locked yes)" in blk})
        else:
            items.append({"k": "s", "span": m.span(), "a": num(blk, "start"), "b": num(blk, "end"), "net": net,
                          "w": float(re.search(r"\(width ([0-9.]+)\)", blk).group(1)), "locked": "(locked yes)" in blk})

    def close(p, q, tol=0.003):
        return math.hypot(p[0] - q[0], p[1] - q[1]) <= tol

    def via_at(x, y):
        return next((it for it in items if it["k"] == "v" and close(it["at"], (x + OX, y + OY), 0.01)), None)
    drop = set()
    n_dang = n_h2h = 0
    for v in d["violations"]:
        if v["type"] == "via_dangling" and os.environ.get("PRUNE_DANGLING") == "1":
            p = v["items"][0]["pos"]
            via = via_at(p["x"] - OX, p["y"] - OY)
            if via is None:
                continue
            drop.add(via["span"])
            n_dang += 1
            for s in items:
                if s["k"] != "s" or s["net"] != via["net"]:
                    continue
                if close(s["a"], via["at"]) or close(s["b"], via["at"]):
                    far = s["b"] if close(s["a"], via["at"]) else s["a"]
                    # keep the stub when another same-net segment ends anywhere along it away from its pad end
                    used = any(o is not s and o["k"] == "s" and o["net"] == s["net"] and
                               any(seg_dist(e, s["a"], s["b"]) <= s["w"] / 2 + 0.01 and not close(e, far, 0.05)
                                   for e in (o["a"], o["b"]))
                               for o in items)
                    if not used:
                        drop.add(s["span"])
        elif v["type"] == "hole_to_hole":
            vs = [via_at(i["pos"]["x"] - OX, i["pos"]["y"] - OY) for i in v["items"]]
            if len(vs) == 2 and all(vs) and all(x["net"] == "GND" for x in vs) and not any(x["span"] in drop for x in vs):
                victim = vs[0] if not vs[0]["locked"] else vs[1]
                if victim["locked"]:
                    continue
                drop.add(victim["span"])
                n_h2h += 1
    for a, b in sorted(drop, reverse=True):
        txt = txt[:a] + txt[b:]
    open(PCB, "w").write(txt)
    print(f"prune: {n_dang} dangling vias, {n_h2h} hole-to-hole GND vias, {len(drop)} items deleted")


if __name__ == "__main__":
    main()
