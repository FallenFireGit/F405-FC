# Gate 4: signal integrity / power integrity review

Reviewer: fresh, independent Gate 4 SI/PI agent, 2026-10-13. This is a review only. I did not modify any design, generator,
KiCad, BOM, fab or docs file, and I made no commits.

**Snapshot reviewed:** `kicad/F405FC.kicad_pcb` md5 `b041447172c8e51efddcb7368042d94d`. That is the board in commits `1f7f722`
through `724d268` (HEAD at the end of this review). It was dumped at 23:27 UTC.
- During the review, someone else's uncommitted work changed the working-tree board (md5 `fa8ff3c3...` at 23:44), along with
  `gen/route.py`, `gen/build_pcb.py`, `lib/` pads and a new `gen/vianudge.py`.
- **I did not review those changes.** Re-run the scripts in `/opt/kroot/tmp/g4/` on the new board.

**Method.**
- `kc 'python3 gen/drc_summary.py'` gives 0 errors, 0 unconnected and 0 parity. It also reports 17 `via_dangling` and 26 `silk_overlap`
  warnings.
- `kc 'python3 gen/placecheck.py'` gives PASS.
- I wrote one READ-ONLY pcbnew dump, `/opt/kroot/tmp/g4/dump.py`. It exports every track, via, pad and filled-zone polygon to
  `/opt/kroot/tmp/g4/board.json`. No board was saved.
- Everything else uses host scripts in `/opt/kroot/tmp/g4/`:
  - `rast.py`: 0.02 mm rasteriser of the stored zone fills.
  - `in1.py` / `in1b.py`: In1 islands.
  - `cuts.py` / `cross.py` / `broad.py`: In1 cuts, slot crossings and broadside overlap.
  - `ref.py`: reference plane under each net.
  - `prox.py` / `at.py`: neighbours and layer queries.
  - `isl.py`: pour fragments and their via ties.
  - `geo.py`: on-plane return-path detours.
  - `neck.py` / `fem.py`: VBAT In2 zone neck and 2-D finite-difference resistance.
  - `solve.py` / `s5v.py` / `s10.py`: DC network solve of track and via resistances.
  - `decap.py`: routed pin-to-cap distance.
- Images: `in1.png`, `in1c.png`, `in2.png`, `b.png`, `f.png`, `in2v_s.png`, `in1buck_s.png` in the same folder.
- Coordinates are board mm (origin = board top-left corner, as in `gen/padpos.py`).

**Stackup assumption.** Per `design/requirements.md:9`, the board is JLC04161H-7628 with 1 oz outer and 0.5 oz inner copper. From
JLC's published stack, I used dielectric thicknesses of about 0.21 mm (F–In1), 1.065 mm (In1–In2) and 0.21 mm (In2–B). The JLC
datasheet is not in the repo, so these are recalled values. The consequences:
- F.Cu references In1.
- B.Cu references **In2**, not In1, so In2 is the image plane of every bottom-side part: the bucks, IMUs, LDOs and flash.
- `kicad/F405FC.kicad_pcb` contains **no stackup section**, and `fab/gerbers/F405FC-job.gbrjob` carries KiCad's default stackup
  (3 × 0.48 mm FR4, 35 µm inner copper). See G4-14.

## Verdict: **FAIL**

| Severity | Count |
|---|---|
| BLOCKER | 1 |
| MAJOR | 4 |
| MINOR | 8 |
| INFO | 3 |

The power stages themselves are laid out well (see "Checked and OK"). The board fails for these reasons:
- The HSE crystal network was broken by placement drift: a load cap sits 7.9 mm from the crystal with a 17.8 mm route over the 5 V buck.
- In1 is not a solid GND plane. It carries 328 mm of signal and power track and is split into 5 pieces.
- GND pour fragments bond MCU/analog decoupling grounds into the buck thermal-via fields.
- The PDN layout around the MCU and IMUs is poor.

