# Gate 4 (rev D, 6-layer): signal integrity / power integrity review

Reviewer: fresh, independent Gate 4 SI/PI agent, 2026-10-15. This is a review only. The only file I wrote in the repo is this report
(not committed). Scratch scripts and data are in `/opt/kroot/tmp/g4d/` (`/tmp/g4d/` inside the chroot).

**Board reviewed:** `kicad/F405FC.kicad_pcb`, master HEAD `0524b43`, md5 `df8f70f5ec8f3499b7965f65a129a286`. The board was last
changed in `a46f5d2`, the same commit as the fab outputs. `git status` was clean apart from this report.

## Method

| Step | Tool | Result |
|---|---|---|
| DRC + parity | `kicad-cli pcb drc --schematic-parity --severity-all` (`/tmp/g4d/drc.json`) | 0 errors, 0 unconnected, 0 parity. Warnings: 16 `via_dangling` and 1 `silk_overlap` |
| Placement check | `kc 'python3 gen/placecheck.py'` | PASS (but see G4D-01: it checks pad centres, not routed length) |
| Geometry dump | `dump.py` (pcbnew, read-only, no save) to `board.json` | 1995 tracks, 267 vias (all F–B through, 0.6/0.3 mm), 495 pads, 33 zones |
| Plane analysis | `plane.py`, `voids.py` (0.02 mm raster of the stored zone fills) | Plane piece count, coverage and void shapes |
| Routed paths | `graph.py`, `decap.py`, `trans.py` | Track/via graph per net: pin-to-cap length, vias, layers, nearest GND via |
| Coupling | `prox.py`, `couple.py`, `broad.py` | Same-layer edge gaps and parallel lengths; In2/In3 broadside overlap |
| VBAT zone | `vbat.py` | Neck width (distance-transform bisection) and a 2-D finite-difference resistance of the In3 VBAT fill |

Coordinates are board mm (file coordinates minus (100, 100)), as in the earlier reports. Copper resistances assume 1 oz outer and
0.5 oz inner copper at 65 °C. Temperature rises are IPC-2221 estimates.

**Stackup.**
- The board file has **no `(stackup)` section**.
- `fab/gerbers/F405FC-job.gbrjob` carries KiCad's default stackup: 5 × 0.274 mm FR4, 35 µm on every layer, `"Finish": "None"`,
  `"Revision": "rev?"`.
- `docs/assembly_and_bringup.md:23` says to pick "a JLC 6-layer 1.6 mm stackup" at order time, without a name or thicknesses.
- For reference planes I assume F and In2 reference In1, and In3 and B reference In4. See G4D-05 for why this is not guaranteed.

## Verdict: **FAIL** (0 BLOCKER, 2 MAJOR)

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 2 |
| MINOR | 12 |
| INFO | 5 |

**Summary.**
- The 6-layer change worked for the planes. In1 and In4 are each **one solid GND piece** with **no tracks**, and no signal track
  anywhere crosses a plane void (G4D-10).
- Gate 4's former MAJORs G4-02, G4-05, G4C-02, G4C-03 and G4C-04 are fixed. The crystal (G4-01/G4C-01) is essentially fixed.
- Two new MAJORs come from the rev D routing:
  1. **CURR_ADC** has its 10 nF filter cap at the wrong end of a **70 mm** In2/In3 loop around the whole board (G4D-01).
  2. **SPI1_MOSI and LED_DIN are routed through the U1/U2 buck footprints** on the bucks' own (noisy) layer. They pass beside the
     BST/SW pins, 0.14 mm from both feedback nodes, and they split the B GND pour (G4D-02).
- Most of the PDN MINORs from rev B/C (G4-06, -07, -08, -09, -11, -12, -13) are still open with unchanged copper.

