"""Replay the pre-route fixed copper (critical routes, MCU fanout, GND fanout) from kicad/route_geom.json onto a freshly built
board, so the finished board has exactly the fixed copper the router routed around. gen/gndfan.py plans differ between runs (set
iteration order), so re-planning after routing put GND vias on top of routed signals (rev D). Run in the KiCad chroot after
gen/build_pcb.py --fresh, instead of gen/critical.py + the two pre-route gen/gndfan.py passes:

  kc 'python3 gen/geomreplay.py'
"""
import json
import os

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
GEOM = os.path.join(os.path.dirname(PCB), "route_geom.json")
OX = OY = 100.0
LAYERS = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu, "In3": pcbnew.In3_Cu, "In4": pcbnew.In4_Cu,
          "B": pcbnew.B_Cu}


def main():
    board = pcbnew.LoadBoard(PCB)
    if any(t.IsLocked() for t in board.GetTracks()):
        print("geomreplay: board already has locked copper; nothing done")
        return
    g = json.load(open(GEOM))

    def pt(p):
        return pcbnew.VECTOR2I(pcbnew.FromMM(OX + p[0]), pcbnew.FromMM(OY + p[1]))
    nt = nv = 0
    for t in g["tracks"]:
        if not t["locked"]:
            continue
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pt(t["a"])); tr.SetEnd(pt(t["b"])); tr.SetWidth(pcbnew.FromMM(t["w"]))
        tr.SetLayer(LAYERS[t["layer"]]); tr.SetNet(board.FindNet(t["net"])); tr.SetLocked(True)
        board.Add(tr)
        nt += 1
    for v in g["vias"]:
        if not v["locked"]:
            continue
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pt((v["x"], v["y"]))); via.SetWidth(pcbnew.FromMM(v["d"])); via.SetDrill(pcbnew.FromMM(v["drill"]))
        via.SetNet(board.FindNet(v["net"])); via.SetLocked(True)
        board.Add(via)
        nv += 1
    board.Save(PCB)
    print(f"geomreplay: {nt} tracks, {nv} vias from {GEOM}")


if __name__ == "__main__":
    main()
