"""Deterministic placement legalizer (used by gen/build_pcb.py stage 2).

Footprints listed in FIXED keep the position from design/placement.py. Every other footprint is moved to the
nearest free location (spiral search on a 0.1 mm grid, both 0/90 degree offsets tried) so that:
  * its courtyard does not overlap another courtyard on the same side (plus a small gap),
  * it stays inside the board outline (EDGE mm margin) and outside the mounting-hole keepouts,
  * it does not sit on top of plated through-holes (via-in-pad, connector posts) of footprints on the other side.
Moves are reported so placement.py can be updated when a move is large.
"""
import math

import pcbnew

EDGE = 0.25          # courtyard to board-edge margin
GAP = 0.05           # extra courtyard-to-courtyard gap
HOLE_KEEP_R = 2.3 + 0.2   # 4.6 mm grommet keepout diameter + margin
RING = 0.8
PTH_GAP = {"U1": 0.6, "U2": 0.6}   # Gate 3 G3R-01: top parts >= 0.6 mm from the buck thermal-via fields
HOLES = [(2.75, 2.75), (33.25, 2.75), (2.75, 33.25), (33.25, 33.25)]


def _bbox(fp, ox, oy):
    """Courtyard bbox in board mm (origin = board corner)."""
    side = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    poly = fp.GetCourtyard(side)
    bb = poly.BBox() if poly.OutlineCount() else fp.GetBoundingBox(False)
    return [pcbnew.ToMM(bb.GetLeft()) - ox, pcbnew.ToMM(bb.GetTop()) - oy,
            pcbnew.ToMM(bb.GetRight()) - ox, pcbnew.ToMM(bb.GetBottom()) - oy]


def _pth(fp, ox, oy):
    out = []
    for p in fp.Pads():
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            bb = p.GetBoundingBox()
            out.append([pcbnew.ToMM(bb.GetLeft()) - ox, pcbnew.ToMM(bb.GetTop()) - oy,
                        pcbnew.ToMM(bb.GetRight()) - ox, pcbnew.ToMM(bb.GetBottom()) - oy])
    return out


def _hit(a, b, g=GAP):
    return a[0] < b[2] + g and b[0] < a[2] + g and a[1] < b[3] + g and b[1] < a[3] + g


def _ok_board(b, w, h):
    if b[0] < EDGE or b[1] < EDGE or b[2] > w - EDGE or b[3] > h - EDGE:
        return False
    for hx, hy in HOLES:
        cx, cy = min(max(hx, b[0]), b[2]), min(max(hy, b[1]), b[3])
        if math.hypot(cx - hx, cy - hy) < HOLE_KEEP_R:
            return False
    return True


def legalize(board, fixed, ox, oy, w, h, priority=None, max_r=9.0, tight=None, tight_r=1.5, reserved=()):
    tight = set(tight or ())
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    placed = {"T": [], "B": []}
    pth = {"T": [], "B": []}       # PTH obstacles that block the given side
    for ref in fixed:
        fp = fps.get(ref)
        if fp is None:
            continue
        s = "B" if fp.IsFlipped() else "T"
        if not ref.startswith("H"):
            placed[s].append((ref, _bbox(fp, ox, oy)))
        for pb in _pth(fp, ox, oy):
            pth["T" if s == "B" else "B"].append((ref, pb))
    # Gate 3 G3R-10: keep a 1.2 mm routing ring clear around the MCU pad field for every top-side part that is not anchored
    mcu_ring = None
    if "U3" in fps:
        u = _bbox(fps["U3"], ox, oy)
        mcu_ring = [u[0] - RING, u[1] - RING, u[2] + RING, u[3] + RING]
    for side, rect in reserved:          # silk label areas next to the user-pad grids (Gate 3 G3-11)
        placed[side].append(("reserved", list(rect)))
    # scripted critical copper (gen/critical.py) is added after placement: keep the non-anchored parts off it
    # (anchored parts sit on it by design: the critical tracks end on their pads)
    crit = {"T": [], "B": []}
    try:
        import critical
        for net, x, y in critical.VIAS:            # through vias block both sides
            for sd in "TB":
                crit[sd].append([x - 0.3, y - 0.3, x + 0.3, y + 0.3])
        for layer, wdt, net, pts in critical.TRACKS:
            sd = {"F.Cu": "T", "B.Cu": "B"}.get(layer)
            if sd is None:
                continue
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(bx - ax, by - ay) / 0.3))
                for k in range(n + 1):
                    x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                    crit[sd].append([x - wdt / 2, y - wdt / 2, x + wdt / 2, y + wdt / 2])
    except ImportError:
        pass
    movable = [r for r in fps if r not in fixed]
    order = priority or {}
    movable.sort(key=lambda r: (-100 if r in tight else order.get(r, 0), -((lambda b: (b[2] - b[0]) * (b[3] - b[1]))(_bbox(fps[r], ox, oy))), r))
    moves = []
    for ref in movable:
        fp = fps[ref]
        s = "B" if fp.IsFlipped() else "T"
        pos0 = fp.GetPosition()
        rot0 = fp.GetOrientationDegrees()
        best = None
        for attempt in ((True, False) if ref in tight else (False,)):
          if best is not None:
              break
          for rot in ((rot0,) if attempt else (rot0, rot0 + 90)):
              fp.SetOrientationDegrees(rot % 360)
              b0 = _bbox(fp, ox, oy)
              step = 0.1
              for ring in range(0, int((tight_r if attempt else max_r) / step) + 1):
                  r = ring * step
                  if best is not None and r >= best[0]:
                      break
                  n = max(1, int(2 * math.pi * r / step)) if r else 1
                  for k in range(n):
                      a = 2 * math.pi * k / n
                      dx, dy = round(r * math.cos(a), 2), round(r * math.sin(a), 2)
                      b = [b0[0] + dx, b0[1] + dy, b0[2] + dx, b0[3] + dy]
                      if not _ok_board(b, w, h):
                          continue
                      if any(_hit(b, o) for _, o in placed[s]):
                          continue
                      if any(_hit(b, o, PTH_GAP.get(pr, 0.15)) for pr, o in pth[s]):
                          continue
                      if mcu_ring and s == "T" and ref not in tight and _hit(b, mcu_ring, 0.0):
                          continue
                      if ref not in tight:
                          core = [b[0] + 0.35, b[1] + 0.35, b[2] - 0.35, b[3] - 0.35]   # ~pad area: vias may sit under a body
                          if any(_hit(core, o, 0.15) for o in crit[s]):
                              continue
                      cost = r + (0.3 if rot != rot0 else 0)
                      if best is None or cost < best[0]:
                          best = (cost, dx, dy, rot % 360, b)
                      break
        if best is None:
            fp.SetOrientationDegrees(rot0)
            moves.append((ref, None))
            continue
        _, dx, dy, rot, b = best
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(pos0.x + pcbnew.FromMM(dx), pos0.y + pcbnew.FromMM(dy)))
        placed[s].append((ref, b))
        for pb in _pth(fp, ox, oy):
            pth["T" if s == "B" else "B"].append((ref, pb))
        if dx or dy or rot != rot0 % 360:
            moves.append((ref, (round(math.hypot(dx, dy), 2), rot)))
    return moves
