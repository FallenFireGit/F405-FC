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
    if any(d.GetLayer() == pcbnew.Edge_Cuts for d in board.GetDrawings()):
        return
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


_KEEP_ALIVE = []


def hole_keepouts(board):
    """4.6 mm grommet keepout around each M3 hole: no tracks or vias (copper pour allowed), all layers."""
    import math
    if any(z.GetIsRuleArea() and z.GetZoneName().startswith("HOLE_KEEPOUT") for z in board.Zones()):
        return  # already present (board.Remove + python GC of the zone segfaults in 10.0.6, so never remove)
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(l)
    polys = _KEEP_ALIVE  # ZONE.SetOutline takes ownership of the pointer: python must never free these
    for hx, hy in ((2.75, 2.75), (33.25, 2.75), (2.75, 33.25), (33.25, 33.25)):
        ps = pcbnew.SHAPE_POLY_SET()   # build geometry before any ZONE exists in this process (SWIG quirk)
        ps.NewOutline()
        for k in range(24):
            a = 2 * math.pi * k / 24
            ps.Append(mm(OX + hx + 2.3 * math.cos(a)), mm(OY + hy + 2.3 * math.sin(a)))
        polys.append(ps)
    lkeep = []   # G2R-08: Würth forbids tracks/vias under the WE-MAPI body: B.Cu rule area between the pads of L1/L2
    for fp in board.GetFootprints():
        if fp.GetReference() in ("L1", "L2"):
            c = fp.GetPosition()
            vert = round(fp.GetOrientationDegrees()) % 180 == 90
            hx, hy = (1.9, 0.6) if vert else (0.6, 1.9)
            ps = pcbnew.SHAPE_POLY_SET()
            ps.NewOutline()
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                ps.Append(c.x + mm(sx * hx), c.y + mm(sy * hy))
            polys.append(ps)
            lkeep.append((fp.GetReference(), fp.GetLayer()))
    nhole = len(polys) - len(lkeep)
    for i, ps in enumerate(polys):
        if i >= nhole:
            ref, layer = lkeep[i - nhole]
            z = pcbnew.ZONE(board)
            z.SetIsRuleArea(True)
            z.SetZoneName(f"IND_KEEPOUT_{ref}")
            z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(False)
            z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
            z.SetLayer(layer)
            z.SetOutline(ps)
            ps.thisown = False
            board.Add(z)
            continue
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName(f"HOLE_KEEPOUT_{i + 1}")
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(ls)
        z.SetOutline(ps)
        ps.thisown = False
        board.Add(z)


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
    ds.m_HoleClearance = mm(0.19)  # GCT USB4105 land pattern has 0.194 mm pad-to-NPTH spacing
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.127)); nc.SetTrackWidth(mm(0.15)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
    ds.SetAuxOrigin(pt(0, H))  # drill/place origin = board bottom-left corner (Gerber, drill and CPL share it)
    board.SetLayerName(pcbnew.In1_Cu, "In1.GND")
    board.SetLayerName(pcbnew.In2_Cu, "In2.PWR")


def tidy_fields(board):
    """Silk: keep only a small reference on the fab layer; hide every other field (MPN, DigiKey, ...)."""
    for fp in board.GetFootprints():
        flipped = fp.IsFlipped()
        for f in fp.GetFields():
            if f.IsReference():
                f.SetLayer(pcbnew.B_Fab if flipped else pcbnew.F_Fab)
                f.SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5)))
                f.SetTextThickness(mm(0.08))
                f.SetVisible(True)
            else:
                f.SetVisible(False)


LABELS = {"J1": "USB", "J2": "ESC", "J3": "VTX 10V", "J4": "GPS 5V", "J5": "ELRS", "P1": "VBAT", "P2": "GND", "P3": "10V",
          "P4": "GND", "P5": "C1", "P6": "C2", "P7": "VID", "P8": "5V", "P9": "G", "P10": "LED", "P11": "5V", "P12": "G",
          "P13": "BZ+", "P14": "BZ-", "P15": "T5", "P16": "R5", "P17": "T6", "P18": "R6", "P19": "S5", "P20": "S6",
          "P21": "S7", "P22": "S8", "P23": "RSSI", "P24": "G", "P25": "5V", "TP1": "DIO", "TP2": "CLK", "TP3": "RST",
          "TP4": "3V3", "TP5": "G", "SW1": "BOOT"}


