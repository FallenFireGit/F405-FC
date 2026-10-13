# Gate 3 re-review: PCB placement rev C (independent)

Board: `kicad/F405FC.kicad_pcb` at HEAD `c747eaa` (the board file is unmodified in the working tree; `gen/build_pcb.py` has an
uncommitted one-line change, see G3R-12). Reviewer: a fresh Gate 3 re-reviewer, 2026-10-12. Review only: nothing in design/, gen/, kicad/,
lib/ or bom/ was changed. Scratch scripts lived in `/tmp/g3r` inside the `kc` chroot.

**Verdict: FAIL.** 0 BLOCKER, 4 MAJOR (G3-11 still open, G3R-01, G3R-02, G3R-10), plus MINOR and INFO items. The power-stage rework (D-19) closes all three previous
BLOCKERs and nine of the eleven MAJOR/MINOR placement items, and I measured that myself. What blocks a pass is narrower:
silkscreen labels that still point at the wrong pads (camera 5 V and the 10 V VTX pad), top-side 0402 pads 0.36 mm from the open buck thermal
vias, a locked VBAT critical route that breaks power.md §5, and routability that is not demonstrated (a trial Freerouting run stalled at
72 unrouted). The first three are small, local fixes. If they are fixed and checked by measurement, the next
pass can be PASS WITH CONDITIONS (the conditions are listed at the end).

> **Scope note (added 2026-10-13):** everything here measures the board at `c747eaa`. While the trial route was running, the
> repository moved on (commits `f088aee` … `6216e29`: D-21 to D-23, labels and pad grids, VBAT In2 zone, U13 move, D7 removed, routing). None of those
> later changes were re-measured in this review. A Gate 3 close-out has to re-check the MAJORs against the current HEAD.

## Method (what I actually did)

1. **Dumped the board with pcbnew** (`/tmp/g3r/dump.py`). For every footprint I took side, position, rotation, courtyard bbox and each pad's net and position. I also dumped every
   track and via with net, layer and width, plus zones and rule areas. All coordinates are board mm, origin top-left, y down.
2. **`gen/placecheck.py`** reports PASS, 66 pad-pair checks, all within the limits. I spot-checked its numbers against the dump: C4/C12, C5/C13, L1/L2 SW
   and the BST trace endpoints all match.
3. **`gen/drc_summary.py`** gives hole_clearance 4, copper_edge_clearance 8, via_dangling 9 (the locked GND stitching vias, with In1 not yet
   filled), silk_overlap 26, silk_over_copper 34, unconnected 327 and parity 0. `gen/drcpos.py` gave the positions.
4. **Custom checks.** I measured pad and courtyard distances to the 4 hole centres and the board edge (`holes.py`) and how close top-side pads sit to the U1/U2 thermal-via PTH pads (`pp.py`).
   For each silkscreen label I found the nearest connector pad (`silk.py`). I counted free via sites around the LQFP-64 (`via.py`/`pack.py`): a 0.6/0.3 via
   with 0.127 clearance, outside every other courtyard on both sides. I also checked via room for the buck EN pins (`pocket.py`).
5. **Trial route.** I ran Freerouting (`gen/route.py 20` with `F405_PCB` pointing at a copy in `/tmp/g3r/trial`) on a copy of the board. The result is in G3R-02.
6. **Power numbers.** I ran `python3 -I gen/power_calc_lmr.py` and redid the D-19 worst-case current-limit floors by hand.
7. **Images.** I viewed `docs/renders/placement_fab_bottom.png` and checked it against the dump. It predates the C5/C13 rotation, so
   I used coordinates for those two parts. I did not regenerate the renders.
8. **Not done / unverified.** No Würth 74438356056 or TDK C3225X7S2A475K200AB PDF is in `datasheets/`. Their heights come from D-19/D-20 and the BOM
   text. I could not parse the JST SH PDF (pdftotext font errors). For the USB4105 drawing, pdftotext shows the dimensions 3.31 and 3.50 but
   I did not confirm which one is the overall height. I re-derived no IMU axis mapping, since U6 and U7 are unchanged from rev B (B, rot 0). No thermal or EMI
   analysis.

## Key measurements (rev C)

