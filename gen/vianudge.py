"""Pull vias off the pads they fan out from (Gate 5 M-3): a tented via whose copper lies closer than TARGET (0.10 mm) to a
same-net SMD pad leaves a solder-mask dam the fab cannot hold, so solder runs onto the via ring. Each such via is moved by the
smallest step (up to 0.20 mm, 24 directions) that puts it >= TARGET from every same-net SMD pad while the via and the
re-stretched ends of its attached tracks keep the board clearances to every other net, hole and the edge. Vias that cannot
move are reported and left. Run in the KiCad chroot before the pours (gen/route_finish.sh); the final DRC re-checks.

  kc 'python3 gen/vianudge.py'
"""
import math
import pcbnew

PCB = "/work/kicad/F405FC.kicad_pcb"
TARGET = 0.10
MM = pcbnew.FromMM
VR = MM(0.3)          # via copper radius
HR = MM(0.15)         # via hole radius
HOLE_CLR = MM(0.25)   # board hole-to-hole minimum (m_HoleToHoleMin)
EDGE = (MM(100.0 + 0.6), MM(100.0 + 0.6), MM(136.0 - 0.6), MM(136.0 - 0.6))   # via centre box: 0.3 copper-to-edge


def main():
    b = pcbnew.LoadBoard(PCB)
    pads = list(b.GetPads())
    smd = [p for p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    holes = [(p.GetPosition(), max(p.GetDrillSize().x, p.GetDrillSize().y) // 2) for p in pads if p.GetDrillSize().x > 0]
    layers = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]

    def near(item_pos, pos, r=MM(4)):
        return (item_pos - pos).EuclideanNorm() < r

    def own_gap(v, pos):
        g = None
        for p in smd:
            if p.GetNetCode() != v.GetNetCode() or not near(p.GetPosition(), pos):
                continue
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(l):
                    d = p.GetEffectivePolygon(l).SquaredDistance(pos) ** 0.5 - VR
                    g = d if g is None else min(g, d)
        return g

    def clear(v, pos, moved):
        if not (EDGE[0] <= pos.x <= EDGE[2] and EDGE[1] <= pos.y <= EDGE[3]):
            return False
        for c, r in holes:
            if (c - pos).EuclideanNorm() < r + HR + HOLE_CLR:
                return False
        for o in vias:
            if o is not v and (o.GetPosition() - pos).EuclideanNorm() < 2 * HR + HOLE_CLR:
                return False
        circle = pcbnew.SHAPE_CIRCLE(pos, VR)
        net = v.GetNetCode()
        vc = v.GetOwnClearance(pcbnew.F_Cu)
        segs = []
        for t, end in moved:
            a = pos if end == 0 else t.GetStart()
            e = pos if end == 1 else t.GetEnd()
            segs.append((t.GetLayer(), pcbnew.SHAPE_SEGMENT(a, e, t.GetWidth()), t.GetOwnClearance(t.GetLayer()), t))
        for o in list(pads) + tracks + vias:
            if o.GetNetCode() == net or o is v:
                continue
            if not near(o.GetPosition() if o.GetClass() != "PCB_TRACK" else o.GetStart(), pos, MM(6)) and \
               not (o.GetClass() == "PCB_TRACK" and near(o.GetEnd(), pos, MM(6))):
                continue
            for l in layers:
                if not o.IsOnLayer(l):
                    continue
                sh = o.GetEffectiveShape(l)
                cl = max(vc, o.GetOwnClearance(l)) + MM(0.005)
                if sh.Collide(circle, cl):
                    return False
                for sl, ss, tc, _t in segs:
                    if sl == l and sh.Collide(ss, max(tc, o.GetOwnClearance(l)) + MM(0.005)):
                        return False
        return True

    moved_n = stuck = 0
    for v in vias:
        pos = v.GetPosition()
        g = own_gap(v, pos)
        if g is None or g >= MM(TARGET):
            continue
        att = []
        for t in tracks:
            if t.GetNetCode() != v.GetNetCode():
                continue
            if (t.GetStart() - pos).EuclideanNorm() < MM(0.005):
                att.append((t, 0))
            elif (t.GetEnd() - pos).EuclideanNorm() < MM(0.005):
                att.append((t, 1))
        done = False
        for step in range(1, 9):
            r = MM(0.025 * step)
            best = None
            for k in range(24):
                a = 2 * math.pi * k / 24
                q = pcbnew.VECTOR2I(int(pos.x + r * math.cos(a)), int(pos.y + r * math.sin(a)))
                gq = own_gap(v, q)
                if gq is None or gq < MM(TARGET):
                    continue
                if best is not None and gq <= best[0]:
                    continue
                if clear(v, q, att):
                    best = (gq, q)
            if best:
                q = best[1]
                v.SetPosition(q)
                for t, end in att:
                    if end == 0:
                        t.SetStart(q)
                    else:
                        t.SetEnd(q)
                moved_n += 1
                done = True
                break
        if not done:
            stuck += 1
            print("stuck: %s at (%.3f, %.3f) gap %.3f" % (v.GetNetname(), pcbnew.ToMM(pos.x) - 100, pcbnew.ToMM(pos.y) - 100,
                                                          pcbnew.ToMM(g)))
    b.Save(PCB)
    print("vianudge: moved", moved_n, "stuck", stuck)


if __name__ == "__main__":
    main()
