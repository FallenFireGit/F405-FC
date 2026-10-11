"""Build kicad/F405FC.kicad_pcb from design/circuit.py: outline, holes, rules, scripted placement.

Run inside the KiCad chroot:  kc 'python3 gen/build_pcb.py'
Placement table: design/placement.py (ref -> x, y, rotation, side). Coordinates in mm, origin = board top-left.
"""
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, os.path.join(ROOT, "design"))

import pcbnew  # noqa: E402

import circuit  # noqa: E402
import pcbgen  # noqa: E402

PCB = os.path.join(ROOT, "kicad", "F405FC.kicad_pcb")
W = H = 36.0
CORNER_R = 2.0
HOLE_PITCH = 30.5
OX, OY = 100.0, 100.0  # board origin on the KiCad canvas


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def outline(board):
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(d)
    r = CORNER_R

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(center, start, angle):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetCenter(pt(*center)); s.SetStart(pt(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)

    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc((W - r, r), (W - r, 0), 90); arc((W - r, H - r), (W, H - r), 90)
    arc((r, H - r), (r, H), 90); arc((r, r), (0, r), 90)


def rules(board):
    ds = board.GetDesignSettings()
    board.SetCopperLayerCount(4)
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_ViasMinAnnularWidth = mm(0.15)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_HoleClearance = mm(0.2)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.127)); nc.SetTrackWidth(mm(0.15)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
    board.SetLayerName(pcbnew.In1_Cu, "In1.GND")
    board.SetLayerName(pcbnew.In2_Cu, "In2.PWR")


def place(board, table):
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = [r for r in fps if r not in table]
    for ref, (x, y, rot, side) in table.items():
        fp = fps.get(ref)
        if fp is None:
            print("WARN placement for unknown ref", ref)
            continue
        if fp.IsFlipped() != (side == "B"):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(rot)
    return missing


def main():
    os.makedirs(os.path.dirname(PCB), exist_ok=True)
    existing = pcbnew.LoadBoard(PCB) if os.path.exists(PCB) and "--fresh" not in sys.argv else None
    board = pcbgen.build(circuit.c, PCB, local_libs={"F405FC": os.path.join(ROOT, "lib", "F405FC.pretty")},
                         existing=existing)
    board = pcbnew.LoadBoard(PCB)  # reload: design settings of a python-created BOARD are not wrapped
    outline(board)
    rules(board)
    import placement
    importlib.reload(placement)
    missing = place(board, placement.PLACE)
    if missing:
        print("UNPLACED:", " ".join(sorted(missing)))
    board.Save(PCB)
    print("saved", PCB, "footprints:", len(board.GetFootprints()))


if __name__ == "__main__":
    main()
