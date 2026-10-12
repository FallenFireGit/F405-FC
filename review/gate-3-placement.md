# Gate 3: PCB placement review (independent)

Board: `kicad/F405FC.kicad_pcb` (read only, not modified). Reviewer: fresh Gate 3 reviewer, 2026-10-12.
**Verdict: FAIL.** 3 BLOCKER, 9 MAJOR, 6 MINOR (details below).

## Method

1. **Actual positions.** I read every footprint from the board with pcbnew (KiCad 10.0.6, in the `kc` chroot). For each one I took ref, side, x/y
   (the 100 mm origin offset subtracted, y down), rotation, courtyard bbox, and the net and position of every pad. The script was
   `/tmp/g3/dump.py` in the chroot. All distances below are pad-centre to pad-centre on the **legalized** board, not the seeds in `design/placement.py`.
   63 parts sit more than 1.5 mm from their seed. Examples: R17 is 9.0 mm off, C11 8.4 mm, C6 8.2 mm, C24 7.5 mm, C52 5.8 mm and C50 5.7 mm.
2. **Pad clearance.** I checked pad and courtyard distances to the board edge and to the four hole centres (grommet keepout radius 2.3 mm), plus the
   rule-area zones and the Edge.Cuts segments.
3. **DRC.** I ran `kc 'python3 gen/drc_summary.py'`. It reports 0 courtyard or clearance violations, 43 `silk_over_copper` and 29 `silk_overlap`
   (362 unconnected, as expected for an unrouted board, parity 0). I also listed every board silkscreen text with its position.
4. **Renders.** I viewed `docs/renders/placement_top/bottom/iso/fab_top/fab_bottom.png`, cross-checked against the coordinates.
5. **Datasheets.** Pin functions came from `datasheets/lmr38020.pdf` (Table 6-1: 1 GND, 2 EN, 3 VIN, 4 RT, 5 FB, 6 PG, 7 BOOT, 8 SW). Axis
   figures came from the ICM-42688-P (Fig. 15) and BMI270 (§8.2, §7.1) datasheets. The USB-C PCB-edge line came from the KiCad
   USB4105 footprint (`Dwgs.User`, local y = +3.675). Heights came from the BOM MPNs, the WE-MAPI figure in design/power.md §2.2 and the KiCad
   STEP models (D_SMB z max 2.15 mm, PTS810 2.50 mm).
6. **Not done.** No thermal or EMI simulation, and no trial routing. Part heights not in the repo are marked "unverified".

## Key measurements

