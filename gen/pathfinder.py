#!/usr/bin/python3.13
"""PathFinder (negotiated-congestion) router for the F405-FC board (host python 3.13 + numpy/scipy).

  kc 'python3 gen/rexport.py'                  # pre-route board (critical routes, MCU fanout, zones) -> route_geom.json
  /usr/bin/python3.13 gen/pathfinder.py [iters] # -> <kicad dir>/route_all.json (every routed track/via)
  bash gen/route_finish.sh                      # rebuild the board with these routes, pour, fill, DRC

Model (0.05 mm grid, layers F / In2 / B; In1 is the solid GND plane and is never routed):
- Fixed copper (pads, PTH, locked critical routes and fanout, the VBAT In2 zone) is a hard obstacle for other nets with the
  exact clearance: centre line >= w/2 + c + SAFE, via centre >= 0.3 + c + SAFE (Euclidean distance transform).
- Routed copper is soft. Every routed net "occupies" the cells within (w/2 + c/2) of its centre lines (via: 0.3 + c/2). Two nets
  that occupy the same cell are closer than the clearance. A net pays present-congestion cost for every cell whose occupancy by
  other nets is within its own half-footprint, plus the history cost of the cell. After each pass the history of every overused
  cell grows and the present factor is raised; nets touching overused cells are ripped and rerouted. Done when nothing is overused.
- Each net is routed as a tree: its fixed islands are joined one at a time by A* from the tree to the nearest remaining island.
  GND is left to the In1 plane and the F/In2/B pours.
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
from mazeroute import CX, CY, EDGE, HOLES, N, RES, cls, poly_mask, seg_mask  # noqa: E402

SAFE = 0.7 * RES  # grid safety to fixed copper: an edge can sit up to RES/sqrt(2) beyond its last rasterized cell centre
HOLE_CLR = 0.19  # board rule min_hole_clearance
OCC_X = 0.3 * RES  # routed-to-routed rasterization margin per net


def occ_k(c):
    """Occupancy half-clearance so that k1 + k2 >= max(c1, c2) for every class pair (0.127 / 0.15 / 0.2)."""
    return (0.0635 if c <= 0.127 else c - 0.0635) + OCC_X



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.path.dirname(os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb")).replace("/work/", ROOT + "/"))
GEOM = os.path.join(KDIR, "route_geom.json")
OUT = os.path.join(KDIR, "route_all.json")
IN1 = os.environ.get("IN1", "0") == "1"      # last-resort hops on the In1 GND plane (high cost; the pour carves around them)
RL = ["F", "In1", "In2", "B"] if IN1 else ["F", "In2", "B"]   # routing layers
ALL = ["F", "In1", "In2", "B"]
LCOST = {"F": 1.0, "In1": float(os.environ.get("IN1_COST", "10")), "In2": 1.15, "B": 1.0}
VIA_COST = 25.0
MOVES = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
DISK = {}


def disk(r):
    k = int(math.ceil(r / RES))
    if k not in DISK:
        y, x = np.mgrid[-k:k + 1, -k:k + 1]
        DISK[k] = (x * x + y * y) <= k * k
    return DISK[k]


class PF:
    def __init__(self, g):
        self.nets = {"": 0}
        self.names = [""]
        self.base = {l: np.zeros((N, N), np.int32) for l in ALL}
        self.vbase = np.zeros((N, N), np.int32)
        self.hole = np.zeros((N, N), bool)
        self.ftrace = {l: np.zeros((N, N), bool) for l in ALL}
        self.fvia = np.zeros((N, N), bool)
        for p in g["pads"]:
            nid = self.nid(p["net"]) if p["net"] else -1
            m = np.zeros((N, N), bool)
            for poly in p["polys"]:
                m |= poly_mask(poly)
            for l in (ALL if p["hole"] else p["layers"]):
                self.base[l][m & (self.base[l] == 0)] = nid
            if p["hole"]:
                self.hole |= seg_mask((p["x"], p["y"]), (p["x"], p["y"]), p["hole"])
                if nid > 0:
                    self.vbase[m] = nid
        self.fixed_routes = []
        for t in g["tracks"]:
            if t["layer"] in ALL and t["locked"]:
                self.base[t["layer"]][seg_mask(t["a"], t["b"], t["w"] / 2)] = self.nid(t["net"])
        for v in g["vias"]:
            if v["locked"]:
                m = seg_mask((v["x"], v["y"]), (v["x"], v["y"]), v["d"] / 2)
                for l in ALL:
                    self.base[l][m] = self.nid(v["net"])
                self.vbase[m] = self.nid(v["net"])
                self.hole |= seg_mask((v["x"], v["y"]), (v["x"], v["y"]), 0.15)
        for z in g.get("planes", []):
            if z["net"] in ("", "GND") or "polys" not in z:
                continue
            m = np.zeros((N, N), bool)
            for poly in z["polys"]:
                m |= poly_mask(poly)
            for l in z["layers"]:
                self.base[l][m & (self.base[l] == 0)] = self.nid(z["net"])
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
            for l in ALL:
                self.ftrace[l] |= hm < 2.3
        self.hist = {l: np.zeros((N, N), np.float32) for l in RL}
        self.occ = {l: np.zeros((N, N), np.int16) for l in RL}     # number of routed nets occupying each cell
        self.own = {}                                               # net -> {layer: bool mask} occupancy
        self.routes = {}                                            # net -> list of records
        self.hard_cache = {}

    def class_ids(self):
        """clearance -> net ids having that clearance (pads without a net count as default)."""
        groups = collections.defaultdict(list)
        for name, i in self.nets.items():
            groups[cls(name)[1] if name else 0.127].append(i)
        groups[0.127].append(-1)
        return groups

    def nid(self, net):
        if net not in self.nets:
            self.nets[net] = len(self.nets)
            self.names.append(net)
        return self.nets[net]

    # ---- static obstacles per net (cached) ----
    def hard(self, n):
        if n in self.hard_cache:
            return self.hard_cache[n]
        w, c = cls(self.names[n])
        hard, vhard = {}, np.zeros((N, N), bool)
        # pairwise clearance = max(own class, other net's class); holes need the 0.19 mm hole clearance
        hole_d = ndimage.distance_transform_edt(~self.hole) * RES
        for l in ALL:
            other = (self.base[l] != 0) & (self.base[l] != n)
            hl = np.zeros((N, N), bool)
            vl = hole_d < 0.3 + HOLE_CLR + SAFE
            for co, ids in self.class_ids().items():
                ob = other & np.isin(self.base[l], ids)
                if not ob.any():
                    continue
                d = ndimage.distance_transform_edt(~ob) * RES
                cc = max(c, co)
                hl |= d < w / 2 + cc + SAFE
                vl |= d < 0.3 + cc + SAFE
            if l in RL:
                ft = ndimage.binary_dilation(self.ftrace[l], structure=disk(w / 2 + 0.03)) if self.ftrace[l].any() else self.ftrace[l]
                hard[l] = hl | (hole_d < w / 2 + HOLE_CLR + SAFE) | (self.edge_dist < w / 2 + 0.02) | ft
            vhard |= vl
        vhard |= (self.edge_dist < 0.32) | ndimage.binary_dilation(self.fvia, structure=disk(0.33))   # whole via body outside keepouts
        self.hard_cache[n] = (hard, vhard)
        return hard, vhard

    # ---- occupancy ----
    def occupy(self, n, recs, sign):
        w, c = cls(self.names[n])
        masks = {l: np.zeros((N, N), bool) for l in RL}
        for r in recs:
            if r["t"] == "t":
                masks[r["l"]] |= seg_mask(r["a"], r["b"], r["w"] / 2 + occ_k(c))
            else:
                m = seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3 + occ_k(c))
                for l in RL:
                    masks[l] |= m
        for l in RL:
            self.occ[l][masks[l]] += sign
        return masks

    def islands(self, n, extra):
        """Fixed copper islands of net n plus its routed copper (extra: records)."""
        cu = {l: (self.base[l] == n) for l in ALL}
        vm = self.vbase == n
        for r in extra:
            if r["t"] == "t":
                cu[r["l"]] |= seg_mask(r["a"], r["b"], r["w"] / 2)
            else:
                m = seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3)
                for l in ALL:
                    cu[l] |= m
                vm = vm | m
        labels, offs, tot = {}, {}, 0
        for l in ALL:
            lab, k = ndimage.label(cu[l], structure=np.ones((3, 3)))
            labels[l], offs[l] = lab, tot
            tot += k
        parent = list(range(tot))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        if vm.any():
            vlab, vk = ndimage.label(vm)
            objs = ndimage.find_objects(vlab)
            for vi, sl in enumerate(objs, 1):
                cells = vlab[sl] == vi
                ids = []
                for l in ALL:
                    v = labels[l][sl][cells]
                    v = v[v > 0]
                    if v.size:
                        ids.append(offs[l] + int(v[0]) - 1)
                for a in ids[1:]:
                    parent[find(a)] = find(ids[0])
        groups = collections.defaultdict(list)
        for l in ALL:
            for k in range(1, int(labels[l].max()) + 1):
                groups[find(offs[l] + k - 1)].append((l, k))
        out = []
        for members in groups.values():
            m = {l: np.zeros((N, N), bool) for l in ALL}
            for l, k in members:
                m[l] |= labels[l] == k
            out.append(m)
        return out

    # ---- A* ----
    def astar(self, n, src, dst, pres, window, allow_via=True):
        w, c = cls(self.names[n])
        hard, vhard = self.hard(n)
        pts = np.argwhere(np.any([src[l] | dst[l] for l in ALL], axis=0))
        k = int(window / RES)
        i0, j0 = max(0, pts[:, 0].min() - k), max(0, pts[:, 1].min() - k)
        i1, j1 = min(N, pts[:, 0].max() + k + 1), min(N, pts[:, 1].max() + k + 1)
        sl = (slice(i0, i1), slice(j0, j1))
        H, W = i1 - i0, j1 - j0
        # present congestion: other nets' occupancy within my half footprint (w/2 + c/2)
        cost, vcost, nearm = {}, np.zeros((H, W), np.float32), {}
        hf = disk(w / 2 + occ_k(c))
        vf = disk(0.3 + occ_k(c))
        for l in RL:
            o = self.occ[l][sl] > 0
            near = ndimage.binary_dilation(o, structure=hf) if o.any() else o
            vnear = ndimage.binary_dilation(o, structure=vf) if o.any() else o
            cost[l] = (LCOST[l] + self.hist[l][sl]) * (1.0 + pres * near)
            nearm[l] = near
            vcost += (self.hist[l][sl] + pres * vnear * 3.0)
        hd = {l: hard[l][sl] for l in RL}
        vh = vhard[sl]
        goal = np.stack([dst[l][sl] for l in RL])
        srcm = np.stack([src[l][sl] for l in RL])
        # In1 copper of the source/destination (PTH pads, vias) is reachable on any layer through its drill
        for l in ("In1",):
            pass
        gpts = np.argwhere(goal.any(0))
        if not len(gpts):
            return None
        gi, gj = gpts[:, 0].mean(), gpts[:, 1].mean()
        g = np.full((len(RL), H, W), np.inf)            # float64: heap keys are python floats (float32 rounding dropped nodes)
        prev = {}
        pq = []
        for kk, i, j in np.argwhere(srcm):
            g[kk, i, j] = 0.0
            pq.append((0.0, 0.0, int(kk), int(i), int(j)))
        heapq.heapify(pq)
        end = None
        exp = 0
        while pq:
            f, gc, kk, i, j = heapq.heappop(pq)
            if gc > g[kk, i, j]:
                continue
            if goal[kk, i, j]:
                end = (kk, i, j)
                break
            exp += 1
            if exp > int(1_500_000 * (0.05 / RES) ** 2):
                break
            l = RL[kk]
            ins = srcm[kk, i, j]
            cl = cost[l]
            for di, dj, cst in MOVES:
                ni, nj = i + di, j + dj
                if ni < 0 or nj < 0 or ni >= H or nj >= W:
                    continue
                if hd[l][ni, nj] and not goal[kk, ni, nj] and not (ins and srcm[kk, ni, nj]):
                    continue
                ng = gc + cst * cl[ni, nj]
                if ng < g[kk, ni, nj]:
                    g[kk, ni, nj] = ng
                    prev[(kk, ni, nj)] = (kk, i, j)
                    heapq.heappush(pq, (ng + 0.95 * math.hypot(ni - gi, nj - gj), ng, kk, ni, nj))
            if allow_via and not vh[i, j]:
                for k2 in range(len(RL)):
                    if k2 == kk:
                        continue
                    if hd[RL[k2]][i, j] and not goal[k2, i, j]:
                        continue
                    ng = gc + VIA_COST + vcost[i, j]
                    if ng < g[k2, i, j]:
                        g[k2, i, j] = ng
                        prev[(k2, i, j)] = (kk, i, j)
                        heapq.heappush(pq, (ng + 0.95 * math.hypot(i - gi, j - gj), ng, k2, i, j))
        if end is None:
            return None
        self.last_cost = float(g[end])
        path = [end]
        while path[-1] in prev:
            path.append(prev[path[-1]])
        path.reverse()
        self.last_conflicts = sum(1 for kk, i, j in path if nearm[RL[kk]][i, j])
        self.last_end = ((path[-1][2] + j0 + 0.5) * RES, (path[-1][1] + i0 + 0.5) * RES)
        # split into same-layer runs, string-pull each run (straight segments where the line stays legal), emit records
        runs, cur = [], [path[0]]
        for p in path[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur)
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        recs = []
        for ri, run in enumerate(runs):
            kk = run[0][0]
            l = RL[kk]
            onpath = {(i, j) for _, i, j in run}
            ok = (~hd[l] & ~nearm[l]) | srcm[kk] | goal[kk]

            def clear(a, b):
                (ia, ja), (ib, jb) = a, b
                k = max(abs(ib - ia), abs(jb - ja)) * 2
                for t in range(k + 1):
                    ii = ia + (ib - ia) * t / max(k, 1)
                    jj = ja + (jb - ja) * t / max(k, 1)
                    for ci, cj in {(int(math.floor(ii)), int(math.floor(jj))), (int(math.ceil(ii)), int(math.ceil(jj)))}:
                        if not (ok[ci, cj] or (ci, cj) in onpath):
                            return False
                return True
            cells = [(i, j) for _, i, j in run]
            pulled = [cells[0]]
            a = 0
            while a < len(cells) - 1:
                b2 = len(cells) - 1
                while b2 > a + 1 and not clear(cells[a], cells[b2]):
                    b2 -= 1
                pulled.append(cells[b2])
                a = b2
            for (ia, ja), (ib, jb) in zip(pulled, pulled[1:]):
                recs.append({"t": "t", "l": l, "a": ((ja + j0 + 0.5) * RES, (ia + i0 + 0.5) * RES),
                             "b": ((jb + j0 + 0.5) * RES, (ib + i0 + 0.5) * RES), "w": w})
            if ri + 1 < len(runs):
                _, vi, vj = runs[ri + 1][0]
                recs.append({"t": "v", "x": (vj + j0 + 0.5) * RES, "y": (vi + i0 + 0.5) * RES})
        return recs

    def route_net(self, n, pres):
        """Route net n as a tree over its fixed islands. Returns records or None if some island is unreachable."""
        isl = self.islands(n, [])
        if len(isl) <= 1:
            return []
        recs = []
        tree = isl[0]
        rest = isl[1:]
        while rest:
            # nearest remaining island by centroid distance
            tc = np.argwhere(np.any([tree[l] for l in ALL], axis=0)).mean(0)
            rest.sort(key=lambda m: np.hypot(*(np.argwhere(np.any([m[l] for l in ALL], axis=0)).mean(0) - tc)))
            dst = rest[0]
            # In1 copper (PTH/via drills) counts on every routing layer at that spot
            src = {l: tree[l] | (tree["In1"] if l in RL and not IN1 else False) for l in ALL}
            dsm = {l: dst[l] | (dst["In1"] if l in RL and not IN1 else False) for l in ALL}
            r, best = None, None
            for win in (4.0, 12.0, 40.0):
                q = self.astar(n, src, dsm, pres, win)
                if q is None:
                    continue
                if best is None or self.last_cost < best:
                    r, best = q, self.last_cost
                if self.last_conflicts == 0:      # no present congestion on this path: wider windows cannot do better
                    break
            if r is None:
                return None
            recs += r
            add = {l: np.zeros((N, N), bool) for l in ALL}
            for q in r:
                if q["t"] == "t":
                    add[q["l"]] |= seg_mask(q["a"], q["b"], q["w"] / 2)
                else:
                    m = seg_mask((q["x"], q["y"]), (q["x"], q["y"]), 0.3)
                    for l in ALL:
                        add[l] |= m
            tree = {l: tree[l] | dst[l] | add[l] for l in ALL}
            rest = rest[1:]
            # an added path may touch other islands too: merge them
            merged = []
            for m in rest:
                if any((m[l] & tree[l]).any() for l in ALL):
                    tree = {l: tree[l] | m[l] for l in ALL}
                else:
                    merged.append(m)
            rest = merged
        return recs


def gnd_pass(P):
    """Tie every GND island that has no via/PTH to the In1 plane: shortest legal path on the island's own layer either to GND
    copper that is already tied (no new via), or to a via site that is not on a GND pad (no via-in-pad: hand assembly; vias are
    tented) and clears all routed copper of other nets on every layer. Returns the number of islands left."""
    n = P.nid("GND")
    P.routes.setdefault(n, [])
    left = 0
    for _round in range(3):          # islands tied in one round become targets for the next
        isl = P.islands(n, P.routes[n])
        vm = (P.vbase == n)
        for r in P.routes[n]:
            if r["t"] == "v":
                vm |= seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3)
        tied = {l: np.zeros((N, N), bool) for l in ALL}
        loose = []
        for m in isl:
            if any((m[l] & vm).any() for l in ALL):
                for l in ALL:
                    tied[l] |= m[l]
            else:
                loose.append(m)
        if not loose:
            break
        left = 0
        hard, vh = P.hard(n)
        gpads = np.any([(P.base[l] == n) for l in ("F", "B")], axis=0)
        # other nets' routed copper does not change during the GND pass: the via-site mask is computed once per round
        others = np.zeros((N, N), bool)
        for l in RL:
            others |= P.occ[l] > 0
        mine = np.zeros((N, N), bool)
        for l, mm_ in P.occupy(n, P.routes[n], 0).items():
            mine |= mm_
        others &= ~mine
        via_block = ndimage.binary_dilation(others, structure=disk(0.3 + occ_k(cls("GND")[1])))
        site0 = ~vh & ~via_block & ~ndimage.binary_dilation(gpads, structure=disk(0.35))
        for m in loose:
            own = np.any([m[l] for l in RL], axis=0)
            ys, xs = np.nonzero(own)
            near_pad = np.zeros((N, N), bool)
            k = int(math.ceil(0.4 / RES))
            sl = (slice(max(0, ys.min() - k), ys.max() + k + 1), slice(max(0, xs.min() - k), xs.max() + k + 1))
            near_pad[sl] = ndimage.binary_dilation(own[sl], structure=disk(0.35))
            site = site0 & ~near_pad
            dst = {l: (site | (tied[l] & ~m[l])) if l in RL and l != "In1" else np.zeros((N, N), bool) for l in ALL}
            src = {l: m[l] for l in ALL}
            r = None
            for win in (1.5, 3.0, 6.0):
                r = P.astar(n, src, dst, 1e6, win, allow_via=False)     # stay on the island's layer
                if r is not None and P.last_conflicts == 0:
                    break
                r = None
            if r is None:
                left += 1
                continue
            x, y = P.last_end
            i, j = min(N - 1, int(y / RES)), min(N - 1, int(x / RES))
            lay = r[-1]["l"] if r and r[-1]["t"] == "t" else None
            if not (lay and tied[lay][i, j]):
                r.append({"t": "v", "x": x, "y": y})
            P.routes[n] += r
            P.occupy(n, r, +1)
            for l in ALL:
                tied[l] |= m[l]
    return left


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


def save(P, path):
    out = {"tracks": [], "vias": []}
    for n, rs in P.routes.items():
        for r in rs:
            if r["t"] == "t":
                out["tracks"].append({"layer": r["l"], "a": r["a"], "b": r["b"], "w": r["w"], "net": P.names[n]})
            else:
                out["vias"].append({"x": r["x"], "y": r["y"], "net": P.names[n]})
    json.dump(out, open(path, "w"))


def main():
    t0 = time.time()
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    g = json.load(open(GEOM))
    P = PF(g)
    span = collections.defaultdict(list)
    for p in g["pads"]:
        span[p["net"]].append((p["x"], p["y"]))
    nets = [n for n in span if n and n != "GND" and not n.startswith("unconnected-")]
    nets.sort(key=lambda n: (max(x for x, y in span[n]) - min(x for x, y in span[n]) + max(y for x, y in span[n]) - min(y for x, y in span[n])))
    nid = {n: P.nid(n) for n in nets}
    pres, hist_inc = 0.5, 0.3
    todo = list(nets)
    if os.environ.get("RESUME") == "1" and os.path.exists(OUT):
        prev = json.load(open(OUT))
        for t in prev["tracks"]:
            P.routes.setdefault(P.nid(t["net"]), []).append({"t": "t", "l": t["layer"], "a": tuple(t["a"]), "b": tuple(t["b"]), "w": t["w"]})
        for v in prev["vias"]:
            P.routes.setdefault(P.nid(v["net"]), []).append({"t": "v", "x": v["x"], "y": v["y"]})
        for net in os.environ.get("RESET_NETS", "").split(","):     # drop these nets' routes (e.g. after a part was removed)
            if net and P.nets.get(net) in P.routes:
                P.routes[P.nets[net]] = []
        for n, rs in P.routes.items():
            P.occupy(n, rs, +1)
        pres = float(os.environ.get("PRES", "50"))
        over = {l: P.occ[l] > 1 for l in RL}
        for l in RL:
            P.hist[l][over[l]] += 3.0
        todo = [net for net in nets if any((over[r["l"]] & seg_mask(r["a"], r["b"], r["w"] / 2 + occ_k(cls(net)[1]))).any()
                                           if r["t"] == "t" else any((over[l] & seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3 + occ_k(cls(net)[1]))).any() for l in RL)
                                           for r in P.routes.get(nid[net], []))]
        # nets whose copper now violates a (re-computed) hard constraint, e.g. via bodies in the inductor keepouts
        for net in nets:
            n = nid[net]
            hard_, vh_ = P.hard(n)
            for r in P.routes.get(n, []):
                if r["t"] == "t":
                    m = seg_mask(r["a"], r["b"], 0.01)
                    bad_ = (hard_[r["l"]] & m).any() if r["l"] in hard_ else False
                else:
                    bad_ = bool(vh_[min(N - 1, int(r["y"] / RES)), min(N - 1, int(r["x"] / RES))])
                if bad_ and net not in todo:
                    todo.append(net)
                    break
        for net in os.environ.get("RESET_NETS", "").split(","):
            if net and net in nets and net not in todo:
                todo.append(net)
        print("resume: nets to reroute", len(todo), todo, flush=True)
    unroutable = set()
    for it in range(1, iters + 1):
        for net in todo:
            n = nid[net]
            if n in P.routes:
                P.occupy(n, P.routes[n], -1)
            r = P.route_net(n, pres)
            if r is None:
                unroutable.add(net)
                r = []
            else:
                unroutable.discard(net)
            P.routes[n] = r
            P.occupy(n, r, +1)
        over = {l: P.occ[l] > 1 for l in RL}
        n_over = int(sum(int(o.sum()) for o in over.values()))
        for l in RL:
            P.hist[l][over[l]] += hist_inc
        # nets touching overused cells are rerouted next pass
        bad = set()
        for net in nets:
            n = nid[net]
            rs = P.routes.get(n, [])
            if not rs:
                continue
            w, c = cls(net)
            for r in rs:
                if r["t"] == "t":
                    m = seg_mask(r["a"], r["b"], r["w"] / 2 + occ_k(c))
                    if (over[r["l"]] & m).any():
                        bad.add(net)
                        break
                else:
                    m = seg_mask((r["x"], r["y"]), (r["x"], r["y"]), 0.3 + occ_k(c))
                    if any((over[l] & m).any() for l in RL):
                        bad.add(net)
                        break
        print(f"pass {it}: overused cells {n_over}, nets in conflict {len(bad)}, unroutable {sorted(unroutable)}, "
              f"pres {pres:.2f} ({time.time() - t0:.0f}s)", flush=True)
        save(P, OUT)
        if n_over == 0 and not unroutable:
            print("pathfinder: converged")
            break
        todo = sorted(bad | unroutable, key=nets.index)
        pres *= 1.6
    if os.environ.get("GND", "1") == "1":
        left = gnd_pass(P)
        save(P, OUT)
        print(f"pathfinder: GND pass, {left} GND islands without a plane tie", flush=True)
    print(f"pathfinder: done in {time.time() - t0:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
