#!/usr/bin/python3.13
"""Tidy the routed tracks (cosmetic + segment count): every chain of track segments between two junctions (pad, via, branch
point, layer change) is string-pulled: the longest straight replacements whose copper stays clear of fixed copper and of
every other net's routed copper (the router's own clearance model) replace the grid staircase. Junctions never move, so
connectivity is unchanged. Run on kicad/route_all.json before gen/route_finish.sh; KiCad DRC re-checks the result.

  ROUTE_RES=0.025 IN1=1 /usr/bin/python3.13 gen/tidy.py
"""
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pathfinder as pf  # noqa: E402
from mazeroute import N, RES, cls, seg_mask  # noqa: E402


def key(p):
    return (round(p[0] / RES * 2), round(p[1] / RES * 2))


def main():
    P = pf.PF(json.load(open(pf.GEOM)))
    r = json.load(open(pf.OUT))
    for t in r["tracks"]:
        P.routes.setdefault(P.nid(t["net"]), []).append({"t": "t", "l": t["layer"], "a": tuple(t["a"]), "b": tuple(t["b"]), "w": t["w"]})
    for v in r["vias"]:
        P.routes.setdefault(P.nid(v["net"]), []).append({"t": "v", "x": v["x"], "y": v["y"]})
    for n, rs in P.routes.items():
        P.occupy(n, rs, +1)
    before = sum(1 for rs in P.routes.values() for x in rs if x["t"] == "t")
    for n in list(P.routes):
        net = P.names[n]
        rs = P.routes[n]
        tracks = [x for x in rs if x["t"] == "t"]
        if len(tracks) < 2:
            continue
        w, c = cls(net)
        P.occupy(n, rs, -1)
        hard, _vh = P.hard(n)
        others = {l: P.occ[l] > 0 for l in pf.RL}
        # fixed nodes: vias, pad copper of this net, ends shared by != 2 segments on a layer
        fixed = set()
        for x in rs:
            if x["t"] == "v":
                for l in pf.RL:
                    fixed.add((l, key((x["x"], x["y"]))))
        deg = collections.Counter()
        for t in tracks:
            deg[(t["l"], key(t["a"]))] += 1
            deg[(t["l"], key(t["b"]))] += 1
        own_pad = {l: (P.base[l] == n) for l in pf.ALL}

        def is_fixed(l, p):
            i, j = min(N - 1, int(p[1] / RES)), min(N - 1, int(p[0] / RES))
            return (l, key(p)) in fixed or deg[(l, key(p))] != 2 or own_pad[l][i, j]
        # chains
        adj = collections.defaultdict(list)
        for idx, t in enumerate(tracks):
            adj[(t["l"], key(t["a"]))].append(idx)
            adj[(t["l"], key(t["b"]))].append(idx)
        used = set()
        new_tracks = []
        for idx, t in enumerate(tracks):
            if idx in used:
                continue
            # walk to one end of the chain
            l = t["l"]
            cur, pt = idx, t["a"]
            seen = {idx}
            while not is_fixed(l, pt):
                nxt = [k for k in adj[(l, key(pt))] if k != cur and k not in seen]
                if not nxt:
                    break
                cur = nxt[0]
                seen.add(cur)
                tt = tracks[cur]
                pt = tt["b"] if key(tt["a"]) == key(pt) else tt["a"]
            # walk forward collecting points
            start = pt
            pts = [start]
            prev = None
            cur_pt = start
            chain = []
            while True:
                cand = [m for m in adj[(l, key(cur_pt))] if m != prev and m not in chain and m not in used]
                if not cand:
                    break
                m = cand[0]
                chain.append(m)
                tt = tracks[m]
                cur_pt = tt["b"] if key(tt["a"]) == key(cur_pt) else tt["a"]
                pts.append(cur_pt)
                prev = m
                if is_fixed(l, cur_pt):
                    break
            used.update(chain)
            if not chain:
                used.add(idx)
                new_tracks.append(t)
                continue
            width = tracks[chain[0]]["w"]

            def legal(a, b):
                core = seg_mask(a, b, RES * 0.75)       # covers every cell the centre line crosses
                if (hard[l] & core & ~own_pad[l]).any():
                    return False
                fp = seg_mask(a, b, width / 2 + pf.occ_k(c))
                return not (others[l] & fp).any()
            out = [pts[0]]
            i = 0
            while i < len(pts) - 1:
                j = len(pts) - 1
                while j > i + 1 and not legal(pts[i], pts[j]):
                    j -= 1
                out.append(pts[j])
                i = j
            for a, b in zip(out, out[1:]):
                if key(a) != key(b):
                    new_tracks.append({"t": "t", "l": l, "a": tuple(a), "b": tuple(b), "w": width})
        P.routes[n] = new_tracks + [x for x in rs if x["t"] == "v"]
        P.occupy(n, P.routes[n], +1)
    after = sum(1 for rs in P.routes.values() for x in rs if x["t"] == "t")
    pf.save(P, pf.OUT)
    print(f"tidy: track segments {before} -> {after}")


if __name__ == "__main__":
    main()