| ID | Sev | Title | Status vs earlier gates |
|---|---|---|---|
| G4D-01 | **MAJOR** | CURR_ADC: MCU pin 9 → filter cap C52 is 70.4 mm routed (3 vias, 56 mm on In2). It loops round the board past VBUS, the USB pair, MOTOR1/8 and ESC_TLM | New (rev D routing) |
| G4D-02 | **MAJOR** | SPI1_MOSI (IMU bus) runs 5.2 mm inside U1 and LED_DIN 6.0 mm inside U2 on B. They pass 0.14 mm from FB_5V/FB_10V and 0.17-0.33 mm from BST/SW. They split U1's and U2's B ground pours | New |
| G4D-03 | MINOR | Crystal residuals: I2C1_SDA 0.139 mm from C36.1 (HSE_IN). CAM_SEL via 0.149 mm from the HSE_OUT track | G4-01/G4C-01 fixed; residual |
| G4D-04 | MINOR | MCU PDN residuals: pin 48's 100 nF (C26) is 14.1 mm routed with 2 vias. VSS pin 18 has 1 via at 2.5 mm. C28 and C53 GND share F fragments with the buck EP vias | G4-03/G4-04 largely fixed; residual |
| G4-06 | MINOR | 5 V east trunk: 0.35 mm B for 9.8 mm plus one 0.3 mm via, about 1.2 A | Still open (unchanged) |
| G4-07 | MINOR | 10 V: L2 → P3 through 3 single vias, L2 → R41 through 5 | Still open |
| G4-08 | MINOR | VBAT zone (now In3) neck to U2 is 0.64 mm: 16.4 mΩ, 3.85 A/mm | Still open (identical numbers) |
| G4-09 | MINOR | USB D+/D− on different layers, ESD pins as stubs, U13 VBUS cap 10.3 mm away | Still open (changed layers) |
| G4-11 | MINOR | 5 V sense / west branch runs 3.4 mm alongside L1's SW pad at 0.16 mm | Still open (changed) |
| G4-12 | MINOR | 16 dangling signal vias | Still open (16, was 17) |
| G4-13 | MINOR | GND stitching: 4 GND vias within 2 mm of the edge; 7.1 % of the board is > 4 mm from a GND via | Still open |
| G4D-05 | MINOR | Stackup undefined, so the In2 reference is unknown. In2/In3 broadside overlaps (up to 4.6 mm), and In2 tracks run over the In3 VBAT zone | New (6-layer specific) |
| G4D-06 | MINOR | 3V3_IMU is 26 mm on 4 layers with 5 vias, alongside UART3/UART5/SPI3_SCK at 0.13-0.15 mm | G4-05 residual |
| G4D-07 | MINOR | EN_5V (UVLO divider node, ≈ 75 kΩ) is routed between C4's pads inside U1's input hot loop, 18.6 mm long | New |
| G4D-08 | MINOR | Flash U10 VDD → C48 is 9.65 mm with 2 vias | Was a "minor" note in rev C; now longer |
| G4D-09 | INFO | 3V3 is a 0.2 mm track tree: U4 → pin 32 is 47 mm, 5 vias, ≈ 0.21 Ω. No 3V3 pour, although In3 has room | New |
| G4-14 | INFO | No stackup in the board. The job file has default 5 × 0.274 mm, 35 µm inner copper, Finish None, rev? | Still open |
| G4-15 | INFO | `review/summary.md` does not exist (D-22 and D-27 point to it for the In1 / inner-5V inventories) | Still open |
| G4-16 | INFO | Video: short, ≥ 10 mm from the SW nodes. CAM1_VID runs 1.46 mm beside 5V on F at 0.20 mm | Essentially unchanged |
| G4D-10 | INFO | Verified OK: plane integrity, hot loops, SW nodes, IMU environment, VDDA, VCAP, LDO decaps | Verification note |

---

## Part 1: previous findings re-checked

