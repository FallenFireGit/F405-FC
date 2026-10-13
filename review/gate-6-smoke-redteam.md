# Gate 6 red team: "this board will smoke at first power-up"

Reviewer: independent adversarial review (Gate 6), 2026-10-13. Review only: no design files were modified.

**Snapshot reviewed:** commit `6b447eb`, `kicad/F405FC.kicad_pcb` md5 `798b268b7a046a0d1e3435be2c6fbb8c`, copied to
`/opt/kroot/tmp/rt6/` so that the running routing jobs could not change it mid-review. All PCB numbers below come from READ-ONLY pcbnew
scripts in `/opt/kroot/tmp/rt6/` (`conn.py`, `tr.py`, `gnd.py`, `path.py`, `zone.py`, `neck.py`, `holes.py`, `via.py`, `hot.py`, `refs.py`).
Coordinates are board-relative mm (origin = board corner, as in `gen/padpos.py`).

## Verdict: **FAIL** (on this snapshot), conditional PASS after the fixes below

I found no schematic-level or footprint-level error that puts battery voltage on a low-voltage rail at first power-up. Every pinout,
divider and rating I checked is correct (see "Checked and OK").

The snapshot still fails for three reasons:
- **BLOCKER:** the remaining GND islands are not cosmetic. They include U5's GND pin (the IMU LDO) and J5 pin 2 (the receiver
  ground), plus others. If the board is built as it stands, IMUs and MCU pins can be damaged.
- **MAJOR:** the bring-up guide's first power-up voltage of 8.4 V can destroy U5 if a single feedback-path assembly fault exists.
- **MAJOR:** the VBAT In2 pour reaches the M3 hole H3.

| ID | Severity | Title |
|---|---|---|
| G6S-01 | **BLOCKER** | GND islands include safety-relevant pads: U5 GND, J5 receiver GND, all baro/mag grounds, VBAT-divider bottom, VCAP1, BOOT0, Q2 gate pulldown |
| G6S-02 | **MAJOR** | Bring-up guide: first power at 8.4 V with U5/D5 fitted. A single FB fault (open R4/U1.5, wrong resistor) kills U5 (6 V abs max). Step 4 (16.8 V) then also exceeds the LP38692's 12 V |
| G6S-03 | **MAJOR** | VBAT In2 pour (and GND pours) fill inside the 4.6 mm grommet keepout, to about 0.19 mm from the H3 hole wall |
| G6S-04 | **MAJOR** | HD-VTX 10 V feed to J3/R41 is 0.45 mm on In2 (0.5 oz) for 8.8 mm; the analog-VTX pad P3 hangs on one 0.3 mm via |
| G6S-05 | MINOR | 5 V trunk is 0.35 mm for the whole 1.7 A budget, and 5 V is routed on the In1 GND plane |
| G6S-06 | MINOR | VBAT vias in or next to pads: half inside U2 pin 3 (0.138 mm from the GND EP), inside J2 pin 1, 0.28 mm from MCU pin 32 (3V3) |
| G6S-07 | MINOR | Bring-up stage lists miss R16 (BOOT0) and R14/R15 (VBAT divider). The guide uses TP5 as GND, but TP5 is currently on an island |
| G6S-08 | MINOR | LED-strip GND uses P4, which sits next to the 10 V pad P3; a miswire puts 10 V on the strip |
| G6S-09 | INFO | Stale power documentation (BAT54S D7/D8 still listed, "rev B" headers, "2 mm" U2 VBAT strip is about 1.5 mm) |
| G6S-10 | INFO | Accepted residual risks, restated for bring-up: no reverse-polarity protection; U1 high-side short puts VBAT on 5V |

---

## Findings

### G6S-01 BLOCKER: GND islands that matter for power-up safety

**Evidence.**
- `kc 'python3 /tmp/rt6/gnd.py'` groups every GND pad by copper connectivity. The main cluster has 114 pads; 21 more clusters are
  isolated. On this snapshot, DRC (`kicad-cli pcb drc --schematic-parity`, and again with `--refill-zones` on a copy) gives 0 errors,
  0 parity issues and 21 unconnected zone islands, which matches the "~21 fragments" status.
- The DRC count does not show *which* pads are stranded. These are the ones that matter for power-up safety:

| Island (pads) | Consequence if built as is |
|---|---|
| **U5.2** (LP5907 GND) + C22.2 (U5 input cap) + **TP5** | The 3V3_IMU LDO has no ground. Its internal reference floats, and the output can rise toward 5V_SYS (about 4.76 V). ICM-42688-P and BMI270 VDD are 3.6 V parts (abs max about 4 V): **IMU damage**. TP5 is also the GND test pad that the bring-up guide and SWD use. |
| **J5.2** (ELRS GND contact) | The JST MP tabs are mechanical only, so the receiver gets 5V_SYS but no ground. Its 50-150 mA supply current returns through its UART pins into PA2/PA3 clamp diodes. STM32 injection limit is 5 mA per pin (DS8626 §6.2, as cited in power.md §1.1). **MCU pin / RX damage.** |
| **U8.3, U8.5 (SDO), U8.8, U8.9** (all BMP390 VSS) + C25.2; **U9.6, U9.8** (all IIS2MDC GND) + C45.2 | Baro and mag are powered from 3V3 with no ground, so they back-bias through their I2C/ESD structures. Not smoke on the board, but the parts are stressed and absent on the bus. |
| **R15.2** (VBAT divider 1 k bottom) + C37.2 | PC0 sees VBAT through 10 k: (25.2 − 3.6)/10 k = 2.2 mA continuous, 3.85 mA at the 42.1 V TVS clamp. That is inside the 5 mA per-pin limit, but with no margin, and it reads full scale. |
| **C33.2** (VCAP1 2.2 uF) | The STM32 core regulator has only VCAP2 decoupling, so the core supply is out of spec. |
| **R16.2** (BOOT0 10 k pulldown) | BOOT0 floats, so random ROM-bootloader starts. The guide's Stage B step 1 check fails. |
| **R12.2** (Q2 gate 100 k pulldown) | Q2 gate floats while PC15 is Hi-Z (reset/DFU, and all of Stage A). The 10 V/VTX rail may switch randomly. |
| **R5.2** (FB_5V 24.3 k bottom) | FB = Vout, so the 5 V rail regulates to 1.0 V. This **fails low (safe)**, but the board is dead on battery. |
| **U13.2** (USBLC6 GND) | No USB ESD protection and no VBUS clamp. |
| C19.2 (U4 input cap), U3.63 (one of the VSS pins), C27/C30/C49/C29 (3V3 decaps), C38/C40 (IMU decaps), U11.2, R21/R22/R24/R31 | Functional or decoupling only. |

**Fix.**
1. Tie every island to In1 (the work in progress).
2. Then gate the release on a **per-pad** check like `/tmp/rt6/gnd.py`: exactly one GND pad cluster. A DRC "unconnected = 0" alone is
   not enough, because an island can also be removed by deleting fill.
3. Priority order if anything has to be hand-wired: U5.2, J5.2, U8/U9, R15.2, C33.2, R16.2, R12.2.

### G6S-02 MAJOR: the bring-up guide's first power-up can destroy U5 on a single assembly fault

**Evidence.**
- `docs/assembly_and_bringup.md` §2 Stage A fits U4, U5 and D5 together with the bucks. §2.1 step 1 then applies **8.4 V**, and step 4
  applies 16.8 V. Nothing says "stop if 5V is out of range" before the voltage is raised.
- Any one of these single faults drives the 5 V rail toward VIN (97 % maximum duty cycle, `lmr38020.pdf` §7.6):
  - R4 (100 k, 5V→FB_5V) open or tombstoned;
  - U1 pin 5 (FB) not soldered;
  - a wrong-value 0402 in the R5 position: any 1 k (R11, R13 and R15 share that reel) gives 101 V nominal, i.e. full VIN.
- A swap of R5 (24.3 k) and R10 (11 k), which sit 15 mm apart on the same side with the same size, gives **10.09 V on 5V**.
- At 8.4 V in, 5V reaches about 8.1 V and 5V_SYS about 7.8 V (after D5). LP5907 abs max is **6 V** on VIN and EN (`lp5907.pdf` §5.1).
- At step 4 (16.8 V), the LP38692 abs max of **12 V** (`lp38692.pdf` §6.1) is also exceeded.
- In Stage C the same fault would also hit U12 (7 V), the receiver, GPS and cameras.

**Fix (guide only, no hardware change needed).**
1. Before the first power-up, measure in-circuit:
   - FB_5V to GND ≈ 24 kΩ;
   - FB_10V to GND ≈ 11 kΩ;
   - 5V to FB_5V ≈ 100 kΩ;
   - 10V to FB_10V ≈ 100 kΩ.
