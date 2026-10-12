#!/usr/bin/python3.13
"""Grid maze router that finishes the connections Freerouting leaves open (host python with numpy/scipy).

  kc 'python3 gen/rexport.py'          # board -> kicad/route_geom.json (copper, keepouts, DRC unconnected pairs)
  python3 gen/mazeroute.py              # -> kicad/route_add.json (new tracks + vias)
  kc 'python3 gen/rapply.py'            # adds them to the board (separate interpreters per item type)

Grid 0.05 mm, 4 layers, 8-connected moves plus through vias (0.6/0.3). For every connection the obstacle map is the Euclidean
distance to copper of other nets (pads, tracks, vias, PTH/NPTH holes) per layer: the centre line must stay
>= width/2 + clearance + 0.03 mm (grid safety) away from it; via centres >= 0.3 + clearance + 0.03 mm on every layer.
Board edge (0.3 mm), mounting-hole keepouts and the inductor keepouts are forbidden. In1 (GND plane) carries a high cost so it is
only used when nothing else works; In2 a small one. Each new route is added to the map before the next one.
"""
import heapq
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.dirname(os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb")).replace("/work/", ROOT + "/"))
GEOM = os.path.join(KDIR, "route_geom.json")
OUT = os.path.join(KDIR, "route_add.json")
RES = 0.05
N = int(round(36 / RES))
LAYERS = ["F", "In1", "In2", "B"]
LCOST = {"F": 1.0, "In1": 12.0, "In2": 1.3, "B": 1.0}
VIA_COST = 40.0           # grid steps (2 mm) per via
SAFE = 0.03
EDGE = 0.3
HOLES = [(2.75, 2.75), (33.25, 2.75), (2.75, 33.25), (33.25, 33.25)]
CLASS = {}  # net -> (width, clearance)
for n in ("VBAT", "5V", "10V", "SW_5V", "SW_10V", "VTX_PWR"):
    CLASS[n] = (0.45, 0.2)
for n in ("5V_SYS", "3V3", "3V3_IMU", "3V3A", "VBUS", "BUZ_N", "BST_5V", "BST_10V", "VCAP1", "VCAP2"):
    CLASS[n] = (0.3, 0.127)
for n in ("USB_DP", "USB_DM"):
    CLASS[n] = (0.2, 0.127)


def cls(net):
    return CLASS.get(net, (0.15, 0.127))


ys, xs = np.mgrid[0:N, 0:N]
CX, CY = (xs + 0.5) * RES, (ys + 0.5) * RES


def poly_mask(poly):
    p = np.array(poly)
    x0, y0 = p.min(0)
    x1, y1 = p.max(0)
    i0, i1 = max(0, int(y0 / RES) - 1), min(N, int(y1 / RES) + 2)
    j0, j1 = max(0, int(x0 / RES) - 1), min(N, int(x1 / RES) + 2)
    m = np.zeros((N, N), bool)
    if i0 >= i1 or j0 >= j1:
        return m
    px, py = CX[i0:i1, j0:j1], CY[i0:i1, j0:j1]
    inside = np.zeros(px.shape, bool)
    n = len(p)
    for k in range(n):
        xa, ya = p[k]
        xb, yb = p[(k + 1) % n]
        cond = (ya > py) != (yb > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xb - xa) * (py - ya) / (yb - ya) + xa
        inside ^= cond & (px < xint)
    m[i0:i1, j0:j1] = inside
    return m


def seg_mask(a, b, r):
    x0, x1 = min(a[0], b[0]) - r, max(a[0], b[0]) + r
    y0, y1 = min(a[1], b[1]) - r, max(a[1], b[1]) + r
    i0, i1 = max(0, int(y0 / RES) - 1), min(N, int(y1 / RES) + 2)
    j0, j1 = max(0, int(x0 / RES) - 1), min(N, int(x1 / RES) + 2)
    m = np.zeros((N, N), bool)
    if i0 >= i1 or j0 >= j1:
        return m
    px, py = CX[i0:i1, j0:j1], CY[i0:i1, j0:j1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = np.zeros(px.shape) if L == 0 else np.clip(((px - a[0]) * dx + (py - a[1]) * dy) / L, 0, 1)
    d = np.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))
    m[i0:i1, j0:j1] = d <= r
    return m