| ID | Rev C status | Rev D status | Evidence |
|---|---|---|---|
| G4-01 / G4C-01 (crystal) | MAJOR | **Fixed**, residual MINOR → G4D-03 | HSE_OUT Y1.3 → C37.1 = **2.89 mm on F, 0 vias**. U3.6 → Y1.3 is 0.72 mm. HSE_IN: Y1.1 → C36.1 0.62 mm and U3.5 → Y1.1 2.76 mm, both F only (`graph.py`). In1 GND under Y1's pads is 100 %. Only F carries foreign copper at the crystal (In1 is solid between it and In2/In3/B). C37 is still beside Y1's GND pad 2: the route runs under the crystal body between the pad rows at y = 15.64 |
| G4-02 (In1 not a plane) | MAJOR | **Fixed** | 0 tracks on In1/In4. In1 and In4 each 1 fill polygon (1060 mm²), and the Gerbers each have 1 `G36` region. Coverage is 81.8 % of 1296 mm²; the losses are via antipads, the edge band and the hole keep-outs. Largest void is a 3.4 mm cluster of 7 antipads at (18.3-21.8, 12.6-15.7) under the MCU. Track length over plane voids, excluding the track's own antipads: F 0, In2 0.32 mm (CURR_ADC), In3 0, B 0 |
| G4-03 (F fragments bond decaps to buck EPs) | MAJOR | **Changed → MINOR** (in G4D-04) | F group #27 (35.6 mm²): C28.2 and U12.1/.3 with 2 vias + 6 U2 EP TH. F group #28 (16.1 mm²): C53.2 + U1 EP TH. VSSA/VDDA are no longer on the U1 web (U3.12 fragment has 7 ties). Solid In1 is now 1 dielectric below every F fragment, so fragment sharing matters far less |
| G4-04 (MCU decoupling) | MAJOR | **Largely fixed**, residual MINOR → G4D-04 | Routed, F only, 0 vias: pin 1 → C25 2.19 mm; pin 64 → C25 1.25; pin 19 → C27 2.28; **pin 32 → C28 4.07** (was 8.5-10.3 via In2); VCAP1 → C33 0.73; **VCAP2 → C34 4.50** (was 8.1 via In1); VDDA → C32/C31 0.93/1.56. Pin 48 → C26 is 14.07 mm (G4D-04) |
| G4-05 (noisy nets through IMUs) | MAJOR | **Fixed** (residual 3V3_IMU → G4D-06) | Inside U6/U7 pad box + 0.5 mm on B (the IMU layer, next to the In4 plane) there are only IMU nets plus NRST 0.61 mm at U6. No MOTOR5/6 or LED_STRIP on any layer in the boxes. F/In2/In3 copper there is shielded by In4 + In1. Foreign vias through the boxes: NRST and CURR_ADC (U6), STATUS_LED_GREEN (U7) |
| G4-06 (5V east trunk) | MINOR | **Still open** | L1.2 → P11: B 8.06 mm (0.35 mm, (25.24, 30.21) → (15.71, 32.54)) plus 1 via (25.76, 29.76). About 1.21 A ⇒ IPC-2221 external ≈ +12 °C |
| G4-07 (10 V single vias) | MINOR | **Still open** | L2.2 → P3: 16.5 mm, **3 vias**. L2.2 → R41: 39.1 mm, **5 vias**. All 0.45 mm tracks; every via is single |
| G4-08 (VBAT neck) | MINOR | **Still open** | The VBAT zone moved from In2 to In3 with the same outline. Neck to U2 **0.64 mm** at GND via (17.30, 24.60). FD solve P1 → U2 vias **16.4 mΩ** (21.3 mV @ 1.3 A), peak **3.85 A/mm at (18.28, 25.08)**. P1 → U1 is 2.1 mΩ. Identical to rev C |
| G4-09 (USB) | MINOR | **Still open, changed** | D+: J1 → F → via (26.71, 15.66) → **In3 2.39 mm** → via (24.54, 15.14) → F → U3.45 (6.7 mm). D−: J1 → F → In3 1.55 → **B 2.38 mm** → F → U3.44 (7.1-8.6 mm, 2-3 vias). U13.3/U13.1 are stubs, ≈ 1 mm. U13.5 VBUS → C51 is 10.3 mm |
| G4-10 (analog near SW) | MINOR | **Fixed as stated**; superseded by G4D-01 | ESC_CURR is now F only (13.8 mm) and VBAT_ADC is F 12.3 / In2 1.8 / B 0.5, all shielded from the B-side bucks by In4 + In1. Residual: RSSI_ADC via 0.47 mm and BUZ_N via 0.16 mm from the SW_5V track on B |
| G4-11 (5 V sense near SW) | MINOR | **Still open, changed** | R4.1 is fed L1.2 → B → (12.59, 32.71 → 31.34) → via (11.41, 30.16) → In3 → R4 (14.8 mm, 2 vias). The B leg runs **3.37 mm parallel to L1.1 (SW_5V) at 0.162 mm** (`couple.py 5V`). It is also the west 5 V load branch, so it is not a Kelvin tap |
| G4-12 (dangling vias) | MINOR | **Still open** | 16 `via_dangling`: UART5_RX, MOTOR7, BEEPER, CAM_SEL, MOTOR8, UART2_RX, SPI1_SCK, SPI1_MISO, GYRO1_INT, MOTOR1, MOTOR4, STATUS_LED_BLUE, SWDIO, **GYRO2_CS** (new), SPI3_SCK, SPI3_MOSI. Most are under U3, where In1/In4 coverage is 77.6 % |
| G4-13 (stitching) | MINOR | **Still open** | 64 GND vias + 20 GND TH (U1/U2 EP 8 each, J1 4). 4 vias within 2 mm of the edge, 10 within 3 mm. Max distance to a GND via is 9.1 mm (corner (35.25, 35.25)). 7.1 % of the area is > 4 mm from one: x 26-32/y 0.5-6, x 28-35/y 29-35, x 0.5-5/y 22-32, x 4-9/y 0.5-4. 20 of 33 F and 7 of 12 B GND pour pieces have exactly one via tie |
| G4-14 (stackup) | INFO | **Still open** | See Stackup above and G4D-05 |
| G4-15 (summary.md) | INFO | **Still open** | `ls review/summary.md` → no such file |
| G4-16 (video) | INFO | Essentially unchanged | CAM1_VID F 2.2 / B 2.5 mm; CAM2_VID B 0.9 / In2 4.6 mm; VTX_VID B 1.5 mm. U11 (4.8, 16.9) is > 13 mm from both SW nodes. CAM1_VID runs beside 5V (F) for 1.46 mm at 0.199 mm |
| G4C-02 (pin-32 3V3 on In2 over U2) | MAJOR | **Fixed** | Pin 32 → C28 is F only. The In3 3V3 run at y = 23.14 is separated from the B-side U2 by In4 GND (U2 pad box: In4 99.3 % GND) |
| G4C-03 (NRST In1 island) | MINOR | **Fixed** | In1 is 1 piece |
| G4C-04 (BMI270 GND) | MINOR | **Fixed** | U7.6/U7.7 → GND via (19.20, 15.53) at 0.56/0.75 mm on the main B pour (54 ties). U13.2 is now on the main F pour |
| G4C-05 (VBAT_ADC stub) | MINOR | **Fixed** | No `track_dangling` in DRC |