| ID | Sev | Title |
|---|---|---|
| G4-01 | **BLOCKER** | HSE_OUT load cap C37 is 7.9 mm from Y1. HSE_OUT is 17.0 mm with 3 vias and runs over U1. The crystal area is not guarded (I2C1_SCL 0.14 mm from C36; 5V_SYS/CAM_SEL/NRST under Y1) |
| G4-02 | **MAJOR** | In1 "solid GND plane" carries 327.9 mm of track from 39 nets. Copper coverage is 72 % (main piece 67 %, 40 % under the MCU). A 57 mm² In1 island under Y1/U6/VDDA is tied by 9 vias |
| G4-03 | **MAJOR** | F-layer GND fragments bond MCU decaps to the buck EP via fields (C28/C29/C33 to U2.9; C27/C53 to U1.9). VSSA, VDDA caps, C37 and the ELRS GND share one via |
| G4-04 | **MAJOR** | MCU decoupling: VDD pin 32 to C28 is about 8 mm through In2 with 2 vias. Pin 48 to C26 is 6.6 mm with vias. VCAP2 to C34 is 8.2 mm with an In1 hop. Cap GND vias are 3.4-4.7 mm away |
| G4-05 | **MAJOR** | IMU environment: DShot MOTOR5/6, LED_STRIP, STATUS_LED_GREEN and UART1 run through the BMI270 footprint on F/In1/In2. U6 sits on the In1 island. In2 under U7 is 58 % GND |
| G4-06 | MINOR | 5 V east branch: 1.21 A in a 0.35 mm B.Cu trace (9.65 mm) and a single 0.3 mm via (G6S-05 residual) |
| G4-07 | MINOR | 10 V to P3 passes three single vias in series at 1.3 A. The J3 path passes 4 more single vias (G6S-04 residual) |
| G4-08 | MINOR | VBAT In2 feed to U2 necks to about 0.6 mm at the C8 return via (17.30, 24.60). FEM gives 16 mΩ and a peak of 3.9 A/mm |
| G4-09 | MINOR | USB D+/D− are routed on different layers and cross the DShot In1 slots. D− uses the ESD part as a stub. There is no local VBUS cap at U13 |
| G4-10 | MINOR | Analog current sense ESC_CURR runs on In2 alongside U1's SW/BST pins and on In1 over L1's SW pad. RSSI_IN/RSSI_ADC cross both SW nodes (shielded) |
| G4-11 | MINOR | The 5 V feedback sense (R4 top) is tapped from a 5V trace that runs over U1's SW pin and beside L1's SW pad |
| G4-12 | MINOR | 17 dangling fanout vias on SPI1/SPI3/motor/SWD nets punch In1/In2 antipads and add stubs |
| G4-13 | MINOR | GND stitching is sparse: 52 GND vias, 3 within 2 mm of the edge, and 23 of 39 F/B pour fragments tied by a single via or TH pad. The ESC GND J2.2 has one via |
| G4-14 | INFO | No stackup in the board, and the job file stackup is wrong. Impedance is not controlled (USB FS tolerates it) |
| G4-15 | INFO | `review/summary.md`, which D-22 says lists the In1 copper, does not exist |
| G4-16 | INFO | Video lines: only perpendicular crossings of UART2/5V/3V3, more than 8 mm from the SW nodes |

---

## Findings

### G4-01 BLOCKER: crystal network (HSE) broken by placement drift

**Evidence**
- C37 (8.2 pF, HSE_OUT load) is at **(7.64, 23.36)** on F.Cu (pads C37.1 (7.16, 23.36), C37.2 (8.12, 23.36)).
  - Y1 is at (8.40, 15.45), and pad Y1.3 (HSE_OUT) is at (9.25, 16.55).
  - The placement intent is `design/placement.py:280` `"C37": ("Y1", 3, 0.0, 1.45, 0, "T")`, i.e. about (9.25, 18.0). The part is 5.4 mm
    from its anchor and **7.9 mm** from Y1.3.
  - C36 (HSE_IN) is where it should be: C36.1 (7.07, 12.75), 1.6 mm from Y1.1.
- HSE_OUT copper (`net.py HSE_OUT`): **17.0 mm total** (F 9.6, B 4.2, In1 3.1 mm) with **3 vias** at (12.44, 16.36), (12.54, 19.14) and (10.16, 22.61).
  - Routed U3.6 → C37.1 = 17.76 mm (`decap.py`).
  - The path runs U3.6 → In1 under U3 pins 7-11 (x = 12.01, y 16.9-18.6) → B.Cu → F.Cu.
  - It then makes a loop at (6.46-10.16, 22.6-26.2) on F, directly above the 5 V buck U1 (B.Cu, (10.20, 25.60)).
  - In projection it crosses U1.4 RT, U1.2 EN and the U1 VIN track (`prox.py HSE_OUT`: RT_5V −0.33 mm, EN_5V −0.32 mm, VBAT −0.46 mm).
  - Its closest approach to the U1 SW pin (12.9, 27.5) is about 3 mm. Part of it runs over an In1 void: In1 GND is absent at (9.0, 24.6) (`at.py`).
- C37.2's GND is F pour fragment 15. That fragment's only via is at (9.66, 19.31), **4.33 mm** away, and it is shared with VSSA, VDDA caps and
  the ELRS GND (see G4-03).
- The crystal area is not guarded (`prox.py HSE_IN`, `seg_in_box`, box around Y1):
  - **I2C1_SCL on F is 0.14 mm from C36.1** (HSE_IN).
  - 5V_SYS on In1 runs 3.4 mm under Y1 and crosses directly under Y1.1 (In1 slot under HSE_IN, `cross.py`).
  - Also under Y1: CAM_SEL (In1 1.4 mm, B 2.5 mm) and NRST (In2 3.7 mm).
  - Y1 sits on the isolated 57 mm² In1 island (G4-02): In1 coverage under Y1 is 85 %, of which only 16 % is the main plane.
