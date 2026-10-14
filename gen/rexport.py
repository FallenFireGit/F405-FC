"""Export board copper + unconnected pairs for the host-side maze router (gen/mazeroute.py).

  kc 'python3 gen/rexport.py'  ->  kicad/route_geom.json  (board mm, origin = board top-left corner)
"""
import json
import os
import subprocess

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
OUT = os.path.join(os.path.dirname(PCB), "route_geom.json")
OX = OY = 100.0
LAYERS = {pcbnew.F_Cu: "F", pcbnew.In1_Cu: "In1", pcbnew.In2_Cu: "In2", pcbnew.In3_Cu: "In3", pcbnew.In4_Cu: "In4",
          pcbnew.B_Cu: "B"}


def mm(v):
    return pcbnew.ToMM(v)


def poly_pts(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out.append([[mm(o.CPoint(k).x) - OX, mm(o.CPoint(k).y) - OY] for k in range(o.PointCount())])
    return out


def main():
    board = pcbnew.LoadBoard(PCB)
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            lays = [n for l, n in LAYERS.items() if p.IsOnLayer(l)]
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            if not lays and not npth:
                continue
            # NPTH holes (USB-C pegs) have no copper but still need the hole clearance in the router
            lid = next(l for l, n in LAYERS.items() if n == lays[0]) if lays else pcbnew.F_Cu
            ps = p.GetEffectivePolygon(lid, pcbnew.ERROR_OUTSIDE)
            q = p.GetPosition()
            hole = None
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                hole = mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2
            pads.append({"ref": fp.GetReference(), "num": p.GetNumber(), "net": p.GetNetname(), "layers": lays,
                         "x": mm(q.x) - OX, "y": mm(q.y) - OY, "polys": poly_pts(ps), "hole": hole})
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            vias.append({"net": t.GetNetname(), "x": mm(q.x) - OX, "y": mm(q.y) - OY, "d": mm(t.GetWidth(pcbnew.F_Cu)),
                         "drill": mm(t.GetDrillValue()), "locked": t.IsLocked()})
        elif t.GetClass() == "PCB_TRACK":
            a, b = t.GetStart(), t.GetEnd()
            tracks.append({"net": t.GetNetname(), "layer": LAYERS.get(t.GetLayer(), "?"), "w": mm(t.GetWidth()),
                           "a": [mm(a.x) - OX, mm(a.y) - OY], "b": [mm(b.x) - OX, mm(b.y) - OY], "locked": t.IsLocked()})
    keepouts, planes = [], []
    for z in board.Zones():
        if z.GetIsRuleArea():
            keepouts.append({"name": z.GetZoneName(), "layers": [n for l, n in LAYERS.items() if z.IsOnLayer(l)],
                             "tracks": z.GetDoNotAllowTracks(), "vias": z.GetDoNotAllowVias(),
                             "polys": poly_pts(z.Outline())})
        else:
            planes.append({"name": z.GetZoneName(), "net": z.GetNetname(),
                           "layers": [n for l, n in LAYERS.items() if z.IsOnLayer(l)], "polys": poly_pts(z.Outline())})
    drc = "/tmp/rexport_drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format", "json", "-o", drc, PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(drc))
    unconn = []
    for v in d.get("unconnected_items", []):
        items = []
        for i in v["items"]:
            desc = i["description"]
            net = desc.split("[")[1].split("]")[0] if "[" in desc else ""
            items.append({"desc": desc, "net": net, "x": i["pos"]["x"] - OX, "y": i["pos"]["y"] - OY})
        unconn.append(items)
    viol = [{"type": v["type"], "items": [{"desc": i["description"], "x": i["pos"]["x"] - OX, "y": i["pos"]["y"] - OY}
                                          for i in v["items"]]} for v in d["violations"]]
    json.dump({"pads": pads, "tracks": tracks, "vias": vias, "keepouts": keepouts, "planes": planes,
               "unconnected": unconn, "violations": viol}, open(OUT, "w"))
    print(f"rexport: {len(pads)} pads, {len(tracks)} tracks, {len(vias)} vias, {len(unconn)} unconnected, "
          f"{len(viol)} violations -> {OUT}")


if __name__ == "__main__":
    main()