---

## Part 2: findings

### G4D-01 MAJOR: CURR_ADC filter cap at the wrong end of a 70 mm loop

**Evidence**
- Net pads: R38.2 (8.08, 24.66) F (the 10 k series resistor); C52.1 (9.995, 18.59) B (the 10 nF filter cap); U3.9 (11.325, 17.75) F (the ADC pin).
- Routed topology (`graph.py`, track listing):
  1. R38.2 → F → via (10.04, 22.71) → B → C52.1. The cap node is fine: 9.27 mm.
  2. From that via, CURR_ADC continues: **In3** (10.34, 23.01 → 28.49) → via (10.34, 28.49) → **In2**.
  3. The In2 leg runs (10.34, 29.81) → (13.46, 32.94) → (19.46, 32.94) → (24.46, 27.71) → (27.71, 22.89) → (31.71, 17.91) → (31.71, 13.41)
     → (30.04, 13.34) → (24.44, 14.61) → (20.39, 16.04) → … → (14.84, 16.44) → via (13.49, 17.79).
  4. It then goes F 1.2 mm to U3.9.
- **U3.9 → C52.1 = 70.44 mm, 3 vias** (B 5.8, In3 5.9, In2 56.0, F 1.2 mm). The net is 74 mm routed against a 7.9 mm pad MST: a
  9.3× detour. The next-worst net in the board is 2.7× (SPI1_MOSI).
- Same-layer neighbours of the unfiltered In2 leg (`couple.py CURR_ADC 0.25`; edge gap; parallel length):

  | Net | Parallel length | Gap |
  |---|---|---|
  | **VBUS** | 5.24 mm | 0.136 mm |
  | **ESC_TLM** | 1.52 mm | 0.137 mm |
  | **MOTOR1** (DShot) | 1.16 mm | 0.137 mm |
  | **MOTOR8** (DShot) | 1.11 mm | 0.137 mm |
  | USB_DP | 0.98 mm | 0.150 mm |
  | USB_DM | 0.40 mm | 0.22 mm |
  | 3V3_IMU | 1.30 mm | — |
  | SPI3_SCK | 0.70 mm | — |
  | VTX_PWR_EN | 0.71 mm | — |
  | 5V | 0.66 mm | — |

  It also has broadside overlap with STATUS_LED_GREEN on In3 for 1.96 mm (`broad.py`), and it is the only signal that crosses an
  In1 void (0.32 mm).
- `gen/placecheck.py` passes this ("C52 -> U3 CURR_ADC 1.57 mm (max 6.0) (other side, via)") because it measures pad-centre distance.
- Order of magnitude (estimate, not simulated):
  - Coupling: about 0.03 pF/mm at 0.14 mm on In2, so MOTOR1 + MOTOR8 + ESC_TLM ≈ 0.1 pF.
  - The node behind the 70 mm trace is about 8 pF of trace (≈ 0.12 pF/mm) to the far 10 nF, through ≈ 50-70 nH of trace inductance.
  - A 3.3 V DShot edge therefore gives tens of mV of ringing at the ADC pin. The ADC LSB is 0.8 mV.
  - The RC filter (fc ≈ 1.6 kHz) does nothing for pickup that is injected after it.
- Effect: current-sensor readings, and so mAh and current limiting, pick up motor- and USB-correlated noise. The analog intent of
  D-23 (10 k + 10 nF at the pin) is defeated.

**Fix**
1. Route U3.9 → C52.1 directly: C52 is on B 1.6 mm from the pin, so use one via beside U3.9 down to C52.1, with ≤ 3 mm total.
2. Delete the In3/In2 leg.
3. Change `placecheck.py`, or add a route check, so that the analog filter caps (C24, C52, C53) and decaps are judged on **routed
   pin-to-cap length** (for example ≤ 3 mm) with a detour-ratio report for every net.

### G4D-02 MAJOR: sensitive and noisy signals routed through both buck footprints on B