| Item | Measured | Target | Result |
|---|---|---|---|
| U1 C4 (100 nF HF) VBAT pad (5.55,25.55) to VIN pin 3 (7.50,24.97); GND pad (5.55,27.10) to GND pin 1 (7.50,27.50) | 2.04 / 1.99 mm. The C4 pad edge is 0.69 mm from the pin pad edge (C4 x ≤ 6.03, pins x ≥ 6.72) | tight HF loop | PASS |
| U2 C12 VBAT (21.95,24.46) to pin 3 (23.90,23.97); GND (21.95,26.01) to pin 1 (23.90,26.50) | 2.01 / 2.01 mm | tight | PASS |
| Bulk input C2 / C3 (U1), C10 / C11 (U2) | 4.45 / 4.91, 4.51 / 4.49 mm | ≤ 4.5-6 | PASS |
| BST caps C5 / C13 to pins 7/8 | 1.71 / 1.71 mm; BST traces 0.3 mm, ≈ 1.7 mm long | < 2 mm | PASS |
| SW pin 8 to inductor SW pad | U1→L1 3.38 mm (track 0.8 mm, ≈ 3.5 mm long), U2→L2 4.30 mm (track 0.8 mm, 4.3 mm) | short | PASS |
| FB divider R5 / R10 to FB pin 5 | 1.96 / 1.74 mm, on the FB/PG side, ≥ 2.9 mm from the SW track | near FB, away from SW | PASS |
| RT R3 / R8 | 1.50 / 1.78 mm | near | PASS |
| Output caps 5 V (from L1.2 (15.78,30.85)) | C6 2.86, C8 3.34, C7 3.68, C9 (HF) 4.36 mm | ≤ 4-5 | PASS |
| Output caps 10 V (from L2.2 (27.01,30.80)) | C14 2.99, C17 (HF) ≈ 4.5, C16 5.31, C15 6.24 mm (C15 sits on the far side of the L2 SW pad) | ≤ 4-5 | PASS / MINOR |
| Top-side copper over the PowerPAD thermal vias (8 per IC, 0.3/0.6 mm PTH, open) | R22 0.36, R32 0.36, R38 0.42, C31 0.47 mm (pad edge to via pad edge) | keep clear (D-19 says "via fields block top-side parts") | **FAIL** (G3R-01) |
| IMU centroid (board centre 18,18) | U6 (15.40,17.00) 2.79 mm, U7 (20.80,17.00) 2.97 mm, both bottom | near centre | PASS |
| IMU to U1 / U2 / L1 / L2 centres | U6: 10.1 / 13.7 / 13.9 / 18.2 mm; U7: 13.3 / 9.6 / 15.4 / 15.6 mm | away from bucks | PASS |
| IMU decoupling | C38 1.40, C40 1.30, C41 1.40, C42 1.90 mm; U6/U7 courtyards 1.81 mm apart | ≤ 2 | PASS |
| Crystal | Y1 rot −90: HSE_OUT pad 3 (9.25,16.55) faces pin 6 (11.33,16.25), HSE_IN pad 1 (7.55,14.35) reaches pin 5 from above, so the traces do not cross. 4.03 / 2.10 mm, load caps C36 / C37 next to pads 1 / 3 | ≤ 5 mm, no crossing | PASS |
| MCU decoupling | C25 1.67, C26 1.74, C27 2.62, C28 2.68, C30 1.38 (B, via), C33 1.93, C34 1.94, C32 2.60, C31 3.41 mm | ≤ 3 | PASS |
| USB | J1 at x = 32.32 (GCT edge line now about 0.5 mm proud). U13 is between J1 and the MCU, 2.73 / 4.15 mm from the J1 D+/D− pads | at the connector | PASS (G3R-07) |
| Hole keepouts | Closest courtyard to a hole centre: D4 2.58 (H2), P1 2.58 (H3), U10 2.61 (H1), P25 2.66, L2 2.71 mm. Closest pad: P1 3.00 mm | ≥ 2.3 mm | PASS |
| Heights, bottom (2.5 mm) | L1/L2 2.1 max (D-19, not independently verified). C2/C3/C10/C11 2.0 nominal (TDK code 200; 2.2 max assumed). 22 uF CL31A226KAHNNNE code H 1.6 ± 0.2. SOT-223 U4 1.8 max. Tallest bottom part is ≤ 2.2 mm | ≤ 2.5 | PASS (vendor PDFs not in repo) |
| Heights, top (3.5 mm, USB-C exempt) | C1 CL32B106KBJNNNE 2.7 max. SW1 PTS810 2.5. D1 SMB 2.15 (KiCad model; Littelfuse max unverified). JST-SH ≈ 2.9 (not confirmed from PDF). LQFP 1.6 | ≤ 3.5 | PASS (partly unconfirmed) |
| Battery entry | P1/P2 (B) 3.4 mm apart at the bottom edge. D1 (T) pads sit over them through 2 + 2 vias (0.36 / 1.25 mm). C1 (T) 3.1 mm | adjacent | PASS |
| Mag U9 (T 9.55,7.70) | P3 10 V pad 26.6 mm, SW1 17.0 mm, D5 8.2 mm, R41 (10 V 0R) 13.0 mm, J3 VTX_PWR pin 11.25 mm | far from high current | PASS (with a routing condition) |
| D-19 current-limit floors | Hand calculation with L −20 %, f −20 % and −8 % SS (552 kHz), IHS,min 2.6 A at 25.2 V gives 5 V: dIL 1.645 A, so **1.78 A**; 10 V: dIL 2.446 A, so **1.38 A**. These match power.md §0/§2/§3. `gen/power_calc_lmr.py` does not compute them (G3R-08) | consistent | PASS / MINOR |