2. Choose one of these first-power strategies:
   - **Fit D5 only after the 5 V rail is verified.** With D5 out, U4 and U5 cannot see a runaway 5 V.
   - Or make the first power-up **6.0-6.5 V**, current-limited. That is above the worst-case EN turn-on of 5.61 V (power.md §2.6), and
     a runaway 5 V then stays at or below about 5.8 V, which keeps 5V_SYS at or below 5.5 V.
3. Add explicit STOP criteria: "5V outside 4.96-5.28 V, or 10V above 10.43 V: switch off, do not raise VIN."
4. Raise to 16.8 V only after 10V reads 9.76-10.43 V at 12-13 V in.

### G6S-03 MAJOR: VBAT pour inside the H3 grommet keepout

**Evidence.**
- `requirements.md` asks for a 4.6 mm keepout diameter around each hole. The rule areas `HOLE_KEEPOUT_1..4` exist on all four
  layers, but they forbid only tracks and vias: `GetDoNotAllowZoneFills() == False` (`/tmp/rt6/holes.py`).
- `VBAT_ZONE` (`gen/route.py:26`) covers (0.5..8.8, 21.6..35.5), which includes H3 at (2.75, 33.25).
- The filled VBAT copper on In2 comes to **1.79 mm from the H3 centre**, i.e. about 0.19 mm from the 3.2 mm NPTH wall. The GND pours
  on F/B/In1 do the same at every hole.
- An M3 screw or standoff, often bonded to a conductive carbon frame, that bites into or chips the hole wall can reach battery copper.

**Fix.** Do one of the following, then refill and re-run DRC:
- set "no copper pours" on the four `HOLE_KEEPOUT_*` rule areas; or
- subtract a circle of r = 2.3 mm plus clearance at (2.75, 33.25) from `VBAT_ZONE`.

The fill near P1 is not current-limited, so there is ample room.

### G6S-04 MAJOR: VTX 10 V copper is undersized for its stated current

**Evidence.** From `/tmp/rt6/lay.py` and `tr.py`:
- The 10V net is 0.45 mm everywhere except the scripted L2→C14..C16 0.8 mm segment.
- **J3 pin 1** (HD VTX, up to 1 A per D-16 / R13) is fed from the P3/C15 area by F.Cu 0.45 mm, then a via at (33.28, 11.78), then
  **8.8 mm of 0.45 mm on In2 (0.5 oz)**, then a via at (25.92, 8.88), then F.Cu to R41.
  - IPC-2221 internal estimate: about +60 °C at 0.9 A and about +80 °C at 1 A. IPC-2152 with adjacent planes would be lower, roughly
    half; that was not computed.
- **P3** (analog VTX, up to 1.3 A) connects to the 10 V bank through one 0.3 mm via at (32.72, 28.03) and about 5 mm of 0.45 mm track.

This does not fail at first power-up, but it is a hot spot in flight next to the In1 plane.

**Fix.**
- Route 10V on F.Cu/B.Cu at ≥ 1.0 mm, or give it a short pour.
- Use ≥ 2 vias at every layer change on the P3 and J3 paths.

### G6S-05 MINOR: 5 V distribution widths and layers

**Evidence.** From `/tmp/rt6/path.py 5V L1.2 ...`:
- L1.2 → D5/P11/U12 all share an 11.4 mm, **0.35 mm B.Cu** trunk. That trunk carries the full 1.7 A budget (power.md §12.1);
  IPC-2221 external estimate is about +26 °C.
- The branch to D5, which feeds all of 5V_SYS, uses **6.8 mm of 0.35 mm on In1.GND**. That is fine thermally at 0.41 A, but it cuts
  the GND reference plane under the power section.
- In total, 5V has 6.8 mm on In1 and 10.2 mm on In2.

**Fix.** Widen the trunk to ≥ 0.8 mm (as `critical.py` does for the output caps) and keep 5V off In1.

### G6S-06 MINOR: VBAT vias in or next to pads

**Evidence** (`/tmp/rt6/via.py`; vias are tented by board default):
- Via (24.69, 23.66), d 0.6: half inside **U2 pin 3** (VIN pad x 23.125-24.675). Its copper edge is **0.138 mm** from U2's EP (GND)
  metal. It wicks solder from the VIN joint and puts VBAT 0.14 mm from GND under the PowerPAD.
- Via (17.49, 30.86) is inside the **J2 pin 1** pad (0.6 mm wide JST-SH), which starves the connector joint.
- Via (20.60, 24.45), VBAT, is **0.28 mm from U3 pin 32 (VDD, 3V3)** on the top side. The guide tells the builder to drag-solder the
  LQFP. A mask defect or a bridge there puts 25 V on 3V3.