**Evidence (`prox.py`, `couple.py`, box listing).** The bucks, their SW/BST nodes and the B GND pour that carries their return are
on B. LMR38020 datasheet §9.5.1.1 (`datasheets/lmr38020.pdf`, text lines 1517-1523): "The GND trace, as well as the VIN and SW
traces, must be constrained to one side of the ground planes. The other side … must be used for sensitive routes." §9.5.1 also
says the FB path "must not be routed near any noise source (such as the SW node)".

**U1 (5 V buck, B, (10.2, 25.6)).**
- **SPI1_MOSI**, the shared MOSI of both IMUs, has 5.21 mm of B copper inside U1's pad box + 0.3 mm.
- Its path: via (14.99, 25.54) → (12.14, 25.54) → (11.91, 25.31) → (11.91, 24.61) → (12.31, 24.21) → (13.71, 24.21) → (15.01, 22.89).
  - It runs between U1's EP and the right pin row, and leaves between pin 6 (PG, n/c) and pin 7 (**BST_5V**).
  - Gaps: BST pad **0.334 mm**, SPI1_MOSI via 0.34 mm from BST, **FB_5V 0.144 mm** (0.26 mm long).
- SW_5V on B also has a BUZ_N via at 0.162 mm, a BEEPER via at 0.333 mm and a RSSI_ADC via at 0.474 mm.

**U2 (10 V buck, B, (26.6, 24.6)).**
- **LED_DIN**, the off-board WS2812 data line after R33 (330 Ω), runs x ≈ 28.3, y 22.3 → 27.1 between U2's EP and pins 5-8. That
  is 6.0 mm inside the box.
- Parallel runs: **FB_10V 1.52 mm at 0.140 mm**, BST_10V 0.95 mm at 0.167 mm, **SW_10V 0.95 mm at 0.180 mm**.
- A MOTOR8 via sits at (24.21, 27.24), beside U2.1 (GND).

**Ground split.**
- These two tracks are what separates the B GND pour into two groups (`decap.py` fragment labelling; boundary-gap tracks are LED_DIN
  3.49 mm and SPI1_MOSI 2.43 mm):
  - group #1 (567 mm²): P2, U1.1/U1.9, C4, C2, C3;
  - group #10 (82.6 mm²): U2.1/U2.9, C12, C10, **and the 5 V output caps C6, C8, C9** plus C14, C16.
- So the 5 V output-ripple return and all of U2's return must go through vias into In4/In1 instead of the B pour.

**Magnitude (estimates).**
- FB_10V's source impedance is R9 ∥ R10 ≈ 9.9 kΩ. About 0.04 pF of coupling to a 5 V LED_DIN edge, against a few pF of pin/trace
  capacitance, gives a transient of order tens of mV on a 1.0 V reference.
- SW_10V couples into LED_DIN behind 330 Ω, with about 0.03 pF × 5 V/ns ≈ 0.15 mA, i.e. about 50 mV. That rides the LED cable off
  the board as EMI.
- SW/BST edges onto SPI1_MOSI are small at the driver (MOSI is push-pull), but the trace carries them to both IMUs.
- None of these is a functional failure on its own. All of them break the datasheet's layout rule on a board whose key metric is gyro
  noise, and they compromise both converters' FB nodes.

**Fix**
- Move SPI1_MOSI off B around U1. F or In2 are available, and both are shielded by In1/In4.
- Move LED_DIN off B around U2: In3 or F, or keep it on B outside the U2 pin box and ≥ 1 mm from SW/BST/FB.
- Add B-layer rule areas (no foreign tracks or vias) over each buck's pad box + 0.5 mm and over the C4/C12 → L1/L2 power area, as was
  already done for the L1/L2 bodies.
- After the moves, re-check that B GND around U1 → C6/C8/C9 is one pour group.

### G4D-03 MINOR: crystal residuals (G4-01 follow-up)

- **I2C1_SDA** on F, (7.54, 12.24) → (5.81, 12.24), passes **0.139 mm** from C36.1 (HSE_IN load cap; pad y 12.44-13.06) for about
  0.56 mm (`prox.py HSE_IN`). Rev C had I2C1_SCL at the same spot.
- A **CAM_SEL** via at (6.39, 15.49) is 0.149 mm from the HSE_OUT track for 0.77 mm. CAM_SEL is a static PINIO, so this is a low risk.
- HSE_IN and HSE_OUT run end to end under Y1 (0.17-0.3 mm, 0.9 mm), which adds a few fF across the crystal. That is negligible against C0.
- Y1.4 and C36.2 are on one F fragment with one via (1.09/1.20 mm). Y1.2 → via 1.24 mm. C37.2 → via 0.76 mm. In1 is solid under all of them.