## Previous findings (review/gate-3-placement.md)

| ID | Sev. | Status | Evidence (rev C) |
|---|---|---|---|
| G3-01 | BLOCKER | **CLOSED** | L1/L2 are `L_Wuerth_MAPI-4020`, 74438356056, "2.1 mm max" (BOM line 28, D-19). Below the 2.5 mm limit by 0.4 mm. I did not see the height in a Würth PDF (none in the repo). |
| G3-02 | BLOCKER | **CLOSED** | U1 (B 10.20,25.60): C4 bridges VIN/GND on the left at 2.04/1.99 mm. C5 1.71 mm on the BST/SW side. R5 1.96 mm at FB. L1 SW 3.38 mm. The hot loop is entirely on B.Cu: VBAT track y = 24.97 and GND track y = 27.50, both 0.8 mm. |
| G3-03 | BLOCKER | **CLOSED** | U2: C12 2.01/2.01 mm, C13 1.71 mm, L2 rotated 180° (SW pad 4.30 mm, track 4.3 mm straight down x ≈ 29.3), R10 1.74 mm, R8 1.78 mm. R7/Q2 (EN) are 7.2/6.1 mm away. That is a DC node, accepted in D-19; see G3R-05. |
| G3-04 | MAJOR | **CLOSED** | Bottom input caps C2/C3/C10/C11 are C3225X7S2A475K200AB (2.0 mm). C1 (2.7 mm max) is now on top. Effective capacitance "≈ 7 uF per IC" is an unverified estimate (D-20); it belongs to Gate 0/2, not placement. |
| G3-05 | MAJOR | **CLOSED** (residual MINOR) | 5 V caps 2.86-4.36 mm and 10 V caps 2.99-6.24 mm from the L.2 pad. C15 sits on the far side of L2's SW pad (G3R-06). |
| G3-06 | MAJOR | **CLOSED** (residual MINOR) | U13 T (25.66,17.70), 2.73/4.15 mm from J1 D+/D−, between J1 and the MCU. Its flow-through axis is perpendicular to the path (G3R-07). |
| G3-07 | MAJOR | **CLOSED** (new MINOR) | C24 1.40, C52 1.57, C53 0.44 mm, all through a via. The clamp D7 (CURR_ADC) moved to (32.0,7.25), 23 mm from pin 9 (G3R-09). |
| G3-08 | MAJOR | **CLOSED** | IMU caps 1.30-1.90 mm. LP5907 input C22 1.91 mm, output C23 2.21 mm, now on the correct sides. |
| G3-09 | MAJOR | **CLOSED** | C20 2.40 mm from U4 VOUT. |
| G3-10 | MAJOR | **CLOSED** (routing condition) | Mag moved to (9.55,7.70). 10 V pads are now at the right edge (26.6 mm). SW1 is on top, 17 mm away. J3 VTX_PWR (connector unchanged) is 11.25 mm away and R41 13.0 mm. Condition: the L2 → R41/J3 10 V route stays on the right half with its GND return directly underneath. |
| G3-11 | MAJOR | **OPEN** | See below. Labels still sit on the wrong pads. |
| G3-12 | MAJOR | **CLOSED** (doc residue) | P1/P2 are adjacent and D1 straddles them. power.md §5 (line ~238) still says "top side", while the pads are on the bottom (B.Cu). The ≥ 1.5 mm VBAT copper rule from the same section is broken by the locked route (G3R-02). |
| G3-13 | MINOR | **OPEN** | `design/betaflight_config.txt:146,149` and `design/inav_target.md:41,47` still say CW0 (placeholder). `docs/assembly_and_bringup.md:92` quotes CW270FLIP / CW0FLIP. There is no forward arrow on the board (no forward-arrow text or graphic found in the board or generators). |
| G3-14 | MINOR | **CLOSED** | SW1 T (26.50,6.40) and D1 T (9.50,33.30) are now on top. |
| G3-15 | MINOR | **CLOSED** | C26 1.74, C28 2.68, C31 3.41, C50 1.60, C48 2.06 mm. |
| G3-16 | MINOR | **CLOSED** | Y1 rotated −90°. The pads face their pins and the traces do not cross. This is a geometric check; nothing is routed yet. |
| G3-17 | MINOR | **CLOSED** | J1 at x = 32.32. |
| G3-18 | MINOR | **OPEN** | 60 silk DRC items (34 silk_over_copper and 26 silk_overlap; previously 72). Examples: `LED` (24.33,21.10) on U3 pads 33/34 and R24; `5V` (28.88,21.11) on R33/C50; `RSSI` on D9 pad 2; `CLK` on D5 pad 2; `S5` on the J1 NPTH. |
| G3-19 | INFO | Superseded | Routability was trial-tested this time (G3R-10 and the Trial route section). |