| Item | Measured | Target | Result |
|---|---|---|---|
| Outline | 36.0 x 36.0 mm, 4 x R2 mm arcs | 36 x 36, rounded | PASS |
| Holes | H1-H4 at (2.75/33.25, 2.75/33.25), pitch 30.5 mm, 3.2 mm, rule areas 4.6 mm (tracks blocked) | 30.5 mm M3, 4.6 mm keepout | PASS |
| Closest courtyard to a hole centre | P14 2.52, P13 2.53, D4 2.53, C16 2.54, P2 2.59 mm | ≥ 2.3 mm | PASS |
| IMU to board centre | U6 2.06 mm, U7 2.24 mm (both **bottom**) | near centroid | PASS |
| IMU to U1 / U2 / L1 / L2 | U6: 11.8 / 14.2 / 16.5 / 18.3; U7: 14.3 / 11.7 / 17.9 / 16.8 mm | away from bucks | PASS |
| U1 VIN pin 3 (6.70, 25.97) to C2 / C3 / C4 VBAT pad | 5.7 / 8.3 / 3.8 mm (all three on the wrong, +x side of the IC) | < 1-2 mm | **FAIL** |
| U2 VIN pin 3 (23.90, 25.97) to C10 / C11 / C12 VBAT pad | 3.0 / 4.7 / 4.7 mm | < 1-2 mm | **FAIL** |
| SW pin 8 to inductor SW pad | U1→L1 4.7 mm; U2→L2 7.1 mm (L2 SW pad on the far side) | short, compact | FAIL (U2) |
| BOOT cap to BOOT pin 7 | C5 to U1: 8.5 mm (C5 is on the opposite side); C13 to U2: 2.8 mm | < 2 mm | **FAIL** (U1) |
| FB divider to FB pin 5 | R5 to U1: 6.0 mm; R10 / R9 to U2: 5.8 / 5.5 mm, R9 FB pad 1.7 mm from U2 SW pin | close to FB, away from SW | **FAIL** |
| Output caps to inductor output | 5 V: C6 9.4, C8 11.8, C7 14.0, C9 16.1 mm. 10 V: C16 6.3, C14 11.6, C17 13.6, C15 18.2 mm | ≤ 3-5 mm | FAIL |
| Crystal | Y1 pad to PH0 / PH1 = 2.2 / 4.2 mm; load caps 2.3-3 mm from Y1 | ≤ 5 mm | PASS (see G3-16) |
| MCU 100 nF to VDD pin | C25 1.86 (p64), C27 1.83 (p19), C28 3.17 (p32), C26 **4.28** (p48), C30 2.01 (p1) mm | ≤ ~2 mm | partial |
| VCAP / VDDA | C33 2.15 (VCAP1), C34 2.69 (VCAP2), C32 2.94 / C31 6.21 (VDDA), FB1 2.73 mm | close | PASS / MINOR |
| USB ESD U13 | 8.6 mm from J1 D+ and 8.0 mm from MCU PA12, offset 7 mm below the D+/D- path | in line, at the connector | **FAIL** |
| ADC RC caps to MCU pin | C24 (VBAT_ADC) 13.6, C52 (CURR) 14.5, C53 (RSSI) 11.1 mm | ≤ 2-3 mm | **FAIL** |
| TVS D1 to battery pads | 9.45 mm to P1 (VBAT), 8.05 mm to P2 (GND); P1 to P2 21.8 mm | adjacent | FAIL |
| LED buffer U12 to P10 | 4.4 mm (via R33, which sits at the board edge) | near | PASS |
| Mag U9 to 10 V / power parts | P3 (10V pad, bottom) 5.6, D5 4.8, J3 VTX_PWR pin 7.4, R41 9.2, SW1 (steel dome) 2.8 mm | far from high current | FAIL |
| Heights, bottom (limit 2.5 mm) | L1, L2 3.1 max; 1210 CL32B106KBJNNNE (C1, C2, C3, C10, C11) 2.5 ± 0.2 = 2.7 max; SW1 2.5; D1 SMB 2.15 model (datasheet max unverified) | ≤ 2.5 | **FAIL** |
| Heights, top (limit 3.5 mm) | JST-SH ≈ 2.9 mm, LQFP 1.6, others < 1.5; USB4105 exempt | ≤ 3.5 | PASS |
| Connectors | J2/J3/J4/J5 mouths face their edge (MP pads at the edge, signal pads inboard; render confirms); clear of holes (≥ 3.3 mm) | edges, outward | PASS |
| USB-C J1 | Mouth +x. GCT "PCB Edge" line at x = 36.575; board edge at 36.0, so the receptacle overhangs 1.08 mm (GCT intends ≈ 0.5) | at edge | MINOR |

## Findings

### G3-01 BLOCKER: L1 and L2 (3.1 mm) on the bottom side break the 2.5 mm bottom height limit
Evidence: L1 (B, 12.00, 33.00) and L2 (B, 25.00, 33.00) are Würth WE-MAPI 4030, 4.1 x 4.1 x **3.1 mm max** (design/power.md §2.2,
design/decisions.md). requirements.md says "bottom side max 2.5 mm". Both parts are 0.6 mm over.
Fix (pick one, then re-run the Gate 0 power calc):
- (a) **Preferred.** Change to a ≤ 2.2 mm 4 x 4 mm molded inductor with the same 6.8 / 8.2 uH values, for example the Würth WE-MAPI 4020 or the
  Coilcraft XGL4020 / XEL4020 families. Gate 0/2 must confirm Isat ≥ 3.5 A (10 %), DCR and DigiKey stock, because this board is already
  current-limit marginal (power.md §0).
