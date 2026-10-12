"""Scripted critical routes (run after gen/build_pcb.py, before gen/route.py): kc 'python3 gen/critical.py'

Buck hot loops, SW / BST nodes, local output copper, the VBAT trunk (battery pads -> U1 input -> In2 -> U2 input) and the
battery-entry stitching vias. VBAT from P1 to both buck inputs is the In2 copper zone made by gen/route.py
(stage zones, Gate 3 G3R-02); these vias stitch it. All items are locked so the Specctra export marks them protected and Freerouting routes around them.
Coordinates: board mm, origin = board top-left corner (pad centres from gen/padpos.py). Each item type is created in its own
interpreter (KiCad 10.0.6 SWIG quirk, see build_pcb._stage). Re-running is a no-op once the tracks exist (rebuild with --fresh).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
OX = OY = 100.0

B, F, IN2 = "B.Cu", "F.Cu", "In2.Cu"
# (layer, width mm, net, [points])
TRACKS = [
    # ---- U1 (5 V) ----
    (B, 0.8, "VBAT", [(3.05, 24.97), (7.5, 24.97)]),                     # C2.1 - C4.1 - U1.VIN
    (B, 0.8, "VBAT", [(3.05, 22.89), (3.05, 24.97)]),                    # C3.1 - C2.1
    (B, 0.8, "GND", [(3.05, 27.5), (9.2, 27.5)]),                         # C2.2 - C4.2 - U1.GND - EP
    (B, 0.8, "SW_5V", [(12.9, 27.5), (13.42, 28.4), (13.42, 30.85)]),     # U1.SW -> L1
    (B, 0.6, "SW_5V", [(12.9, 27.5), (14.6, 27.34)]),                     # U1.SW -> C5 (boot)
    (B, 0.3, "BST_5V", [(12.9, 26.23), (14.6, 26.39)]),
    (B, 0.8, "5V", [(15.78, 30.85), (15.78, 29.1), (16.45, 28.4), (16.45, 27.58)]),   # L1 -> C8
    (B, 0.8, "5V", [(15.78, 32.32), (18.23, 32.32)]),                     # L1 -> C6
    (B, 0.8, "5V", [(15.78, 32.32), (15.78, 33.3), (15.01, 34.45)]),      # L1 -> C7 (clear of the L1 body keepout)
    (B, 0.5, "5V", [(18.23, 32.32), (20.11, 31.33)]),                     # C6 -> C9
    (B, 0.8, "VBAT", [(5.0, 24.97), (5.0, 23.85)]), (B, 0.8, "VBAT", [(4.0, 24.97), (4.0, 23.95)]),                      # U1 input -> In2 trunk vias (clear of J5 on top)
    (B, 0.8, "VBAT", [(6.0, 24.97), (6.0, 23.7)]),
    # ---- U2 (10 V) ----
    (B, 0.8, "VBAT", [(17.6, 20.9), (17.6, 21.7), (18.4, 22.45), (19.67, 22.45)]),   # In2 trunk -> C11.1
    (B, 0.8, "VBAT", [(19.5, 22.45), (19.5, 24.24)]),                    # C11.1 - C10.1
    (B, 0.8, "VBAT", [(19.4, 24.24), (21.95, 24.46), (23.9, 23.97)]),     # C10.1 - C12.1 - U2.VIN
    (B, 0.8, "GND", [(19.4, 27.19), (21.95, 26.4), (25.6, 26.4)]),        # C10.2 - C12.2 - U2.GND - EP
    (B, 0.8, "SW_10V", [(29.3, 26.5), (29.38, 30.8)]),                    # U2.SW -> L2
    (B, 0.6, "SW_10V", [(29.3, 26.5), (31.0, 26.34)]),                    # U2.SW -> C13 (boot)
    (B, 0.3, "BST_10V", [(29.3, 25.23), (31.0, 25.39)]),
    (B, 0.8, "10V", [(27.01, 32.28), (21.91, 32.28)]),                    # L2 -> C14 -> C16
    (B, 0.5, "10V", [(23.77, 32.28), (23.77, 33.99)]),                    # -> C17
    # ---- GND stubs from cap return pads to their stitching vias ----
    (B, 0.5, "GND", [(6.6, 28.2), (6.6, 27.5)]),
    (B, 0.5, "GND", [(5.55, 27.5), (5.9, 28.4)]),
    (B, 0.5, "GND", [(18.6, 28.2), (18.8, 27.19)]), (B, 0.5, "GND", [(19.9, 28.2), (19.9, 27.19)]),
    (B, 0.5, "GND", [(18.6, 28.2), (18.23, 29.38)]),
    (B, 0.5, "GND", [(17.3, 24.6), (16.45, 24.63)]),
    (B, 0.5, "GND", [(19.1, 34.45), (17.96, 34.45)]),
    (B, 0.5, "GND", [(20.11, 29.6), (20.11, 30.37)]),
    (B, 0.5, "GND", [(21.91, 29.32), (24.41, 29.32)]),
    (B, 0.5, "GND", [(26.2, 34.0), (25.32, 33.99)]),
    (B, 0.5, "GND", [(33.9, 25.6), (32.85, 25.63)]),
    # ---- battery entry, top side: C1 -> D1 ----
    (F, 0.8, "VBAT", [(7.3, 30.07), (7.3, 32.6)]),
]
# (net, x, y): 0.6/0.3 through vias
VIAS = [
    ("VBAT", 5.0, 23.85), ("VBAT", 6.0, 23.7), ("VBAT", 4.0, 23.95),   # U1 input -> In2 VBAT zone (G3R-02) ("VBAT", 17.6, 21.7), ("VBAT", 17.6, 20.9),       # In2 trunk ends
    ("VBAT", 6.6, 32.6), ("VBAT", 7.6, 32.6), ("VBAT", 6.6, 33.8), ("VBAT", 7.6, 33.8),         # P1 (bottom) <-> D1/C1 (top)
    ("GND", 11.1, 32.6), ("GND", 11.1, 33.8),                                                   # P2 (bottom) <-> D1 anode (top)
    ("GND", 5.9, 28.4), ("GND", 6.6, 28.2),                                # U1 input-cap returns
    ("GND", 18.6, 28.2), ("GND", 19.9, 28.2),                             # U2 input-cap returns
    ("GND", 17.3, 24.6), ("GND", 19.1, 34.45), ("GND", 20.11, 29.6),    # 5 V output-cap returns
    ("GND", 26.2, 34.0), ("GND", 33.9, 25.6),                             # 10 V output-cap returns
]


def stage(name):
    import pcbnew

    def pt(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))

    board = pcbnew.LoadBoard(PCB)
    have = [t for t in board.GetTracks() if t.IsLocked()]
    if name == "tracks":
        if any(t.GetClass() == "PCB_TRACK" for t in have):
            print("critical tracks present")
            return
        n = 0
        for layer, w, net, pts in TRACKS:
            ni = board.FindNet(net)
            assert ni is not None, net
            lid = {B: pcbnew.B_Cu, F: pcbnew.F_Cu, IN2: pcbnew.In2_Cu}[layer]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pt(*a)); t.SetEnd(pt(*b)); t.SetWidth(pcbnew.FromMM(w))
                t.SetLayer(lid); t.SetNet(ni); t.SetLocked(True)
                board.Add(t)
                n += 1
        print("tracks", n)
    elif name == "vias":
        if any(t.GetClass() == "PCB_VIA" for t in have):
            print("critical vias present")
            return
        for net, x, y in VIAS:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pt(x, y)); v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetNet(board.FindNet(net)); v.SetLocked(True)
            board.Add(v)
        print("vias", len(VIAS))
    board.Save(PCB)


def main():
    if "--stage" in sys.argv:
        return stage(sys.argv[sys.argv.index("--stage") + 1])
    for st in ("tracks", "vias"):
        subprocess.run([sys.executable, os.path.abspath(__file__), "--stage", st], check=True)


if __name__ == "__main__":
    main()