**Fix.**
- Move the U2 via off pad 3 by ≥ 0.2 mm (outboard of the pin), or fill and cap it.
- Move the J2 via off the pad.
- Move the (20.60, 24.45) via ≥ 0.5 mm from the LQFP pin row, or note it in the guide.

### G6S-07 MINOR: bring-up stage contents

**Evidence** (`docs/assembly_and_bringup.md` §2-§3):
- Stage B checks "SW1 open = BOOT0 low", but R16 (the BOOT0 10 k) is not in the Stage B list. It falls under Stage C "remaining
  passives".
- R14/R15 (VBAT divider) appear in no stage list. If R14 is fitted before R15, PC0 gets VBAT through 10 k (see G6S-01).
- The bare-board and NRST steps use **TP5** as GND, but TP5 is on the U5 island in this snapshot.

**Fix.**
- Add R16, R14, R15 and the CS/WP/HOLD pull-ups to Stage B.
- Use P2 as the GND reference until G6S-01 is closed.

### G6S-08 MINOR: LED-strip GND shares P4, next to the 10 V pad P3

**Evidence.**
- P3 (10V) is at (34.2, 23.0) and P4 (GND) at (34.2, 27.0), both top side.
- The LED strip uses P10/P11 at (26.0/28.4, 28.3) and, per D-21, P4 for GND.
- A builder who lands the strip's +5 V on P3 by mistake puts 10 V on WS2812s (abs max about 5.3-6 V).

**Fix.** Add a bold silk "10V / VTX ONLY" beside P3 and a line in §5 of the guide.

### G6S-09 INFO: stale power documentation

- `design/power.md` §10.2 and the §13 table still describe the BAT54S clamps D7/D8, which D-23 removed. The guide is already correct.
- Headers say "rev B" (`power.md` line 1, `circuit.py` docstring and the PWR sheet note), and §5 says the U2 VBAT strip is "2 mm wide".
- Measured: the narrowest neck of the In2 VBAT fill on the U2 path is about 1.5 mm (`/tmp/rt6/neck.py`; vertical strip/corner near
  (17.8, 24.6), band ≥ 1.53 mm). That is adequate: about +25 °C at 1.5 A by IPC-2221 internal. Only the documented figure is wrong.

### G6S-10 INFO: accepted risks to keep in the bring-up guide

- **No reverse-polarity protection** (power.md §1.1 / P0-09). A reversed pack forward-biases D1 and both LMR38020 body diodes.
  - On the bench, the 100 mA limit protects the board.
  - In the field, the ESC harness sets polarity.
- **U1 high-side short** puts VBAT on 5V and 5V_SYS (R12): no OVP or crowbar.
- **R41 fitted while the VTX is also powered from VBAT** back-drives U2 (D-11/D-16).

---

## Checked and OK (evidence)

**Pinout and footprint orientation.** Each footprint pad was checked against the datasheet pinout.

| Part | Footprint pads (from PCB) | Datasheet reference |
|---|---|---|
| U1, U2 LMR38020 | 1 GND, 2 EN, 3 VIN, 4 RT/SYNC, 5 FB, 6 PG (open), 7 BOOT, 8 SW, 9 EP=GND | `lmr38020.pdf` Table 6-1 |
| Custom HSOIC footprint | Pins 1-4 on one side, 5 opposite 4, standard SOIC CCW numbering, before and after the bottom-side flip | — |
| U4 LP38692MP SOT-223-5 | 1 EN, 2 N/C, 3 OUT, 4 IN, 5 (tab) GND; PCB pads 1/4 = 5V_SYS, 3 = 3V3, 5 = GND | `lp38692.pdf` §5 NDC drawing |
| U5 LP5907 SOT-23-5 | 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT | `lp5907.pdf` Table 4-2 |
| Q1 PMV40UN2, Q2 NX7002AK | 1 G, 2 S, 3 D | Nexperia Table 2 |
| D1, D4, D5, D9 | Pad 1 = cathode: D1.1 VBAT, D4.1/D5.1 5V_SYS, D9.1 5V | PMEG4030ER Table 2 (pin 1 = K); KiCad `Nexperia_CFP3_SOD-123W` and `D_SMB` pad 1 = K |
| U12 SN74LV1T125 | 1 OE=GND, 2 A, 3 GND, 4 Y, 5 VCC | — |
| U13 USBLC6-2SC6 | 1/6 I/O1, 3/4 I/O2, 2 GND, 5 VBUS | — |