- (b) Move L1/L2 to the **top** side directly above each buck, with the SW node reaching it through ≥ 2 vias right at pin 8. For example L1 at
  T (9.6, 28.6) and L2 at T (26.8, 28.6), after clearing the small parts there (R14, R22, R38, C24, C52, D7 / Q1, D12, R28, U12 area). This
  puts a switching node on the MCU side, so (a) is better.

### G3-02 BLOCKER: U1 (5 V buck) hot loop, BOOT and FB placed against the pinout
Evidence (U1 B (9.40, 26.60), rot 0, pins 1-4 on the left at x = 6.70, pins 5-8 on the right at x = 12.10):
- **VIN/GND loop.** VIN pin 3 is at (6.70, 25.97) and GND pin 1 at (6.70, 28.51), both on the **left**. All input caps sit on the right or top:
  C4 (100 nF HF) is 3.8 mm away, C2 5.7 mm, C3 8.3 mm. The HF loop C4 → VIN → GND → C4 must run around the IC, about 8 mm of loop
  instead of about 2 mm.
- **BOOT.** BOOT pin 7 is at (12.10, 27.24) and SW pin 8 at (12.10, 28.51), but C5 is at (3.77, 24.92), 8.5 mm away on the far side. The
  SW node would need a long trace to reach it.
- **FB.** FB pin 5 is at (12.10, 24.70). R5 (FB pad 9.21, 30.00) is 6.0 mm away and R4 7.9 mm. Both sit between L1's SW pad (10.8, 33.0),
  the U1 SW pin (3.3 mm away) and the VBAT pad P1. The FB trace would have to cross the SW region.
- **Root cause.** The seeds in `design/placement.py` put C2/C3/C4 at x = 12.4 (the +x side) and C5 at x = 4.2 (the -x side), the reverse
  of the actual pinout. The legalizer then pushed C3 a further 3.0 mm.

Fix (keep U1 where it is): put C4 at B (5.30, 27.20) rot 90, so its pads bridge pin 3 and pin 1 (≈ 1.4 mm each). Put C2 at B (3.40, 27.20)
rot 90 and C3 at B (3.40, 23.80) rot 90. Move the output caps C6/C7/C8 out of that area (see G3-05). Move C5 to B (13.30, 27.90) rot 90,
between pins 7 and 8. Move R5/R4 to B (13.30, 24.20) / (13.30, 23.10), next to FB pin 5 and ≥ 4 mm from pin 8. Mark these parts FIXED in
`placement.py` so the legalizer cannot move them.

### G3-03 BLOCKER: U2 (10 V buck) hot loop, SW path, and FB/RT/EN on the wrong side
Evidence (U2 B (26.60, 26.60); VIN pin 3 (23.90, 25.97) and GND pin 1 (23.90, 28.51) on the left; FB, PG, BOOT and SW pins on the right at x = 29.30):
- **HF cap.** C12 (100 nF) is at (21.79, 29.42): VBAT pad 4.7 mm from VIN, GND pad 2.1 mm. C11 is above the IC at (25.17, 22.15), 4.7 mm away.
  C10 is 3.0 mm away, but its GND pad (21.03, 23.78) is 5.5 mm from pin 1.
- **SW path.** SW pin 8 (29.30, 28.51) to L2 SW pad (23.82, 33.00) is **7.1 mm**. L2's SW pad faces away from the IC, and the trace passes **R9's FB pad
  (28.90, 30.15), 1.7 mm from pin 8**.
