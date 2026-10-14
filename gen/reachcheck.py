#!/usr/bin/python3.13
"""Routability pre-check: for every net, are all its fixed copper islands mutually reachable through free space?

Free space per net = cells where a trace of that net's class may run (pads/holes/edge/keepouts of other nets excluded with the
exact clearance; routed copper ignored). Layers join only at cells where a via is legal. Prints the islands that cannot be reached:
these need a placement change, no router can connect them.   Usage: /usr/bin/python3.13 gen/reachcheck.py [net ...]
"""
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json  # noqa: E402
import pathfinder as pf  # noqa: E402


def components(P, n, isl):
    hard, vh = P.hard(n)
    own = {l: np.any([m[l] | m["In1"] for m in isl], axis=0) for l in pf.RL}
    labs, offs, tot = {}, {}, 0
    for l in pf.RL:
        lab, k = ndimage.label(~hard[l] | own[l], structure=np.ones((3, 3)))
        labs[l], offs[l] = lab, tot
        tot += k
    parent = np.arange(tot + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    vok = ~vh
    for a_l in range(len(pf.RL)):
        for b_l in range(a_l + 1, len(pf.RL)):
            la, lb = labs[pf.RL[a_l]], labs[pf.RL[b_l]]
            sel = vok & (la > 0) & (lb > 0)
            pairs = np.unique(np.stack([la[sel] + offs[pf.RL[a_l]], lb[sel] + offs[pf.RL[b_l]]], 1), axis=0)
            for x, y in pairs:
                rx, ry = find(x), find(y)
                if rx != ry:
                    parent[rx] = ry
    roots = []
    for m in isl:
        rs = set()
        for l in pf.RL:
            mm = m[l] | m["In1"]
            v = labs[l][mm]
            for x in np.unique(v[v > 0]):
                rs.add(find(x + offs[l]))
        roots.append(rs)
    return roots


def main():
    g = json.load(open(pf.GEOM))
    P = pf.PF(g)
    nets = sorted({p["net"] for p in g["pads"] if p["net"] and p["net"] != "GND" and not p["net"].startswith("unconnected-")})
    if len(sys.argv) > 1:
        nets = sys.argv[1:]
    bad = 0
    for net in nets:
        n = P.nid(net)
        isl = P.islands(n, [])
        if len(isl) <= 1:
            continue
        roots = components(P, n, isl)
        # union-find over islands sharing a root
        grp = list(range(len(isl)))
        for i in range(len(isl)):
            for j in range(i + 1, len(isl)):
                if roots[i] & roots[j]:
                    gi, gj = grp[i], grp[j]
                    grp = [gi if x == gj else x for x in grp]
        if len(set(grp)) > 1:
            bad += 1
            desc = []
            for k, m in enumerate(isl):
                c = np.argwhere(np.any([m[l] for l in pf.ALL], axis=0)).mean(0) * pf.RES
                lay = "".join(l[0] if l != "In2" else "2" for l in pf.ALL if m[l].any())
                desc.append(f"#{grp[k]}@({c[1]:.1f},{c[0]:.1f}){lay}{'' if roots[k] else ' (no free exit)'}")
            print(f"UNREACHABLE {net}: " + "  ".join(desc), flush=True)
    print(f"reachcheck: {bad} nets with unreachable islands")


if __name__ == "__main__":
    main()
