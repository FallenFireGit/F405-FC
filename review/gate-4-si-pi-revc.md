# Gate 4 (rev C): signal integrity / power integrity re-review

Reviewer: fresh, independent Gate 4 SI/PI agent, 2026-10-15. This is a review only. The only file I wrote in the worktree is this report.
I did not modify, rebuild or save any board, schematic, generator, fab or doc file, and I made no commits. All scratch work is in
`/opt/kroot/tmp/g4c/` (that is `/tmp/g4c/` inside the chroot).

**Board reviewed:** `/home/user/F405-FC-revc/kicad/F405FC.kicad_pcb`, branch `rev-c`.
- The analysis was done at HEAD `6080bc0` (md5 `2b8bd0a02124adb21a1ecd50cf108240`).
- The board was then rebuilt at HEAD `83286de` (md5 `ea50a34145a7a44231a3ed9e3851899d`; L1/L2 fields, silk and docs changed). I re-dumped it:
  - every track, via and footprint position is identical;
  - every zone fill has the same polygon and vertex counts;
  - In1 is still 6 pieces;
  - DRC with parity gives the same result;
  - the release Gerbers still match.
  All findings therefore apply to `83286de`.
- The md5 did not change during any of my tool runs, and `git status` showed only this report as untracked.

## Method

- **DRC.** `kc4 'kicad-cli pcb drc --schematic-parity --severity-all --format json -o /tmp/g4c/drc.json …'`.
  - Result: 0 errors, 0 unconnected, 0 parity.
  - Warnings: 17 `via_dangling`, 3 `silk_overlap` and 1 `track_dangling` (VBAT_ADC).
- **Zone fills are current.** `refill.py` refilled every zone in memory with `pcbnew.ZONE_FILLER` and did not save.
  - Every zone's filled area and outline count is identical to the stored fill.
  - In1 GND is **6 outlines** by KiCad's own count.
- **Release Gerbers match the board.** I re-exported F/In1/In2/B to `/tmp/g4c/gbr/`.
  - The coordinates are identical to `fab/gerbers/*` apart from one constant origin offset of (100, −136) mm.
  - So the fabrication files contain exactly the copper reviewed here.
- **Data dump.** The read-only pcbnew dump `dump.py` writes `board.json` with every track, via, pad and filled-zone polygon. The
  previous Gate 4 host scripts were copied to `/opt/kroot/tmp/g4c/` and re-pointed at it (`rast`, `in1`, `cross`, `ref`, `prox`,
  `decap`, `s5v`, `s10`, `neck`, `fem`). I added these scripts:
  - `box.py`: per-layer copper, pads and zone coverage in a rectangle.
  - `in1inv.py`: In1 inventory and coverage under parts.
  - `frag.py`: F/B GND copper groups with their pads and vias.
  - `piece.py`: which In1 piece a point lies on.
  - `couple.py`: parallel and broadside length near a net.
- **What changed since the reviewed rev B.** I diffed rev C against the previous reviewer's dump `/opt/kroot/tmp/g4/board.json` (rev B
  snapshot md5 `b0414471…`):
  - Parts moved: only C37 and R15.
  - Copper changed (≥ 0.05 mm per net and layer): HSE_OUT, NRST and VTX_VID.
  - Every other change is under 0.3 mm per net, from via nudging (D-26 M-3).
  - Zone fills changed at the J1 shell thermal reliefs and wherever vias moved.
  - **Every non-crystal Gate 4 finding therefore concerns copper that is essentially unchanged.**
- **Coordinates.** Board mm, origin at the board's top-left corner, as in the previous report.
- **Stackup.** Same assumption as before: JLC04161H-7628, F–In1 ≈ 0.21 mm, In1–In2 ≈ 1.065 mm, In2–B ≈ 0.21 mm, 1 oz outer and
  0.5 oz inner copper.

## Verdict: **FAIL**

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 6 |
| MINOR | 11 |
| INFO | 4 |

**Summary.**
- G4-01 is no longer a blocker: C37 now sits 3.27 mm (centre to centre) from Y1.3, and HSE_OUT no longer runs over the 5 V buck.
  - It is **not fixed** as Gate 4 specified, though. C37 was placed beside Y1's **GND pin 2**, not beside the HSE_OUT pin 3.
  - So the load cap is reached by an 11.8 mm, 2-via In2 detour that loops back under the crystal.
- The four MAJOR PDN/plane findings G4-02 to G4-05 are open, as D-27 itself states.
- G4-02 and G4-03 are slightly worse in rev C:
  - In1 is now in **6** pieces (the NRST re-route split off a new 18 mm² island).
  - VSSA and the VDDA caps now share an F pour fragment with the 5 V buck's EP vias and the battery bulk cap.
- One mechanism was missed at Gate 4: the MCU VDD pin-32 decoupling track runs on In2 directly over the 10 V buck's VIN/GND pins (G4C-02).