**Fix.** Re-route I2C1_SDA ≥ 0.4 mm from C36 (or on In2), move the CAM_SEL via ≥ 0.4 mm from HSE_OUT, and add an F-layer rule area over
Y1 + C36/C37 + the HSE traces.

### G4D-04 MINOR: MCU PDN residuals (G4-03/G4-04 follow-up)

- **Pin 48 → C26 (its designated 100 nF, `design/placement.py:261`) is 14.07 mm with 2 vias** (F 3.46 + B 7.41).
  - The path is pin 48 → via (23.44, 13.29) → B → C20 → U4.3 → via → F → C26. C26 is in effect a second LDO output cap.
  - Pin 48's nearest cap is C20 (2.2 µF, B), 2.38 mm with 1 via. That is adequate up to roughly 20-50 MHz, but there is no 100 nF at the pin.
- **VSS pins.**
  - U3.18 reaches its only via in 2.48 mm, through the hand dog-leg track (D-27).
  - U3.63 reaches its only via in 1.38 mm. U3.12 (VSSA) reaches a via in 1.57 mm (7 ties).
- **Decap GND to nearest via (`decap.py`):**
  - C28 2.81 mm, to a U2 EP thermal via, on F group #27;
  - C26 2.10 mm, C34 1.74 mm, C33 1.51 mm;
  - the rest ≤ 1.04 mm.
- C28.2 and U12 GND share F group #27 with 6 U2 EP thermal vias. C53.2 (RSSI filter) shares F group #28 with U1 EP vias. With In1
  0.1-0.2 mm (assumed) below, the shared current is small.

**Fix.**
- Put a 100 nF (C26) at pin 48 on F, ≤ 2 mm, with no via.
- Give C28, C26 and C34 GND vias ≤ 0.5 mm away.
- Add a second via for U3.18.
- Clear the F pour back from the U1/U2 EP via fields (or isolate those patches) so decaps do not share copper with them.

### G4-06 MINOR: 5 V east trunk (still open)

As in Part 1:
- 0.35 mm × 9.8 mm B track plus one 0.3 mm via (25.76, 29.76) at about 1.21 A (P11 0.8 A + D5 0.41 A budget). IPC-2221 external: about +12 °C.
- A single 0.3 mm via with about 20 µm plating has about 0.019 mm² of barrel. IPC-2221 with the internal constant gives about 0.76 A at
  10 °C rise; with the external constant, about 1.5 A. This is an estimate: vias are short and spread heat.

**Fix.** Use a ≥ 0.8 mm trunk and 2-3 vias.

### G4-07 MINOR: 10 V single vias (still open)

- L2 → P3: 3 single vias in series at up to 1.3 A.
- L2 → R41/J3: 5 single vias.
- Vias: (26.11, 31.89), (32.74, 27.59), (31.36, 29.54), (32.73, 21.85), (31.56, 11.64), (23.66, 8.49).

**Fix.** Use 2 vias per transition.

### G4-08 MINOR: VBAT neck to U2 (still open)

See Part 1.
- The C8 return GND via (17.30, 24.60) sits in the 1.6 mm VBAT strip (zone outline x 16.7-18.3).
- With In3 now a shared signal/VBAT layer, the strip could simply be widened: In3 GND pour surrounds it.

**Fix.** Move the via, or widen the strip to ≥ 3 mm.

### G4-09 MINOR: USB (still open)

See Part 1. FS USB tolerates this.

**Fix.**
- Route D+/D− together on F through U13's flow-through pins (3→4, 1→6) over In1.
- Add 100 nF at U13.5 (VBUS).

### G4-11 MINOR: 5 V sense branch beside L1 SW (still open, changed)

See Part 1.

**Fix.** Take R4's top from C8.1 (16.45, 27.58) with a dedicated trace on F or In2, away from L1.1.

### G4-12 MINOR: 16 dangling vias (still open)

Each one punches a 0.854 mm antipad (0.6 mm pad + 2 × 0.127 mm) through In1-In4 under the MCU. They are 1.6 mm stubs.

**Fix.** Remove them (a stub-aware prune), then refill.

### G4-13 MINOR: stitching (still open)

See Part 1.

**Fix.**
- Add an edge via fence (about 3 mm pitch) where the edge pads allow.
- Use ≥ 2 vias per F/B pour piece.
- J2.2 (ESC GND) has its nearest via at 2.07 mm (group of 4 ties); give it its own pair.

### G4D-05 MINOR: stackup undefined, so the inner-layer reference is unknown

- The design premise (D-27) is that In2 references In1 and In3 references In4. That holds only if In1–In2 and In3–In4 are the
  **thin** dielectrics.