class Board:
    def __init__(self, g):
        self.nets = {"": 0}
        self.occ = {l: np.zeros((N, N), np.int32) for l in LAYERS}
        self.hole = np.zeros((N, N), bool)          # NPTH / PTH drill: obstacle on every layer for every net
        self.ftrace = {l: np.zeros((N, N), bool) for l in LAYERS}
        self.fvia = np.zeros((N, N), bool)
        self.pads = g["pads"]
        for p in g["pads"]:
            nid = self.nid(p["net"]) if p["net"] else -1
            m = np.zeros((N, N), bool)
            for poly in p["polys"]:
                m |= poly_mask(poly)
            lays = p["layers"] if not p["hole"] else LAYERS
            for l in lays:
                self.occ[l][m & (self.occ[l] == 0)] = nid
            if p["hole"]:
                self.hole |= seg_mask((p["x"], p["y"]), (p["x"], p["y"]), p["hole"])
        for t in g["tracks"]:
            if t["layer"] in self.occ:
                self.add_seg(t["layer"], t["a"], t["b"], t["w"], t["net"])
        for v in g["vias"]:
            self.add_via(v["x"], v["y"], v["net"], v["d"])
        # board edge (rounded 2 mm corners) and keepouts
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

    def nid(self, net):
        if net not in self.nets:
            self.nets[net] = len(self.nets)
        return self.nets[net]

    def add_seg(self, layer, a, b, w, net):
        m = seg_mask(a, b, w / 2)
        self.occ[layer][m] = self.nid(net)

    def add_via(self, x, y, net, d=0.6):
        m = seg_mask((x, y), (x, y), d / 2)
        for l in LAYERS:
            self.occ[l][m] = self.nid(net)
        self.hole |= seg_mask((x, y), (x, y), 0.15)


def item_cells(b, it, net):
    """Grid cells (layer, i, j) of an unconnected item (pad / track end / via)."""
    desc = it["desc"]
    out = []
    if desc.startswith("Pad "):
        num = desc.split()[1]
        ref = desc.split(" of ")[1].split()[0]
        for p in b.pads:
            if p["ref"] == ref and p["num"] == num and p["net"] == net:
                m = np.zeros((N, N), bool)
                for poly in p["polys"]:
                    m |= poly_mask(poly)
                ii, jj = np.nonzero(m)
                lays = p["layers"] if not p["hole"] else LAYERS
                for l in lays:
                    out += [(l, i, j) for i, j in zip(ii, jj)]
                if not len(ii):
                    out += [(l, int(p["y"] / RES), int(p["x"] / RES)) for l in lays]
                return out
    i, j = int(it["y"] / RES), int(it["x"] / RES)
    if desc.startswith("Via"):
        return [(l, i, j) for l in LAYERS]
    lay = "F" if "F.Cu" in desc else "B" if "B.Cu" in desc else "In2" if "In2" in desc else "In1"
    return [(lay, i, j)]