- **FB, RT, EN.** FB (pin 5) parts are 5.5-5.8 mm away (R9, R10). RT: R8 is 8.6 mm from pin 4. EN: R7 is 7.3 mm, the Q2 drain 8.4 mm and R6 11.0 mm from
  pin 2. All of them sit on the SW/BOOT side while RT and EN are on the VIN side, so the high-impedance RT and EN nodes (EN = VTX pit switch)
  would cross SW.

Fix: move C12 to B (22.50, 27.20) rot 90, bridging pins 3 and 1, and C10 to B (20.40, 27.20) rot 90. Move C11 to B (20.40, 23.80) rot 90,
or onto the VIN side next to C10. Rotate L2 to 180° so its SW pad is at (26.19, 33.0), 4.5 mm from pin 8, or move it closer. Move R9 and R10 to
B (30.60, 24.20) / (30.60, 23.10) next to FB pin 5, R8 to B (22.30, 24.20) next to RT pin 4, and R7 plus the Q2 drain next to EN pin 2 on the
left (≈ (22.3, 25.5)). Mark them FIXED.

### G3-04 MAJOR: 1210 input caps exceed the 2.5 mm bottom limit
Evidence: C1, C2, C3, C10 and C11 are bottom-side Samsung CL32B106KBJNNNE. The thickness code "J" is 2.5 ± 0.2 mm, so 2.7 mm max. The BOM's
own alternate UMK325AB7106KM-T is listed as "2.5 mm max" (bom/digikey_bom_costed.csv), which is right at the limit.
Fix: use a 2.0 mm 1210, for example Murata GRM32DR71H106KA01L (10 uF/50 V X7R, 2.0 ± 0.2 mm), or 2 x 4.7 uF/50 V X7R 1206 (≤ 1.8 mm). Check
derated capacitance against power.md §1.2 (≥ 4.7 uF effective per IC) and DigiKey stock.

### G3-05 MAJOR: Buck output capacitors far from the inductors
Evidence: 5 V output pad L1.2 is at (13.19, 33.00). C6 is 9.4 mm away, C8 11.8, C7 14.0 and C9 (HF 100 nF) 16.1 mm. 10 V output pad L2.2 is at
(26.19, 33.00). C16 is 6.3 mm away, C14 11.6, C17 13.6 and C15 18.2 mm (C15 sits beside the USB shell at the right edge). The legalizer moved C6
by 8.2 mm, C16 by 5.0 mm and C17 by 5.4 mm.
Fix: group each rail's output caps within about 4 mm of L.2, with their GND returning to the IC's GND pin 1 / EP side. Combined with
G3-01/02/03 this means re-seeding the whole power quadrant. For example, put the 5 V caps along the bottom edge between L1 and D1 after
moving D1/C1 right (D1 to B (19.6, 33.3)), and the 10 V caps along x ≈ 28-31, y 30-32 after G3-03's L2 rotation. Check again by measurement.

### G3-06 MAJOR: USB ESD (U13) is not in the D+/D- path
Evidence: U13 is at T (26.85, 21.69). J1 D+/D- pads are at x = 29.22, y 13.75-15.25, and MCU PA11/PA12 at (22.68, 15.75/15.25). U13 is 8.6 mm from
the connector and 8.0 mm from the MCU, about 7 mm below the straight 6.5 mm path. TP2 (26.0, 14.8) and TP1 (26.0, 17.0) sit on that path.
The placement.py comment ("under the USB connector") does not match the result.
Fix: put U13 at T (26.40, 14.90) rot 90, between J1 and U3, so D+/D- pass through its pins. Move TP1/TP2 to T (26.0, 20.6) / (26.0, 22.6)
(the space U13 frees), with their labels.

