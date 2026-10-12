#!/usr/bin/python3.13
"""Rip-up-and-reroute finisher (host python 3.13 with numpy/scipy) for the board Freerouting leaves incomplete.

  kc 'python3 gen/rexport.py'      # board -> <kicad dir>/route_geom.json
  /usr/bin/python3.13 gen/ripup.py   # -> <kicad dir>/route_all.json: the COMPLETE list of unlocked tracks/vias
  (gen/route_finish.py rebuilds the board fresh: build_pcb, critical routes, then these tracks/vias, pours, fill)

Model: 0.05 mm grid, 4 layers. "base" copper = pads, PTH holes and locked items (critical routes): never moved.
"routed" copper = Freerouting's and this router's tracks/vias, kept as per-net records. A connection between two copper islands
of a net is searched with A*: other-net base copper is a hard obstacle, other-net routed copper is a soft one (penalty grows with
how often that net was ripped). The records that conflict with the found path are ripped, the path is committed, and the ripped
nets go back on the queue. GND is complete when every island touches a GND via/PTH (In1 is a solid GND plane).
Clearances: centre line >= width/2 + netclass clearance + 0.03 mm from other-net copper; via centres >= 0.3 + clearance + 0.03.
"""
import collections
import heapq
import json
import math
import os
import sys
import time

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mazeroute import (CX, CY, EDGE, HOLES, LAYERS, N, RES, SAFE, cls, poly_mask, seg_mask)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.dirname(os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb")).replace("/work/", ROOT + "/"))
GEOM = os.path.join(KDIR, "route_geom.json")
OUT = os.path.join(KDIR, "route_all.json")
LCOST = {"F": 1.0, "In1": float(os.environ.get("IN1_COST", "1e9")), "In2": 1.2, "B": 1.0}   # In1 = GND plane
VIA_COST = 30.0
LI = {l: k for k, l in enumerate(LAYERS)}
MOVES = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]


def seg_seg_dist(a, b, c, d):
    def pd(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
        return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)

    def inter(a, b, c, d):
        def cr(o, p, q):
            return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
        d1, d2, d3, d4 = cr(c, d, a), cr(c, d, b), cr(a, b, c), cr(a, b, d)
        return (d1 * d2 < 0) and (d3 * d4 < 0)
    if inter(a, b, c, d):
        return 0.0
    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))


