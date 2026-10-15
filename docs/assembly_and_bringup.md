# F405-FC hand assembly and bring-up guide

Board (rev D): 36 x 36 mm, 6 layers, 1.6 mm, parts on both sides (0402 minimum, no BGA). Reference designators and nets below come from
`kicad/F405FC.kicad_pcb`; the interactive BOM (`bom/F405FC_ibom.html`) shows every part's location per side.
Power design and limits: `design/power.md`. Decisions and deviations: `design/decisions.md`.

**Rule for the whole procedure: the MCU (U3) and the sensors are fitted only after every power rail has been checked on a
current-limited bench supply.**

## 0. What you need

- Bench supply with adjustable current limit (0-30 V, 0-3 A), DMM, oscilloscope (≥ 50 MHz) for ripple checks.
- Hot plate **and** hot-air station, fine-tip iron and a ≥ 60 W iron with a 2-3 mm chisel tip (USB-C shell), flux, magnification.
- Solder paste (SAC305 or Sn63Pb37, type 4 or finer) and a **0.10 mm** stainless stencil (`fab/F405FC_stencil.zip`). The
  BMP390's 0.25 x 0.275 mm apertures have an area ratio of 0.65 at 0.10 mm and only 0.55 at 0.12 mm (Gate 5 m-6).
- Mounting: **nylon** M3 screws/standoffs or the grommets on all four holes. VBAT and VBUS copper (P1, D1, D4) is 3.0-3.4 mm from
  the hole centres; a metal nut or standoff can touch a battery-lead fillet (Gate 5 m-5).

### 0.1 Fab order settings (JLCPCB; the job file is not read by JLC)

| Setting | Value |
|---|---|
| Layers / thickness | 6 layers, 1.6 mm, a JLC 6-layer 1.6 mm stackup (pick it on the JLC order page; the name and dielectric thicknesses were not verified here). Gerber names give the layer roles: In1 = GND, In2 = SIG, In3 = PWR (signals + VBAT), In4 = GND |
| Copper | 1 oz outer, 0.5 oz inner |
| Surface finish | **ENIG** (HASL is uneven on 0.25 mm LGA and 0.5 mm LQFP pads) |
| Via covering | **Epoxy filled and capped (POFV): required.** About 51 vias (15 of them in-pad) sit < 0.10 mm (closest 0.018 mm, U3 pin 48; rev D Gate 5 count) from same-net fine-pitch or 0402 pads (U3, U6-U8, U10) and a few VBAT vias touch the C10/C12/C8/D1 pads; filled vias stop solder wicking there (Gate 5 M-3, D-26). POFV on JLC 6-layer boards was not checked on the live JLC page |
| Min track / space, via | 0.127 / 0.127 mm, 0.3 / 0.6 mm |
| Mask / silk | any colour; silk text height 0.8 mm |

This option and its cost on 6-layer boards were not checked against the live JLC page.
- ST-LINK (SWD) is optional; USB DFU works.
- Electronic load (or power resistors) for the full-load test: 5 V at 1.7 A (≈ 3 Ω, 10 W) and 10 V at 1.3 A (≈ 7.5 Ω, 15 W).
- A fan for every full-load or thermal test (the board is not rated for full load in still air, `design/power.md` §12.5, D-12).

## 1. Bare-board checks (before any part)

Measure resistance to GND (P2) with the DMM. All must read open (> 1 MΩ) on a bare board:
VBAT (P1), 5V (P8 / P11), 10V (P3), 5V_SYS (J5 pin 1), 3V3 (TP4), VBUS (USB-C), SW nodes (L1/L2 pad 1 lands).
Any short here is a fab defect: do not populate.

## 2. Stage A: bottom side in one hot-plate pass, then the power checks

**Side order (Gate 5 M-2).** Every bottom-side part except three goes on in **one** hot-plate reflow, before anything is fitted on
the top. The bottom IMUs U6/U7 sit directly under the MCU (U3), and the flash U10 sits under the magnetometer U9, so none of them
may be soldered by local hot air after the other side is populated. The top side is then done with hot air or the iron while the
board rests on standoffs, never back on the hot plate, so the bottom-side inductors and 1210 caps do not reflow and drop.