| ID | Sev | Title | Status vs Gate 4 |
|---|---|---|---|
| G4C-01 (was G4-01) | **MAJOR** | HSE_OUT load cap C37 is next to Y1 but is reached by an 11.8 mm, 2-via In2 detour that passes through the MCU pin and under the crystal. The crystal area is still unguarded | Changed: partly fixed, downgraded from BLOCKER |
| G4-02 | **MAJOR** | In1 is not a plane: 327.5 mm of track from 39 nets, **6** GND pieces, main piece 64.4 % of the board | Still open, slightly worse |
| G4-03 | **MAJOR** | F GND fragments bond MCU/analog grounds to the buck EP via fields. VSSA, the VDDA caps, C27 and C53 now share a fragment with U1's EP, C1 (battery bulk) and the ELRS GND | Still open, changed (worse for VSSA) |
| G4-04 | **MAJOR** | MCU decoupling: pin 32 → C28 ≈ 8.5-10.3 mm via In2 (2 vias), pin 48 → C26 6.6 mm (2 vias), VCAP2 → C34 8.1 mm via In1. Decap GND vias up to 4.7 mm away | Still open, unchanged |
| G4-05 | **MAJOR** | MOTOR5/6, LED_STRIP, STATUS_LED_GREEN, UART1 and GYRO2_CS run through the BMI270 footprint. U6 sits on an In1 island (0 % main plane) | Still open, unchanged |
| G4C-02 | **MAJOR** | (new; missed at Gate 4) The pin-32 VDD decoupling track (3V3, In2) runs 0.21 mm above U2's VIN/EN/GND pins and slots the In2 image plane of the 10 V hot loop | New |
| G4-06 | MINOR | 5 V east branch: 1.21 A in 0.35 mm B.Cu and one 0.3 mm via | Still open |
| G4-07 | MINOR | 10 V: three single vias in series at 1.3 A (P3), four more on the J3 path | Still open |
| G4-08 | MINOR | VBAT In2 neck to U2 ≈ 0.64 mm, 16.4 mΩ, 3.86 A/mm peak | Still open |
| G4-09 | MINOR | USB D+/D− on different layers, ESD clamp as a stub on D−, motor In1 cuts under the pair, no VBUS cap at U13 | Still open |
| G4-10 | MINOR | ESC_CURR on In2 over U1 and on In1 over L1's SW pad. RSSI lines cross both SW nodes | Still open |
| G4-11 | MINOR | 5 V feedback top taken from a trace over U1's SW pin | Still open |
| G4-12 | MINOR | 17 dangling fanout vias | Still open (same 17 nets) |
| G4-13 | MINOR | GND stitching: 53 GND vias, 3 within 2 mm of the edge, 20 of 34 F/B GND copper groups tied by a single via or TH | Still open |
| G4C-03 | MINOR | (new, rev C regression) The NRST via move split a new 18.1 mm² In1 island under U8 (BMP390), C43/C44 and J3, tied by one via | New |
| G4C-04 | MINOR | (new) BMI270 GND pads are 3.0 mm from their nearest GND via, and that B fragment shares its vias with the USB ESD clamp U13 | New |
| G4C-05 | MINOR | (new, rev C regression) 2.2 mm dangling VBAT_ADC stub left from R15's old position, ending over U1's VIN pin | New |
| G4-14 | INFO | No stackup in the board, and the job file has KiCad's default (3 × 0.48 mm, 35 µm inner, finish "None"). The assembly guide §0 now names JLC04161H | Partly fixed (docs only) |
| G4-15 | INFO | `review/summary.md` still does not exist. D-27 now also points to it for the rev C residual risks | Still open |
| G4-16 | INFO | Video: VTX_VID now has 2.6 mm on In1. CAM2_VID on In2 passes 0.09 mm (in projection) from C37.1 | Changed |
| G4C-06 | INFO | Release Gerbers match the board, zone fills are current, and DRC/parity are clean | Verification note |

---

## Part 1: Gate 4 findings re-checked

### G4-01 → G4C-01 MAJOR (was BLOCKER): crystal network, partly fixed

**What was fixed.**
- C37 moved from (7.64, 23.36) to **(5.50, 16.50)**, rotated 180°. Its pads are C37.1 HSE_OUT (5.98, 16.50) and C37.2 GND (5.02, 16.50).
  - Y1.3 (HSE_OUT) is at (9.25, 16.55), so Y1.3 → C37.1 is **3.27 mm centre to centre** and 2.39 mm pad edge to pad edge.
  - D-27's "3.3 mm pad-to-pad" is the centre distance.
- HSE_OUT no longer goes near U1:
  - total length 10.18 mm (was 17.0 mm), 2 vias (was 3);
  - layers F 2.49 mm and In2 7.69 mm;
  - no B or In1 copper.
- `gen/placecheck.py:34` now has `("C36","HSE_IN","Y1",2.5), ("C37","HSE_OUT","Y1",3.5)`.
- Y1.2 and Y1.4 now have GND vias at 1.3/1.1 mm: (8.44, 15.54), (9.31, 15.41) and (6.51, 14.21) on F fragment #11.