class Router:
    def __init__(self, g):
        self.nets = {"": 0}
        self.netname = [""]
        self.base = {l: np.zeros((N, N), np.int32) for l in LAYERS}
        self.routed = {l: np.zeros((N, N), np.int32) for l in LAYERS}
        self.vbase = np.zeros((N, N), np.int32)      # layer-joining cells (PTH, locked vias)
        self.vrout = np.zeros((N, N), np.int32)      # routed vias
        self.hole = np.zeros((N, N), bool)
        self.ftrace = {l: np.zeros((N, N), bool) for l in LAYERS}
        self.fvia = np.zeros((N, N), bool)
        self.rec = collections.defaultdict(list)     # net -> routed records
        self.hist = collections.Counter()
        self.pres = 1.0          # present-congestion multiplier, grows with iterations (PathFinder style)
        self.pads = g["pads"]
        for p in g["pads"]:
            nid = self.nid(p["net"]) if p["net"] else -1
            m = np.zeros((N, N), bool)
            for poly in p["polys"]:
                m |= poly_mask(poly)
            lays = LAYERS if p["hole"] else p["layers"]
            for l in lays:
                self.base[l][m & (self.base[l] == 0)] = nid
            if p["hole"]:
                hm = seg_mask((p["x"], p["y"]), (p["x"], p["y"]), p["hole"])
                self.hole |= hm
                if nid > 0:
                    self.vbase[m] = nid
        for t in g["tracks"]:
            if t["layer"] not in LAYERS:
                continue
            if t["locked"]:
                self.base[t["layer"]][seg_mask(t["a"], t["b"], t["w"] / 2)] = self.nid(t["net"])
            else:
                self.add(t["net"], {"t": "t", "l": t["layer"], "a": tuple(t["a"]), "b": tuple(t["b"]), "w": t["w"]})
        for v in g["vias"]:
            if v["locked"]:
                m = seg_mask((v["x"], v["y"]), (v["x"], v["y"]), v["d"] / 2)
                for l in LAYERS:
                    self.base[l][m] = self.nid(v["net"])
                self.vbase[m] = self.nid(v["net"])
                self.hole |= seg_mask((v["x"], v["y"]), (v["x"], v["y"]), 0.15)
            else:
                self.add(v["net"], {"t": "v", "x": v["x"], "y": v["y"]})
        inside = (CX > EDGE) & (CY > EDGE) & (CX < 36 - EDGE) & (CY < 36 - EDGE)
        for cx, cy in ((2, 2), (34, 2), (2, 34), (34, 34)):
            corner = ((CX < 2) if cx == 2 else (CX > 34)) & ((CY < 2) if cy == 2 else (CY > 34))
            inside &= ~(corner & (np.hypot(CX - cx, CY - cy) > 2 - EDGE))
        self.edge_dist = ndimage.distance_transform_edt(inside) * RES
        for k in g["keepouts"]:
            m = np.zeros((N, N), bool)
            for poly in k["polys"]:
                m |= poly_mask(poly)
            for l in k["layers"]:
                if k["tracks"]:
                    self.ftrace[l] |= m
            if k["vias"]:
                self.fvia |= m
        for hx, hy in HOLES:
            hm = np.hypot(CX - hx, CY - hy)
            self.fvia |= hm < 2.3 + 0.3
            for l in LAYERS:
                self.ftrace[l] |= hm < 2.3

    def nid(self, net):
        if net not in self.nets:
            self.nets[net] = len(self.nets)
            self.netname.append(net)
        return self.nets[net]

    # ---- routed copper bookkeeping ----
    def draw(self, n, r):
        if r["t"] == "t":
            m = seg_mask(r["a"], r["b"], r["w"] / 2)
            self.routed[r["l"]][m & (self.routed[r["l"]] == 0)] = n
        else:
            m = seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3)
            for l in LAYERS:
                self.routed[l][m & (self.routed[l] == 0)] = n
            self.vrout[m] = n

    def add(self, net, r):
        n = self.nid(net)
        self.rec[n].append(r)
        self.draw(n, r)

    def redraw(self, n):
        for l in LAYERS:
            self.routed[l][self.routed[l] == n] = 0
        self.vrout[self.vrout == n] = 0
        for r in self.rec[n]:
            self.draw(n, r)

    # ---- connectivity ----
    def islands(self, n):
        """Connected copper islands of net n: list of (mask per layer dict). Layers join only through via/PTH cells."""
        labels, offs, tot = {}, {}, 0
        for l in LAYERS:
            m = (self.base[l] == n) | (self.routed[l] == n)
            lab, k = ndimage.label(m, structure=np.ones((3, 3)))
            labels[l], offs[l] = lab, tot
            tot += k
        parent = list(range(tot))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        vm = (self.vbase == n) | (self.vrout == n)
        if vm.any():
            vlab, vk = ndimage.label(vm)
            for vi in range(1, vk + 1):
                cells = vlab == vi
                ids = [offs[l] + int(labels[l][cells].max()) - 1 for l in LAYERS if labels[l][cells].max() > 0]
                for a in ids[1:]:
                    parent[find(a)] = find(ids[0])
        groups = collections.defaultdict(list)
        for l in LAYERS:
            for k in range(1, int(labels[l].max()) + 1):
                groups[find(offs[l] + k - 1)].append((l, k))
        out = []
        for gid, members in groups.items():
            masks = {l: np.zeros((N, N), bool) for l in LAYERS}
            for l, k in members:
                masks[l] |= labels[l] == k
            # GND: an island that contains a GND via/PTH cell is tied to the solid In1 plane
            plane = self.netname[n] == "GND" and any(bool((masks[l] & vm).any()) for l in LAYERS)
            out.append((masks, plane))
        return out

    # ---- search ----
    def search(self, n, src, dst_mask, window, gnd_plane=False, soft=True):
        w, c = cls(self.netname[n])
        req, vreq = w / 2 + c + SAFE, 0.3 + c + SAFE
        pts = np.argwhere(np.any([src[l] for l in LAYERS], axis=0))
        if dst_mask is not None:
            pts = np.vstack([pts, np.argwhere(np.any([dst_mask[l] for l in LAYERS], axis=0))])
        i0, j0 = max(0, pts[:, 0].min() - int(window / RES)), max(0, pts[:, 1].min() - int(window / RES))
        i1, j1 = min(N, pts[:, 0].max() + int(window / RES)), min(N, pts[:, 1].max() + int(window / RES))
        sl = (slice(i0, i1), slice(j0, j1))
        H, W = i1 - i0, j1 - j0
        hard, pen, vhard, vpen = {}, {}, np.zeros((H, W), bool), np.zeros((H, W))
        for l in LAYERS:
            ob = ((self.base[l][sl] != 0) & (self.base[l][sl] != n)) | self.hole[sl]
            db = ndimage.distance_transform_edt(~ob) * RES
            orr = (self.routed[l][sl] != 0) & (self.routed[l][sl] != n)
            dr, idx = ndimage.distance_transform_edt(~orr, return_indices=True)
            dr = dr * RES
            hard[l] = (db < req) | (self.edge_dist[sl] < w / 2 + 0.02) | self.ftrace[l][sl]
            vhard |= db < vreq
            if soft:
                blk = self.routed[l][sl][idx[0], idx[1]]
                hcost = np.array([0] + [(60 + 60 * self.hist[k]) * self.pres for k in range(1, len(self.netname))], float)
                p = np.where(dr < req, hcost[np.clip(blk, 0, len(hcost) - 1)], 0.0)
                pen[l] = p
                vpen += np.where(dr < vreq, hcost[np.clip(blk, 0, len(hcost) - 1)], 0.0)
            else:
                hard[l] |= dr < req
                vhard |= dr < vreq
                pen[l] = np.zeros((H, W))
        vhard |= (self.edge_dist[sl] < 0.3 + 0.02) | self.fvia[sl]
        goal = np.zeros((4, H, W), bool)
        if dst_mask is not None:
            for l in LAYERS:
                goal[LI[l]] = dst_mask[l][sl]
        if not goal.any() and not gnd_plane:
            return None
        gpts = np.argwhere(goal.any(0)) if goal.any() else np.argwhere(np.any([src[l][sl] for l in LAYERS], axis=0))
        gi, gj = gpts[:, 0].mean(), gpts[:, 1].mean()
        g = np.full((4, H, W), np.inf)
        prev = {}
        pq = []
        srcm = np.stack([src[l][sl] for l in LAYERS])
        for k, i, j in np.argwhere(srcm):
            g[k, i, j] = 0.0
            heapq.heappush(pq, (0.0, 0.0, int(k), int(i), int(j)))
        end, exp = None, 0
        while pq:
            f, gc, k, i, j = heapq.heappop(pq)
            if gc > g[k, i, j]:
                continue
            if goal[k, i, j] or (gnd_plane and k == LI["In1"]):
                end = (k, i, j)
                break
            exp += 1
            if exp > 2_000_000:
                break
            l = LAYERS[k]
            ins = srcm[k, i, j]
            for di, dj, cst in MOVES:
                ni, nj = i + di, j + dj
                if not (0 <= ni < H and 0 <= nj < W):
                    continue
                if not goal[k, ni, nj]:
                    if hard[l][ni, nj] and not (ins and srcm[k, ni, nj]):
                        continue
                ng = gc + cst * LCOST[l] + pen[l][ni, nj]
                if ng < g[k, ni, nj]:
                    g[k, ni, nj] = ng
                    prev[(k, ni, nj)] = (k, i, j)
                    heapq.heappush(pq, (ng + 0.9 * math.hypot(ni - gi, nj - gj), ng, k, ni, nj))
            if not vhard[i, j]:
                for k2 in range(4):
                    if k2 == k:
                        continue
                    l2 = LAYERS[k2]
                    if l2 == "In1" and not gnd_plane and LCOST["In1"] > 1e6:
                        continue
                    if hard[l2][i, j] and not goal[k2, i, j]:
                        continue
                    ng = gc + VIA_COST + vpen[i, j]
                    if ng < g[k2, i, j]:
                        g[k2, i, j] = ng
                        prev[(k2, i, j)] = (k, i, j)
                        heapq.heappush(pq, (ng + 0.9 * math.hypot(i - gi, j - gj), ng, k2, i, j))
        if end is None:
            return None
        path = [end]
        while path[-1] in prev:
            path.append(prev[path[-1]])
        path.reverse()
        return [(LAYERS[k], (j + j0 + 0.5) * RES, (i + i0 + 0.5) * RES) for k, i, j in path], w

    def commit(self, n, path, w):
        recs = []
        run = [path[0]]
        for p in path[1:]:
            if p[0] != run[-1][0]:
                recs += segs(run, w)
                recs.append({"t": "v", "x": p[1], "y": p[2]})
                run = [p]
            else:
                run.append(p)
        recs += segs(run, w)
        if self.netname[n] == "GND":
            recs = [r for r in recs if not (r["t"] == "t" and r["l"] == "In1")]
        # rip conflicting routed records of other nets
        c = cls(self.netname[n])[1]
        ripped = set()
        for m in list(self.rec):
            if m == n or not self.rec[m]:
                continue
            wm, cm = cls(self.netname[m])
            keep = []
            for r in self.rec[m]:
                hit = False
                for q in recs:
                    need = max(c, cm) + 0.01
                    if r["t"] == "t" and q["t"] == "t":
                        hit = r["l"] == q["l"] and seg_seg_dist(r["a"], r["b"], q["a"], q["b"]) < r["w"] / 2 + q["w"] / 2 + need
                    elif r["t"] == "t":
                        hit = seg_seg_dist(r["a"], r["b"], (q["x"], q["y"]), (q["x"], q["y"])) < r["w"] / 2 + 0.3 + need
                    elif q["t"] == "t":
                        hit = seg_seg_dist(q["a"], q["b"], (r["x"], r["y"]), (r["x"], r["y"])) < q["w"] / 2 + 0.3 + need
                    else:
                        hit = math.hypot(r["x"] - q["x"], r["y"] - q["y"]) < 0.6 + need
                    if hit:
                        break
                if hit:
                    ripped.add(m)
                else:
                    keep.append(r)
            if len(keep) != len(self.rec[m]):
                self.rec[m] = keep
                self.redraw(m)
        for r in recs:
            self.rec[n].append(r)
            self.draw(n, r)
        return ripped