**A1, hot plate, bottom side:** all bottom parts in the interactive BOM **except D5, U4 and U5**:

| Block | Parts (bottom) |
|---|---|
| 5 V buck | U1, L1, C2, C3, C4, C5, C6, C7, C8, C9, R1, R2, R3, R4, R5 |
| 10 V buck | U2, L2, C10, C11, C12, C13, C14, C15, C16, C17, R6, R7, R8, R9, R10 |
| VTX switch | Q2 and its gate resistors |
| Logic, unpowered in Stage A | U6 (ICM-42688-P), U7 (BMI270), U10 (flash), U11 (video switch), D10-D12, all remaining bottom passives (incl. the U4/U5 caps) |

Then, top side by iron or hot air: D1 (TVS) and C1 (10 uF 1210), and R41 (0R 0805, VTX feed; leave it **out** on 2S HD builds,
D-11/D-16). Nothing else on the top yet.

Every bottom logic part is supplied only from 3V3 (U4) or 3V3_IMU (U5), which in turn are fed only through D5 (5V_SYS). With D5, U4
and U5 left off they cannot see a rail during the power checks: a wrong or open feedback resistor that drives 5 V towards VIN cannot
reach them (Gate 6 G6S-02). **A2** (step 2.1.8) fits D5, U4 and U5 (SOD-123 / SOT-223 / SOT-23-5) by hot air or iron once the
5 V and 10 V rails are verified; they sit away from U6/U7/U10.

Notes for U1/U2 (TI HSOIC-8 PowerPAD): the exposed pad needs solder. Print paste through the stencil (three windows per pad,
`fab/F405FC_stencil.zip`), then reflow. Check pin 1 orientation against the silk pin-1 triangle before reflow. Use a **0.10 mm** stencil (the
BMP390/BMI270 apertures need it, see §0) and inspect the LGA parts (U6/U7) and the WSON flash (U10) for bridging at the outer pads
under magnification; their joints cannot be reworked once the top is populated, so get them right in this pass.
Part heights against vendor drawings were not verified (see review/summary.md); check them with calipers before closing a stack.

### 2.1 First power-up (current limited)

0. Before power, with the DMM: R4 (100k) and R5 (24.3k) in place and reading those values in circuit (5 V feedback), R9 (100k) /
   R10 (11.0k) for the 10 V feedback, U1/U2 pin 1 orientation, no solder bridge on U1/U2 pins 3/4/5.
   **Stop criteria for every step below:** supply in current limit, any rail outside its window, or anything warm: switch off and
   find the cause before going on.
1. Supply **6.5 V** first (5V regulates, 10V is in dropout), current limit **100 mA**, to P1 (+) / P2 (−). 5V must read
   4.96-5.28 V before the input goes any higher. Then go to 8.4 V, same limit. Watch the current while switching on.
2. Expected: the supply stays out of current limit (FPWM no-load draw of both bucks is a few tens of mA; record the value).
   If it hits the limit, switch off and look for a short or a reversed part.
3. Rails (DMM):

| Rail | Where | Expected | Notes |
|---|---|---|---|
| 5V | P8 / P11 | 4.96-5.28 V (5.115 V nominal) | FB 100k / 24.3k |
| 10V | P3 | **in dropout at 8.4 V** (≈ 7.2-8.1 V at no load) | Regulates above ≈ 11.5 V input |

4. Raise to 16.8 V (4S), limit 150 mA: 10V must read 9.76-10.43 V; all other rails unchanged.
5. Raise to 25.2 V (6S), limit 150 mA: rails unchanged. Do not exceed 25.2 V (the TVS starts conducting at 28.9 V).
6. UVLO: lower the input slowly from 8 V. Both bucks switch off between 3.8 V and 4.9 V and restart between 4.4 V and 5.6 V.
7. VTX power switch: with 16.8 V in, apply 3.3 V through a 1 kΩ resistor to the VTX_PWR_EN node (or, after Stage B, toggle PINIO1):
   10V must drop to 0 V. Remove it: 10V returns within about 5 ms (soft start).
8. Switch off, fit D4 (top), D5, U4 and U5 (A2; their caps went on in A1), then repeat steps 1-3 at 8.4 V and also check:

