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
VBAT_ZONE = [(0.5, 21.6), (8.8, 21.6), (8.8, 33.6), (16.7, 33.6), (16.7, 23.5), (23.0, 23.5), (23.0, 25.1), (18.3, 25.1),
             (18.3, 35.5), (0.5, 35.5)]   # 1.6 mm riser on In2 (G3R-02) to the three U2-input vias on the C10-C12-U2 VIN track


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
        vbat_ps = None
        if name == "zones" and not any(z.GetZoneName() == "VBAT_In2" for z in board.Zones()):
            # Gate 3 G3R-02: VBAT copper on In2 from the battery pads (P1 vias) to the U1 input caps and up to the U2 input vias
            vbat_ps = pcbnew.SHAPE_POLY_SET()
            vbat_ps.NewOutline()
            for x, y in VBAT_ZONE:
                vbat_ps.Append(mm(OX + x), mm(OY + y))
        for layer in layers:
            ps = pcbnew.SHAPE_POLY_SET()
            ps.NewOutline()
            for x, y in ((0.2, 0.2), (W - 0.2, 0.2), (W - 0.2, H - 0.2), (0.2, H - 0.2)):
                ps.Append(mm(OX + x), mm(OY + y))
            polys.append((layer, ps))
        if vbat_ps is not None:
            z = pcbnew.ZONE(board)
            z.SetLayer(pcbnew.In2_Cu)
            z.SetNet(board.FindNet("VBAT"))
            z.SetZoneName("VBAT_In2")
            z.SetLocalClearance(mm(0.2))
            z.SetMinThickness(mm(0.25))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetAssignedPriority(2)
            z.SetOutline(vbat_ps)
            vbat_ps.thisown = False
            _KEEP.append(vbat_ps)
            board.Add(z)
        for layer, ps in polys:
            z = pcbnew.ZONE(board)
            z.SetLayer(layer)
            z.SetNet(gnd)
            z.SetZoneName("GND_" + board.GetLayerName(layer).replace(".", "_"))
            z.SetLocalClearance(mm(0.127))     # board minimum; KiCad still applies the larger PWR_HI class clearance (0.15)
            z.SetMinThickness(mm(0.127))
            z.SetThermalReliefGap(mm(0.25))
            z.SetThermalReliefSpokeWidth(mm(0.3))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD pads solid (no starved spokes), THT pads thermal
            z.SetAssignedPriority(0)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)   # unconnected copper islands are dropped
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
    elif name == "lockall":
        # freeze every existing track and via: Freerouting then only completes what is still unrouted (gen/fr_finish.sh)
        n = 0
        for t in board.GetTracks():
            if not t.IsLocked():
                t.SetLocked(True)
                n += 1
        print("locked", n)
    elif name == "minwidth":
        # Freerouting necks traces down to 0.75 x width at pins (0.1124 mm for 0.15 mm): restore the 0.127 mm fab minimum
        n = 0
        for t in board.GetTracks():
            if t.GetClass() == "PCB_TRACK" and t.GetWidth() < mm(0.127):
                t.SetWidth(mm(0.127))
                n += 1
        print("widened", n)
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
    subprocess.run([py, os.path.abspath(__file__), "--stage", "minwidth"], check=True)
    subprocess.run([py, os.path.abspath(__file__), "--stage", "pours"], check=True)
    subprocess.run([py, os.path.abspath(__file__), "--stage", "fill"], check=True)


if __name__ == "__main__":
    main()