- `gen/placecheck.py:33` constrains only Y1 to U3, not C36/C37 to Y1, so the drift was not caught. It PASSES today.
- Load-capacitance effect: 17 mm × ≈ 0.076 pF/mm (0.127 mm microstrip, h = 0.21 mm, εr 4.4) plus 3 vias ≈ **+2 pF on HSE_OUT only**.
  - CL rises about 0.5 pF over D-07's figures, and gm_crit worst case goes from 0.80 to about 0.86 mA/V (still < 1 mA/V).
  - So start-up margin is not the main risk. The risks are injection of buck switching noise (750 kHz with spread spectrum, sharp
    edges) and of I2C/GPIO edges into the oscillator, which gives HSE jitter and spurs. The 48 MHz USB clock and the 168 MHz SYSCLK
    are derived from HSE. This also violates AN2867's layout rules (load caps next to the crystal, short symmetric traces, guard ring,
    no other signals nearby).

**Fix**
1. Put C37 back on its anchor (about 1.45 mm below Y1.3) and route Y1.3–C37.1 as a ≤ 2 mm F.Cu stub. Delete the In1/B detour.
2. Add `("C36","HSE_IN","Y1",1.6)` and `("C37","HSE_OUT","Y1",1.6)` to `gen/placecheck.py`.
3. Add a rule area (no tracks or vias of other nets on F and In1, and ideally In2/B) over Y1 + C36/C37 + the HSE traces. Move I2C1_SCL,
   5V_SYS, CAM_SEL and NRST out of it.
4. Give Y1.2/Y1.4 and C36.2/C37.2 a dedicated GND via (≤ 0.5 mm) to the main In1 plane.

### G4-02 MAJOR: In1 is not a solid GND plane

**Evidence (`in1.py`, `cuts.py`; image `in1.png` / `in1c.png`)**
- **192 track segments, 327.9 mm, 39 nets** are on In1, including power nets: 3V3 14.6 mm, 5V_SYS 9.2 mm, 3V3A 4.7 mm, VCAP2 2.4 mm and
  3V3_IMU 3.1 mm.
- In1 GND fill = 72 % of the board, and the main piece = 67 %.

  | Area | In1 GND | of which main piece | In2 GND |
  |---|---|---|---|
  | Under U3 body | 40 % | 17 % | 56 % |
  | Under U6 | 84 % | **0 %** | 71 % |
  | Under U7 | 57 % | 57 % | 58 % |
  | Under Y1 | 85 % | 16 % | 89 % |

