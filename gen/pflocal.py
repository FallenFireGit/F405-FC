#!/usr/bin/python3.13
"""Local GND repair on a finished PathFinder result: rip the named signal nets (RIP=NET1,NET2), tie the GND islands listed in
GND_NEED with the strict GND pass (no overlap with anything; same-layer ties to GND copper that already reaches the plane are
preferred), then route the ripped nets back with overlap forbidden. Saves only if nothing overlaps.

  F405_PCB=<dir>/F405FC.kicad_pcb ROUTE_RES=0.025 IN1=1 IN1_COST=1.0 GND_NEED=<json> RIP=VTX_PWR_EN \
      /usr/bin/python3.13 gen/pflocal.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from scipy import ndimage  # noqa: E402
import pathfinder as pf  # noqa: E402
from mazeroute import cls  # noqa: E402
from pffinish import conflicts, load  # noqa: E402


def _orders(nets, cap=24):
    """Up to `cap` routing orders, spread so that every net gets to go first (n! explodes for more than four nets)."""
    import itertools
    import random
    nets = list(nets)
    if len(nets) <= 4:
        return list(itertools.permutations(nets))[:cap]
    rnd = random.Random(1)
    out = []
    for i in range(cap):
        first = nets[i % len(nets)]
        rest = [x for x in nets if x != first]
        rnd.shuffle(rest)
        out.append(tuple([first] + rest))
    return out


def main():
    P = pf.PF(json.load(open(pf.GEOM)))
    load(P, pf.OUT)
    bad, ov = conflicts(P)
    print("start: overuse", ov, sorted(bad), flush=True)
    rip = [x for x in os.environ.get("RIP", "").split(",") if x]
    for net in rip:
        n = P.nid(net)
        P.occupy(n, P.routes.get(n, []), -1)
        P.routes[n] = []
    left = pf.gnd_pass(P)
    print("GND pass: islands still untied:", left, flush=True)
    import itertools
    nets = list(rip)
    for attempt in range(3):
        best = None
        for order in _orders(nets):
            recs = {}
            for net in order:
                n = P.nid(net)
                r = P.route_net(n, 1e7)
                if r is None:
                    break
                recs[net] = r
                P.routes[n] = r
                P.occupy(n, r, +1)
            bad, ov = conflicts(P)
            print(f"  nets {order}: overuse {ov} {sorted(bad)}", flush=True)
            if len(recs) == len(order) and ov == 0:
                pf.save(P, pf.OUT)
                print("saved")
                return
            if best is None or ov < best[0]:
                best = (ov, sorted(b for b in bad if b != "GND"), order)
            for net, r in recs.items():
                n = P.nid(net)
                P.occupy(n, r, -1)
                P.routes[n] = []
        # widen: rip the signal nets the best order still collided with; if those are already in the set, rip the nets that
        # pass within 1.5 mm of the collision instead (they hold the space the colliding nets need)
        extra = [b for b in best[1] if b not in nets]
        if not extra:
            for order in [best[2]]:
                for net in order:
                    n = P.nid(net)
                    r = P.route_net(n, 1e7)
                    if r is None:
                        break
                    P.routes[n] = r
                    P.occupy(n, r, +1)
            over = np.zeros((pf.N, pf.N), bool)
            for l in pf.RL:
                over |= P.occ[l] > 1
            zone = ndimage.binary_dilation(over, structure=pf.disk(1.5))
            near = set()
            for n2, rs in P.routes.items():
                name = P.names[n2]
                if name in nets or name == "GND" or cls(name)[0] >= 0.35 or not rs:
                    continue
                for l, m in P.occupy(n2, rs, 0).items():
                    if (m & zone).any():
                        near.add(name)
                        break
            for net in best[2]:
                n = P.nid(net)
                P.occupy(n, P.routes[n], -1)
                P.routes[n] = []
            extra = sorted(near)
            if not extra:
                break
        for net in extra:
            n = P.nid(net)
            P.occupy(n, P.routes.get(n, []), -1)
            P.routes[n] = []
        nets += extra
        print("widening to", nets, flush=True)
    print("no overlap-free result; nothing saved")


if __name__ == "__main__":
    main()
