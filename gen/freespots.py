"""List free spots for a w x h courtyard on a side: kc 'python3 gen/freespots.py B 4.0 3.5'"""
import sys
import pcbnew
sys.path.insert(0, "/work/gen")
import legalize as L
b = pcbnew.LoadBoard("/work/kicad/F405FC.kicad_pcb")
side, w, h = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
occ, pth = [], []
for fp in b.GetFootprints():
    s = "B" if fp.IsFlipped() else "T"
    if s == side and not fp.GetReference().startswith("H"):
        occ.append(L._bbox(fp, 100, 100))
    if s != side:
        pth += L._pth(fp, 100, 100)
spots = []
y = 0.0
while y < 36:
    x = 0.0
    while x < 36:
        bb = [x, y, x + w, y + h]
        if L._ok_board(bb, 36, 36) and not any(L._hit(bb, o) for o in occ) and not any(L._hit(bb, o, 0.15) for o in pth):
            spots.append((round(x + w / 2, 2), round(y + h / 2, 2)))
        x += 0.25
    y += 0.25
win = [float(v) for v in sys.argv[4:8]] if len(sys.argv) >= 8 else None   # optional x0 y0 x1 y1 window: list all spots in it
if win:
    spots = [s for s in spots if win[0] <= s[0] <= win[2] and win[1] <= s[1] <= win[3]]
    print(len(spots), "free centres in window:", spots)
else:
    print(len(spots), "free centres; sample:", spots[::max(1, len(spots) // 40)])