def silk_labels(board):
    """Function labels next to every user pad/connector (Gate 1 D-15: VTX vs GPS connectors clearly marked)."""
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) for d in board.GetDrawings()):
        return  # labels already present (re-run build with --fresh to regenerate)
    for fp in board.GetFootprints():
        lab = LABELS.get(fp.GetReference())
        if not lab:
            continue
        bb = fp.GetBoundingBox(False)
        c = bb.GetCenter()
        cx, cy = pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY
        hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
        # put the label on the side facing the board centre, just outside the footprint
        dx, dy = W / 2 - cx, H / 2 - cy
        if abs(dx) > abs(dy):
            tx, ty = cx + (hw + 0.9) * (1 if dx > 0 else -1), cy
        else:
            tx, ty = cx, cy + (hh + 0.5) * (1 if dy > 0 else -1)
        t = pcbnew.PCB_TEXT(board)
        t.SetText(lab)
        t.SetPosition(pt(tx, ty))
        flipped = fp.IsFlipped()
        t.SetLayer(pcbnew.B_SilkS if flipped else pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        t.SetTextThickness(mm(0.15))
        if flipped:
            t.SetMirrored(True)
        board.Add(t)


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


def anchor(board, anchors):
    """Place parts relative to a pad of another part: ref -> (anchor_ref, anchor_pad, dx, dy, rot, side).
    Anchored parts are then treated as FIXED by the legalizer (Gate 3 G3-02/03: hot-loop parts must not drift)."""
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, (aref, apad, dx, dy, rot, side) in anchors.items():
        a = fps[aref]
        pad = [p for p in a.Pads() if p.GetNumber() == str(apad)][0]
        q = pad.GetPosition()
        fp = fps[ref]
        if fp.IsFlipped() != (side == "B"):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(q.x + mm(dx), q.y + mm(dy)))


RULES = {  # JLC04161H-7628 capability with margin (brief: 0.127/0.127 trace/space, 0.3/0.6 vias)
    "min_track_width": 0.127, "min_clearance": 0.127, "min_copper_edge_clearance": 0.3, "min_via_diameter": 0.6,
    "min_through_hole_diameter": 0.3, "min_via_annular_width": 0.15, "min_hole_to_hole": 0.25,
    "min_hole_clearance": 0.19,  # GCT USB4105 land pattern has 0.194 mm pad-to-NPTH spacing
}


def write_rules(pro_path):
    """pcbnew's python Save does not write the .kicad_pro, so the DRC minimums live here (kicad-cli DRC reads the project)."""
    import json
    with open(pro_path) as f:
        pro = json.load(f)
    pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update(RULES)
    with open(pro_path, "w") as f:
        json.dump(pro, f, indent=2)


def _stage(name):
    """One board mutation per interpreter: KiCad 10.0.6's SWIG wrappers stop resolving types (BOARD_DESIGN_SETTINGS,
    SHAPE_POLY_SET, ...) once python has created a board item of another type in the same process."""
    board = pcbnew.LoadBoard(PCB)
    if name == "place":
        rules(board)
        import placement
        importlib.reload(placement)
        missing = place(board, placement.PLACE)
        anchor(board, getattr(placement, "ANCHOR", {}))
        missing = [r for r in missing if r not in getattr(placement, "ANCHOR", {})]
        if missing:
            print("UNPLACED:", " ".join(sorted(missing)))
        import legalize
        moves = legalize.legalize(board, list(placement.FIXED), OX, OY, W, H, placement.PRIORITY,
                                  tight=list(getattr(placement, "ANCHOR", {})))
        for ref, mv in moves:
            if mv is None or mv[0] > 1.5:
                print("LEGALIZE", ref, "FAILED (no free spot)" if mv is None else f"moved {mv[0]} mm rot {mv[1]}")
        tidy_fields(board)
    elif name == "keepouts":
        hole_keepouts(board)
    elif name == "labels":
        silk_labels(board)
    elif name == "outline":
        outline(board)
    board.Save(PCB)
    print("stage", name, "ok; footprints:", len(board.GetFootprints()))


STAGES = ("place", "keepouts", "labels", "outline")


def main():
    if "--stage" in sys.argv:
        return _stage(sys.argv[sys.argv.index("--stage") + 1])
    os.makedirs(os.path.dirname(PCB), exist_ok=True)
    existing = pcbnew.LoadBoard(PCB) if os.path.exists(PCB) and "--fresh" not in sys.argv else None
    pcbgen.build(circuit.c, PCB, local_libs={"F405FC": os.path.join(ROOT, "lib", "F405FC.pretty")}, existing=existing)
    import schgen
    schgen.write_project(circuit.c, os.path.dirname(PCB), *circuit.net_settings())  # pcbnew's save dropped them
    write_rules(PCB.replace(".kicad_pcb", ".kicad_pro"))
    import subprocess
    for st in STAGES:
        subprocess.run([sys.executable, os.path.abspath(__file__), "--stage", st], check=True)


if __name__ == "__main__":
    main()
