#!/usr/bin/env python3
"""Generate the F405-FC custom footprint library (lib/F405FC.pretty).

Plain Python (no pcbnew needed); output is deterministic (no UUIDs, no
timestamps), so re-running produces byte-identical files.

    python3 gen/footprints.py [output_dir]

Dimension sources (see review/footprint_build_notes.md):
  * BMP390   : BMP390_DS.pdf rev 1.7, p.46 (pin-out), p.49 (7.1 outline, 7.2 landing pattern)
  * BMI270   : BMI270_DS.pdf, p.134 (pin-out), p.143 (8.1 outline), p.145 (8.3 landing pattern)
  * LMR38020 : lmr38020.pdf p.37 (DDA0008B outline), p.38 (example board layout), p.39 (stencil)
  * solder pads: project-defined sizes (design/circuit.py FP map)
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "lib", "F405FC.pretty")

VERSION = 20260206          # KiCad 10 footprint file format
SILK_W = 0.12
FAB_W = 0.10
CRT_W = 0.05
CRT_CLEAR = 0.25            # courtyard clearance around body/pads
SILK_PAD_CLEAR = 0.2        # min silk-to-copper distance


def f(v):
    """Format a number: fixed 4 decimals max, no trailing zeros, no -0."""
    v = round(float(v), 4)
    if v == 0:
        v = 0.0
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def grid(v, g=0.01, up=True):
    """Round a courtyard coordinate outward onto a 0.01 mm grid."""
    n = v / g
    n = math.ceil(n - 1e-9) if up else math.floor(n + 1e-9)
    return round(n * g, 4)


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


class FP:
    def __init__(self, name, descr, tags, attrs=("smd",)):
        self.name, self.descr, self.tags, self.attrs = name, descr, tags, attrs
        self.items = []
        self.pads = []
        self.ref_at = (0, -2)
        self.val_at = (0, 2)
        self.fab_text_size = 0.5

    # graphics -------------------------------------------------------
    def line(self, x1, y1, x2, y2, layer, w):
        self.items.append(
            f"\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n"
            f"\t\t(stroke\n\t\t\t(width {f(w)})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer {q(layer)})\n\t)")

    def rect(self, x1, y1, x2, y2, layer, w, fill=False):
        self.items.append(
            f"\t(fp_rect\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n"
            f"\t\t(stroke\n\t\t\t(width {f(w)})\n\t\t\t(type solid)\n\t\t)\n"
            f"\t\t(fill {'yes' if fill else 'no'})\n\t\t(layer {q(layer)})\n\t)")

    def poly(self, pts, layer, w, fill=False):
        xy = "\n".join(f"\t\t\t(xy {f(x)} {f(y)})" for x, y in pts)
        self.items.append(
            f"\t(fp_poly\n\t\t(pts\n{xy}\n\t\t)\n"
            f"\t\t(stroke\n\t\t\t(width {f(w)})\n\t\t\t(type solid)\n\t\t)\n"
            f"\t\t(fill {'yes' if fill else 'no'})\n\t\t(layer {q(layer)})\n\t)")

    def circle(self, cx, cy, r, layer, w, fill=False):
        self.items.append(
            f"\t(fp_circle\n\t\t(center {f(cx)} {f(cy)})\n\t\t(end {f(cx + r)} {f(cy)})\n"
            f"\t\t(stroke\n\t\t\t(width {f(w)})\n\t\t\t(type solid)\n\t\t)\n"
            f"\t\t(fill {'yes' if fill else 'no'})\n\t\t(layer {q(layer)})\n\t)")

    def courtyard(self, x1, y1, x2, y2):
        self.rect(grid(x1, up=False), grid(y1, up=False), grid(x2), grid(y2), "F.CrtYd", CRT_W)

    def fab_body(self, w, h, chamfer, corner="tl"):
        """Body outline on F.Fab with a pin-1 chamfer at the given corner."""
        x, y, c = w / 2, h / 2, chamfer
        if corner == "tl":
            pts = [(-x + c, -y), (x, -y), (x, y), (-x, y), (-x, -y + c)]
        elif corner == "tr":
            pts = [(-x, -y), (x - c, -y), (x, -y + c), (x, y), (-x, y)]
        else:
            raise ValueError(corner)
        self.poly(pts, "F.Fab", FAB_W)

    # pads -----------------------------------------------------------
    def pad(self, num, x, y, w, h, shape="rect", layers=("F.Cu", "F.Mask", "F.Paste"),
            kind="smd", rratio=None, drill=None, mask_margin=None, extra=()):
        s = f"\t(pad {q(num)} {kind} {shape}\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(w)} {f(h)})\n"
        if drill is not None:
            s += f"\t\t(drill {f(drill)})\n"
        s += "\t\t(layers " + " ".join(q(l) for l in layers) + ")\n"
        if kind == "thru_hole":
            s += "\t\t(remove_unused_layers no)\n"
        if rratio is not None:
            s += f"\t\t(roundrect_rratio {f(rratio)})\n"
        if mask_margin is not None:
            s += f"\t\t(solder_mask_margin {f(mask_margin)})\n"
        for e in extra:
            s += f"\t\t{e}\n"
        s += "\t)"
        self.pads.append(s)

    # output ---------------------------------------------------------
    def text(self):
        def prop(name, value, at, layer, hide=False, size=1.0, th=0.15):
            h = "\t\t(hide yes)\n" if hide else ""
            return (f"\t(property {q(name)} {q(value)}\n\t\t(at {f(at[0])} {f(at[1])} 0)\n"
                    f"\t\t(layer {q(layer)})\n{h}\t\t(effects\n\t\t\t(font\n"
                    f"\t\t\t\t(size {f(size)} {f(size)})\n\t\t\t\t(thickness {f(th)})\n\t\t\t)\n\t\t)\n\t)")
        out = [f"(footprint {q(self.name)}",
               f"\t(version {VERSION})",
               '\t(generator "F405FC_footprints_py")',
               '\t(layer "F.Cu")',
               f"\t(descr {q(self.descr)})",
               f"\t(tags {q(self.tags)})",
               prop("Reference", "REF**", self.ref_at, "F.SilkS"),
               prop("Value", self.name, self.val_at, "F.Fab"),
               prop("Datasheet", "", (0, 0), "F.Fab", hide=True),
               prop("Description", self.descr, (0, 0), "F.Fab", hide=True),
               "\t(attr " + " ".join(self.attrs) + ")"]
        out += self.items
        ts = self.fab_text_size
        out.append(f'\t(fp_text user "${{REFERENCE}}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n'
                   f"\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(ts)} {f(ts)})\n"
                   f"\t\t\t\t(thickness {f(ts * 0.15)})\n\t\t\t)\n\t\t)\n\t)")
        out += self.pads
        out.append(")")
        return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# 1. BMP390, Bosch LGA-10 2.0x2.0x0.75, P0.5
#    BMP390_DS rev1.7 p.49 Fig.26 bottom view: side pads 0.275 (x) x 0.250 (y), 6x,
#    centres 1.525 apart, rows 0.5 apart; top/bottom pads 0.250 (x) x 0.275 (y), 4x,
#    0.500 apart; all pads 0.100 from the package edge. 7.2: land pattern = pad
#    outline 1:1. Pin numbers from p.46 Fig.23 TOP view (pin 1 = VDDIO top edge,
#    right of centre; counter-clockwise seen from top). Vent hole Ø0.25 at 0.6/0.6
#    from the pin-1 corner (top view).
# ---------------------------------------------------------------------------
def bmp390():
    name = "Bosch_LGA-10_2x2mm_P0.5mm_BMP390"
    fp = FP(name,
            "Bosch BMP390 LGA-10 2.0x2.0x0.75mm, 0.5mm pitch, land pattern 1:1 per "
            "BMP390 datasheet BST-BMP390-DS002-07 rev1.7 sec 7.1/7.2 (p.49); "
            "pin numbering per Fig.23 top view (p.46). Keep vent hole unobstructed.",
            "Bosch BMP390 LGA-10 pressure sensor")
    body = 2.0
    e = 0.1                       # pad-to-package-edge
    sx, sy = 0.275, 0.250         # side pads (cols)
    tx, ty = 0.250, 0.275         # top/bottom pads
    cx = body / 2 - e - sx / 2    # 0.7625  (2*cx = 1.525 per drawing)
    cy = body / 2 - e - ty / 2    # 0.7625
    pads = {
        1: (0.25, -cy, tx, ty), 2: (-0.25, -cy, tx, ty),
        3: (-cx, -0.5, sx, sy), 4: (-cx, 0.0, sx, sy), 5: (-cx, 0.5, sx, sy),
        6: (-0.25, cy, tx, ty), 7: (0.25, cy, tx, ty),
        8: (cx, 0.5, sx, sy), 9: (cx, 0.0, sx, sy), 10: (cx, -0.5, sx, sy),
    }
    for n in sorted(pads):
        x, y, w, h = pads[n]
        fp.pad(str(n), x, y, w, h)
    b = body / 2
    # fab: body with chamfer at the pin-1 (top-right) corner + vent hole
    fp.fab_body(body, body, 0.3, corner="tr")
    fp.circle(0.4, -0.4, 0.125, "F.Fab", FAB_W)
    # silk: corner brackets just outside body
    s = b + 0.11
    L = 0.3
    for sxn in (-1, 1):
        for syn in (-1, 1):
            fp.line(sxn * s, syn * s, sxn * (s - L), syn * s, "F.SilkS", SILK_W)
            fp.line(sxn * s, syn * s, sxn * s, syn * (s - L), "F.SilkS", SILK_W)
    # pin-1 marker: filled triangle outside the top-right corner, pointing at pin 1
    fp.poly([(0.25, -1.2), (0.1, -1.42), (0.4, -1.42)], "F.SilkS", SILK_W, fill=True)
    fp.courtyard(-b - CRT_CLEAR, -b - CRT_CLEAR, b + CRT_CLEAR, b + CRT_CLEAR)
    fp.ref_at, fp.val_at = (0, -2.2), (0, 2.2)
    fp.fab_text_size = 0.4
    return fp


# ---------------------------------------------------------------------------
# 3. BMI270, Bosch LGA-14 3.0x2.5x0.83, P0.5
#    BMI270_DS p.145 sec 8.3 landing pattern: pads 0.475 x 0.25, side pads inner
#    edge 0.925 from centre (=> centre x 1.1625, outer edge 1.4 = 0.1 inside body),
#    top/bottom pads inner edge 0.675 from centre (=> centre y 0.9125); same as the
#    package pads on p.143. Pin-out p.134 top view.
# ---------------------------------------------------------------------------
def bmi270():
    name = "Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270"
    fp = FP(name,
            "Bosch BMI270 LGA-14 3.0x2.5x0.83mm, 0.5mm pitch, landing pattern per "
            "BMI270 datasheet BST-BMI270-DS000-08 sec 8.3 (p.145), outline sec 8.1 (p.143), "
            "pin-out sec 7.1 (p.134)",
            "Bosch BMI270 LGA-14 IMU")
    W, H = 3.0, 2.5
    L, Wd = 0.475, 0.25
    cx = 0.925 + L / 2            # 1.1625
    cy = 0.675 + L / 2            # 0.9125
    pads = {}
    for i, y in enumerate((-0.75, -0.25, 0.25, 0.75)):
        pads[1 + i] = (-cx, y, L, Wd)            # 1..4 left, top->bottom
        pads[11 - i] = (cx, y, L, Wd)            # 11..8 right, top->bottom
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        pads[5 + i] = (x, cy, Wd, L)             # 5..7 bottom, left->right
        pads[14 - i] = (x, -cy, Wd, L)           # 14..12 top, left->right
    for n in sorted(pads):
        x, y, w, h = pads[n]
        fp.pad(str(n), x, y, w, h)
    bx, by = W / 2, H / 2
    fp.fab_body(W, H, 0.4, corner="tl")
    s_x, s_y = bx + 0.11, by + 0.11
    Ls = 0.35
    for sxn in (-1, 1):
        for syn in (-1, 1):
            fp.line(sxn * s_x, syn * s_y, sxn * (s_x - Ls), syn * s_y, "F.SilkS", SILK_W)
            fp.line(sxn * s_x, syn * s_y, sxn * s_x, syn * (s_y - Ls), "F.SilkS", SILK_W)
    # pin-1 marker: filled triangle left of pin 1, pointing right
    fp.poly([(-1.68, -0.75), (-1.9, -0.9), (-1.9, -0.6)], "F.SilkS", SILK_W, fill=True)
    fp.courtyard(-bx - CRT_CLEAR, -by - CRT_CLEAR, bx + CRT_CLEAR, by + CRT_CLEAR)
    fp.ref_at, fp.val_at = (0, -2.3), (0, 2.3)
    fp.fab_text_size = 0.6
    return fp


# ---------------------------------------------------------------------------
# 5. LMR38020 DDA (DDA0008B PowerPAD SOIC-8), TI example board layout p.38:
#    signal pads 8x 1.55 x 0.6 R0.05, row centres 5.4 apart, pitch 1.27;
#    thermal pad metal 2.95 x 4.9 (solder-mask defined), mask opening 2.71 x 3.4;
#    8 thermal vias on TI's 1.3 mm grid, enlarged to 0.3 drill / 0.6 pad to meet the board via rule (0.3/0.6); stencil p.39: 2.71 x 3.4 @0.125 mm.
#    Package p.37: body 3.9 x 4.9 (nom), EP 2.11-2.71 x 2.8-3.4.
# ---------------------------------------------------------------------------
def lmr_dda():
    name = "TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA"
    fp = FP(name,
            "TI DDA0008B PowerPAD SOIC-8 (HSOIC-8) 3.9x4.9mm, P1.27mm, per TI example board "
            "layout (lmr38020.pdf p.37-39): 1.55x0.6 pads, thermal metal 2.95x4.9mm "
            "solder-mask-defined opening 2.71x3.4mm, paste in 3 windows clear of the vias (~45 %), "
            "8x 0.3/0.6mm thermal vias on TI's 1.3mm grid, solid zone connection",
            "TI DDA0008B HSOIC PowerPAD SO-8 LMR38020 thermal vias")
    pw, ph, rx, p = 1.55, 0.6, 2.7, 1.27
    ys = [-1.5 * p, -0.5 * p, 0.5 * p, 1.5 * p]
    for i, y in enumerate(ys):
        fp.pad(str(1 + i), -rx, y, pw, ph, shape="roundrect", rratio=round(0.05 / ph, 4))
        fp.pad(str(8 - i), rx, y, pw, ph, shape="roundrect", rratio=round(0.05 / ph, 4))
    # thermal pad: mask-defined opening + paste 2.71x3.4 on top of 2.95x4.9 metal
    solid = ("(zone_connect 2)",)  # solid to the GND pours: the vias are the only heat path (Gate 2 G2F-04)
    fp.pad("9", 0, 0, 2.71, 3.4, layers=("F.Cu", "F.Mask"), extra=solid)
    fp.pad("9", 0, 0, 2.95, 4.9, layers=("F.Cu",), extra=solid)
    # paste in three windows clear of the four inner vias at (+-0.65, +-0.65), so solder does not wick through
    # them (TI note 10; Gate 2 G2F-03): centre strip x +-0.25 and two outer strips x 1.0..1.355 => ~45 % coverage
    fp.pad("", 0, 0, 0.5, 3.4, layers=("F.Paste",))
    fp.pad("", -1.1775, 0, 0.355, 3.4, layers=("F.Paste",))
    fp.pad("", 1.1775, 0, 0.355, 3.4, layers=("F.Paste",))
    # (no opposite-side copy: this IC is mounted on the bottom of a dense board; the 8 vias reach the inner GND planes)
    for x in (-0.65, 0.65):
        for y in (-1.95, -0.65, 0.65, 1.95):
            fp.pad("9", x, y, 0.6, 0.6, shape="circle", kind="thru_hole", drill=0.3,
                   layers=("*.Cu",), extra=solid)
    bw, bh = 3.9, 4.9
    bx, by = bw / 2, bh / 2
    fp.fab_body(bw, bh, 0.8, corner="tl")
    # silk: top/bottom body edges, top line extended to pad-1 outer edge (KLC style)
    sy = by + 0.11
    sx = bx + 0.11
    pad_top = ys[0] - ph / 2
    fp.line(-sx, -sy, sx, -sy, "F.SilkS", SILK_W)
    fp.line(-sx, sy, sx, sy, "F.SilkS", SILK_W)
    fp.line(-sx, -sy, -sx, pad_top - SILK_PAD_CLEAR, "F.SilkS", SILK_W)
    fp.line(sx, -sy, sx, pad_top - SILK_PAD_CLEAR, "F.SilkS", SILK_W)
    fp.line(-sx, sy, -sx, -pad_top + SILK_PAD_CLEAR, "F.SilkS", SILK_W)
    fp.line(sx, sy, sx, -pad_top + SILK_PAD_CLEAR, "F.SilkS", SILK_W)
    # pin-1 marker: filled triangle above pad 1
    x1 = -rx
    fp.poly([(x1, pad_top - 0.25), (x1 - 0.2, pad_top - 0.55), (x1 + 0.2, pad_top - 0.55)],
            "F.SilkS", SILK_W, fill=True)
    cx = max(rx + pw / 2, bx) + CRT_CLEAR
    cy = max(-ys[0] + ph / 2, by) + CRT_CLEAR
    fp.courtyard(-cx, -cy, cx, cy)
    fp.ref_at, fp.val_at = (0, -3.4), (0, 3.4)
    fp.fab_text_size = 0.8
    return fp


# ---------------------------------------------------------------------------
# 4. Solder pads (battery, 10V, motor, UART/video signal). Single SMD pad "1",
#    rounded rect, paste included (pre-tinning), mask opening = copper.
# ---------------------------------------------------------------------------
def solder_pad(w, h):
    name = f"Pad_SMD_{w:.1f}x{h:.1f}mm"
    fp = FP(name,
            f"Single SMD solder/wire pad {w:.1f}x{h:.1f}mm, rounded rectangle, paste for "
            "pre-tinning, solder mask opening = copper (0 margin)",
            "solder pad wire pad SMD",
            attrs=("smd", "exclude_from_pos_files", "exclude_from_bom"))
    r = min(0.25, round(0.25 / min(w, h), 4))     # ~0.25 mm corner radius
    fp.pad("1", 0, 0, w, h, shape="roundrect", rratio=r, mask_margin=0)
    x, y = w / 2, h / 2
    fp.rect(-x, -y, x, y, "F.Fab", FAB_W)
    so = SILK_PAD_CLEAR + SILK_W / 2
    # no silk ring: the mask opening marks the pad, and a ring struck through the function labels (Gate 5 m-3)
    c = max(CRT_CLEAR, so + SILK_W / 2 + 0.05)    # keep the silk ring inside the courtyard
    fp.courtyard(-x - c, -y - c, x + c, y + c)
    fp.ref_at, fp.val_at = (0, -y - 0.9), (0, y + 0.9)
    fp.fab_text_size = min(0.8, round(min(w, h) * 0.35, 2))
    return fp


def all_footprints():
    fps = [bmp390(), bmi270(), lmr_dda()]
    for w, h in ((2.5, 4.0), (2.0, 3.0), (1.5, 2.0), (1.2, 1.6)):
        fps.append(solder_pad(w, h))
    return fps


GROMMET_HOLE = """(footprint "MountingHole_3.2mm_M3_Grommet4.6mm"
	(version 20260206)
	(generator "f405fc_footprints")
	(layer "F.Cu")
	(descr "M3 mounting hole 3.2 mm NPTH for soft-mount grommets: 4.6 mm diameter keepout (requirements.md), no tracks/vias inside")
	(tags "mountinghole M3 grommet")
	(property "Reference" "REF**" (at 0 0 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))
	(property "Value" "M3 grommet" (at 0 2.9 0) (layer "F.Fab") (hide yes) (effects (font (size 0.6 0.6) (thickness 0.1))))
	(attr exclude_from_pos_files exclude_from_bom)
	(fp_circle (center 0 0) (end 2.3 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
	(fp_circle (center 0 0) (end 2.3 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))
	(fp_circle (center 0 0) (end 2.3 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
	(pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask"))
	(embedded_fonts no)
)
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    os.makedirs(out, exist_ok=True)
    for fp in all_footprints():
        path = os.path.join(out, fp.name + ".kicad_mod")
        with open(path, "w", newline="\n") as fh:
            fh.write(fp.text())
        print("wrote", path)
    with open(os.path.join(out, "MountingHole_3.2mm_M3_Grommet4.6mm.kicad_mod"), "w", newline="\n") as fh:
        fh.write(GROMMET_HOLE)


if __name__ == "__main__":
    main()