### G3-11 (still OPEN, MAJOR): pad labels sit on the wrong or neighbouring pads

Evidence: `silk.py` lists each board silk text with its nearest connector pad on the same side. DRC confirms each overlap.
- **Bottom, camera/video block.** `C1` (3.49,14.60) is **0.44 mm from P8 = 5 V** and 1.89 mm from P5 = CAM1_VID. `C2` (3.64,12.30) is **0.34 mm from P7 =
  VTX_VID** and 2.09 mm from P6 = CAM2_VID. DRC reports `C1` silk_over_copper on P8 [5V] and `C2` on P7 [VTX_VID]. This is the same miswiring
  case G3-11 described: the "C1" camera lead lands on the 5 V pad and drives camera video or ground into 5 V, or the camera 5 V lead goes into
  the TS5A3159A. The pads are also irregular: P5 r180, P6 r90, P7 r180, P8 r90, with about 0.9 mm copper gaps for wire soldering.
- **Top, VTX power.** `10V` (31.90,23.00) is **2.03 mm from P11 = 5 V** and 2.30 mm from P3 = 10 V. Read with its nearest pad, the 10 V label
  marks the 5 V pad. A 5 V-only device soldered to "the other" pad then gets 10 V.
- **Bottom, right edge.** `T6` (32.31,13.00) sits on P20 = MOTOR6 (0.41 mm, DRC silk_over_copper), not on P17 = UART6_TX (2.09 mm). `R6`
  (32.31,15.20) is 1.99 mm from P19 = MOTOR5 and 2.09 mm from P18 = UART6_RX. The four pads form an irregular 2 x 2 group with no clean column:
  P20 (31.90,13.00), P17 (34.40,13.00), P18 (34.40,15.20), P19 (31.91,17.15).
- **Top, buzzer.** `BZ-` (12.38,27.75) is 1.10 mm from P13 = 5 V (BZ+) and 1.69 mm from P14 = BUZ_N. A user reading by proximity reverses the buzzer.
- **Bottom, test points.** `3V3` (13.16,12.36) sits on **TP5 = GND** (0.63 mm, DRC silk_over_copper) and is 1.53 mm from TP4 = 3V3. `RST`
  (14.40,10.12) is 1.43 mm from TP4 = 3V3 and 1.53 mm from TP3 = NRST. Someone powering the MCU through the "3V3" test point for SWD shorts the supply to GND.

