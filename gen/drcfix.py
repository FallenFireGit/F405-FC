"""Geometric repair of small clearance violations left by the grid router (run inside the KiCad chroot, after the board is built).

  kc 'python3 gen/drcfix.py [rounds]'

For every DRC clearance / hole_clearance violation that involves an unlocked router track or via:
  - power-class tracks (wider than 0.127 mm) are narrowed just enough (never below 0.127 mm), else
  - the track segment (or via) is moved away from the other item by the deficit + 0.01 mm, perpendicular to the segment; every
    other track end that sat on a moved end point moves with it, so connectivity is kept.
Then DRC runs again, up to [rounds] times. Locked items (critical routes, fanout) are never touched. Each round is one process
that only modifies existing items (no new board items: KiCad 10.0.6 SWIG quirk, see build_pcb._stage).
"""
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.environ.get("F405_PCB", os.path.join(ROOT, "kicad", "F405FC.kicad_pcb"))
DRC = "/tmp/drcfix.json"
MINW = 0.127


def run_drc():
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format", "json", "-o", DRC, PCB],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(DRC))
    return [v for v in d["violations"] if v["type"] in ("clearance", "hole_clearance")], d


def one_round():
    import pcbnew
    viol, _ = run_drc()
    if not viol:
        print("drcfix: clean")
        return 0
    board = pcbnew.LoadBoard(PCB)
    byid = {}
    for t in board.GetTracks():
        byid[t.m_Uuid.AsString()] = t
    for fp in board.GetFootprints():
        for p in fp.Pads():
            byid[p.m_Uuid.AsString()] = p
    for z in board.Zones():
        byid[z.m_Uuid.AsString()] = z

    def get(uuid):
        it = byid.get(uuid)
        return it.Cast() if it is not None else None

    def mm(v):
        return pcbnew.ToMM(v)
    fixed = 0
    moved_pts = []
    for v in viol:
        m = re.search(r"clearance ([0-9.]+) mm; actual ([0-9.]+) mm", v["description"])
        if not m:
            continue
        deficit = float(m.group(1)) - float(m.group(2)) + 0.01
        items = [get(i["uuid"]) for i in v["items"]]
        if any(it is None for it in items):
            continue
        movable = [it for it in items if it.GetClass() in ("PCB_TRACK", "PCB_VIA") and not it.IsLocked()]
        if not movable:
            continue
        it = movable[0]
        other = items[1] if items[0] is it else items[0]
        # narrow a power track first
        if it.GetClass() == "PCB_TRACK" and mm(it.GetWidth()) - 2 * deficit >= MINW:
            it.SetWidth(pcbnew.FromMM(mm(it.GetWidth()) - 2 * deficit))
            fixed += 1
            continue
        # direction away from the other item
        op = other.GetPosition() if other.GetClass() != "PCB_TRACK" else None
        if it.GetClass() == "PCB_VIA":
            p = it.GetPosition()
            if op is None:
                a, b = other.GetStart(), other.GetEnd()
                op = nearest(a, b, p)
            dx, dy = mm(p.x) - mm(op.x), mm(p.y) - mm(op.y)
            L = math.hypot(dx, dy) or 1.0
            sh = (dx / L * deficit, dy / L * deficit)
            old = (p.x, p.y)
            it.SetPosition(pcbnew.VECTOR2I(p.x + pcbnew.FromMM(sh[0]), p.y + pcbnew.FromMM(sh[1])))
            moved_pts.append((old, sh))
            fixed += 1
            continue
        a, b = it.GetStart(), it.GetEnd()
        mid = pcbnew.VECTOR2I((a.x + b.x) // 2, (a.y + b.y) // 2)
        if op is None:
            oa, ob = other.GetStart(), other.GetEnd()
            op = nearest(oa, ob, mid)
        sx, sy = mm(b.x) - mm(a.x), mm(b.y) - mm(a.y)
        L = math.hypot(sx, sy) or 1.0
        nx, ny = -sy / L, sx / L
        q = nearest(a, b, op)
        if (mm(q.x) - mm(op.x)) * nx + (mm(q.y) - mm(op.y)) * ny < 0:
            nx, ny = -nx, -ny
        sh = (nx * deficit, ny * deficit)
        for end, setter in ((a, it.SetStart), (b, it.SetEnd)):
            moved_pts.append(((end.x, end.y), sh))
            setter(pcbnew.VECTOR2I(end.x + pcbnew.FromMM(sh[0]), end.y + pcbnew.FromMM(sh[1])))
        fixed += 1
    # drag every other unlocked track end that sat on a moved point (keeps connectivity)
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.IsLocked():
            continue
        for get_p, set_p in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            p = get_p()
            for (ox, oy), sh in moved_pts:
                if abs(p.x - ox) <= 1000 and abs(p.y - oy) <= 1000:      # within 1 um
                    set_p(pcbnew.VECTOR2I(ox + pcbnew.FromMM(sh[0]), oy + pcbnew.FromMM(sh[1])))
                    break
    board.Save(PCB)
    print(f"drcfix: {len(viol)} clearance violations, {fixed} adjusted")
    return len(viol)


def nearest(a, b, p):
    import pcbnew
    dx, dy = b.x - a.x, b.y - a.y
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / L))
    return pcbnew.VECTOR2I(int(a.x + t * dx), int(a.y + t * dy))


if __name__ == "__main__":
    if "--round" in sys.argv:
        one_round()
    else:
        rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
        for _ in range(rounds):
            subprocess.run([sys.executable, os.path.abspath(__file__), "--round"], check=True)
        viol, d = run_drc()
        print(f"drcfix: {len(viol)} clearance violations remain")
