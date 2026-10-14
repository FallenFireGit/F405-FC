#!/usr/bin/python3.13
"""Tidy the routed tracks (cosmetic + segment count): every chain of track segments between two junctions (pad, via, branch
point, layer change) is string-pulled: the longest octilinear (0/45/90 degree, at most one bend) replacements whose copper stays clear of fixed copper and of
every other net's routed copper (the router's own clearance model) replace the grid staircase. Junctions never move, so
connectivity is unchanged. Run on kicad/route_all.json before gen/route_finish.sh; KiCad DRC re-checks the result.

  ROUTE_RES=0.025 IN1=1 /usr/bin/python3.13 gen/tidy.py
"""
import collections
import json
import math
import os
import sys

OCT = os.environ.get("OCT", "1") == "1"   # 0/45/90-degree output (routing appearance)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pathfinder as pf  # noqa: E402
from mazeroute import N, RES, cls, seg_mask  # noqa: E402


def key(p):
    return (round(p[0] / RES * 2), round(p[1] / RES * 2))


def split_tees(tracks, on_pad=lambda l, p: False):
    """Router T-junctions can end a branch part-way along another segment (copper overlap, no shared end point). Split such
    segments at the projection of the branch end and snap the end onto it, so the junction is a real node (degree 3) and the
    string-pull below keeps it."""
    # branch ends that sit near (not on) another segment's vertex: snap them onto it
    for t in tracks:
        for end in ("a", "b"):
            p = t[end]
            best = None
            for o in tracks:
                if o is t or o["l"] != t["l"]:
                    continue
                for v in (o["a"], o["b"]):
                    if key(v) == key(p):
                        best = None
                        break
                    d = math.hypot(p[0] - v[0], p[1] - v[1])
                    if d <= (o["w"] + t["w"]) / 2 and (best is None or d < best[0]):
                        best = (d, v)
                else:
                    continue
                break
            if best and not on_pad(t["l"], p) and not any(key(x) == key(p) for o in tracks if o is not t and o["l"] == t["l"]
                                                          for x in (o["a"], o["b"])):
                t[end] = best[1]
    changed = True
    while changed:
        changed = False
        ends = [(t["l"], p) for t in tracks for p in (t["a"], t["b"])]
        for k, t in enumerate(tracks):
            ax, ay = t["a"]
            bx, by = t["b"]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 < 1e-9:
                continue
            for l, p in ends:
                if l != t["l"] or key(p) in (key(t["a"]), key(t["b"])):
                    continue
                u = ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2
                if not 0.0 < u < 1.0:
                    continue
                q = (ax + u * dx, ay + u * dy)
                if math.hypot(p[0] - q[0], p[1] - q[1]) > t["w"] / 2 + 0.07:
                    continue
                if key(q) in (key(t["a"]), key(t["b"])):
                    continue
                # snap the branch end onto the segment and split it there
                for o in tracks:
                    if o["l"] == l:
                        if key(o["a"]) == key(p):
                            o["a"] = q
                        if key(o["b"]) == key(p):
                            o["b"] = q
                tracks[k] = dict(t, b=q)
                tracks.append(dict(t, a=q, b=(bx, by)))
                changed = True
                break
            if changed:
                break
    return tracks


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
    reverted = []
    for n in list(P.routes):
        net = P.names[n]
        rs = P.routes[n]
        tracks = [x for x in rs if x["t"] == "t"]
        if len(tracks) < 2:
            continue
        w, c = cls(net)
        P.occupy(n, rs, -1)

        def on_pad(l, p):
            i, j = min(N - 1, int(p[1] / RES)), min(N - 1, int(p[0] / RES))
            return bool(P.base[l][i, j] == n) or any(math.hypot(p[0] - v["x"], p[1] - v["y"]) < 0.31 for v in rs if v["t"] == "v")
        tracks = split_tees([dict(t) for t in tracks], on_pad)
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
            def octo(a, b):
                """Candidate 0/45/90-degree paths a -> b: straight when already octilinear, else a 45-degree leg plus an
                axis-aligned leg (both orders). Each is a list of points after a."""
                dx, dy = b[0] - a[0], b[1] - a[1]
                if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6:
                    return [[b]]
                d = min(abs(dx), abs(dy))
                sx, sy = math.copysign(d, dx), math.copysign(d, dy)
                return [[(a[0] + sx, a[1] + sy), b], [(b[0] - sx, b[1] - sy), b]]

            def path_ok(a, cand):
                q = a
                for r in cand:
                    if not legal(q, r):
                        return False
                    q = r
                return True
            out = [pts[0]]
            i = 0
            while i < len(pts) - 1:
                j = len(pts) - 1
                got = None
                while j > i:
                    for cand in (octo(pts[i], pts[j]) if OCT else [[pts[j]]]):
                        if path_ok(pts[i], cand):
                            got = cand
                            break
                    if got or j == i + 1:
                        break
                    j -= 1
                out += got if got else [pts[j]]
                i = j
            for a, b in zip(out, out[1:]):
                if key(a) != key(b):
                    new_tracks.append({"t": "t", "l": l, "a": tuple(a), "b": tuple(b), "w": width})
        cand = new_tracks + [x for x in rs if x["t"] == "v"]
        if len(P.islands(n, cand)) > len(P.islands(n, rs)):     # never trade connectivity for looks: keep the router's copper
            reverted.append(net)
            cand = rs
        P.routes[n] = cand
        P.occupy(n, P.routes[n], +1)
    after = sum(1 for rs in P.routes.values() for x in rs if x["t"] == "t")
    pf.save(P, pf.OUT)
    print(f"tidy: track segments {before} -> {after}; kept as routed (tidy would split them): {reverted or 'none'}")


if __name__ == "__main__":
    main()