Fix: place every pad label with a rule. The label's nearest pad must be its own pad, and the label must be ≥ 0.6 mm closer to it than to any other pad
(check this in `placecheck.py` the same way as the pad distances). Put the bottom video pads on a regular grid with one rotation. Example: P5-P8 at x = 1.6 / 3.9
with 2.3 mm pitch, all r90, labels outside toward the board centre. Make P17-P20 a 2.2 mm column (or a 2 x 2 grid with labels on the outside).
Put `10V` on the right of or below P3, not between P3 and P11. Move `BZ-` below P14, and `3V3` / `RST` to the far side of TP4 / TP3. Then DRC must report 0
silk_over_copper on label texts.

## New findings

### G3R-01 MAJOR: top-side 0402 pads 0.36-0.47 mm from the open buck thermal vias (solder-wicking shorts)
Evidence: U1/U2 each have 8 PTH thermal pads (0.3 mm drill, 0.6 mm pad, open; G2R-07 kept them open) at (9.55/10.85, 23.65-27.55) and
(25.95/27.25, 22.65-26.55). Measured top-side pad edge to via pad edge (`pp.py`):
- R22.1 (UNUSED_PC3) 0.36 mm and R22.2 (GND) 0.36 mm, vias (9.55/10.85, 27.55).
- **R32.1 (LED_STRIP) 0.36 mm and R32.2 (LED_DIN_BUF) 0.36 mm**, vias (25.95, 26.55/25.25).
- **R38.2 (CURR_ADC) 0.42 mm, R38.1 (ESC_CURR) 0.47 mm**, via (9.55, 24.95/26.25).
- C31.1 (3V3A) 0.47 mm, via (9.55, 23.65).

These boards are hand-assembled. Paste on the bottom EP wicks up 0.3 mm open vias and comes out as beads on the top annular ring. With a 0402 pad
0.36 mm away, the next hot-air pass on the top bridges LED_STRIP, CURR_ADC or 3V3A to GND. D-19 itself says the via fields block
top-side parts over the ICs, but R22, R32 and R38 still sit there (DRC passes because 0.36 mm > 0.127 mm).
Fix: move R22, R32, R38 and C31 so each pad is ≥ 1.0 mm from every thermal-via pad. There is room: R32 to about (24.0,27.6) near U12/P10, R38 to the
J2 side of the U1 field. Or tent the thermal vias on F.Cu only (solder mask over the top annulus, bottom left open for outgassing). This stops the bead
from wetting the top, and it is standard practice. Add a top-pad-to-thermal-via ≥ 1.0 mm check to `placecheck.py`.

### G3R-02 MAJOR: locked VBAT critical route breaks power.md §5 (0.8 / 1.0 mm vs ≥ 1.5 mm) and runs a 19 mm edge detour
Evidence (gen/critical.py output on the board):
- **P1 to U1.** VBAT on B.Cu, 0.8 mm: P1 (6.20,31.40) → (4.60,29.70) → (0.90,29.70) → (0.90,25.60) → (1.60,24.97) → C2 (3.05,24.97) → pin 3 (7.50,24.97).
  That is about 19 mm, with the x = 0.90 leg 0.50 mm from the board edge (exactly the min_copper_edge_clearance). The detour exists because the 0.8 mm GND
  track (3.05,27.50)-(9.20,27.50) and C2's GND pad block the direct path.
- **U2 feed.** In2.PWR, 1.0 mm, 0.5 oz inner (JLC04161H-7628): vias (5.00,23.85)/(6.00,23.70) → (6.60,22.10) → (16.90,22.10) →
  (17.60,20.90/21.70), then B.Cu to C11/C10/C12. That is about 12 mm on In2 plus about 4 mm on B.Cu. In2 has no VBAT zone; the only zones are GND_In1 and rule areas.
- **Current.** power.md §5 states the board input current as 2.95 A worst case at 2S and requires "≥ 1.5 mm traces or pours on L1 + L3" from the pads.
  IPC-2221 needs about 1.3 mm of 1 oz outer copper for 3 A at a 10 °C rise. A 0.8 mm trace is roughly a 25-30 °C rise (my estimate), and the inner 1.0 mm / 0.5 oz trunk is worse per amp.
  The tracks are locked, so the later route/pour stage will not widen them, and the planned F/B/In2 pours are GND.

