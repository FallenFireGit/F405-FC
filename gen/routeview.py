#!/usr/bin/python3.13
"""Render a zoomed view of route_geom.json + route_all.json around (x, y): routeview.py x y [half_mm] out.png"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathfinder as pf  # noqa: E402

x0, y0 = float(sys.argv[1]), float(sys.argv[2])
hw = float(sys.argv[3]) if len(sys.argv) > 4 else 2.5
out = sys.argv[-1]
S = 900 / (2 * hw)
g = json.load(open(pf.GEOM))
r = json.load(open(pf.OUT))
img = Image.new("RGB", (900, 900), "white")
d = ImageDraw.Draw(img, "RGBA")
col = {"F": (220, 40, 40, 140), "In1": (40, 160, 40, 140), "In2": (200, 160, 0, 140), "B": (40, 80, 220, 140)}


def P(x, y):
    return ((x - x0 + hw) * S, (y - y0 + hw) * S)
for p in g["pads"]:
    for poly in p["polys"]:
        lay = "F" if "F" in p["layers"] else "B"
        d.polygon([P(*q) for q in poly], fill=col[lay][:3] + (60,), outline=col[lay][:3] + (255,))
    if abs(p["x"] - x0) < hw and abs(p["y"] - y0) < hw:
        d.text(P(p["x"], p["y"]), f'{p["ref"]}.{p["num"]}\n{p["net"][:10]}', fill=(0, 0, 0))
for src, alpha in ((g["tracks"], 255), (r["tracks"], 180)):
    for t in src:
        if t.get("locked", True) or src is r["tracks"]:
            c = col.get(t["layer"], (0, 0, 0, 255))
            d.line([P(*t["a"]), P(*t["b"])], fill=c[:3] + (alpha,), width=max(1, int(t["w"] * S)))
for src in (g["vias"], r["vias"]):
    for v in src:
        if src is r["vias"] or v.get("locked"):
            a, b = P(v["x"] - 0.3, v["y"] - 0.3), P(v["x"] + 0.3, v["y"] + 0.3)
            d.ellipse([a, b], outline=(0, 0, 0), width=2)
for t in r["tracks"]:
    mx, my = (t["a"][0] + t["b"][0]) / 2, (t["a"][1] + t["b"][1]) / 2
    if abs(mx - x0) < hw and abs(my - y0) < hw and ((t["a"][0] - t["b"][0]) ** 2 + (t["a"][1] - t["b"][1]) ** 2) > 0.3:
        d.text(P(mx, my), t["net"][:9], fill=(90, 0, 90))
img.save(out)
