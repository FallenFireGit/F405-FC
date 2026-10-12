#!/usr/bin/python3.13
"""List the remaining PathFinder conflicts (pairs of nets closer than the clearance) with locations, from route_all.json."""
import collections
import json
import os
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathfinder as pf  # noqa: E402

d = json.load(open(pf.OUT))
occ = {l: collections.defaultdict(set) for l in pf.RL}
masks = {}
for t in d["tracks"]:
    w, c = pf.cls(t["net"])
    m = pf.seg_mask(t["a"], t["b"], t["w"] / 2 + c / 2)
    masks.setdefault((t["net"], t["layer"]), np.zeros((pf.N, pf.N), bool))
    masks[(t["net"], t["layer"])] |= m
for v in d["vias"]:
    w, c = pf.cls(v["net"])
    m = pf.seg_mask((v["x"], v["y"]), (v["x"], v["y"]), 0.3 + c / 2)
    for l in pf.RL:
        masks.setdefault((v["net"], l), np.zeros((pf.N, pf.N), bool))
        masks[(v["net"], l)] |= m
pairs = collections.Counter()
where = {}
for l in pf.RL:
    keys = [k for k in masks if k[1] == l]
    cnt = np.zeros((pf.N, pf.N), np.int16)
    for k in keys:
        cnt += masks[k]
    over = cnt > 1
    if not over.any():
        continue
    lab, nlab = ndimage.label(over)
    for i in range(1, nlab + 1):
        cells = lab == i
        nets = sorted({k[0] for k in keys if (masks[k] & cells).any()})
        yx = np.argwhere(cells).mean(0) * pf.RES
        pairs[(l, tuple(nets))] += int(cells.sum())
        where[(l, tuple(nets))] = (round(yx[1], 2), round(yx[0], 2))
for k, v in pairs.most_common():
    print(f"{k[0]:4} {' x '.join(k[1]):40} cells {v:4} at {where[k]}")