Fix: make VBAT a filled zone instead of traces. Put a VBAT copper zone on In2 covering P1 → C2/C3 → U1 VIN → C10/C11/C12 → U2 VIN
(In2 is named "PWR"). Stitch it with ≥ 4 vias at P1, ≥ 2 at each input-cap group and ≥ 2 at each pin 3. Keep the B.Cu hot-loop stubs short. If In2 must
stay mostly GND, make the B.Cu route ≥ 1.5 mm. For example, move C3 from (3.05,21.42) to the left of C2, so that P1 → C2 runs up x ≈ 4.6 inside a ≥ 1.5 mm pour
under R14/C4, with the GND bus brought in from the right of C4 instead of from C2. Update power.md §5 "top side" to "bottom side".

### G3R-03 MINOR: 5 V output-cap ground is bonded into U2's input hot-loop ground
Evidence: GND B.Cu tracks (18.60,28.20)-(18.80,27.19) and (19.90,28.20)-(19.90,27.19) tie the C6 GND pad (18.23,29.38) and its via onto the C10 GND
pad (19.40,27.19; the 1210 pad spans x 18.05-20.75). The 0.8 mm GND track (19.40,27.19)-(21.95,26.40)-(25.60,26.40) then carries it to U2 pin 1 and the EP.
So the 5 V output ripple return shares copper with the 10 V converter's input loop: common-impedance coupling between the two converters.
Fix: delete the two C6→C10 GND stubs in gen/critical.py. Give C6 its own 2 vias to In1 (it already has (18.60,28.20)), and keep U1's output return and U2's
input-loop return separate on B.Cu.

### G3R-04 MINOR: VBAT 1210 input cap C11 against the BMI270
Evidence: C11 B (19.67,20.97), courtyard [18.03,18.63,21.31,23.32]. U7 courtyard ends at y = 18.55, a 0.08 mm gap. C11's GND pad (19.67,19.50) is 1.0 mm from the
U7 body. The VBAT feed via pair (17.60,20.90/21.70) sits between U6 and U7, 2.35 mm below them. C11 carries U2 input ripple. A 1210 X7S under
ripple is a piezo source (audible/ultrasonic "singing" and board vibration), and here it is mechanically coupled to the IMU.
Fix: move C11 off the IMU edge. For example, put it beside C10 toward the bottom edge after G3R-06 frees space, or between C8 and C10 with VBAT supplied through the In2
zone of G3R-02. Keep ≥ 3 mm between any VBAT bulk MLCC and U6/U7.

### G3R-05 MINOR: buck EN pins are boxed in by the locked hot-loop tracks
Evidence: EN pin 2 of U1 (7.50,26.23) has the 0.8 mm VBAT track above it (y 24.57-25.37), the 0.8 mm GND track below (y 27.10-27.90), C4 on the left (pad x ≤ 6.03) and the EP on the right.
The pocket is 0.69 mm wide (6.03 to 6.72), and a 0.6 mm via needs 0.854 mm. U2 has the same geometry (C12 pad x ≤ 22.43, pin pad x ≥ 23.12). The only exits are a 0.127 mm
track between C4's pads (0.65 mm gap) to a via under the C2 body (`pocket.py` found sites at x 1.75-4.4, y 25.95-26.4), or a 0.32 mm channel between the pin
column and the EP. EN_10V then has to reach Q2's drain at (25.84,19.50), on the opposite (FB) side of U2, 6.1 mm away.
Fix: rotate C4/C12 to 0° and place them directly below pin 1/3. Or plan the EN escape explicitly in critical.py: a short 0.15 mm track between the C4/C12 pads to a tented
via under C2/C10. Put the EN pull-down/divider (R2, R7) on the via side.

