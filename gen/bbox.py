"""Courtyard bboxes in board mm: kc 'python3 gen/bbox.py [B|T] [x0 y0 x1 y1]' lists footprints on that side within the window."""
import sys
import pcbnew
b = pcbnew.LoadBoard("/work/kicad/F405FC.kicad_pcb")
side = sys.argv[1] if len(sys.argv) > 1 else "B"
win = [float(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [0, 0, 36, 36]
for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    s = "B" if fp.IsFlipped() else "T"
    if s != side:
        continue
    poly = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    bb = poly.BBox() if poly.OutlineCount() else fp.GetBoundingBox(False)
    x0, y0, x1, y1 = (pcbnew.ToMM(bb.GetLeft()) - 100, pcbnew.ToMM(bb.GetTop()) - 100,
                      pcbnew.ToMM(bb.GetRight()) - 100, pcbnew.ToMM(bb.GetBottom()) - 100)
    if x1 < win[0] or x0 > win[2] or y1 < win[1] or y0 > win[3]:
        continue
    p = fp.GetPosition()
    print(f"{fp.GetReference():5} {fp.GetValue()[:10]:10} c=({pcbnew.ToMM(p.x)-100:5.2f},{pcbnew.ToMM(p.y)-100:5.2f}) r{fp.GetOrientationDegrees():4.0f} "
          f"crt x {x0:5.2f}..{x1:5.2f} y {y0:5.2f}..{y1:5.2f}")