- My recollection of JLC's standard 6-layer 1.6 mm builds (not verified, see "Not verified") is the opposite: thin outer prepregs,
  about 0.5 mm cores at L2–L3 and L4–L5, and a thinner centre prepreg. That would put In2 and In3 closer to **each other** than to their planes.
- In that case these become the dominant couplings:
  - In2/In3 broadside overlaps (`broad.py`, edge overlap in projection):

    | In2 net | In3 net | Overlap |
    |---|---|---|
    | UART3_TX | SPI3_MISO | 4.63 mm |
    | VTX_PWR_EN | STATUS_LED_GREEN | 3.99 mm |
    | CURR_ADC | STATUS_LED_GREEN | 1.96 mm |
    | ESC_TLM | 5V | 1.64 mm |
    | MOTOR8 | STATUS_LED_BLUE | 1.20 mm |
    | GYRO1_CS | GYRO1_INT | 1.07 mm |
    | MOTOR6 | MOTOR5 | 0.61 mm |
    | BUZ_N | RSSI_ADC | 0.41 mm |

  - In2 tracks over the **In3 VBAT zone**: BEEPER 4.2, UART2_RX 3.8, MOTOR1 2.3, MOTOR4 1.8, ESC_TLM 1.6, CURR_ADC 1.6, UART2_TX 1.6 mm.
    Their nearest plane would then be VBAT, which is decoupled to GND only at the buck input caps.
- The job file stackup is KiCad's default (equal 0.274 mm dielectrics), so the fab gets no stackup intent.

