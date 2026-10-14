"""Placement constraint check (Gate 3): every critical part must sit within a max distance of the pin it serves.

kc 'python3 gen/placecheck.py'  -> prints each constraint and exits 1 on any violation.
Constraint: (ref_a, net, ref_b, max_mm): the closest pad of ref_a on `net` to the closest pad of ref_b on `net`.
Different sides (top/bottom) are allowed (a via joins them) but reported.
"""
import math
import sys

import pcbnew

# Limits: hot-loop caps <= 2-2.5 mm; second/third bulk caps further; DC nodes (EN) up to 6-7 mm.
# Limits are pad-centre to pad-centre; 2.1 mm for the BST/input caps is the courtyard-limited minimum for an
# 0402/0603 beside the HSOIC-8 courtyard (D-19).
C = [
    # 5 V buck U1: input caps to VIN/GND, boot, FB, RT, SW -> inductor
    ("C4", "VBAT", "U1", 2.1), ("C4", "GND", "U1", 3.0), ("C2", "VBAT", "U1", 4.5), ("C3", "VBAT", "U1", 6.0),
    ("C5", "BST_5V", "U1", 2.1), ("C5", "SW_5V", "U1", 2.5), ("R5", "FB_5V", "U1", 2.5), ("R4", "FB_5V", "U1", 3.1),
    ("R3", "RT_5V", "U1", 2.5), ("R2", "EN_5V", "U1", 6.0), ("L1", "SW_5V", "U1", 4.5),
    ("C6", "5V", "L1", 4.0), ("C7", "5V", "L1", 5.5), ("C8", "5V", "L1", 7.5),
    # 10 V buck U2
    ("C12", "VBAT", "U2", 2.1), ("C12", "GND", "U2", 3.0), ("C10", "VBAT", "U2", 4.6), ("C11", "VBAT", "U2", 6.0),
    ("C13", "BST_10V", "U2", 2.1), ("C13", "SW_10V", "U2", 2.5), ("R10", "FB_10V", "U2", 2.5), ("R9", "FB_10V", "U2", 3.3),
    ("R8", "RT_10V", "U2", 2.5), ("R7", "EN_10V", "U2", 7.5), ("Q2", "EN_10V", "U2", 7.5), ("L2", "SW_10V", "U2", 4.5),
    ("C14", "10V", "L2", 4.0), ("C15", "10V", "L2", 6.5), ("C16", "10V", "L2", 7.5),
    # battery entry
    ("D1", "VBAT", "P1", 6.0), ("C1", "VBAT", "P1", 6.0), ("D1", "GND", "P2", 6.0),
    # LDOs
    ("C20", "3V3", "U4", 2.5), ("C19", "5V_SYS", "U4", 3.0), ("C22", "5V_SYS", "U5", 2.1), ("C23", "3V3_IMU", "U5", 3.2),
    # MCU decoupling (top) and crystal
    ("C25", "3V3", "U3", 3.4), ("C26", "3V3", "U3", 3.5), ("C27", "3V3", "U3", 3.6), ("C28", "3V3", "U3", 4.1),
    ("C33", "VCAP1", "U3", 3.0), ("C34", "VCAP2", "U3", 4.5), ("C32", "3V3A", "U3", 3.0), ("C31", "3V3A", "U3", 4.0),
    ("C30", "3V3", "U3", 3.4), ("Y1", "HSE_IN", "U3", 5.0), ("Y1", "HSE_OUT", "U3", 5.0), ("C35", "NRST", "U3", 3.5),
    ("C36", "HSE_IN", "Y1", 2.5), ("C37", "HSE_OUT", "Y1", 3.5),   # load caps at the crystal (Gate 4 G4-01)
    # IMUs
    ("C38", "3V3_IMU", "U6", 2.0), ("C39", "3V3_IMU", "U6", 3.5), ("C40", "3V3_IMU", "U6", 2.5),
    ("C41", "3V3_IMU", "U7", 2.0), ("C42", "3V3_IMU", "U7", 2.5),
    # other ICs
    ("C48", "3V3", "U10", 3.0), ("C49", "3V3", "U11", 3.0), ("C50", "5V", "U12", 3.0), ("C46", "3V3", "U9", 2.5),
    ("C45", "MAG_C1", "U9", 2.5), ("C43", "3V3", "U8", 2.5),
    # ADC filters near MCU, USB ESD near connector
    ("C24", "VBAT_ADC", "U3", 6.0), ("C52", "CURR_ADC", "U3", 6.0), ("C53", "RSSI_ADC", "R39", 1.5),
    ("U13", "USB_DP", "J1", 6.0), ("U13", "USB_DM", "J1", 6.0),
]


def pads(fp, net):
    return [p for p in fp.Pads() if p.GetNetname() == net]


def main():
    b = pcbnew.LoadBoard("/work/kicad/F405FC.kicad_pcb")
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    bad = 0
    for ra, net, rb, mx in C:
        pa, pb = pads(fps[ra], net), pads(fps[rb], net)
        if not pa or not pb:
            print(f"?? {ra}/{rb} no pads on {net}")
            bad += 1
            continue
        d = min(math.hypot(pcbnew.ToMM(x.GetPosition().x - y.GetPosition().x), pcbnew.ToMM(x.GetPosition().y - y.GetPosition().y))
                for x in pa for y in pb)
        side = "" if fps[ra].IsFlipped() == fps[rb].IsFlipped() else " (other side, via)"
        ok = d <= mx
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {ra:>4} -> {rb:<4} {net:<10} {d:5.2f} mm (max {mx}){side}")
    print("placecheck:", "PASS" if not bad else f"FAIL ({bad})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