### G3R-06 MINOR: 10 V bulk cap C15 and the P3 output are on the far side of L2's SW pad
Evidence: L2.2 (10 V) is at (27.01,30.80). C15's 10 V pad (32.85,28.58) and P3 (T 34.20,23.00) are to the right of the L2 SW pad (29.38,30.80), the SW track x ≈ 29.3 and
C13. The 10 V net must either go around the SW node on B.Cu or via to the top through the 0.93 mm gap between P12 and P4 (the H4 keepout blocks the corner).
Fix: put C15 on the C14 side, e.g. at (21.9/24.4, 26.9) after G3R-04, or route 10 V on In2 as a zone from L2.2 to P3/R41. Then confirm the P3 path with the trial route.

### G3R-07 MINOR: USB ESD flow-through axis perpendicular to the D+/D− path, with VCAP2 cap in the path
Evidence: U13 is at r90, so its flow-through pins line up along y (D− pins 1/6 at x 24.71, D+ pins 3/4 at x 26.61, y 16.56/18.84). J1 D+/D− are at x 28.64,
y 13.75-15.25, and the MCU pins 44/45 at (22.67,15.75/15.25). C34 (VCAP2) pads at (24.55/26.11,14.75) sit right on the straight path. Between C34's pads (y ≤ 15.2) and
U13's pads (y ≥ 16.0) there is a 0.8 mm channel, which holds two 0.15 mm traces at minimum clearance. The pair is split by 1.9 mm at U13.
Fix: rotate U13 to r0 at about (25.7,15.5) so that D+/D− pass straight through pins 6→1 / 4→3 along x. Move C34 to the bottom under pin 47, or above
C26. This is acceptable for 12 Mb/s FS, so it is MINOR.

### G3R-08 MINOR: D-19 numbers are correct but not reproducible from the script; power.md has stale lines
Evidence: `gen/power_calc_lmr.py` computes only nominal L/f. At 25.2 V it prints "Iout_max(guar.)" 2.12 A (5 V) and 1.88 A (10 V), and
it still runs the 10 V rail at 1.5 A (line 45). The docstring says "Rev B". The D-19 floors (1.78 / 1.38 A) are right by my hand calculation (see the table), but
nothing in the repo produces them. power.md line 40 says the 1.71 A budget "leaves ≥ 0.16 A", while lines 149 and 391 say 0.07 A (1.78 − 1.71). Line 523
(R6) still says "10 V 2 A → 1.5 A". Line 7 admits that the §12 loss/thermal tables are still rev B (4030, 1.5 A).
Also: IHS,max = 3.8 A is above Isat(10 %) = 2.65 A typ, so in current limit or a short both inductors run deep into saturation. That needs a Gate 0 note, not a placement change.
Fix: add a worst-case column (L × 0.8, f × 0.8 × 0.92) to the script and run the 10 V rail at 1.3 A. Correct power.md lines 40 and 523, and redo §12 with 4020 / 81 mOhm.

### G3R-09 MINOR: CURR_ADC clamp D7 is 23 mm from its pin
Evidence: D7 B (32.00,7.25), CURR_ADC pad 3 (32.94,7.25). MCU pin 9 is at (11.33,17.75), and the CURR_ADC source is J2 at the bottom edge. The net becomes
a board-crossing high-impedance trace (J2 → R38 → pin 9 → D7 at the top-right corner). D-19 calls it "slow, not critical". For noise pickup the
trace length is what matters: it passes the USB, LED and buck areas.
Fix: put D7 next to C52 on the bottom (a SOT-23 needs about 3.2 x 3.0 mm; candidates are the left of U11 or under J5 after the G3-11 pad regrid). Or use
a BAT54S in SOT-323. Or drop D7 and rely on R38 (10 k) plus the MCU clamp diodes, as D8/RSSI does.

### G3R-10 MAJOR: MCU escape room: right-side wall and almost no outer via sites
Evidence (`pack.py`):
- **Via room.** In the band 0-2.5 mm outside the LQFP pad ring there are only **5** free via sites, all on the left at (9.8,12.7)/(10.6,12.7), and **0** on the top, right and bottom
  sides. Under the LQFP body there are 32 free sites, outside every bottom courtyard. All bottom-going nets therefore escape inward.
- **Right row.** C26, C34, U13, R24 and R23 form a wall 1.0 mm from the right-row pad tips (pad tips x = 23.41, U13 pin 6 pad x = 24.41).
  Pins 33-48 (UART6, MOTOR5/6, LED_STRIP, UART1, USB, SWDIO) have one trace channel along the row plus the inner vias.