**What is not fixed.**

1. **C37 sits on the wrong side of the crystal.**
   - `design/placement.py:280` anchors C37 to **Y1 pad 2**: `"C37": ("Y1", 2, -1.95, -0.05, 180, "T")`. Pad 2 is GND.
   - Y1.2 (GND, (7.55, 16.55)) therefore lies between C37.1 and Y1.3, and no direct F stub is possible.
   - The routed path (`decap.py`, track listing) is Y1.3 → F (9.84→10.56, 16.24) → U3.6 → F 0.35 mm → via (12.44, 16.36) → In2
     (12.44, 16.36) → (9.56, 14.94) → (8.76, 14.89) → (5.09, 15.01) → via → F 1.42 mm → C37.1.
   - **Y1.3 → C37.1 is 11.8 mm routed with 2 vias. U3.6 → C37.1 is 11.1 mm.**
   - Topologically the load cap is now a 10 mm stub on the far side of the MCU pin, not a cap at the crystal. The oscillator's
     load-cap current loop runs Y1.3 → MCU pin field → back under Y1 on In2 → C37 → GND.
   - Gate 4's fix item 1 asked for a "≤ 2 mm F.Cu stub" and to "delete the In1/B detour". The detour now runs on In2 instead.
   - The `placecheck` rule passes at 3.27 mm (< 3.5 mm) because it checks pad centres, not routed length.
2. **Other copper in the crystal area** (box x 4.6-10.0, y 12.2-17.3, `box.py`, `couple.py`):
   - **F:** I2C1_SCL is still **0.14 mm from C36.1** (HSE_IN): segment (7.19, 12.24) → (6.81, 12.24), 1.86 mm inside the box.
   - **In1:** **5V_SYS** (the ELRS 5 V feed) runs diagonally (10.74, 11.84) → (4.66, 18.01), 8.66 mm, straight under Y1.
     - It passes **directly under C37.1**: In1 GND is absent at (5.98, 16.50) (`at.py`).
     - It also passes under Y1.1 and the crystal centre: In1 void at (7.0, 15.5).
     - HSE_IN crosses this slot for 0.60 mm (`cross.py`).
     - CAM_SEL on In1 is 1.18 mm in the box.
   - **In2**, the layer HSE_OUT now uses, carries these nets in the box:
     - HSE_OUT 4.97 mm, NRST 3.53 mm, **CAM2_VID 2.33 mm** (analog video, which passes 0.09 mm in projection from C37.1), FLASH_WP 1.24 mm;
     - VTX_PWR_EN 0.43 mm from HSE_OUT;
     - GYRO2_INT 0.46 mm from HSE_OUT (`prox.py`).
   - Copper overlapping HSE_OUT (`couple.py`, within 0.5 mm):
     - CAM_SEL B under HSE_OUT for 2.15 mm, and In1 for 1.54 mm;
     - 5V_SYS In1 for 1.93 mm;
     - 3V3 B for 1.25 mm (C49.1 pad);
     - NRST In2 0.76 mm.
     In2 lies 0.21 mm above B, and B under the crystal box is only 58 % GND. It carries 3V3 6.1 mm, CAM_SEL 2.3 mm and the U11 video-switch pads.
   - The In1/In2 HSE_IN/HSE_OUT crossing at (10.34, 15.33) has In1 GND between the two, so it is shielded.
3. **Ground.**
   - Y1 is still on the isolated In1 piece #4 (59.7 mm², was 57.4). In1 under Y1 is 85 % copper, but only **14 %** of it is the main
     plane (`in1inv.py`).
   - C36.2 is alone on F fragment #10 with a single via (10.57, 13.06), 2.6 mm away, which lands on that island (`piece.py`).
   - C37.2 is 2.7 mm from its nearest via, (6.51, 14.21), which is on the main plane.

**Quantified effect.**
- Extra stray capacitance on HSE_OUT ≈ 0.8-1.1 pF. This is a closed-form estimate: In2 7.7 mm at roughly 0.04-0.06 pF/mm, F 2.5 mm at
  0.076 pF/mm, and 2 vias. HSE_IN has about 0.3 pF.
- CL shifts by about +0.2-0.4 pF, so start-up margin (D-07: gm_crit ≤ 0.86 mA/V) and frequency pulling (a few ppm) are **not** at risk.
- The coupling capacitances to the neighbours are small, about 0.02 pF for the 5V_SYS overlap under C37.1.
- The residual risk is jitter and spurs injected into an oscillator whose layout breaks AN2867's rules:
  - load caps next to the crystal;
  - short, symmetric traces;
  - no foreign nets under the crystal;
  - a solid ground beneath it.
  The HSE drives the 48 MHz USB clock and SYSCLK.
- Hence MAJOR, not BLOCKER. The decision log (D-27) and commit `08cadf9` record G4-01 as fixed, which overstates it.