| Rail | Where | Expected | Notes |
|---|---|---|---|
| 5V_SYS | J5 pin 1 | ≈ 4.7-4.9 V | 5V through D5 |
| 3V3 | TP4 | 3.25-3.35 V | LP38692 |
| 3V3_IMU | U5 output cap | 3.25-3.35 V | LP5907 |

### 2.2 Loaded checks (fan running)

1. 16.8 V in, limit 3 A. Load 5V with 1.7 A: 5V stays above 4.96 V. Ripple at C8 < 50 mV p-p (scope, short ground spring).
2. Load 10V with 1.3 A (the rev C continuous budget, D-19): 10V stays above 9.76 V.
3. Repeat at 25.2 V. Measure VIN ripple at the U1/U2 VIN pins at full load (target < 250 mV p-p; D-20 input-cap check).
4. Thermal check per `design/power.md` §12.5: after 10 minutes at full budget with airflow, (U1/U2 case − ambient) ≤ the pass limit
   given there. Without airflow, keep the total output below 1 W.

## 3. Stage B: MCU and USB

Fit U3 (STM32F405RGT6, LQFP-64, **top**: drag-solder with flux, then inspect every pin under magnification; check pin 1), Y1 + C36/C37,
the top MCU decoupling (C25-C29, C31-C34), C53 (RSSI filter), R14/R15 (VBAT divider), R16 (BOOT0 pull-down), **R17 (BOOT1/PB2
pull-down: the ROM bootloader needs BOOT1 low, so DFU can fail without it)**, R19 (GYRO2_CS pull-up), **R34/R35 (USB-C CC 5.1k
pull-downs: without them a C-to-C cable supplies no VBUS)**, R36/C51 (VBUS sense), FB1, U13 (USB ESD), J1 (USB-C), SW1 (BOOT)
(the bottom-side parts, U10 flash, LEDs D10-D12 and C24/C30/C35/C52 went on in A1; TP1-TP5 are bare pads).

J1 shell: the four shell slots have thermal reliefs (Gate 5 M-1) but still connect to GND on all six copper layers. Use a ≥ 60 W iron with a 2-3 mm
chisel tip and preheat the board from the top with hot air (≈ 150 °C) before soldering the shell; fill each slot from the top
until solder shows at the bottom. These four joints hold the connector. Check the bottom side afterwards: R7 (10 V buck enable) sits
0.35 mm from a shell slot, and a bridge there disables the 10 V rail; R6 pad 1 is **VBAT** 0.74 mm from a GND slot ring, and a bridge
there shorts the battery (check R6 pad 1 to P2 reads open before any power).

1. Before power (DMM, unpowered): across the two SW1 pads on the BOOT0 side: open with the button released, ≈ 0 Ω pressed.
   BOOT0 (U3 pin 60) to GND ≈ 10 kΩ (R16); PB2 (U3 pin 28) to GND ≈ 10 kΩ (R17); J1 CC1 and CC2 pins to GND ≈ 5.1 kΩ each (R34/R35).
2. USB only (battery disconnected): plug USB-C into a current-limited USB port or a USB power meter. 5V_SYS ≈ 4.6-4.7 V (via D4),
   3V3 present, **5V and 10V must stay at 0 V** (GPS/LED/camera rails are battery-only by design).
3. Bench 8.4 V, limit 200 mA. Expect ≈ 40-80 mA more than Stage A. 3V3 stays at 3.3 V.
4. DFU (USB power only, pinmap R-08): **switch the bench supply off**, hold BOOT, then plug USB (BOOT0 is sampled only at reset;
   alternatively hold BOOT and short TP3 NRST to P2 GND briefly). The PC must enumerate "STM32 BOOTLOADER" (0483:DF11). Flash Betaflight (STM32F405 target), then apply
   `design/betaflight_config.txt` in the CLI (paste, `save`). Alternative: SWD via TP1 SWDIO, TP2 SWCLK, TP3 NRST, TP5 GND (check TP5 to P2 continuity first), TP4 3V3 sense.
5. USB-only DFU note: on USB power the 5 V rail is off, so GPS/LEDs/cameras stay dark. This is intended. The Betaflight `bl`
   command enters the same ROM bootloader, so use it on USB power only too: with a battery the VTX/GPS UARTs can capture it.