The trial route (below) stalled at 72 unrouted after 12 passes, so this cannot be accepted on trust.
Fix: move U13 per G3R-07 and move C34/C26 to the bottom (pins 47/48 through vias), which opens a channel of
≥ 2 mm in front of pins 33-46. Then re-run the trial route (or do a scripted MCU fan-out first) until it reaches 0 unrouted before Gate 3 is closed.

### G3R-11 MINOR: DRC errors in footprints at the edge
Evidence: copper_edge_clearance ×8: the JST MP pads of J2/J3/J4/J5 have centres 1.22 mm from the edge (for example J2 MP (16.20,34.78)), against the
0.5 mm rule. hole_clearance ×4: J1 A1/B12 pads (28.64,17.70) are about 0.18 mm from the NPTH peg (29.72,17.39) (my estimate from pad and peg sizes; rule 0.25 mm).
The previous review reported none of these, so a rule changed. All these pads are GND.
Fix: move the four JST connectors 0.2 mm inboard, or add a documented rule exception for MP pads. Check the USB4105 land pattern against
`datasheets/USB4105_drawing.pdf` and JLC's NPTH-to-pad minimum at Gate 5.

### G3R-12 INFO
- **Working tree.** `gen/build_pcb.py` has an uncommitted deletion of `board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)`. The reviewed board file
  is the committed one. If the board is rebuilt, In1 becomes a signal layer for Freerouting, which undermines the solid GND plane. Revert, or record the reason.
- **Assembly order.** Both sides carry no-lead parts: 2 x LGA-14, WSON-8 and 2 x HSOIC-PowerPAD on the bottom; LQFP-64 on top. The IMUs sit directly under the LQFP. Hot-air
  work on U3 reheats U6/U7 from above. Put a side order and a "no hot air on U3 above 300 °C / > 60 s" note in the assembly guide.
- **Heights not confirmed from vendor PDFs:** Würth 74438356056, TDK C3225X7S2A475K200AB, Littelfuse SMBJ26A, JST SM0xB-SRSS-TB, and USB4105 (drawing shows 3.31 and
  3.50; USB-C is exempt anyway).
- **IMU alignment.** U6/U7 are unchanged (B, rot 0), so the rev B provisional values (U6 CW270FLIP, U7 CW0FLIP) still apply, pending the bench
  test. I did not re-derive them from the datasheets.

## Trial route

I ran Freerouting 2.5.0 through `gen/route.py 20` on a copy of the board, with the locked critical routes in place and In1 as the GND plane. The fanout stage
escaped 370 of 474 SMD pins (78.1 %). Autorouting then started with **126 unrouted** items. After 12 passes (13:05, killed by my 25-minute `timeout`) it
had **72 unrouted and 30 violations**, and passes 7-12 had stalled at 72-84 unrouted. No .ses was produced, so I cannot list which nets failed.
A stalled Freerouting run does not prove the board is unroutable, because a hand fan-out can do better. It does mean routability is **not demonstrated**, and it agrees
with the via-room count in G3R-10. The trial files lived only in `/tmp/g3r/trial` (deleted afterwards).

## Verdict

**FAIL.** BLOCKER: none. MAJOR: **G3-11** (labels on the wrong pads), **G3R-01** (top 0402 pads 0.36 mm from the open thermal vias), and
**G3R-02** (locked VBAT route 0.8 / 1.0 mm vs the ≥ 1.5 mm rule in power.md §5, 19 mm edge detour), and **G3R-10** (no via room outside
the LQFP; the trial route stalled at 72 unrouted).

The power-stage placement itself (hot loops, BST, FB/RT, SW, output caps, IMU distance, decoupling, crystal, USB, holes, heights) is now
sound. I measured all of that rather than taking it from placecheck.

Conditions for a PASS WITH CONDITIONS on the next pass, after the four MAJORs are fixed:
1. Fix or explicitly accept the MINORs G3R-03 to G3R-07 (power and USB) and G3-13 (forward arrow plus consistent align values).
2. A full trial route to 0 unrouted, with the 10 V path to R41/J3 on the right half (G3-10).
3. power.md §5 and §12 brought in line with rev C, and the floors computed in the script (G3R-08).