**Fix.**
1. Move C37 to the Y1.3 side: south of Y1.3, about (9.25, 18.0) as the original anchor intended.
   - Move the VBAT_ADC via (9.29, 17.69) and nudge FB1 to make room.
   - Route Y1.3 → C37.1 as a ≤ 1.5 mm F stub, with C37.2 on its own GND via ≤ 0.5 mm away.
   - Delete the In2 run and both HSE_OUT vias.
2. Change `placecheck` for C36 and C37 to measure **the routed length from the Y1 signal pin** (≤ 2 mm), not the pad-centre distance.
3. Move 5V_SYS and CAM_SEL off In1 under Y1/C36/C37. Move I2C1_SCL ≥ 0.5 mm from C36.1. Add a rule area for other nets on F/In1/In2
   over Y1 + C36/C37.
4. Give C36.2 a via ≤ 0.5 mm away to the main In1 plane.

### G4-02 MAJOR: In1 is not a solid GND plane (still open, slightly worse)

**Evidence.** From `in1inv.py`, `in1.py`, and KiCad's own fill outline count (6).
- **208 segments, 327.5 mm, 39 nets on In1** (Gate 4: 192 segments, 327.9 mm, 39 nets).
  - Longest: ESC_TLM 17.1, STATUS_LED_GREEN 16.9, MOTOR8 16.2, 3V3 14.6, UART5_TX 14.2, SPI3_SCK 13.6, MOTOR5 12.7 mm.
  - Power nets: 3V3 14.6, 5V_SYS 9.2, 3V3A 4.7, 3V3_IMU 3.1 and VCAP2 2.4 mm.
  - VTX_VID (2.6 mm) is new on In1.
- In1 GND fill is 71.0 % of the board. The **main piece is 64.4 %** (Gate 4: 72 % / 67 %).
- **6 pieces:**

  | Piece | Area (mm²) | Location | GND via ties |
  |---|---|---|---|
  | Main | 835.0 | whole board | 55 |
  | 4 | 59.7 | x 4.9-18.5, y 5.5-20.2 (Y1, U6, FB1, VDDA caps, U9) | 9 |
  | 2 | 18.1 | x 13.6-21.7, y 2.8-9.1, new (G4C-03) | 1 |
  | 3 | 5.6 | | 1 |
  | 6 | 1.2 | | 2 |
  | 5 | 0.6 | | 1 |

- Coverage under parts (pad bounding boxes):

  | Part | In1 GND | of which main piece |
  |---|---|---|
  | U3 | 49 % | 26 % |
  | U6 | 85 % | **0 %** |
  | U7 | 57 % | 57 % |
  | Y1 | 85 % | 14 % |
  | U9 | 77 % | 4 % |

- Reference-plane split crossings (`cross.py`, F tracks over In1 slots):
  - 3V3 7.3 mm, UART5_RX 7.1, BEEPER 2.1, MOTOR2 2.0, SWDIO 1.8, I2C1_SCL 1.7 mm;
  - USB_DP 0.94 mm (MOTOR6 slot), USB_DM 0.30 mm (MOTOR5 slot), HSE_IN 0.60 mm (5V_SYS slot).
- The clocks themselves sit **in** the plane layer: SPI3_SCK 13.6 of 16.7 mm and SPI1_SCK 5.7 of 11.8 mm are on In1 (`ref.py`).

**Fix.** Same as Gate 4:
- restrict In1 to short hops that do not close contours;
- add a release check that In1 GND is exactly 1 outline with ≥ 90 % coverage.

D-27 says this needs the 6-layer stackup. I agree that is the realistic fix. On the 4-layer rev C it remains a MAJOR residual risk.

### G4-03 MAJOR: GND fragments bond sensitive and power grounds (still open, changed)

**Evidence.** `frag.py` (F/B GND copper groups = pour + GND pads + GND tracks, 8-connected):
- **F group #12 (81.6 mm², 8 vias + 7 U1.9 EP thermal TH)** contains:
  - **U3.12 VSSA**, C31.2/C32.2 (VDDA), C27.2 (VDD pin 19), C53.2 (RSSI filter);
  - **C1.2** (battery bulk 10 µF at (7.3, 28.6)), R15.2 (VBAT divider), **J5.2** (ELRS GND);
  - **U1.9** (5 V buck EP).

  At Gate 4 the VSSA/VDDA group (frag 15) and the U1-EP group (frag 18) were separate. In rev C they form one F web from (11.3, 19.3)
  down to U1 and C1 (bbox x 2.5-21.1, y 14.9-30.4). R15's move is the visible cause.
- **F #16 (21.7 mm², 1 via (22.69, 23.04) + 2 U2.9 TH):** C33.2 (VCAP1, 4.7 mm to the via), C28.2, C29.2. Unchanged.
- **F #21:** J2.2 (ESC GND), 1 via (20.11, 29.60), the C9 return. Unchanged.