### G3-07 MAJOR: ADC filter capacitors 11-14.5 mm from the ADC pins
Evidence: VBAT_ADC is pin 8 (11.33, 17.25), CURR_ADC pin 9 (11.33, 17.75) and RSSI_ADC pin 25 (17.25, 23.18). C24 is 13.6 mm from its pin, C52
14.5 mm and C53 11.1 mm. All three sit in the bottom-left corner, next to the ESC/RSSI series resistors and above U1/L1 (bottom), so the
long high-impedance ADC traces would pick up buck noise. Clamps: D8 is 4.5 mm from its pin but D7 is 10.1 mm. R15 is 6.1 mm.
Fix: put the caps at the pins. C24 at B (11.00, 16.70) rot 0 and C52 at B (11.00, 17.80) rot 0 (free space under the MCU's left row; via at the
pin), C53 at T (17.25, 24.60) or B (17.3, 21.5). Keep R38/R39 at the connector side, so each ADC trace runs from the series resistor to the
cap at the pin.

### G3-08 MAJOR: IMU and IMU-LDO decoupling not at the pins
Evidence:
- **IMU decoupling.** C38 (100 nF) is 3.96 mm from U6 VDD pin 8 (17.36, 16.25), C40 is 2.42 mm from VDDIO pin 5, C41 3.11 mm from U7
  pin 5, and C42 1.75 mm from U7 pin 8. U6 and U7 are butted together (U6 courtyard right edge 18.00, U7 left edge 18.20), so U6's VDD pin
  faces U7 with no room for a cap.
- **LP5907 (U5).** The caps are on the wrong sides. Input C22 is at (21.23, 13.39), next to OUT pin 5, and output C23 is at (15.28, 13.44), next to
  IN pins 1/3. C22 is 4.17 mm from IN, C23 4.06 mm from OUT.

Fix: spread the IMUs to U6 B (15.6, 17.0) and U7 B (20.6, 17.0). Put a 100 nF on each VDD/VDDIO pin within 1 mm, for example C38 at
B (18.1, 16.3) rot 90 for U6 pin 8, C41 at B (18.4, 17.0) rot 90 for U7 pins 1-5, C42 at B (22.6, 16.6). Swap C22 and C23: C23 to
B (21.23, 13.39) and C22 to B (15.28, 13.44).

### G3-09 MAJOR: LP38692 output capacitor 7.6 mm from VOUT
Evidence: U4 VOUT pin 3 is at (23.55, 10.35). C20 (2.2 uF, the stability cap; ESR/placement was a Gate 1 topic) is at B (30.17, 8.74), 7.6 mm
away beyond the J1 shell pad.
Fix: put C20 at B (24.0, 12.6) rot 0, below the pin row, ≤ 2 mm from pin 3, with GND to the tab plane.

### G3-10 MAJOR: Magnetometer next to the VTX power entry and a ferromagnetic switch
Evidence: U9 (IIS2MDC) is at T (13.60, 7.78). The 10 V pad P3 (B, 13.60, 2.20) is 5.6 mm away, the J3 VTX_PWR pin (20.5, 5.1) 7.4 mm and R41
(10 V 0R, 2 A) 9.2 mm. The 5V→5V_SYS diode D5 (B) is 4.8 mm away and SW1 (PTS810, steel dome/frame, B) 2.8 mm. A 1.5 A VTX current 6 mm
away gives up to about 50 uT (2e-7·1.5/0.006), the same order as Earth's field, and it changes with VTX power and pit mode. The 10 V path
from L2 (bottom right) to P3/J3 (top centre) also crosses the board.
Fix: swap the baro and mag (U9 to T (9.6, 7.6), U8 to T (13.6, 7.8)) and move the 10 V pads P3/P4 to the right half (for example B (28.6, 6.0) /
B (28.6, 3.4), clear of the H2 keepout). Route 10 V up the right side so it stays ≥ 15 mm from U9, and move SW1 ≥ 6 mm from U9. If that cannot
be met, document in decisions.md that the external GPS mag is the primary mag.