**Fix.**
- Choose the stackup now, not at order time. Prefer one with thin F–In1, In1–In2, In3–In4 and In4–B, and a thick In2–In3 dielectric
  (a custom stack if JLC's standard one is the opposite).
- Enter it in Board Setup so the job file and impedance numbers are real.
- Otherwise, route In2 and In3 orthogonally and keep In2 signals off the VBAT zone.

### G4D-06 MINOR: 3V3_IMU routing (G4-05 residual)

- U5.5 → U6.5 is 21.3 mm with 4 vias (B 10.9, F 2.3, In3 3.6). U5.5 → U7.5 is 13.3 mm with 2 vias. The net is 26.1 mm in total on all four routable layers.
- On B it runs beside UART3_TX (1.13 mm at 0.137 mm), UART3_RX (1.06 mm at 0.149), UART5_RX (1.0 mm at 0.132) and SPI3_SCK
  (0.63 mm at 0.132). On F it runs beside NRST (0.89 mm at 0.156).
- Pin caps are good: U6.5 → C40 0.69 mm, U6.8 → C38 1.15, U7.8 → C41 0.87, U7.5 → C42 1.56 mm. The LDO is quiet and IMU current
  is small, so the risk is coupled noise only.

**Fix.** Route 3V3_IMU on B or In3 with ≥ 0.3 mm to clocks/UARTs, or add a GND guard. Fewer layer changes.

### G4D-07 MINOR: EN_5V inside U1's input hot loop

- EN_5V (the R1/R2 UVLO divider node, 301 k/100 k, ≈ 75 kΩ source) runs on B (2.44, 26.21) → (6.74, 26.21) → U1.2.
- That passes **between C4's pads** (C4.1 (5.55, 25.55) VIN, C4.2 (5.55, 27.10) GND), i.e. through the VIN-C4-GND hot loop.
- The net is 18.6 mm long (2.5× its MST) with an In2 hop.
- The pinout forces EN between VIN and GND at the pin, but the 4 mm run under C4 is avoidable.
- A slowly varying EN near the threshold can chatter. No cap on EN_5V was found on the board.

**Fix.** Leave U1.2 straight out and take EN to In2 with a via next to the pin (outside the C4 loop), or add a small EN filter cap.
Shorten the route.

### G4D-08 MINOR: flash decoupling

U10.8 → C48 (100 nF) is 9.65 mm with 2 vias (B 4.52, F 1.93); it was 5.3 mm in rev C. W25N01 program/erase current pulses then
draw through the 3V3 tree.

**Fix.** Place C48 at U10.8 on B (≤ 1.5 mm).

### G4D-09 INFO: 3V3 distribution is a thin tree

- All 3V3 copper is 0.2 mm track: F 44.1, B 31.0, In3 18.8, In2 12.0 mm, with 11 vias.
- Graph paths from U4.3:
  - pin 48: 5.5 mm (12.9 mΩ);
  - pins 1 and 64: about 22 mm (≈ 95 mΩ);
  - pin 19: 40 mm (≈ 158 mΩ);
  - **pin 32: 47 mm, 5 vias (≈ 209 mΩ)**.
- At about 100 mA the DC drop is ≤ 21 mV, which is fine. The local caps (C27 2.3 mm, C28 4.1 mm, C29 4.7 µF 4.9 mm) carry the AC current.
- A 3V3 pour on In3 (where the GND pour is now) would cut this to a few mΩ. Optional.

### G4-14 / G4-15 / G4-16 INFO

See Part 1.

### G4D-10 INFO: verified OK

- **Planes.** See G4-02 above. The plane Gerbers `F405FC-In1_GND.g1` / `-In4_GND.g4` each have 1 region and 287 flashes (267 via
  pads + 20 TH). The non-GND via pads on In1/In4 are unconnected rings.
  - Option: set "remove unconnected via layers" on the planes. The antipad would shrink from 0.854 mm to about 0.68 mm (drill + 0.19
    hole clearance) and raise coverage.
- **Buck hot loops.**
  - U1: VIN → C4 1.50 mm routed, C2 2.19 mm, C3 4.27 mm.
  - U2: VIN → C12 0.78 mm, C10 1.54 mm, C11 3.33 mm.
  - All on B, 0.8 mm tracks.
  - The adjacent plane In4 is GND: U1 pad box 100 %, U2 99.3 %, L1 100 %, L2 99.9 %.
  - Nothing above In4 couples to them except through vias.
- **SW nodes.** SW_5V and SW_10V are B-only (0.8/0.6 mm), with no vias. L1/L2 have B keep-outs. Foreign proximity is as listed in
  G4D-02/G4-10.
- **IMU decaps.** 0.69-1.56 mm (G4D-06).
- **LDOs.** U4.1 → C19 0.67 mm, U4.3 → C20 3.09 mm, U5.1 → C22 1.10 mm, U5.5 → C23 1.92 mm.
- **Other decaps.** U8 0.77-0.99 mm, U9 0.43-1.64 mm, U11 0.72 mm, U12 1.10 mm.
- **VDDA/VCAP.** See G4-04 row.
- **Return paths.** Every F/In2 ↔ In3/B layer change on SPI1/SPI3/USB/DShot/video has a GND via within 0.74-2.97 mm
  (`trans.py`). The worst are MOTOR6 4.27 mm at (30.61, 14.21) and SPI3_SCK 3.97 mm, on a same-reference change. That is acceptable
  at these edge rates.
- **VBAT.**
  - Via counts: P1 4, U1 feed 3, U2 feed 3, J2.1 1 (JST, ≤ 1 A).
  - 0.8 mm B feed tracks: about +10 °C at 2 A (IPC-2221 external, estimate).
  - P1 → U1 zone resistance 2.1 mΩ.
- **Floating copper.** None. Every F/B/In2/In3 GND pour piece is tied by a via, a TH pad or a GND pad. The three pieces with no via
  inside (F 1.8 mm², B 2.4 mm², In2 2.1 mm²) are tied only by a J1 shell-slot thermal spoke.
- **DRC/parity.** Clean, as above.

---

## Not verified

- **Stackup.** Not known: the board has none, and the guide defers the choice. My statement about JLC's standard 6-layer
  construction (outer prepreg thin, about 0.5 mm cores, thinner centre prepreg) is recalled. A web search did not confirm the
  thicknesses of any specific JLC 6-layer stackup. All reference-plane statements for In2/In3 depend on it.
- **No field solving or simulation.** I did no field solving (impedance, crosstalk, mutual inductance) and no SPICE/EMI/thermal
  simulation. Coupling capacitances and spike amplitudes in G4D-01/G4D-02 are closed-form order-of-magnitude estimates.
- **No hardware measurements.** HSE start-up/jitter, ADC noise, gyro noise and buck FB disturbance were not measured.
- **Temperature and via ratings.** Temperature rises are IPC-2221 only (no IPC-2152). Via current comments assume about 20 µm plating,
  not a JLC figure. Inner copper is assumed 0.5 oz: the job file says 35 µm and the real stackup is unknown.
- **Routed lengths.** Routed lengths come from my centreline graph (`graph.py`: joints by geometric overlap, via hop modelled as
  0.32 mm per layer pair). I hand-checked HSE_OUT/HSE_IN, CURR_ADC, pin 48 → C26, the USB pair, the 5 V sense branch and the VBAT
  tracks against the track listing. I did not hand-check every decap number.
- **Coupling scans.** These cover tracks, vias and pads on the same layer (and In2/In3 broadside only). I did not check F↔In2
  broadside, because In1 is between them.
- **Release Gerbers.** I only checked the In1/In4 Gerbers' region/flash counts. I did not compare every layer of the release Gerbers
  with the board geometry. They come from the same commit as the board.
- **Not checked:** effective capacitance under DC bias, cap SRF/ESL, the LMR38020 EVM layout, the USBLC6-2SC6 datasheet, AN2867,
  and the W25N01 current profile.
- **Not re-checked here:** via-in-pad and paste/thermal-via DFM (Gate 5 scope).