- **The In1 GND fill is 5 separate polygons** (KiCad's own fill, `dump.py`; confirmed by raster labelling):

  | Piece | Area | Location | GND vias | Bounded by In1 tracks of |
  |---|---|---|---|---|
  | Main | 865 mm² | whole board | 59 vias/TH | — |
  | Island | **57.4 mm²** | x 4.9-18.5, y 5.5-19.6 (under Y1, U6 ICM-42688-P, FB1/C31/C32, C24/C30/C35) | 9 | SPI3_MOSI, FLASH_HOLD, CAM_SEL, 5V_SYS, 3V3, HSE_OUT, 3V3A, 3V3_IMU, VBAT_ADC, MOTOR8, GYRO2_CS, SPI1_SCK, SPI3_SCK |
  | Island | 5.56 mm² | — | 1 | UART5_TX, STATUS_LED_GREEN, UART3_TX, SWDIO |
  | Island | 1.16 mm² | — | 2 | UART1_TX, VCAP2 |
  | Island | 0.61 mm² | — | 1 | SPI3_SCK, I2C1_SCL |

- Longest cuts:

  | Net | In1 length (mm) | bbox | F nets crossing over | In2 nets crossing under |
  |---|---|---|---|---|
  | ESC_TLM | 17.1 | x11.2-25.1 y22.5-30.9 | 3V3, 5V, BEEPER, BUZ_N, ESC_CURR, GYRO1_CS, MOTOR1, MOTOR2, RSSI_ADC | ESC_CURR, MOTOR3 |
  | STATUS_LED_GREEN | 16.9 | x8.7-21.4 y1.2-11.8 | SWCLK, UART3_TX, UART5_RX | BOOT0, MOTOR7, NRST, UART3_TX |
  | MOTOR8 | 16.2 | x13.2-23.2 y18.8-27.2 | 3V3, SPI1_MISO, SPI1_SCK, VBAT | 3V3, SPI1_MOSI, VTX_PWR_EN |
  | 3V3 | 14.6 | x7.1-27.7 y5.2-20.6 | 3V3A, 5V, I2C1_SDA, MOTOR7, MOTOR8, SPI1_MISO, SPI1_SCK | SPI1_MOSI, UART1_RX, UART2_RX |
  | UART5_TX | 14.2 | x8.5-18.7 y1.9-10.7 | 3V3, SPI3_MISO, UART5_RX | NRST, SPI3_MISO, UART3_RX/TX |
  | SPI3_SCK | 13.6 | x8.4-17.2 y4.0-13.7 | 3V3, FLASH_CS, I2C1_SCL, SPI3_MOSI | 3V3, BOOT0, I2C1_SDA, MOTOR7, NRST, SPI3_MISO, UART3_RX/TX |
  | MOTOR5 | 12.7 | x19.0-30.6 y14.7-17.8 | MOTOR6, USB_CC1, **USB_DM**, VBUS | LED_STRIP, STATUS_LED_BLUE/GREEN, **USB_DP** |
  | STATUS_LED_BLUE | 12.6 | x14.1-25.3 y2.6-8.2 | BOOT0, UART1_RX, VTX_PWR | BOOT0, MOTOR7, UART1_RX |
  | VBAT_ADC | 11.7 | x7.6-9.3 y17.9-28.5 | 3V3, 3V3A, BUZ_N, CURR_ADC, ESC_CURR, HSE_OUT | 3V3A, UART2_RX/TX |
  | FLASH_HOLD | 11.2 | x6.6-11.8 y3.8-12.9 | 3V3, I2C1_SCL, I2C1_SDA, MAG_C1 | NRST, SPI3_MISO, UART3_RX/TX |
  | UART1_TX 11.1, SPI3_MOSI 11.0, GYRO2_CS 10.8, ESC_CURR 10.2, UART6_RX 9.9, SWDIO 9.8, BEEPER 9.6, 5V_SYS 9.2, CAM_SEL 9.1, MOTOR6 9.1, MOTOR4 8.3, MOTOR1 7.1, LED_STRIP 6.9, I2C1_SCL 6.4, SPI1_SCK 5.7, UART3_TX 5.5, I2C1_SDA 5.3, UART6_TX 5.1, BUZ_N 5.0, 3V3A 4.7, GYRO1_CS 4.1, BUZ_G 4.1, USB_CC2 3.5, LED_DIN_BUF 3.2, HSE_OUT 3.1, 3V3_IMU 3.1, VCAP2 2.4, USB_CC1 2.2, BOOT0 1.4 | | | | |

- F.Cu signals that run over In1 slots (track plus clearance band, excluding via antipads; `cross.py`):
  - UART5_RX 7.8 mm and 3V3 7.3 mm, mostly running along In1 tracks.
  - BEEPER 2.1, MOTOR2 2.1, SWDIO 1.8, I2C1_SCL 1.7, FLASH_CS 1.5, SPI3_MISO 1.3, SPI1_MISO 1.1 mm.
  - USB_DP 0.9 mm (over MOTOR6), USB_DM 0.3 mm (over MOTOR5), HSE_IN 0.6 mm (over 5V_SYS).
- Return detours on In1 (`geo.py`, path on In1 copper vs. straight line):
  - 5 V output-cap return vias to the U1 EP: 1.8× (C8), 2.0× (C6) and 2.0× (C9). The ESC_TLM/BUZ_N/BUZ_G/ESC_CURR cuts sit between U1 and
    its output caps (image `in1buck_s.png`).
  - B.Cu carries those returns at 1.0-1.4×, so the buck itself is not compromised.
  - Y1 GND → MCU VSS18 and U6 → U2 EP have **no path on In1 at all** (different In1 pieces).
- D-22 accepted In1 hops "checked at Gate 4". The check shows this is not "short hops": several In1 tracks are 10-17 mm long, and they
  close contours that cut out a plane piece under the most sensitive circuits.

**Fix**
- Re-run the finisher with In1 restricted to ≤ 3 mm hops that do not close contours.
- Add a release check: `ndimage.label` (or the KiCad fill outline count) of the In1 GND fill must be exactly 1 piece, and In1 coverage
  should be ≥ 90 %.
- First take off In1:
  - everything under Y1 and both IMUs: 5V_SYS, CAM_SEL, HSE_OUT, 3V3_IMU, SPI1_SCK, MOTOR5, MOTOR6, GYRO2_CS;
  - the power nets: 3V3, 5V_SYS, 3V3A, VCAP2;
  - the long runs: ESC_TLM, STATUS_LED_GREEN, MOTOR8, UART5_TX, SPI3_SCK/MOSI, FLASH_HOLD.
- Slow nets (LEDs, BEEPER, UART5) can go to In2/B instead.

### G4-03 MAJOR: GND pour fragmentation bonds sensitive grounds to power grounds

**Evidence (`isl.py` and fragment listing).** F.Cu GND has 25 fragments and B.Cu has 14. All are anchored, so there is no floating copper.
These F fragments matter:

| F frag | Area | GND vias | Pads on it |
|---|---|---|---|
| 17 | 21.6 mm² | 1 at (22.69, 23.04) | **C28.2, C29.2 (MCU VDD decaps), C33.2 (VCAP1)** and **U2.9** (10 V buck EP thermal vias) |
| 18 | 40.3 mm² | 4 | **C27.2 (MCU VDD decap), C53.2 (RSSI ADC filter)**, C1.2 (battery bulk cap) and **U1.9** (5 V buck EP) |
| 15 | 14.1 mm² | 1 at (9.66, 19.31) | **U3.12 VSSA, C31.2/C32.2 (VDDA), C37.2 (HSE), R15.2 (VBAT divider bottom)** and **J5.2 (ELRS receiver GND)** |
| 13 | 30.8 mm² | 1 + J1 shell | J1 GND pins, **U2.9**, C50.2, U12.1 |
| 25 | 8.5 mm² | 1 at (20.11, 29.60), the C9 5 V output-cap return via | **J2.2** (ESC signal/power GND) |
| 16 | 3.2 mm² | 1, 1.89 mm away | U3.18 (VSS) |
| 9 | 4.8 mm² | 2, 1.14 mm away | U3.63 (VSS) |

- The MCU decaps' return to VSS therefore passes through the buck EP via fields, which carry the converters' switching ground currents.
- The ELRS supply return (50-150 mA, RF-bursty) flows through the same copper and single via as VSSA and the VDDA decaps. ADC LSB = 0.8 mV.

**Fix**
- Clear the F pour back from the U1/U2 thermal-via fields, or make those F patches their own fragment, so that MCU decaps do not tie into them.
- Give every MCU/analog decap GND pad its own via within 0.5 mm.
- Tie J5.2 and J2.2 with ≥ 2 vias in their own copper, away from the VSSA/VDDA fragment and the C9 return.

### G4-04 MAJOR: MCU power-distribution layout

**Evidence (`decap.py` routed distance; manual check of 3V3 tracks).**

| Pin | Cap | Routed path | Notes |
|---|---|---|---|
| VDD pin 32 (20.75, 23.18) | C28 | F 1.05 mm → via (21.94, 23.04) → **In2 ≈ 5.4 mm** → via (24.44, 27.24) → F 1.22 mm → C28.1 (23.15, 26.41). About 7.7 mm and 2 vias, i.e. ≈ 9 nH | `placecheck` reports 4.02 mm straight-line |
| VDD pin 48 | C26 | 6.6 mm with vias | |
| Pins 1 and 64 | C25 (shared) | 5.8 / 4.3 mm | |
| Pin 19 | C27 | 3.7 mm | |
| VCAP2 pin 47 | C34 | 8.2 mm, with an In1 hop | C34 GND nearest via **3.42 mm** (fragment 8) |
| VCAP1 | C33 | 0.62 mm | C33 GND nearest via **4.69 mm** (fragment 17, G4-03) |

- VSS pins 18/63 reach their nearest via in 1.9/1.1 mm, through 3-5 mm² fragments.
- In1 under the MCU body is 40 % copper (G4-02).
- Decap effectiveness above about 20-50 MHz is lost: the STM32 runs 168 MHz core and GPIO edges of about 2 ns. Expect ground/supply
  bounce, EMI and noise in ADC readings rather than outright failure.

**Fix**
- Route each VDD pin to its 100 nF on F.Cu in ≤ 2 mm, with no layer change. Place a 100 nF at pin 32 (C28 can move to the free area
  below pins 30-32).
- Give each decap GND a via within 0.5 mm into a contiguous In1.
- Route VCAP2 on F only.
- Add a routed-length check, not only a pad-centre check, to `placecheck`.

### G4-05 MAJOR: noisy nets through the IMU footprints

**Evidence.** Copper inside the courtyard boxes (`seg_in_box`):
- **U7 BMI270 (B, (20.80, 17.00))**:
  - In1: **MOTOR5 3.0 mm**, **MOTOR6 1.1 mm**, GYRO2_CS 1.3, SPI1_SCK 0.9, UART6_RX 0.9.
  - F: **MOTOR5 2.7 mm**, UART1_TX 2.9, LED_STRIP 1.7, UART1_RX 1.0.
  - In2 (the plane 0.21 mm above the IMU pads): **LED_STRIP 2.3 mm**, **STATUS_LED_GREEN 2.7 mm**.
  - In2 GND under U7: 58 %.
- **U6 ICM-42688-P (B, (15.40, 17.00))**:
  - In2: VTX_PWR_EN 3.0 mm, SPI1_MOSI 1.5 mm.
  - In1: 3V3_IMU 1.1 mm.
  - F: SPI1_MISO 3.0, SPI1_MOSI 1.6.
  - U6 sits entirely on the separate 57 mm² In1 island (0 % main plane).
- **3V3_IMU** (D-25, 0.127 mm, 15.0 mm) leaves B.Cu twice:
  - F 1.5 mm between vias (18.56, 14.81) and (18.51, 16.31), under the MCU pin field;
  - In1 3.1 mm (16.11-18.29, 16.49-18.66).
  - DC drop is negligible (10 mA × ≈ 60 mΩ ≈ 0.6 mV). The concern is noise pickup between the low-noise LDO and the IMUs. The pin caps
    C38/C40/C41/C42 are 0.67-0.83 mm routed, which is good.
- MOTOR5/6 are DShot outputs (about 2 ns edges), and LED_STRIP is WS2812 at 800 kHz. Gyro noise is this product's key performance metric.

**Fix**
- Keep In2 (the IMUs' adjacent plane) solid GND under both IMU courtyards plus 1 mm. Keep In1 GND there too.
- Move MOTOR5/6, LED_STRIP and STATUS_LED_GREEN out of the IMU footprints.
- Keep 3V3_IMU on B.Cu.

### G4-06 MINOR: 5 V distribution (G6S-05 residual)

**Evidence.** DC solve (`s5v.py`; budget loads P11 0.8 A, D5 0.41 A, P8 0.4 A, J4 0.1 A, P13 0.08 A; copper at 65 °C):
- The east branch carries **1.21 A** through a single **0.3 mm via (25.76, 29.76)** and 9.65 mm of **0.35 mm** B.Cu, (25.24, 30.21) → (15.84, 32.41).
- IPC-2221 external: about **+12 °C** at 1.21 A.
- Drops: P11 20 mV, D5 43 mV, P8 37 mV, J4 36 mV. The via resistance is 1.5 mΩ.
- 5 V no longer uses In1 or In2.

**Fix.** Widen the east trunk to ≥ 0.8 mm (as for L1 → C6) and use ≥ 2 vias at (25.76, 29.76).

### G4-07 MINOR: 10 V vias (G6S-04 residual)

**Evidence (`s10.py`).**
- The 10 V net is now F/B only, 0.45 mm (the In2 run from G6S-04 is gone).
- The path L2 → P3 at **1.3 A** passes 3 single 0.3 mm vias in series: (26.19, 31.94), (31.36, 29.54), (32.74, 27.66). Drop 24 mV.
- L2 → R41/J3 at 1 A adds vias (31.36, 11.64), (31.39, 19.49), (32.86, 21.89) and (26.56, 8.79), 51 mV in total.
- IPC-2221 external on 0.45 mm at 1.3 A: about **+9 °C**.

**Fix.** Use 2 vias at every 10 V layer change.

### G4-08 MINOR: VBAT In2 zone neck to U2

**Evidence.**
- The In2 VBAT zone is 136.5 mm², one polygon.
- U1 feed: the minimum path width (distance-transform bisection, `neck.py`) is 2.96 mm, and the FEM gives 2.1 mΩ (4 mV at 2 A).
- U2 feed: the bottleneck is **≈ 0.64 mm**. The 1.7 mm vertical strip (x 16.6-18.3) contains the GND via **(17.30, 24.60)** (C8 return,
  `gen/critical.py` VIAS) with its antipad.
- The second notch is GND via (11.10, 33.80) in the bottom band.
- FEM (`fem.py`, 0.5 oz at 65 °C): P1 vias → U2 vias = **16.3 mΩ**, 21 mV at 1.3 A, about 28 mW. Peak linear current density is
  **3.9 A/mm at (18.28, 25.08)**.
- IPC-2221 internal for the 1.7 mm strip at 1.3 A gives about +16 °C. IPC-2221 is not meaningful for the 0.6 mm × about 0.6 mm
  constriction itself; it spreads heat into the wide copper around it.

**Fix.** Move the C8 return via out of the VBAT strip, or route the strip around it.

### G4-09 MINOR: USB D+/D−

**Evidence (`net.py USB_DP USB_DM`, `decap.py`).**
- D+: J1 → F → U13 pins 4/3 (flow-through) → via (26.41, 17.66) → **In2 2.9 mm** → via (25.74, 14.84) → F → U3.45.
- D−: J1 → via (29.56, 15.11) → **B 4.8 mm** → via (24.81, 15.66) → F → U3.44. U13.6/U13.1 are reached by a 0.9-1.9 mm stub, so the
  ESD clamp is not in line.
- The two lines are on different layers, so they are never a coupled pair.
- J1 → MCU lengths: D+ 9.2 mm (A6), D− 8.9/9.4 mm, a mismatch ≤ 0.5 mm. Width 0.2 mm, about 67 Ω single-ended on F (formula, not
  field-solved).
- D+ (In2) crosses under the **MOTOR6** In1 slot and D− (F) crosses over the **MOTOR5** slot. The Betaflight motors tab spins motors while
  on USB.
- The U13 VBUS pin has no local cap: C51 is 14.2 mm routed away. The U13 GND via is 1.05 mm away.
- At 12 Mb/s FS (edges ≥ 4 ns, critical length about 100 mm) none of this is functionally limiting.

**Fix.**
- Route D+/D− together on F through U13's flow-through pins, over continuous In1.
- Add 100 nF at U13 pin 5.
- Keep motor lines from crossing under the pair.

### G4-10 MINOR: analog inputs near the 5 V switching node

**Evidence (`prox.py`, `at.py`).**
- **ESC_CURR** (pre-filter current-sense input, 23.8 mm, 3 vias):
  - On **In2**, (11.94, 22.76) → (11.11, 29.96) runs 7.25 mm over U1. In2 sits 0.21 mm above B.Cu, about 0.5-0.8 mm beside the SW/BST
    pins (12.13-13.68 mm) and over the EP. It also cuts the In2 GND that shields U1.
  - On In1, (11.19, 31.04) → (20.46, 32.11) passes over L1's SW pad, with In2 GND between.
- **RSSI_IN** (F, 18 mm) crosses over L1.1 and L2.1 SW pads. **RSSI_ADC** (F) crosses the SW_5V track at (13.79, 28.66). In both cases
  In1 and In2 GND are present between.
- **VBAT_ADC** runs on In1 for 11.7 mm across U1.
- The HSE_OUT In1 segment runs under U3 pins 8/9 (VBAT_ADC/CURR_ADC).
- All ADC inputs have 10 k / 10 nF RC (fc ≈ 1.6 kHz), so this is MINOR.

**Fix.** Keep ESC_CURR off In2 over U1 and off In1 over L1, and route it on F away from the bucks.

### G4-11 MINOR: 5 V feedback sense routing

**Evidence.**
- The FB node itself is fine: 4.1 mm on B.Cu with In2 GND above it, checked at (15.25, 22.6), (15.9, 23.0) and (12.9, 23.7). R5 is
  1.96 mm from U1.5.
- R4's top (5V) is fed from via (12.66, 22.96). That via comes from the 0.35 mm west 5 V branch, which carries 0.58 A:
  - on F, (12.06, 28.26) → (12.14, 25.46) → (12.66, 22.96), running directly over U1's SW/BST pins. In1 is void at (12.9, 27.5);
    In2 is GND there;
  - on B, (11.79, 29.39) → (12.59, 32.64), 0.3-0.9 mm beside L1's SW pad.
- The LMR38020 datasheet §9.5.1 says: "this latter trace must not be routed near any noise source (such as the SW node)".
- Because 5 V is a low-impedance node, the practical effect is small.

**Fix.** Take R4's top from C8/C6 by a dedicated trace that stays away from SW.

### G4-12 MINOR: dangling fanout vias

**Evidence.** DRC reports 17 `via_dangling`: UART5_RX, BEEPER, MOTOR8, UART2_RX, MOTOR1, MOTOR4, ESC_TLM, CAM_SEL, **SPI1_SCK,
SPI1_MISO**, GYRO1_INT, STATUS_LED_BLUE, SWDIO, SWCLK, **SPI3_SCK, SPI3_MOSI**, MOTOR7.
- Each is a 1.6 mm stub (≈ 0.2-0.3 pF), which is negligible at SPI rates.
- Each also punches a 0.6 mm + clearance antipad through In1 and In2 under the MCU, where In1 is already 40 %.

**Fix.** Delete them with `gen/prune.py`, then refill.

### G4-13 MINOR: GND stitching density

**Evidence.**
- 52 GND vias plus 16 buck thermal vias plus 4 J1 shell pins on 1296 mm².
- Only 3 GND vias are within 2 mm of the board edge.
- 0 GND vias are within 3 mm of U1/U2/L2/J1/U4 (other than the EP fields).
- **23 of 39** F/B GND pour fragments (14 of 25 on F, 9 of 14 on B) are tied to the planes by exactly one via or TH pad. Three F fragments (20, 21, 24) are tied only through U1's thermal-via pads.
- J2.2 (ESC GND, the DShot return and the harness ground) has a single via (20.11, 29.60), shared with C9 (G4-03).
- J5.2 has a single via 4.7 mm away.

**Fix.**
- Add a GND via ring along the board edge, about every 3 mm where space allows.
- Use ≥ 2 vias per pour fragment and per connector GND pin.

### G4-14 INFO: stackup and impedance

- `kicad/F405FC.kicad_pcb` has no `(stackup ...)` section.
- `fab/gerbers/F405FC-job.gbrjob` MaterialStackup is KiCad's default: 3 × 0.48 mm FR4 and 35 µm on In1/In2. That contradicts
  `design/requirements.md:9` (JLC04161H-7628, 0.5 oz inner). Gate 5 (`review/gate-5-dfm.md` ≈ line 195) noted the same.
- Every PI number in this report assumes 0.5 oz inner copper, which is the worse case for In1/In2 resistance.
- No net is impedance-controlled. USB FS and SPI at these lengths (≤ 20 mm) do not need it.

**Fix.** Set the stackup in the board, or add fab notes.

### G4-15 INFO: missing In1 inventory

D-22 says "the In1 copper is listed in `review/summary.md`". That file does not exist. The table in G4-02 can serve as that list.

### G4-16 INFO: video lines

- CAM1_VID 5.3 mm (B), CAM2_VID 5.7 mm (B + In2 4.8 mm, 2 vias), VTX_VID 3.7 mm (B/F, 2 vias). U11 is at (6.50, 17.60).
- Crossings are perpendicular, adjacent-layer only: UART2_TX/RX on In2, 5V on F (2 planes between), 3V3/3V3A.
- All three are more than 8 mm from either SW node.
- The overlap capacitance per crossing is ≈ 0.003 pF.

---

## Power distribution summary (Q3)

Current rating is IPC-2221 (k = 0.048 external, 0.024 internal), with 1 oz outer and 0.5 oz inner copper. IPC-2152 was not computed;
it typically allows the same or more current, especially internally. IR drops come from the track/via network solve at 65 °C copper.

| Rail / segment | Width, layer | Current used | IPC-2221 ΔT | Drop | Vias at transitions |
|---|---|---|---|---|---|
| VBAT P1 → U1 (In2 zone + 3 vias + B 0.8) | zone, ≥ 2.96 mm neck | 2.0 A | — | 4 mV (zone) | P1: 4; U1: 3; U2: 3 |
| VBAT P1 → U2 (In2 zone) | zone, ≈ 0.6 mm neck (G4-08) | 1.3 A | +16 °C (1.7 mm strip) | 21 mV | 3 |
| VBAT U1/U2 hot-loop tracks | 0.8 mm B | ≤ 1.4 A | +4 °C | — | — |
| VBAT ESC pin J2.1 | 0.35 mm F → 1 via (16.86, 30.89) | ≤ 1 A (JST) | — | — | 1 |
| 5V L1 → C6/C7/C8 | 0.8 mm B | 1.8 A | +8 °C | — | — |
| 5V east trunk | 0.35 mm B + 1 via | 1.21 A | **+12 °C** | 20-43 mV | 1 (G4-06) |
| 5V west branch | 0.35 mm F/B | 0.58 A | +2 °C | ≤ 37 mV | 1 |
| 10V → P3 / → R41-J3 | 0.45 mm F/B | 1.3 A / 1.0 A | +9 °C | 24 / 51 mV | 3 / 7 single (G4-07) |
| 5V_SYS D5 → U4 | 0.2 mm B | 0.41 A | +3 °C | 2 mV | — |
| 5V_SYS → J5 (In1 0.2 mm, 9.2 mm) | inner | 0.15 A | +4 °C | 18 mV | — |
| 3V3 (0.2 mm; 14.6 mm on In1, 7.9 mm on In2) | outer / inner | ≤ 0.25 A | +1 °C outer, +13 °C inner (conservative) | small (≈ 2.5/4.9 mΩ/mm) | single vias |
| 3V3_IMU 0.127 mm, 15 mm (D-25) | B/F/In1 | 10 mA | ≈ 0 | < 1 mV | 3 vias (G4-05) |
| 3V3A (FB1 → VDDA), 13 mm incl. In1 4.7 | 0.2 mm | < 5 mA | ≈ 0 | < 0.1 mV | — |

## Checked and OK

- **Hot loops.**
  - U1: VIN pin 3 (7.50, 24.97) → C4.1 (5.55, 25.55) → C4.2 (5.55, 27.10) → GND pin 1 (7.50, 27.50). About 1.95 × 2.5 mm ≈ 5 mm², all
    on B.Cu with 0.8 mm tracks. C4 is 2.04 mm from the pin.
  - U2: C12 at 2.01 mm, loop ≈ 4.5 mm².
  - The bulk input caps are 3.4-5.6 mm away (routed).
  - In2 above U1's loop is the VBAT zone and above U2's loop is GND. Both are solid image planes.
- **SW nodes.**
  - SW_5V ≈ 8.7 mm² and SW_10V ≈ 9.3 mm² (tracks + pads), both on B.Cu only.
  - In2 is GND directly above both. I checked (12.9, 27.5), (13.6, 29.5), (13.42, 30.0), (29.35, 27.0) and (29.38, 28.0).
  - No In2 or B track of another net is within 1.5 mm, except ESC_CURR on In2 near U1 (G4-10).
  - The nearest sensitive parts are more than 8 mm away: IMUs about 10 mm, Y1 about 11 mm.
- **BST loops.** C5/C13 are 1.71 mm from the pin, with 0.3 mm BST and 0.6 mm SW tracks.
- **FB_10V.** 1.5 mm total, away from SW_10V. R9's top is on the 10 V output trace.
- **Thermal pads.** 8 thermal vias per EP, connected to In1 and In2 GND.
- **Decoupling.**
  - IMU decaps are 0.67-0.83 mm routed from the pins.
  - LDOs: U4 input 0.75 mm, U5 in/out 0.70/0.90 mm.
  - VDDA caps C32/C31 are 1.20/1.45 mm from pin 13, with FB1 next to them.
  - U9/U8 decaps are ≤ 1 mm. U12 C50 is 1.65 mm. U10 C48 is 4.8 mm with vias (minor).
- **GND pour fragments.** No floating GND copper on any layer (every fragment touches a GND pad, via or track).
- **Grommet keepouts.** Pours stay 2.27 mm (raster resolution) from all four hole centres. G6S-03 is fixed.
- **DRC.** 0 errors, 0 unconnected, 0 parity.

## Not verified

- I did not field-solve impedance or crosstalk. Impedances and capacitances are closed-form estimates. JLC dielectric thicknesses are recalled, not read from a JLC document.
- I computed no IPC-2152 values. All temperature rises are IPC-2221. I did no thermal simulation of the VBAT neck or the bucks.
- The routed lengths come from my centreline graph (`solve.py` / `decap.py`). Joints are snapped at ≤ 0.2 mm and via hops are
  approximated. I checked the key values by hand from the track listing (pin 32 → C28, HSE_OUT, USB, 5 V/10 V paths), but not every
  decap number.
- I did not simulate or compute EMI, radiated emissions, crystal start-up on hardware, HSE jitter, ADC noise or gyro noise. These are
  layout-rule judgements.
- USBLC6-2SC6 VBUS-cap guidance: no ST datasheet is in `datasheets/`. The "add 100 nF" advice is general practice, not a quoted
  requirement.
- I did not compare against the LMR38020 EVM layout (not in the repo). The guidelines quoted come from `datasheets/lmr38020.pdf`
  §9.5.1 (read as text).
- I did not open the fab Gerbers. I analysed the stored zone fills in the .kicad_pcb, which DRC also uses. Whether the Gerbers match
  the refilled board was not checked.
- Effective input capacitance under DC bias and cap SRF/ESL were not checked.