### G3-11 MAJOR: Silkscreen pad labels sit on the wrong pads after legalization (miswiring risk)
Evidence (label position vs. pad position; DRC lists each overlap):
- `T6` at (32.31, 21.6) sits 0.7 mm from P10 **LED_DIN** and 2.1 mm from P17 UART6_TX.
- `S5` at (29.40, 29.44) sits on P20 **MOTOR6** (29.20, 29.24).
- `R6` at (32.35, 29.5) sits on P19 **MOTOR5**.
- `BZ-` at (29.73, 30.03) touches P19/P20 (DRC).
- Bottom: `C1` (CAM1) at (3.49, 14.6) sits on P8, the **camera 5 V** pad. A user who solders the camera's 5 V lead to the "CAM1" pad puts 5 V into
  the 3.3 V TS5A3159A input.
- `VBAT` sits on R4/R5 and `GND` on R9.

The right-edge pad block P13/P14/P17-P20 has collapsed into an irregular cluster (P18 moved 5.7 mm, P19 4.5, P20 5.3).
Fix: re-seed the right-edge pads as a clean column (for example P17-P20 at x = 34.4 with 2.2 mm pitch, after G3-06 frees space) and keep
them FIXED. Generate each label from its pad's actual position with a fixed, collision-checked offset. Re-run DRC until it reports zero
silk_over_copper on pad-label texts.

### G3-12 MAJOR: Battery entry: TVS far from the pads, pads 22 mm apart, side differs from power.md
Evidence: P1 VBAT is at B (7.2, 33.2) and P2 GND at B (29.0, 33.2), 21.8 mm apart. D1's VBAT pad is 9.45 mm from P1 and its GND pad 8.05 mm from
P2, so the battery-lead loop spans the whole board width with L1 and L2 inside it. power.md §5 says the pads are "top side, at the board
edge next to the ESC connector". The board puts them on the bottom, and decisions.md does not record the change.
Fix: put P1/P2 side by side with D1 and C1 directly between or behind them. For example, on the bottom: P1 at (14.6, 33.2), D1 at (18.0, 31.8),
P2 at (21.4, 33.2), with C1 next to D1. The inductors move per G3-01/05. Then update power.md §5 or log the deviation.

### G3-13 MINOR: IMU axis alignment: both IMUs flipped and 90° apart; config placeholders are wrong
Evidence:
- Both IMUs are on the bottom at rot 0. From the pad map (pin 1 at the lower-left in the top view, pins 1-4 running up) and the datasheet figures:
  - ICM-42688-P (U6): sensor +X → board +x (right), +Y → board +y (toward the J2/ESC edge), +Z → down.
  - BMI270 (U7): sensor +X → +y (toward ESC), +Y → -x (left), +Z → down.
- The two IMUs therefore differ by 90° and both need a FLIP alignment.
- `design/betaflight_config.txt` and `inav_target.md` still use the placeholder CW0. No forward arrow is on the silkscreen.

Fix: add a forward arrow (suggested: toward J3/top edge). Assume the Betaflight body frame is X forward, Y left, Z up and the forward edge
is J3. The provisional values are then gyro_1_sensor_align = CW270FLIP (U6) and gyro_2_sensor_align = CW0FLIP (U7). Confirm with a
bench tilt test. As an option, rotate U7 by 90° so both IMUs share one alignment.

### G3-14 MINOR: Other bottom-side heights at or near the limit
Evidence:
- SW1 (PTS810, B (15.85, 9.51)) is 2.5 mm nominal, exactly at the limit, and decisions.md says "top side".
- D1 (SMBJ26A, SMB) is 2.15 mm in the KiCad model. The Littelfuse maximum was not checked (no PDF in the repo); DO-214AA outlines reach 2.4-2.6 mm.

Fix: move SW1 to the top (for example T (21.5, 7.6), near BOOT0 pin 60), or pick a ≤ 2.0 mm tact switch. Pull the Littelfuse PDF. If the max is over 2.5 mm,
use an SMA-sized 26 V TVS with a power rating re-checked in power.md §1, or move D1 to the top.

