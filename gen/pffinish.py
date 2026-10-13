#!/usr/bin/python3.13
"""Finish a nearly converged PathFinder result: freeze the GND plane ties as fixed copper, re-route the signal nets that
still conflict with everything else hard (no overlap accepted), then re-tie any GND island whose tie had to go.

  F405_PCB=<dir>/F405FC.kicad_pcb ROUTE_RES=0.025 IN1=1 IN1_COST=1.0 GND_NEED=<gnd_need.json> \
      /usr/bin/python3.13 gen/pffinish.py        (reads/writes <dir>/route_all.json)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pathfinder as pf  # noqa: E402
from mazeroute import cls, seg_mask  # noqa: E402


def load(P, path):
    r = json.load(open(path))
    for t in r["tracks"]:
        P.routes.setdefault(P.nid(t["net"]), []).append({"t": "t", "l": t["layer"], "a": tuple(t["a"]), "b": tuple(t["b"]), "w": t["w"]})
    for v in r["vias"]:
        P.routes.setdefault(P.nid(v["net"]), []).append({"t": "v", "x": v["x"], "y": v["y"]})
    for n, rs in P.routes.items():
        P.occupy(n, rs, +1)


def conflicts(P):
    over = {l: P.occ[l] > 1 for l in pf.RL}
    bad = set()
    for n, rs in P.routes.items():
        c = cls(P.names[n])[1]
        for r in rs:
            if r["t"] == "t":
                m = seg_mask(r["a"], r["b"], r["w"] / 2 + pf.occ_k(c))
                hit = (over[r["l"]] & m).any()
            else:
                m = seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3 + pf.occ_k(c))
                hit = any((over[l] & m).any() for l in pf.RL)
            if hit:
                bad.add(P.names[n])
                break
    return bad, int(sum(int(o.sum()) for o in over.values()))


def main():
    g = json.load(open(pf.GEOM))
    P = pf.PF(g)
    load(P, pf.OUT)
    gid = P.nid("GND")
    if os.environ.get("FORCE_GND") == "1":
        # tie the GND islands listed in GND_NEED first (they may overlap signals); the signals then move around them
        made = pf.gnd_force(P, float(os.environ.get("GND_PRES", "20")))
        print("forced GND ties:", made, flush=True)
        P.gnd_ties = []
    bad, ov = conflicts(P)
    print("start: overuse", ov, "nets", sorted(bad), flush=True)
    # GND ties that overlap a signal are dropped (re-tied at the end); the rest become fixed GND copper
    sig_bad = sorted(b for b in bad if b != "GND")
    gnd_recs = P.routes.get(gid, [])
    over = {l: P.occ[l] > 1 for l in pf.RL}
    keep, drop = [], []
    for r in gnd_recs:
        if r["t"] == "t":
            hit = (over[r["l"]] & seg_mask(r["a"], r["b"], r["w"] / 2 + pf.occ_k(0.127))).any()
        else:
            hit = any((over[l] & seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3 + pf.occ_k(0.127))).any() for l in pf.RL)
        (drop if hit and os.environ.get("FORCE_GND") != "1" else keep).append(r)
    P.occupy(gid, gnd_recs, -1)
    P.routes[gid] = keep
    P.occupy(gid, keep, +1)
    print(f"GND records kept {len(keep)}, dropped {len(drop)}", flush=True)
    # signals in conflict: rip all, then try every routing order with a prohibitive overlap cost; keep the first order
    # in which every net routes without overlapping anything
    import itertools
    for net in sig_bad:
        n = P.nid(net)
        P.occupy(n, P.routes[n], -1)
        P.routes[n] = []
    ok = False
    orders = list(itertools.islice(itertools.permutations(sig_bad), 24))   # n! explodes: cap the tries
    for order in orders:
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
        print(f"order {order}: routed {len(recs)}/{len(order)}, overuse {ov}, conflicts {sorted(bad)}", flush=True)
        if len(recs) == len(order) and ov == 0:
            ok = True
            break
        for net, r in recs.items():
            n = P.nid(net)
            P.occupy(n, r, -1)
            P.routes[n] = []
    if not ok:
        print("pffinish: no overlap-free order found; result NOT saved")
        return
    left = pf.gnd_pass(P)
    bad, ov = conflicts(P)
    print(f"GND pass: {left} islands left untied; final overuse {ov}, conflicts {sorted(bad)}", flush=True)
    pf.save(P, pf.OUT)


if __name__ == "__main__":
    main()
