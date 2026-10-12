"""Routing pipeline for kicad/F405FC.kicad_pcb (run after gen/build_pcb.py).

  kc 'python3 gen/route.py [passes]'

Stages (each in its own interpreter, see build_pcb._stage for the SWIG reason):
  zones   - In1 solid GND plane (the only plane Freerouting sees)
  dsn     - pcbnew.ExportSpecctraDSN -> kicad/F405FC.dsn
  route   - Freerouting 2.5.0 (Java 25) -> kicad/F405FC.ses
  ses     - pcbnew.ImportSpecctraSES
  pours   - GND pours on In2 / F / B
  fill    - fill all zones
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
DSN = os.path.splitext(PCB)[0] + ".dsn"
SES = os.path.splitext(PCB)[0] + ".ses"
JAVA = "/opt/jdk/bin/java"
FR = "/opt/fr/freerouting-2.5.0.jar"
OX = OY = 100.0
W = H = 36.0
_KEEP = []


def stage(name, passes):
    import pcbnew

    def mm(v):
        return pcbnew.FromMM(v)

    board = pcbnew.LoadBoard(PCB)
    if name in ("zones", "pours"):
        layers = (pcbnew.In1_Cu,) if name == "zones" else (pcbnew.In2_Cu, pcbnew.F_Cu, pcbnew.B_Cu)
        have = {z.GetLayer() for z in board.Zones() if (not z.GetIsRuleArea()) and z.GetZoneName().startswith("GND_")}
        layers = [l for l in layers if l not in have]
        if not layers:
            print("zones present")
            return
        gnd = board.FindNet("GND")
        polys = []
        for layer in layers:
            ps = pcbnew.SHAPE_POLY_SET()
            ps.NewOutline()
            for x, y in ((0.2, 0.2), (W - 0.2, 0.2), (W - 0.2, H - 0.2), (0.2, H - 0.2)):
                ps.Append(mm(OX + x), mm(OY + y))
            polys.append((layer, ps))
        for layer, ps in polys:
            z = pcbnew.ZONE(board)
            z.SetLayer(layer)
            z.SetNet(gnd)
            z.SetZoneName("GND_" + board.GetLayerName(layer).replace(".", "_"))
            z.SetLocalClearance(mm(0.2))
            z.SetMinThickness(mm(0.2))
            z.SetThermalReliefGap(mm(0.25))
            z.SetThermalReliefSpokeWidth(mm(0.3))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.SetAssignedPriority(0)
            z.SetOutline(ps)
            ps.thisown = False
            _KEEP.append(ps)
            board.Add(z)
    elif name == "dsn":
        ok = pcbnew.ExportSpecctraDSN(board, DSN)
        # In1 is the solid GND plane: no net class may route traces on it (GND reaches it through gen/gndfan.py vias)
        txt = open(DSN).read()
        sig = "(use_layer F.Cu In2.PWR B.Cu)"
        n = txt.count("(circuit\n")
        txt = txt.replace("(circuit\n", "(circuit\n        " + sig + "\n")
        open(DSN, "w").write(txt)
        print("dsn", ok, "classes restricted:", n)
        return
    elif name == "ses":
        ok = pcbnew.ImportSpecctraSES(board, SES)
        print("ses", ok)
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
    elif name == "fill":
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
    board.Save(PCB)
    print("stage", name, "saved")


def main():
    if "--stage" in sys.argv:
        return stage(sys.argv[sys.argv.index("--stage") + 1], 0)
    passes = sys.argv[1] if len(sys.argv) > 1 else "100"
    py = sys.executable
    for st in ("zones", "dsn"):
        subprocess.run([py, os.path.abspath(__file__), "--stage", st], check=True)
    if os.path.exists(SES):
        os.remove(SES)
    subprocess.run([JAVA, "-Djava.awt.headless=true", "-jar", FR, "-de", DSN, "-do", SES, "-mp", passes, "-mt", "3"],
                   check=True)
    subprocess.run([py, os.path.abspath(__file__), "--stage", "ses"], check=True)
    subprocess.run([py, os.path.abspath(__file__), "--stage", "pours"], check=True)
    subprocess.run([py, os.path.abspath(__file__), "--stage", "fill"], check=True)


if __name__ == "__main__":
    main()