### G3-15 MINOR: Several decoupling caps farther than needed
Evidence: C26 (VDD pin 48) is 4.28 mm away, C28 (pin 32) 3.17 mm, C31 (VDDA 1 uF) 6.21 mm, C50 (U12 VCC pin 5) 6.94 mm, C48 (flash VCC pin 8)
3.63 mm and C22 4.17 mm.
Fix: C26 to T (24.0, 13.0) rot 90 (beside pin 48), C50 to T (28.0, 23.2), C48 to B (11.2, 4.2) beside U10 pin 8, C31 next to C32.

### G3-16 MINOR: HSE traces cross
Evidence: Y1 pad 1 (HSE_IN) is at (9.25, 16.55) but goes to pin 5 (y 15.75). Pad 3 (HSE_OUT) is at (7.55, 14.35) but goes to pin 6 (y 16.25). The two
traces must cross or one must loop around the crystal.
Fix: rotate Y1 to 270° (same centre). Pad 3 then lands at (9.25, 16.55) facing pin 6, and pad 1 at (7.55, 14.35) routes above to pin 5 with no
crossing. C36/C37 stay as they are.

### G3-17 MINOR: USB-C set 0.575 mm proud of GCT's edge reference
Evidence: the J1 footprint's PCB-edge line (local y +3.675) lands at x = 36.575, so the shell overhangs the board by 1.08 mm (courtyard to 37.12)
instead of about 0.5 mm. Fix: move J1 to x = 32.325 (shift R36, C17 and TP4 accordingly), or accept and note the overhang for frame fit.

### G3-18 MINOR: Silkscreen clutter
Evidence: 72 silk DRC items. Examples: `USB` overlaps the TP2 `CLK` label, `RST` sits on C37, `DIO` on R32 and U3 pin 41, and `LED` on U13/R28.
Fix: with G3-11, place labels after legalization and clear all `silk_over_copper` and `silk_overlap` items.

### G3-19 INFO
- **Routability.** In1/In2 are the GND/PWR planes, so only F.Cu and B.Cu carry signals. The bottom is about 60 % taken by the power stage, IMUs, LDOs
  and flash, so most of the 64-pin fan-out runs on top through vias. Watch congestion at the MCU's bottom row (C27/C29/C33/C28, D7/D8, R18,
  TP5 and the J2 pins at y = 30.9 within 7.7 mm) and its left side (Y1, C32, C35, C37, FB1, R15, TP3). The U1/U2 EP thermal vias
  (8.75-10.05, 24.65-28.55) and (25.95-27.25, ...) also block top-layer routing under R14/C31/D7 and D11/D12. Allow for that in the re-seed.
- **Assembly.** Both sides carry fine-pitch parts (LQFP-64 top; 2 x LGA-14, WSON-8 and 2 x HSOIC-PowerPAD bottom). Hand or hot-air
  assembly needs a defined side order (bottom first with LGA/PowerPAD, then top with low-temp paste or local hot air). This is not a placement defect.
- **Passes.** Outline, holes and grommet keepouts, IMU centroid and distance from the bucks, connector edges and mouth directions, crystal ≤ 5 mm, top-side
  heights, LED buffer near its pad, and DRC with 0 courtyard or clearance violations all pass.

## Verdict

**FAIL.** BLOCKERs: G3-01, G3-02 and G3-03. MAJORs: G3-04 through G3-12. Root cause: the seeds in design/placement.py do not follow the
LMR38020 pin sides, and the legalizer moved 63 parts more than 1.5 mm, including hot-loop, ADC and decoupling caps, with nothing
checking pin distance afterwards. Recommendation: re-seed the power quadrant and the pin-critical caps against actual pad positions, mark them
FIXED, then add a pin-distance check (like the table above) to the build so a regression shows up automatically.