def segs(run, w):
    if len(run) < 2:
        return []
    out, a, d0 = [], run[0], None
    for k in range(1, len(run)):
        d = (round((run[k][1] - run[k - 1][1]) / RES), round((run[k][2] - run[k - 1][2]) / RES))
        if d0 is not None and d != d0:
            out.append({"t": "t", "l": run[0][0], "a": (a[1], a[2]), "b": (run[k - 1][1], run[k - 1][2]), "w": w})
            a = run[k - 1]
        d0 = d
    out.append({"t": "t", "l": run[0][0], "a": (a[1], a[2]), "b": (run[-1][1], run[-1][2]), "w": w})
    return out


def main():
    t0 = time.time()
    g = json.load(open(GEOM))
    R = Router(g)
    nets = sorted({p["net"] for p in g["pads"] if p["net"] and not p["net"].startswith("unconnected-")})
    queue = collections.deque(nets)
    queued = set(nets)
    iters, failed = 0, collections.Counter()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    while queue and iters < limit:
        net = queue.popleft()
        queued.discard(net)
        n = R.nid(net)
        isl = R.islands(n)
        if net == "GND":
            todo = [m for m, plane in isl if not plane]
            if not todo:
                continue
            src = todo[0]
            res = R.search(n, src, None, 3.0, gnd_plane=True)
        else:
            if len(isl) <= 1:
                continue
            # nearest pair of islands: route from the smallest island to the union of the others
            isl.sort(key=lambda m: sum(int(m[0][l].sum()) for l in LAYERS))
            src = isl[0][0]
            dst = {l: np.any([m[0][l] for m in isl[1:]], axis=0) for l in LAYERS}
            res = None
            for win in (10.0, 40.0):   # wide first: a clean detour must beat ripping a neighbour
                res = R.search(n, src, dst, win)
                if res:
                    break
        iters += 1
        R.pres = min(1e4, 1.25 ** (iters / 100.0))
        if iters % 250 == 0:
            print(f"--- iter {iters}: queue {len(queue)}", flush=True)
        if not res:
            failed[net] += 1
            print(f"[{iters}] FAIL {net}", flush=True)
            if failed[net] < 3:
                queue.append(net)
                queued.add(net)
            continue
        path, w = res
        ripped = R.commit(n, path, w)
        for m in ripped:
            R.hist[m] += 1
            nm = R.netname[m]
            if nm not in queued:
                queue.append(nm)
                queued.add(nm)
        if net not in queued:
            queue.appendleft(net)
            queued.add(net)
        print(f"[{iters}] {net}: {len(path)} cells, ripped {[R.netname[m] for m in ripped]} ({time.time() - t0:.0f}s)", flush=True)
    left = []
    for net in nets:
        n = R.nid(net)
        isl = R.islands(n)
        bad = len([1 for m, p in isl if not p]) if net == "GND" else len(isl) - 1
        if bad > 0:
            left.append(f"{net}:{bad}")
    out = {"tracks": [], "vias": []}
    for n, rs in R.rec.items():
        for r in rs:
            if r["t"] == "t":
                out["tracks"].append({"layer": r["l"], "a": r["a"], "b": r["b"], "w": r["w"], "net": R.netname[n]})
            else:
                out["vias"].append({"x": r["x"], "y": r["y"], "net": R.netname[n]})
    json.dump(out, open(OUT, "w"))
    print(f"ripup: {iters} iterations, {time.time() - t0:.0f}s; incomplete: {' '.join(left) or 'none'} -> {OUT}")


if __name__ == "__main__":
    main()