**Regulator settings.**
- Feedback: VREF = 1.000 V ±1.5 % (`lmr38020.pdf` §7.5). 100 k/24.3 k gives 5.115 V; 100 k/11 k gives 10.09 V. A divider that opens
  low (R5 or R10 open) fails safe at 1.0 V. A top-resistor open or a FB-pin open fails high (G6S-02).
- RT 34.8 k gives about 743 kHz (Eq. 2). At 25.2 V and 42.1 V, tON stays above the 131 ns maximum tON-MIN.
- EN: abs max is VIN + 0.3 V. 301 k/100 k puts 10.5 V on EN at 42.1 V, which is fine. Q2 (60 V) on EN_10V is fine.
- BOOT-SW 5.5 V across a 16 V cap. RT/FB 5.5 V abs max.

**Voltage ratings on VBAT at the 42.1 V TVS clamp.** All have margin:
- C1 50 V;
- C2/C3/C10/C11 and C4/C12 100 V;
- R1/R6 301 k and R14 are 0603;
- LMR38020 VIN/SW 85 V;
- JST-SH 50 V.

The SMBJ26A VWM of 26 V is above 25.2 V (6S) and 26.1 V (LiHV).

**Voltage ratings on the other rails:**
- 5V output caps 25 V;
- 10V output caps 25 V (equal to the 6S level only in the accepted U2-short double fault);
- 5V_SYS caps 16-25 V;
- LP38692 on 5V_SYS (12 V abs max);
- LP5907 at 4.76 V (6 V abs max);
- U12 at ≤ 5.28 V.

**Back-feed paths.**
- USB only: VBUS → D4 → 5V_SYS. D5 blocks 5V, so there is no VBAT back-feed through U1's body diode.
- Battery present: D4 blocks the host.
- 10V cannot reach 5V: there is no shared node.
- U12 has Ioff for the unpowered-5V case.
- The VTX pads are 10V only.

**Copper connectivity.**
- Every power net is one copper cluster: VBAT, 5V, 10V, 5V_SYS, VBUS, 3V3, 3V3_IMU, 3V3A, SW/BST/EN/FB/RT, VTX_PWR, BUZ_N
  (`/tmp/rt6/conn.py`, with and without an in-memory zone refill; DRC `--refill-zones` on a copy gives 0 errors).
- **VBAT reaches U2 VIN** by this path: P1 → 4 vias (6.6/7.6, 32.6/33.8) → In2 `VBAT_In2` → vias (20.6, 24.45), (21.4, 24.05) and
  (22.4, 23.95), all inside the fill (`zone.py`) → B.Cu 0.8 mm C10.1 → C12.1 → U2.3.
- U1 VIN: In2 → vias (4.0, 23.95), (5.0, 23.85), (6.0, 23.7) → B.Cu 0.8 mm → C2/C3/C4 → U1.3.
- The U1 input caps' GND and U1 GND/EP share one B.Cu fill polygon (`hot.py`).
- DRC with schematic parity: 0 errors, 0 parity issues. The only unconnected items are the 21 GND islands. There are 18
  `via_dangling` warnings on signal nets (not power).

**Inrush and current limit.** Both bucks have a 4 ms internal soft start. The worst-case output-cap charge is about 55 mA. The 100 mA
bench limit holds unless there is a fault.

## Not verified

- **Datasheets not on file, so not read:**
  - SMBJ26A (VBR/VC values taken from power.md);
  - Würth 74438356056 (Isat, DCR);
  - TDK C3225X7S2A475K200AB DC-bias curve;
  - SN74LV1T125, USBLC6-2SC6, IIS2MDC;
  - STM32F405 DS8626 (the injection limits are cited from power.md, not re-read).
- **Thermal behaviour.** Trace temperature rises are IPC-2221 estimates, not IPC-2152 or simulation. Buck/LDO thermals were not
  re-derived.
- **Not inspected on the PCB:** silkscreen polarity marks (D1/D4/D5/D9 bands, U1/U2/U4/U5 pin-1 dots), paste and stencil apertures, and
  part heights.
- **Signal nets:** no signal-integrity, ERC or betaflight-level review (see `review/gate-6-betaflight-redteam.md`).
- **Live board:** I did not check the board after this snapshot. Routing and GND-tie jobs were still running, so G6S-01 must be
  re-checked on the final file.
- **Not done at all:** a short check between rails by DMM simulation, and any measurement on real hardware (none exists).
