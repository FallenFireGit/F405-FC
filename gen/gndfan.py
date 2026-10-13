"""GND fanout: one stitching via (0.6/0.3) next to every SMD GND pad that has no GND via within reach, plus a short stub.

Run after gen/critical.py, before gen/route.py:  kc 'python3 gen/gndfan.py'
With every GND pad tied to the In1 plane by its own via, In1 can be a Specctra power layer: Freerouting then never routes signals
across the GND plane and does not have to route GND at all. Candidate via positions are searched around each pad (outward first)
and checked against every pad, track, via, board edge, mounting-hole keepout and rule area on all layers (through via).
Tracks and vias are created in separate interpreters (KiCad 10.0.6 SWIG quirk, see build_pcb._stage).
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
PLAN = os.path.join("/tmp", "gndfan_plan.json")
MODE = os.environ.get("FANOUT", "gnd")   # "gnd" (default) or "mcu" (U3 inward fanout)
OX = OY = 100.0
W = H = 36.0
VIA_R = 0.3
CLR = 0.15            # via/stub copper to other-net copper
STUB_W = 0.3
HOLES = [(2.75, 2.75), (33.25, 2.75), (2.75, 33.25), (33.25, 33.25)]
SKIP_REFS = {"U1", "U2", "P2", "J1", "J2", "J3", "J4", "J5"}   # PowerPAD via arrays / scripted entry vias / connector GND by router


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def crosses(a, b, c, d):
    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    return (cr(c, d, a) * cr(c, d, b) < 0) and (cr(a, b, c) * cr(a, b, d) < 0)


def rect_dist(px, py, r):
    cx, cy = min(max(px, r[0]), r[2]), min(max(py, r[1]), r[3])
    return math.hypot(px - cx, py - cy)


def seg_rect_dist(a, b, r, n=12):
    return min(rect_dist(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, r) for k in range(n + 1))


def plan():
    import pcbnew

    def mm(v):
        return pcbnew.ToMM(v)

    board = pcbnew.LoadBoard(PCB)
    pads = []   # (rect, net, layerset 'F'/'B'/'FB', ref)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            r = [mm(bb.GetLeft()) - OX, mm(bb.GetTop()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY]
            ls = p.GetLayerSet()
            lay = ("F" if ls.Contains(pcbnew.F_Cu) else "") + ("B" if ls.Contains(pcbnew.B_Cu) else "")
            pads.append((r, p.GetNetname(), lay, fp.GetReference(), p))
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            q = t.GetPosition()
            vias.append((mm(q.x) - OX, mm(q.y) - OY, mm(t.GetWidth(pcbnew.F_Cu)) / 2, t.GetNetname()))
        else:
            a, b = t.GetStart(), t.GetEnd()
            lay = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}.get(t.GetLayer(), "I")
            tracks.append(((mm(a.x) - OX, mm(a.y) - OY), (mm(b.x) - OX, mm(b.y) - OY), mm(t.GetWidth()) / 2, t.GetNetname(), lay))
    keep = []   # rule areas that forbid vias (inductor keepouts)
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.GetZoneName().startswith("IND_"):
            bb = z.GetBoundingBox()
            keep.append([mm(bb.GetLeft()) - OX, mm(bb.GetTop()) - OY, mm(bb.GetRight()) - OX, mm(bb.GetBottom()) - OY])

    def via_ok(x, y, own):
        if x < 0.3 + VIA_R + 0.05 or y < 0.3 + VIA_R + 0.05 or x > W - 0.65 or y > H - 0.65:
            return False
        if any(math.hypot(x - hx, y - hy) < 2.3 + VIA_R + 0.05 for hx, hy in HOLES):
            return False
        if any(rect_dist(x, y, k) < VIA_R + 0.05 for k in keep):
            return False
        for r, net, lay, ref, p in pads:
            if p is own:
                continue
            if rect_dist(x, y, r) < VIA_R + (0.05 if net == "GND" and MODE == "gnd" else CLR):
                return False
        for vx, vy, vr, net in vias:
            if math.hypot(x - vx, y - vy) < VIA_R + vr + (0.25 if net == "GND" and MODE == "gnd" else CLR + 0.1):
                return False
        for a, b, hw, net, lay in tracks:
            if lay == "I" and net == "GND":
                continue
            if seg_dist(x, y, *a, *b) < VIA_R + hw + (0.05 if net == "GND" and MODE == "gnd" else CLR):
                return False
        return True

    def stub_ok(a, b, side, own):
        for r, net, lay, ref, p in pads:
            if p is own or net == "GND" or side not in lay:
                continue
            if seg_rect_dist(a, b, r) < STUB_W / 2 + CLR:
                return False
        for t0, t1, hw, net, lay in tracks:
            if net != "GND" and lay == side and (crosses(a, b, t0, t1) or min(seg_dist(*t0, *a, *b), seg_dist(*t1, *a, *b),
                                                      seg_dist(*a, *t0, *t1), seg_dist(*b, *t0, *t1)) < STUB_W / 2 + hw + CLR):
                return False
        for vx, vy, vr, net in vias:          # through vias of other nets are on every layer
            if MODE == "gnd" and net != "GND" and seg_dist(vx, vy, *a, *b) < STUB_W / 2 + vr + CLR:
                return False
        return True

    new_vias, new_stubs, missed = [], [], []
    if MODE == "mcu":
        return plan_mcu(pads, vias, tracks, via_ok, stub_ok)
    for r, net, lay, ref, p in pads:
        if net != "GND" or ref in SKIP_REFS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or ref.startswith("H"):
            continue
        side = "F" if "F" in lay else "B"
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if any(math.hypot(cx - vx, cy - vy) < 1.0 and net_v == "GND" for vx, vy, _, net_v in vias):
            continue    # already stitched (critical vias, earlier fanout)
        if any(t[3] == "GND" and t[4] == side and rect_dist(t[0][0], t[0][1], r) < 0.05 for t in tracks):
            continue    # already tied to GND copper by a locked track (critical routes)
        near = sorted((math.hypot(cx - vx, cy - vy), vx, vy) for vx, vy, _, net_v in vias if net_v == "GND")
        shared = next(((vx, vy) for dd, vx, vy in near if dd < 1.8 and stub_ok((cx, cy), (vx, vy), side, p)), None)
        if shared:
            tracks.append(((cx, cy), shared, STUB_W / 2, "GND", side))
            new_stubs.append((side, cx, cy, *shared))
            continue
        fp = p.GetParent()
        fc = fp.GetPosition()
        fx, fy = mm(fc.x) - OX, mm(fc.y) - OY
        out = math.atan2(cy - fy, cx - fx) if (cx, cy) != (fx, fy) else 0.0
        hx, hy = (r[2] - r[0]) / 2, (r[3] - r[1]) / 2
        best = None
        for dist in (0.0, 0.15, 0.35, 0.6, 0.9, 1.2, 1.5, 1.8):
            for off in [0.0] + [sg * i * math.pi / 8 for i in range(1, 9) for sg in (1, -1)]:
                a = out + off
                ex = hx * abs(math.cos(a)) + hy * abs(math.sin(a))
                d = ex + VIA_R + 0.02 + dist
                x, y = cx + d * math.cos(a), cy + d * math.sin(a)
                if via_ok(x, y, p) and stub_ok((cx, cy), (x, y), side, p):
                    best = (x, y)
                    break
            if best:
                break
        if best is None:
            missed.append(f"{ref}.{p.GetNumber()}")
            continue
        x, y = best
        vias.append((x, y, VIA_R, "GND"))
        tracks.append(((cx, cy), (x, y), STUB_W / 2, "GND", side))
        new_vias.append((x, y))
        new_stubs.append((side, cx, cy, x, y))
    json.dump({"vias": new_vias, "stubs": new_stubs}, open(PLAN, "w"))
    print(f"gndfan: {len(new_vias)} vias planned; no spot for: {' '.join(missed) or 'none'}")


def plan_mcu(pads, vias, tracks, via_ok, stub_ok):
    """U3 (LQFP-64) inward fanout: signal pins whose net has no other top-side pad within 4 mm get a stub toward the package
    centre and a via under the body (rows 0.45 mm and 1.25 mm inside the pad ends, alternating), so the router can leave the
    pin field on In2/B instead of squeezing every escape between the top-side support parts."""
    import pcbnew
    skip = {"GND", "3V3", "3V3A", "VCAP1", "VCAP2", ""}
    import pcbnew
    board = pads[0][4].GetParent().GetBoard()
    imu_keep = []      # keep fanout vias 0.8 mm outside the IMU courtyards so their own pads can still escape
    for ref in ("U6", "U7"):
        fp = board.FindFootprintByReference(ref)
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd).BBox()
        imu_keep.append([pcbnew.ToMM(bb.GetLeft()) - OX - 0.8, pcbnew.ToMM(bb.GetTop()) - OY - 0.8,
                         pcbnew.ToMM(bb.GetRight()) - OX + 0.8, pcbnew.ToMM(bb.GetBottom()) - OY + 0.8])
    u3 = [(r, net, lay, ref, p) for r, net, lay, ref, p in pads if ref == "U3"]
    cx, cy = 17.0, 17.5
    new_vias, new_stubs, done, missed = [], [], [], []
    for r, net, lay, ref, p in sorted(u3, key=lambda t: int(t[4].GetNumber())):
        if net in skip or net.startswith("unconnected-"):
            continue
        px, py = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        near = [q for q in pads if q[1] == net and q[3] != "U3" and "F" in q[2]
                and math.hypot((q[0][0] + q[0][2]) / 2 - px, (q[0][1] + q[0][3]) / 2 - py) < 4.0]
        if near:
            continue
        horiz = (r[2] - r[0]) > (r[3] - r[1])          # pad long axis along x: left/right side
        if horiz:
            ux, uy = (1.0 if px < cx else -1.0), 0.0
            end = (r[2] if px < cx else r[0], py)
        else:
            ux, uy = 0.0, (1.0 if py < cy else -1.0)
            end = (px, r[3] if py < cy else r[1])
        num = int(p.GetNumber())
        rows = (0.45, 1.25) if num % 2 else (1.25, 0.45)
        best = None
        for d in rows + (2.05, 2.85, 3.65):
            for lat in (0.0, 0.25, -0.25, 0.5, -0.5):
                x, y = end[0] + ux * d + uy * lat, end[1] + uy * d + ux * lat
                knee = (end[0] + ux * (d - 0.3), end[1] + uy * (d - 0.3))
                if any(rect_dist(x, y, k) < VIA_R for k in imu_keep):
                    continue
                if lat == 0.0:
                    ok = via_ok(x, y, p) and stub_ok((px, py), (x, y), "F", p)
                else:
                    ok = via_ok(x, y, p) and stub_ok((px, py), knee, "F", p) and stub_ok(knee, (x, y), "F", p)
                if ok:
                    best = (x, y, None if lat == 0.0 else knee)
                    break
            if best:
                break
        if best is None:
            missed.append(f"U3.{num}({net})")
            continue
        x, y, knee = best
        pts = [(px, py)] + ([knee] if knee else []) + [(x, y)]
        vias.append((x, y, VIA_R, net))
        new_vias.append((x, y, net))
        for a0, b0 in zip(pts, pts[1:]):
            tracks.append((a0, b0, 0.127 / 2, net, "F"))
            new_stubs.append(("F", a0[0], a0[1], b0[0], b0[1], net))
    json.dump({"vias": new_vias, "stubs": new_stubs}, open(PLAN, "w"))
    print(f"mcufan: {len(new_vias)} pins fanned in; no spot: {' '.join(missed) or 'none'}")


def apply(kind):
    import pcbnew
    board = pcbnew.LoadBoard(PCB)
    d = json.load(open(PLAN))
    gnd = board.FindNet("GND")

    def pt(x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
    if kind == "stubs":
        for st in d["stubs"]:
            side, ax, ay, bx, by = st[:5]
            net = board.FindNet(st[5]) if len(st) > 5 else gnd
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pt(ax, ay)); t.SetEnd(pt(bx, by)); t.SetWidth(pcbnew.FromMM(STUB_W if len(st) == 5 else 0.127))
            t.SetLayer(pcbnew.F_Cu if side == "F" else pcbnew.B_Cu); t.SetNet(net); t.SetLocked(True)
            board.Add(t)
    else:
        for vv in d["vias"]:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pt(vv[0], vv[1])); v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetNet(board.FindNet(vv[2]) if len(vv) > 2 else gnd); v.SetLocked(True)
            board.Add(v)
    board.Save(PCB)
    print("gndfan", kind, "added")


def main():
    if "--plan" in sys.argv:
        return plan()
    if "--apply" in sys.argv:
        return apply(sys.argv[sys.argv.index("--apply") + 1])
    me = os.path.abspath(__file__)
    subprocess.run([sys.executable, me, "--plan"], check=True)
    subprocess.run([sys.executable, me, "--apply", "stubs"], check=True)
    subprocess.run([sys.executable, me, "--apply", "vias"], check=True)


if __name__ == "__main__":
    main()