def route(b, net, src, dst, window=7.0):
    w, c = cls(net)
    n = b.nets.get(net, b.nid(net))
    pts = [(i, j) for _, i, j in src + dst]
    i0 = max(0, min(p[0] for p in pts) - int(window / RES)); i1 = min(N, max(p[0] for p in pts) + int(window / RES))
    j0 = max(0, min(p[1] for p in pts) - int(window / RES)); j1 = min(N, max(p[1] for p in pts) + int(window / RES))
    sl = (slice(i0, i1), slice(j0, j1))
    free, vok = {}, np.ones((i1 - i0, j1 - j0), bool)
    for l in LAYERS:
        other = ((b.occ[l][sl] != 0) & (b.occ[l][sl] != n)) | b.hole[sl]
        dist = ndimage.distance_transform_edt(~other) * RES
        free[l] = (dist >= w / 2 + c + SAFE) & (b.edge_dist[sl] >= w / 2) & ~b.ftrace[l][sl]
        vok &= (dist >= 0.3 + c + SAFE)
    vok &= (b.edge_dist[sl] >= 0.3) & ~b.fvia[sl]
    for hx, hy in HOLES:
        hole_m = np.hypot(CX[sl] - hx, CY[sl] - hy) < 2.3 + 0.3
        vok &= ~hole_m
        for l in LAYERS:
            free[l] &= ~(np.hypot(CX[sl] - hx, CY[sl] - hy) < 2.3 + w / 2)
    goal = {(l, i - i0, j - j0) for l, i, j in dst}
    gi = np.mean([g[1] for g in goal]); gj = np.mean([g[2] for g in goal])
    LI = {l: k for k, l in enumerate(LAYERS)}
    H, Wd = i1 - i0, j1 - j0
    g = np.full((4, H, Wd), np.inf)
    prev = {}
    pq = []
    for l, i, j in src:
        ii, jj = i - i0, j - j0
        if 0 <= ii < H and 0 <= jj < Wd:
            g[LI[l], ii, jj] = 0
            heapq.heappush(pq, (math.hypot(ii - gi, jj - gj), 0.0, l, ii, jj))
    moves = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    end = None
    expanded = 0
    while pq:
        f, gc, l, i, j = heapq.heappop(pq)
        if gc > g[LI[l], i, j]:
            continue
        if (l, i, j) in goal:
            end = (l, i, j)
            break
        expanded += 1
        if expanded > 1_500_000:
            break
        insrc = gc == 0
        for di, dj, cst in moves:
            ni, nj = i + di, j + dj
            if not (0 <= ni < H and 0 <= nj < Wd):
                continue
            if not free[l][ni, nj] and (l, ni, nj) not in goal:
                if not (insrc and b.occ[l][ni + i0, nj + j0] == n):
                    continue
            ng = gc + cst * LCOST[l]
            if ng < g[LI[l], ni, nj]:
                g[LI[l], ni, nj] = ng
                prev[(l, ni, nj)] = (l, i, j)
                heapq.heappush(pq, (ng + math.hypot(ni - gi, nj - gj), ng, l, ni, nj))
        if vok[i, j]:
            for l2 in LAYERS:
                if l2 == l:
                    continue
                if not free[l2][i, j] and (l2, i, j) not in goal:
                    continue
                ng = gc + VIA_COST
                if ng < g[LI[l2], i, j]:
                    g[LI[l2], i, j] = ng
                    prev[(l2, i, j)] = (l, i, j)
                    heapq.heappush(pq, (ng + math.hypot(i - gi, j - gj), ng, l2, i, j))
    if end is None:
        return None
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    pts = [(l, (j + j0 + 0.5) * RES, (i + i0 + 0.5) * RES) for l, i, j in path]
    tracks, vias = [], []
    run = [pts[0]]
    for p in pts[1:]:
        if p[0] != run[-1][0]:
            tracks += simplify(run, w, net)
            vias.append((p[1], p[2], net))
            run = [p]
        else:
            run.append(p)
    tracks += simplify(run, w, net)
    return tracks, vias


def simplify(run, w, net):
    if len(run) < 2:
        return []
    out = []
    a = run[0]
    d0 = None
    for k in range(1, len(run)):
        d = (round((run[k][1] - run[k - 1][1]) / RES), round((run[k][2] - run[k - 1][2]) / RES))
        if d0 is not None and d != d0:
            out.append((run[0][0], (a[1], a[2]), (run[k - 1][1], run[k - 1][2]), w, net))
            a = run[k - 1]
        d0 = d
    out.append((run[0][0], (a[1], a[2]), (run[-1][1], run[-1][2]), w, net))
    return out


def main():
    g = json.load(open(GEOM))
    b = Board(g)
    add_t, add_v, failed = [], [], []
    pairs = g["unconnected"]
    pairs.sort(key=lambda p: math.hypot(p[0]["x"] - p[1]["x"], p[0]["y"] - p[1]["y"]))
    only = sys.argv[1:]
    for pr in pairs:
        net = pr[0]["net"] or pr[1]["net"]
        if only and net not in only:
            continue
        src, dst = item_cells(b, pr[0], net), item_cells(b, pr[1], net)
        res = None
        for win in (4.0, 9.0, 40.0):
            res = route(b, net, src, dst, win)
            if res:
                break
        if not res:
            failed.append(f"{net}: {pr[0]['desc'][:40]} -> {pr[1]['desc'][:40]}")
            continue
        tr, vi = res
        for l, a, bb, w, nn in tr:
            b.add_seg(l, a, bb, w, nn)
        for x, y, nn in vi:
            b.add_via(x, y, nn)
        add_t += [{"layer": l, "a": a, "b": bb, "w": w, "net": nn} for l, a, bb, w, nn in tr]
        add_v += [{"x": x, "y": y, "net": nn} for x, y, nn in vi]
        print(f"routed {net}: {len(tr)} segs, {len(vi)} vias", flush=True)
    json.dump({"tracks": add_t, "vias": add_v}, open(OUT, "w"))
    print(f"mazeroute: {len(pairs) - len(failed)} routed, {len(failed)} failed")
    for f in failed:
        print("  FAILED", f)


if __name__ == "__main__":
    main()