**Fix.** Same as Gate 4: clear the F pour off the buck EP fields, and give each MCU/analog decap its own via within 0.5 mm. Additionally,
restore the separation of the VSSA/VDDA area from the U1/C1 web (a pour keep-out strip on F around y ≈ 22-23 at x 6-12).

### G4-04 MAJOR: MCU decoupling (still open, copper unchanged)

Routed pin-to-cap distances are from `decap.py`. They are centreline-graph lengths including pad-to-pad, so they are a little longer
than a manual trace.

| Pin | Cap | Routed | Vias / layers | Cap GND → nearest via (fragment) |
|---|---|---|---|---|
| VDD 1 | C25 | 5.86 mm | 0, F | 0.7 mm (#6, 1 via, shared with U8) |
| VDD 64 | C25 | 4.37 mm | 0, F | same |
| VDD 19 | C27 | 3.72 mm | 0, F | 0.8 mm (#12, U1 EP web, G4-03) |
| VDD 32 | C28 | **10.27 mm** (manual ≈ 8.5 mm: F 1.05 → via (21.94, 23.04) → In2 ≈ 6.2 → via (24.44, 27.24) → F 1.22) | 2, F/In2 | 2.5 mm (#16, 1 via + U2 EP) |
| VDD 48 | C26 | 6.55 mm | 2, B/F | 1.7 mm (#8, 1 via shared with C34) |
| VCAP1 31 | C33 | 0.62 mm | 0 | **4.7 mm** (#16) |
| VCAP2 47 | C34 | **8.08 mm** | F/In1 | 3.4 mm (#8) |
| VDDA 13 | C32 / C31 | 1.20 / 1.45 mm | 0 | 0.8 / 1.8 mm (#12) |

- VSS pins 18 and 63 reach their vias in 1.9 mm and 1.2 mm.
- **Both pin-63 vias, (16.61, 14.34) and (13.64, 13.01), land on In1 island #4, not on the main plane** (`piece.py`).

**Fix.** Same as Gate 4: every VDD to its 100 nF on F in ≤ 2 mm with no layer change, VCAP2 on F only, and cap GND vias ≤ 0.5 mm.

### G4-05 MAJOR: noisy nets through the IMU footprints (still open, unchanged)

`box.py`, pad box + 0.5 mm.

**U7 BMI270 (B, (20.80, 17.00)):**

| Layer | Copper in the box |
|---|---|
| F | UART1_TX 3.10, **MOTOR5 3.09**, LED_STRIP 1.72, UART1_RX 0.94, MOTOR6 0.74 mm |
| In1 | **MOTOR5 3.81**, GYRO2_CS 2.30, MOTOR6 1.47, UART6_RX 1.27 mm; GND 48 % |
| In2 (the plane 0.21 mm from the IMU pads) | **STATUS_LED_GREEN 3.31**, **LED_STRIP 2.13 mm**; GND 54 % |
| Vias in the box | MOTOR5, MOTOR6, LED_STRIP, UART6_RX, SPI1_SCK, SPI1_MOSI |

**U6 ICM-42688-P (B, (15.40, 17.00)):**

| Layer | Copper in the box |
|---|---|
| F | SPI1_MISO 3.6, SPI1_MOSI 2.1, VTX_PWR_EN 0.9 mm |
| In1 | 3V3_IMU 1.8 mm; all of it on island #4 (0 % main plane) |
| In2 | VTX_PWR_EN 3.63, SPI1_MOSI 1.58, NRST 1.22 mm; GND 66 % |

The IMU decaps are good: 0.68-0.83 mm routed.

**Fix.** Same as Gate 4.

### G4-06 MINOR: 5 V east branch (still open)

`s5v.py`:
- The east trunk carries **1.21 A** from (27.66, 29.11) through the single via **(25.76, 29.76)** into 0.35 mm B.Cu, (25.24, 30.21) → (20.11, 31.33).
- IPC-2221 external ΔT ≈ +12 °C (recomputed: 0.35 mm × 1 oz = 19 mil² at 1.21 A).
- Drops: P11 20.1 mV, D5 42.6 mV.
- The script's graph did not join the P8/J4 branch, a node-snapping artefact of nudged vias; DRC reports 0 unconnected. So the
  P8/J4 drops were not recomputed.

**Fix:** ≥ 0.8 mm trunk and ≥ 2 vias.

### G4-07 MINOR: 10 V vias (still open)

`s10.py`:
- L2 → P3 at 1.3 A passes the single vias (32.74, 27.59), (31.36, 29.54) and (26.12, 31.96) (nudged from rev B). Drop 24.7 mV.
- L2 → R41 passes 4 more single vias. Drop 52.1 mV.
- 0.45 mm track at 1.3 A: IPC-2221 ≈ +9 °C.
- A single 0.3 mm via (≈ 20 µm plating) at 1.3 A is close to a conservative (internal-k) IPC rating.

**Fix:** use 2 vias per transition.

### G4-08 MINOR: VBAT In2 neck to U2 (still open)

- `neck.py`: the U2 feed neck is **0.64 mm**, at the C8 return GND via (17.30, 24.60). The U1 feed neck is 2.96 mm.
- `fem.py` (0.5 oz, 65 °C):
  - P1 → U2 = **16.4 mΩ**, 21.3 mV at 1.3 A, peak **3.86 A/mm at (18.28, 25.08)**;
  - P1 → U1 = 2.1 mΩ.
- These are identical to Gate 4.

### G4-09 MINOR: USB (still open, unchanged)

- D+: J1 → F → U13.4/U13.3 → via (26.41, 17.66) → **In2 2.90 mm** → via (25.74, 14.84) → F → U3.45. Total 9.07 mm.
- D−: J1 → via (29.56, 15.11) → **B 4.80 mm** → via (24.81, 15.66) → F → U3.44. Total 8.24 mm.
  - U13.1/U13.6 are stubs of 0.97/0.35 mm.
- Slot crossings: D+ crosses the MOTOR6 In1 cut (0.94 mm) and D− crosses MOTOR5 (0.30 mm).
- U13.5 VBUS → C51 is 14.23 mm, so there is no local cap.
- The single-ended impedance of the 0.2 mm F trace is about 67-73 Ω (closed form, w/h ≈ 0.95, εr 4.4).

FS USB tolerates all of this, hence MINOR. **Fix:** same as Gate 4.

### G4-10 MINOR: analog inputs near the SW nodes (still open)

- ESC_CURR: 5.04 mm on In2 inside U1's pad box, plus In1 over L1.1 (SW pad), −0.55 mm in projection.
- VBAT_ADC: 11.6 mm on In1 across U1.
- RSSI_IN and RSSI_ADC still cross the SW pads and tracks (with In1/In2 GND between).
- The ESC_CURR/VBAT_ADC/RSSI copper is unchanged from rev B.

### G4-11 MINOR: 5 V feedback sense (still open)

- R4's top is still fed from via (12.66, 22.96).
- That via sits on the 0.35 mm F trace (12.06, 28.26) → (12.14, 25.46) → (12.66, 22.96), which runs over U1.8 (SW): −0.13 mm in projection (`prox.py SW_5V`).

### G4-12 MINOR: dangling vias (still open)

The DRC lists the same 17 nets as Gate 4: BEEPER, CAM_SEL, MOTOR8, ESC_TLM, UART2_RX, **SPI1_SCK, SPI1_MISO**, GYRO1_INT, MOTOR1,
MOTOR4, STATUS_LED_BLUE, SWDIO, SWCLK, UART5_RX, **SPI3_SCK, SPI3_MOSI**, MOTOR7. Most are under the MCU, where In1 is 49 % copper.

### G4-13 MINOR: GND stitching (still open)

- 53 GND vias (Gate 4: 52), all 0.6/0.3 mm, plus 20 GND TH: U1/U2 EP thermal vias and the J1 shell.
- 3 GND vias within 2 mm of the edge, and 10 within 3 mm.
- F has 21 GND copper groups and B has 13. **20 of the 34** are tied by a single via or TH.
- J2.2 still has 1 via, and J5.2 is 4.7 mm from its nearest via.

### G4-14 INFO: stackup (partly fixed)

- `docs/assembly_and_bringup.md:23-24` now states JLC04161H-7628 with 1 oz outer and 0.5 oz inner copper.
- The board has no `(stackup)` section.
- `fab/gerbers/F405FC-job.gbrjob` still has 3 × 0.48 mm FR4 and 0.035 mm inner copper, `"Finish": "None"` and `"Revision": "rev?"`.

### G4-15 INFO: `review/summary.md` missing (still open)

D-22 points to it for the In1 inventory and D-27 for the rev C residual risks, but the file does not exist. The pipeline step 9 in
`design/agent_brief.md` requires it.

### G4-16 INFO: video (changed)

- VTX_VID is now B 1.28 mm + **In1 2.64 mm**, (4.44, 15.94) → (2.07, 16.39) (was B/F). It is a new In1 cut, near the west edge.
- CAM2_VID is on In2 for 4.76 mm, (2.76, 16.11) → (7.16, 17.69), 0.09 mm (in projection) from C37.1.
- Both are more than 10 mm from either SW node.

---

## Part 2: new findings (own review)

### G4C-02 MAJOR: VDD pin-32 decoupling track runs over the 10 V buck's input loop (missed at Gate 4)

**Evidence.**
- The 3V3 In2 segment **(23.19, 22.79) → (24.44, 27.24)** (0.2 mm, 4.62 mm) is the middle of the pin-32 → C28 path (G4-04).
  - It runs at x ≈ 23.3-24.4, y 22.8-27.2.
  - That is directly over U2's left pin row: U2.4 RT (23.9, 22.70), **U2.3 VIN (23.9, 23.97)**, U2.2 EN, **U2.1 GND (23.9, 26.51)**,
    pads x 23.12-24.67. Only the 0.21 mm In2–B dielectric separates them.
- U2's hot loop is C12.1 → 0.8 mm VBAT track (21.95, 24.46) → (23.9, 23.97) → U2.3 … U2.1 → GND (21.95, 26.4) ← C12.2.
  - Its pin-3 → pin-1 leg runs in y, **parallel to and under** the 3V3 trace.
- In2 coverage over the hot-loop box x 21.47-24.67, y 23.67-26.81: **GND 58 %, VBAT 23 %, 3V3 track 7 %, void 13 %**.
  - The ASCII raster shows a continuous slot along the pin row, from y 22.4 to 27.4.
  - Gate 4's "Checked and OK" line "In2 above … U2's loop is GND" is therefore not correct.
- Order of magnitude, not simulated:
  - mutual inductance of 2.5 mm of parallel conductor at about 0.5 mm ≈ 0.5-0.7 nH;
  - with input-current edges of about 1.3 A in 5-10 ns, that gives **tens to ~150 mV** spikes;
  - they are induced in series with the decoupling path of VDD pin 32, at 750 kHz.
- The same trace also cuts U2's In2 GND image plane between the hot loop and the EP.

**Fix.**
- Route pin 32 to a 100 nF on F next to the pin. There is free space below pins 30-32 (G4-04).
- Remove the In2 3V3 segment.
- Keep In2 solid GND (or VBAT) over x 21-25, y 22-27.5.
- Add a rule-area keep-out on In2 over both buck hot loops.

### G4C-03 MINOR: new In1 island from the NRST re-route (rev C regression)

**Evidence.**
- Comparing rev B and rev C fills: In1 went from 5 to 6 pieces, and the main piece shrank from 865.3 to 835.0 mm².
- The new piece #2 (18.1 mm², x 13.6-21.7, y 2.8-9.1) is tied by **one** GND via (19.09, 8.71).
- The cause is the NRST via moving from (14.56, 3.14) to **(13.51, 3.31)**. Its antipad, together with the existing In1 tracks
  (UART5_TX, UART3_TX, STATUS_LED_*, SWDIO, I2C1_SDA, UART1_TX), closes the neck: In1 lost 0.54 mm² at x 13.04-13.92, y 2.84-3.80.
- Parts over the island: U8 BMP390, C43/C44, J3 (HD VTX), R37, and on B C18 (5V_SYS LDO input cap) and TP1-TP5.

**Fix.** Move the NRST via back east of x ≈ 14.4, or re-route one of the In1 tracks that bound the neck. Add the 1-piece check from G4-02.

### G4C-04 MINOR: BMI270 ground

**Evidence (`frag.py`).**
- U7.6 and U7.7 (GND) are on B group #3 (22.8 mm², 4 vias). Their nearest via is **3.0 mm** away, at (21.31, 13.11)/(21.99, 13.16).
- Two of that group's four vias, **(25.14, 17.94) and (25.68, 17.85)**, are U13.2's (USB ESD clamp) GND vias.
  - So an ESD event on the USB connector returns partly through the copper that grounds the BMI270.
- The group also carries Q2.2, C23.2 (3V3_IMU LDO output cap), C41.2 and C42.2.
- U6 (ICM-42688-P), by contrast, is on the main B pour with its GND pads 0.7-1.4 mm from vias.

**Fix.** Add a GND via within 0.5 mm of U7.6/U7.7 (outside the LGA, beside pins 6/7), and give U13.2 its own vias away from the IMU copper.

### G4C-05 MINOR: dangling VBAT_ADC stub from R15's move (rev C regression)

**Evidence.**
- The DRC `track_dangling` warning is at (7.49, 24.99). The whole chain from R15.1 (8.11, 23.60) → (8.44, 23.84) → (7.74, 24.21) →
  (7.54, 24.46) → (7.49, 24.99) → **(7.11, 25.44)** is a ≈ 2.2 mm open stub. It is the old route to R15's rev B position, (6.99, 25.19).
- It hangs on the high-impedance divider node (VBAT_ADC) and ends over U1.3 (VIN) and U1.2 (EN) on B.
- In1 GND is present underneath, so the pickup is small. The 10 nF C24 at the MCU filters it.

**Fix.** Delete the stub segments (and keep it out of the release check: treat `track_dangling` as an error).

### G4C-06 INFO: verification notes

- The release Gerbers equal the current board (origin offset only), and the zone fills are current (KiCad in-memory refill matches).
- DRC with `--schematic-parity`: 0 errors, 0 unconnected, 0 parity.

## Checked and OK (rev C)

- **Hot loops.**
  - U1: C4 (100 nF 100 V, B) pads are 0.69 mm from U1.3/U1.1.
    - Loop: VBAT 0.8 mm (3.05 → 7.5, 24.97), then C4.2 → GND via (6.6, 28.2) and B pour to U1.1.
    - In2 above the U1 loop is **100 % VBAT** zone, which is a valid AC image plane.
  - U2: C12 pads are 0.70 mm from U2.3/U2.1, on 0.8 mm tracks. The In2 image plane above U2 is compromised; see G4C-02.
- **SW nodes.**
  - SW_5V: U1.8 → C5 0.6 mm and → L1.1 0.8 mm (13.42, 28.4 → 30.85), on B only.
  - SW_10V: U2.8 → L2.1 0.8 mm, 4.3 mm long, and → C13 0.6 mm, on B only.
  - In2 GND is present above them at (12.9, 27.5), (13.4, 29.5), (13.4, 31.5), (29.3, 26.5), (29.4, 28.0), (29.4, 31.0) and (30.4, 26.3).
  - In1 is void at (12.9, 27.5) and (13.4, 29.5), under ESC_TLM/BUZ cuts; In2 GND remains between those and the SW copper.
  - Distances: IMUs more than 9 mm away, Y1 more than 10 mm.
- **LDO, sensor and IMU decaps.**
  - U4 0.75/2.12 mm, U5 0.70/0.90 mm, U11 0.67 mm.
  - U8 0.71-1.0 mm (pin 6 has a longer, second path).
  - U9 0.97-2.1 mm.
  - IMUs 0.68-0.83 mm.
  - U10 → C48 5.3 mm with 2 vias, which is minor and unchanged.
- **HSE_IN.** Y1.1 → C36.1 0.62 mm and Y1.1 → U3.5 3.67 mm, F only, no vias.
- **No floating GND copper.** Every F/B GND group contains at least one via or TH.

## Power distribution (rev C, unchanged from Gate 4 except where noted)

| Path | Width / layer | Current | IPC-2221 ΔT | Drop | Vias |
|---|---|---|---|---|---|
| VBAT P1 → U1 (In2 zone) | ≥ 2.96 mm neck | 2.0 A | — | 4.1 mV (2.1 mΩ) | 3-4 |
| VBAT P1 → U2 (In2 zone) | 0.64 mm neck | 1.3 A | — | 21.3 mV (16.4 mΩ) | 3 |
| 5 V L1 → C6/C8 | 0.8 mm B | 1.8 A | ≈ +8 °C | — | — |
| 5 V east trunk | 0.35 mm B, 1 via | 1.21 A | ≈ +12 °C | P11 20 mV, D5 43 mV | 1 |
| 10 V → P3 | 0.45 mm F/B | 1.3 A | ≈ +9 °C | 24.7 mV | 3 single |
| 10 V → R41/J3 | 0.45 mm F/B | 1.0 A | ≈ +6 °C | 52.1 mV | 4 more single |
| 5V_SYS D5 → U4/U5/J5 | 0.2 mm B/F/In1 | ≤ 0.41 A | ≈ +3 °C outer | 2.2 / 6.9 / 17.8 mV | — |

## Not verified

- **No field solving.** I did no field solving of impedance, crosstalk or the mutual inductance in G4C-02. All capacitance and
  inductance figures are closed-form, order-of-magnitude estimates. The JLC dielectric thicknesses are recalled, not read from a
  JLC document.
- **No simulation.** I did not simulate or measure EMI, HSE jitter or start-up, ADC noise, gyro noise, or supply bounce at pin 32.
- **Temperature and via ratings.** Temperature rises are IPC-2221 only (no IPC-2152, no thermal simulation). The via current
  comments assume about 20 µm barrel plating, not a JLC figure.
- **Rev B baseline.** For the "what changed" diff I used the previous reviewer's dump `/opt/kroot/tmp/g4/board.json`
  (md5 `b0414471…`, per the Gate 4 report). I did not regenerate it from git history.
- **5 V solve.** The graph did not join the P8/J4 branch (node snapping after via nudges), so the P8/J4 drops were not recomputed
  for rev C. KiCad DRC reports the net as connected.
- **3V3 PDN.** The 3V3 track graph splits into components the script could not join (U4.3 not attached), so I did not compute a
  3V3 DC drop from U4 to the MCU pins.
- **Routed lengths.** These come from the centreline graph (0.2 mm snap, via ≈ 0.53 mm per hop). I hand-checked the key ones:
  HSE_OUT, pin 32 → C28, USB, and the 5 V/10 V trunks.
- **Fragment counts.** `frag.py` merges GND pads and tracks into pour groups, so its group counts (21 F, 13 B) are not directly
  comparable with Gate 4's 25/14 pour fragments.
- **Datasheets and layouts.** I did not read the USBLC6-2SC6 or ECS crystal datasheets. I did not compare against the LMR38020 EVM
  or the AN2867 text; the AN2867 rules are cited from general knowledge.
- **Other Gerber layers.** I did not open the stencil, drill or silk Gerbers. Only F/In1/In2/B copper was compared with the release files.
- **Electrical behaviour.** The capacitor DC-bias derating and the cap SRF/ESL were not checked.
