"""List the GND pads whose filled pour fragment has no GND via or THT pad (run inside the KiCad chroot on the routed, filled
board): these are the pads DRC reports as unconnected GND zone islands. Output kicad/gnd_need.json = [[x, y, layer, fragment], ...] in
board mm (origin = board corner) for gen/pathfinder.py (env GND_NEED), which then ties one pad of each fragment to the In1 plane (the pour joins the rest).

  kc 'python3 gen/gndneed.py'
"""
import json
import os

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
OUT = os.path.join(os.path.dirname(PCB), "gnd_need.json")
OX = OY = 100.0
LN = {pcbnew.F_Cu: "F", pcbnew.In2_Cu: "In2", pcbnew.B_Cu: "B"}


def main():
    b = pcbnew.LoadBoard(PCB)
    g = b.FindNet("GND").GetNetCode()
    tied = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == g]
    pads = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetCode() == g]
    tied += [p.GetPosition() for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    need, names = [], []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != g:
            continue
        for l, ln in LN.items():
            if not z.IsOnLayer(l):
                continue
            f = z.GetFilledPolysList(l)
            for i in range(f.OutlineCount()):
                fr = pcbnew.SHAPE_POLY_SET()
                fr.AddOutline(f.Outline(i))
                if any(fr.Contains(v) for v in tied):
                    continue
                for p in pads:
                    if p.IsOnLayer(l) and fr.Contains(p.GetPosition()):
                        q = p.GetPosition()
                        need.append([pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY, ln, f"{ln}{i}"])
                        names.append(f"{p.GetParentFootprint().GetReference()}.{p.GetNumber()}")
    json.dump(need, open(OUT, "w"))
    print(f"gndneed: {len(need)} GND pads in untied pour fragments: {' '.join(names)}")


if __name__ == "__main__":
    main()
