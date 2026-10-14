"""Add kicad/route_add.json (from gen/mazeroute.py) to the board: kc 'python3 gen/rapply.py'. One item type per interpreter."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
ADD = os.path.join(os.path.dirname(PCB), os.environ.get("F405_ROUTES", "route_add.json"))
OX = OY = 100.0


def stage(kind):
    import pcbnew
    board = pcbnew.LoadBoard(PCB)
    d = json.load(open(ADD))
    L = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu, "In3": pcbnew.In3_Cu, "In4": pcbnew.In4_Cu, "B": pcbnew.B_Cu}

    def pt(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
    if kind == "tracks":
        for t in d["tracks"]:
            s = pcbnew.PCB_TRACK(board)
            s.SetStart(pt(*t["a"])); s.SetEnd(pt(*t["b"])); s.SetWidth(pcbnew.FromMM(t["w"]))
            s.SetLayer(L[t["layer"]]); s.SetNet(board.FindNet(t["net"]))
            board.Add(s)
    else:
        for v in d["vias"]:
            s = pcbnew.PCB_VIA(board)
            s.SetPosition(pt(v["x"], v["y"])); s.SetWidth(pcbnew.FromMM(0.6)); s.SetDrill(pcbnew.FromMM(0.3))
            s.SetNet(board.FindNet(v["net"]))
            board.Add(s)
    board.Save(PCB)
    print("rapply", kind, len(d[kind]))


if __name__ == "__main__":
    if "--stage" in sys.argv:
        stage(sys.argv[sys.argv.index("--stage") + 1])
    else:
        for k in ("tracks", "vias"):
            subprocess.run([sys.executable, os.path.abspath(__file__), "--stage", k], check=True)
