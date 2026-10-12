"""Print board-coordinate pad positions (origin = board corner) for refs: kc 'python3 gen/padpos.py U1 U2'"""
import sys
import pcbnew
b = pcbnew.LoadBoard("/work/kicad/F405FC.kicad_pcb")
for ref in sys.argv[1:]:
    fp = b.FindFootprintByReference(ref)
    side = "B" if fp.IsFlipped() else "T"
    p0 = fp.GetPosition()
    print(f"{ref} {side} at ({pcbnew.ToMM(p0.x)-100:.2f},{pcbnew.ToMM(p0.y)-100:.2f}) rot {fp.GetOrientationDegrees():.0f}")
    seen = set()
    for p in fp.Pads():
        if not p.GetNumber() or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNumber() in seen:
            continue
        seen.add(p.GetNumber())
        q = p.GetPosition()
        print(f"   pad {p.GetNumber():>3} {p.GetNetname():<14} ({pcbnew.ToMM(q.x)-100:6.2f},{pcbnew.ToMM(q.y)-100:6.2f})")