## 4. Stage C: top-side sensors and remaining parts

Fit (top side, hot air with a 3-5 mm nozzle, Kapton over the neighbours, or iron): U8 (BMP390), U9 (IIS2MDC), U12 (LED buffer),
D9, Q1, the remaining top passives and the connectors J2-J5. U6/U7 (IMUs) and U11 are already on (A1).
**Do not fit R32 or R37** (DNP 0R links; the iBOM omits them). R32 shorts the MCU LED_STRIP pin to the 5 V output of U12; fit it only
with U12 removed. R37 links the HD-VTX R2 pin to UART5_RX (non-inverted SBUS option only).

Paste on the top side after the bottom is populated: either print through the stencil with the board on a support carrier
(a plate with pockets for the bottom parts, so the board sits flat), or dispense paste from a syringe (fine needle, type 4/5
paste) on U8 and U9, or tin their pads with the iron and reflow with hot air and flux. Preheat from below (≈ 120-150 °C) for
top-side hot air: most top GND pads are poured solid into the planes (incl. U8 pads 3 and 8). Y1 went on in Stage B.

In the Betaflight CLI:
- `status`: gyro and accelerometer detected, CPU load normal, no I2C errors.
- `resource` / `dma show`: matches `design/betaflight_config.txt`.
- Gyro alignment: the values in the config are **provisional** (U6 CW270FLIP, U7 CW0FLIP from the placement review). Verify on the
  bench with the Betaflight Setup tab 3D model: tilt the board nose-down and roll right; correct `gyro_1_sensor_align` /
  `gyro_2_sensor_align` until both match. Record the final values in the config file.
- Cold-boot check: power-cycle (unplug USB) at least five times; `status` must list both gyros every time. Both IMUs share SPI1
  and start in I2C mode, and Betaflight remembers the gyros it found: if gyro 2 is ever missing, run `defaults`, re-paste the config
  and `save`, then repeat the check.
- Magnetometer: `align_mag` is not derived (IIS2MDC datasheet not on file). Calibrate and check the heading in the Setup tab;
  set `align_mag` on the bench if the heading moves the wrong way.
- VBAT and current ADC inputs have 10k + 10 nF RC filters but no diode clamps (D-23): do not drive the CURR pad above 3.3 V.
- Baro and magnetometer detected: Betaflight reports the BMP390 as **BMP388** and the IIS2MDC as **LIS2MDL** (same drivers).
- Board front: the **J3 (VTX) edge**, marked "FRONT" with an arrow on both silk layers. Mount it facing forward or set `align_board_yaw`.
- Before the first flight, also check: blackbox (`flash_info`, record and download a short log), motors in the Motors tab with
  props off (DShot, direction), ESC telemetry if wired, OSD/MSP on the VTX, LED strip, beeper, VBAT reading against a DMM and the
  current-sensor scale, and assign USER1/USER2 (PINIO1/2) modes in the Modes tab.
- PINIO1 (VTX power) and PINIO2 (camera switch): toggle with the mode switch and confirm 10V and the camera source change.

## 5. Installation notes for users

- Solder the battery leads to the **P1 (VBAT) / P2 (GND)** bottom pads, or check the ESC harness current rating (JST-SH pins are 1 A).
- Fit a low-ESR electrolytic of 470-1000 uF, ≥ 35 V across the ESC battery pads.
- 10 V rail: 1.3 A continuous (DJI O3 / Walksnail / HDZero OK). On 2S, HD VTXs must be powered from VBAT and R41 removed (D-11).
- **J3 (front; its silk warning "J3 VTX 10V" is on the back, there is no room beside the connector on the front) carries 10 V** for the VTX: never plug a GPS or other 5 V device into it (D-15). GPS goes to J4.
- Connect the battery before USB, or reboot after plugging the battery: on USB alone the 5 V/10 V peripherals are unpowered and
  are not detected (D-15).
- LED strip wiring: DIN to P10, 5 V to P11, GND to P4 (the 10 V VTX GND pad, shared; D-21). P4 sits next to the 10 V pad P3:
  solder the LED GND wire first and check P3-P4 for bridges before power.
- LED strip: limit to 0.8 A (≈ 13 WS2812 at full white) or set `ledstrip_brightness` ≤ 50 %.
