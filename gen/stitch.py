"""Stitch isolated GND pour fragments to the In1 GND plane (run inside the KiCad chroot after the zone fill).

  kc 'python3 gen/stitch.py'

A filled GND fragment on F / In2 / B that holds no GND via or GND THT pad is only tied to the rest of GND through its own pads,
which DRC reports as unconnected. For each such fragment one 0.6/0.3 mm via is dropped where its pad overlaps the fragment by at least 0.1 mm and
clears all other-net copper (tracks, pads, vias, other-net zone fill) by 0.2 mm on every layer; on In1 it must also sit inside
the GND fill (shrunk by the via radius + 0.01 mm) or clear the In1 signal cuts the same way. Vias are tented (board setup), so a via may sit next to a GND pad but
not within 0.05 mm of its edge (no via-in-pad, hand assembly; other-net pads are covered by the clearance
test) or 0.56 mm of any other drill (0.25 mm hole-to-hole) are skipped. Only vias are created (one board-item type per process, KiCad 10.0.6 SWIG quirk).
"""
import math
import os

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
VIA_D, VIA_DRILL, CLR = 0.6, 0.3, 0.2
LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def mm(v):
    return pcbnew.FromMM(v)


def main():
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("GND")
    gcode = gnd.GetNetCode()
    fill = {l: pcbnew.SHAPE_POLY_SET() for l in LAYERS}
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != gcode:
            continue
        for l in LAYERS:
            if z.IsOnLayer(l):
                fill[l].Append(z.GetFilledPolysList(l))
    shrunk = {}
    for l, ps in fill.items():
        s = pcbnew.SHAPE_POLY_SET(ps)
        s.Deflate(mm(VIA_D / 2 + 0.01), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.005))
        shrunk[l] = s
    drills, pads, other = [], [], {l: [] for l in LAYERS}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            drills.append(t.GetPosition())
            if t.GetNetCode() != gcode:
                for l in LAYERS:
                    other[l].append(("v", t.GetPosition(), t.GetWidth(pcbnew.F_Cu) / 2))
        elif t.GetNetCode() != gcode:
            other.setdefault(t.GetLayer(), []).append(("t", t.GetStart(), t.GetEnd(), t.GetWidth() / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads.append(p)
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                drills.append(p.GetPosition())
    other_zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetCode() != gcode]

    def clear_other(l, pt):
        r = mm(VIA_D / 2 + CLR)
        for it in other.get(l, []):
            if it[0] == "v":
                if (it[1] - pt).EuclideanNorm() < r + it[2]:
                    return False
            else:
                seg = pcbnew.SEG(it[1], it[2])
                if seg.Distance(pt) < r + it[3]:
                    return False
        for p in pads:
            if p.GetNetCode() != gcode and p.IsOnLayer(l):
                if p.GetEffectivePolygon(l, pcbnew.ERROR_OUTSIDE).Collide(pt, r):
                    return False
        for z in other_zones:
            if z.IsOnLayer(l) and z.GetFilledPolysList(l).Collide(pt, r):
                return False
        return True

    def ok(pt):
        if not shrunk[pcbnew.In1_Cu].Contains(pt) and not clear_other(pcbnew.In1_Cu, pt):
            return False
        if any((d - pt).EuclideanNorm() < mm(0.56) for d in drills):
            return False
        for p in pads:
            if p.GetNetCode() == gcode and (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)) and \
                    p.GetEffectivePolygon(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu,
                                          pcbnew.ERROR_OUTSIDE).Collide(pt, mm(VIA_D / 2 + 0.05)):
                return False
        for l in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if not clear_other(l, pt):
                return False
        return True

    gvias = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gcode]
    gtht = [p.GetPosition() for p in pads if p.GetNetCode() == gcode and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    added, failed = 0, []
    for l in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ps = fill[l]
        for i in range(ps.OutlineCount()):
            frag = pcbnew.SHAPE_POLY_SET()
            frag.AddOutline(ps.Outline(i))
            for h in range(ps.HoleCount(i)):
                frag.AddHole(ps.Hole(i, h))
            if any(frag.Contains(v) for v in gvias + gtht):
                continue
            bb = frag.BBox()
            bb.Inflate(mm(0.3))
            best = None
            step = mm(0.05)
            cx, cy = bb.Centre().x, bb.Centre().y
            y = bb.GetTop()
            while y <= bb.GetBottom():
                x = bb.GetLeft()
                while x <= bb.GetRight():
                    pt = pcbnew.VECTOR2I(x, y)
                    if frag.Collide(pt, mm(VIA_D / 2 - 0.1)) and ok(pt):
                        d = math.hypot(x - cx, y - cy)
                        if best is None or d < best[0]:
                            best = (d, pt)
                    x += step
                y += step
            if best is None:
                c = bb.Centre()
                failed.append((board.GetLayerName(l), round(pcbnew.ToMM(c.x) - 100, 2), round(pcbnew.ToMM(c.y) - 100, 2),
                               round(pcbnew.ToMM(bb.GetWidth()), 2), round(pcbnew.ToMM(bb.GetHeight()), 2)))
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(best[1])
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(gnd)
            board.Add(v)
            gvias.append(best[1])
            drills.append(best[1])
            added += 1
    board.Save(PCB)
    print(f"stitch: {added} vias added, {len(failed)} fragments without a legal via site")
    for f in failed:
        print("  no site:", f)


if __name__ == "__main__":
    main()
