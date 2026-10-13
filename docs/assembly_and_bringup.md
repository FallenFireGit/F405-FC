# F405-FC hand assembly and bring-up guide

Board: 36 x 36 mm, 4 layers, 1.6 mm, parts on both sides (0402 minimum, no BGA). Reference designators and nets below come from
`kicad/F405FC.kicad_pcb`; the interactive BOM (`bom/F405FC_ibom.html`) shows every part's location per side.
Power design and limits: `design/power.md`. Decisions and deviations: `design/decisions.md`.

**Rule for the whole procedure: the MCU (U3) and the sensors are fitted only after every power rail has been checked on a
current-limited bench supply.**

## 0. What you need

- Bench supply with adjustable current limit (0-30 V, 0-3 A), DMM, oscilloscope (≥ 50 MHz) for ripple checks.
- Hot plate or hot-air station, fine-tip iron, flux, 0.4 mm stencil-printed or syringe paste (SAC305 or Sn63Pb37), magnification.
- ST-LINK (SWD) is optional; USB DFU works.
- Electronic load (or power resistors) for the full-load test: 5 V at 1.7 A (≈ 3 Ω, 10 W) and 10 V at 1.3 A (≈ 7.5 Ω, 15 W).
- A fan for every full-load or thermal test (the board is not rated for full load in still air, `design/power.md` §12.5, D-12).

## 1. Bare-board checks (before any part)

Measure resistance to GND (TP5 or P2) with the DMM. All must read open (> 1 MΩ) on a bare board:
VBAT (P1), 5V (P8 / P11), 10V (P3), 5V_SYS (J5 pin 1), 3V3 (TP4), VBUS (USB-C), SW nodes (L1/L2 pad 1 lands).
Any short here is a fab defect: do not populate.

## 2. Stage A: power section only

Fit, bottom side first (all are bottom-side parts unless noted):

| Block | Parts |
|---|---|
| Battery entry | D1 (TVS, **top**), C1 (10 uF 1210, **top**) |
| 5 V buck | U1, L1, C2, C3, C4, C5, C6, C7, C8, C9, R1, R2, R3, R4, R5 |
| 10 V buck | U2, L2, C10, C11, C12, C13, C14, C15, C16, C17, R6, R7, R8, R9, R10 |
| VTX switch | Q2, and the 1k / 100k gate resistors on VTX_PWR_EN / VTX_OFF_G |
| 5V_SYS OR | D4 (**top**), D5 |
| LDOs | U4 (3V3) + its caps, U5 (3V3_IMU) + its caps |
| VTX feed | R41 (0R 0805; leave it **out** on 2S HD builds, D-11/D-16) |

Notes for U1/U2 (TI HSOIC-8 PowerPAD): the exposed pad needs solder. Print paste through the stencil (three windows per pad,
`fab/F405FC_stencil.zip`) or tin the pad lightly, then reflow with the hot plate or hot air from the bottom. Check pin 1 orientation
against the silk dot. The inductors are polarity-free but heavy: reflow them with the bucks so the second-side reflow does not move them.

Side order: the bottom side carries the bucks, inductors and most power parts, so reflow it first on the hot plate. The top side
(MCU, IMUs, connectors) is then done with hot air or the iron while the board rests on standoffs, never back on the hot plate,
so the bottom-side inductors and 1210 caps do not reflow and drop. Keep hot air away from the bottom side once it is populated.
Part heights against vendor drawings were not verified (see review/summary.md); check them with calipers before closing a stack.

### 2.1 First power-up (current limited)

1. Supply 8.4 V, current limit **100 mA**, to P1 (+) / P2 (−). Watch the current while switching on.
2. Expected: the supply stays out of current limit (FPWM no-load draw of both bucks is a few tens of mA; record the value).
   If it hits the limit, switch off and look for a short or a reversed part.
3. Rails (DMM):

| Rail | Where | Expected | Notes |
|---|---|---|---|
| 5V | P8 / P11 | 4.96-5.28 V (5.115 V nominal) | FB 100k / 24.3k |
| 10V | P3 | **in dropout at 8.4 V** (≈ 7.2-8.1 V at no load) | Regulates above ≈ 11.5 V input |
| 5V_SYS | J5 pin 1 | ≈ 4.7-4.9 V | 5V through D5 |
| 3V3 | TP4 | 3.25-3.35 V | LP38692 |
| 3V3_IMU | U5 output cap | 3.25-3.35 V | LP5907 |

4. Raise to 16.8 V (4S), limit 150 mA: 10V must read 9.76-10.43 V; all other rails unchanged.
5. Raise to 25.2 V (6S), limit 150 mA: rails unchanged. Do not exceed 25.2 V (the TVS starts conducting at 28.9 V).
6. UVLO: lower the input slowly from 8 V. Both bucks switch off between 3.8 V and 4.9 V and restart between 4.4 V and 5.6 V.
7. VTX power switch: with 16.8 V in, apply 3.3 V through a 1 kΩ resistor to the VTX_PWR_EN node (or, after Stage B, toggle PINIO1):
   10V must drop to 0 V. Remove it: 10V returns within about 5 ms (soft start).
8. USB only (battery disconnected): plug USB-C into a current-limited USB port or a USB power meter. 5V_SYS ≈ 4.6-4.7 V (via D4),
   3V3 present, **5V and 10V must stay at 0 V** (GPS/LED/camera rails are battery-only by design).

### 2.2 Loaded checks (fan running)

1. 16.8 V in, limit 3 A. Load 5V with 1.7 A: 5V stays above 4.96 V. Ripple at C8 < 50 mV p-p (scope, short ground spring).
2. Load 10V with 1.3 A (the rev C continuous budget, D-19): 10V stays above 9.76 V.
3. Repeat at 25.2 V. Measure VIN ripple at the U1/U2 VIN pins at full load (target < 250 mV p-p; D-20 input-cap check).
4. Thermal check per `design/power.md` §12.5: after 10 minutes at full budget with airflow, (U1/U2 case − ambient) ≤ the pass limit
   given there. Without airflow, keep the total output below 1 W.

## 3. Stage B: MCU and USB

Fit U3 (STM32F405RGT6, LQFP-64, **top**: drag-solder with flux, then inspect every pin under magnification; check pin 1), Y1 + C36/C37,
all MCU decoupling (C24-C35, C52, C53), FB1, U13 (USB ESD), J1 (USB-C), SW1 (BOOT), U10 (flash), LEDs D10-D12 + resistors, TP1-TP5.

1. Before power: SW1 open = BOOT0 low (measure BOOT0 to 3V3: open circuit unless the button is pressed).
2. Bench 8.4 V, limit 200 mA. Expect ≈ 40-80 mA more than Stage A. 3V3 stays at 3.3 V.
3. DFU (USB power only, pinmap R-08): **switch the bench supply off**, hold BOOT, then plug USB (BOOT0 is sampled only at reset;
   alternatively hold BOOT and short TP3 NRST to TP5 GND briefly). The PC must enumerate "STM32 BOOTLOADER" (0483:DF11). Flash Betaflight (STM32F405 target), then apply
   `design/betaflight_config.txt` in the CLI (paste, `save`). Alternative: SWD via TP1 SWDIO, TP2 SWCLK, TP3 NRST, TP5 GND, TP4 3V3 sense.
4. USB-only DFU note: on USB power the 5 V rail is off, so GPS/LEDs/cameras stay dark. This is intended. The Betaflight `bl`
   command enters the same ROM bootloader, so use it on USB power only too: with a battery the VTX/GPS UARTs can capture it.

## 4. Stage C: sensors and remaining parts

Fit U6 (ICM-42688-P) and U7 (BMI270) (LGA, bottom side: local hot air with a small nozzle, Kapton tape over the neighbouring
bottom-side parts, paste or pre-tinned pads, no iron), U8 (BMP390), U9 (IIS2MDC), U11 (video switch),
U12 (buffer), D9, Q1 and the remaining passives, connectors J2-J5.

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
- Baro (`status` lists BMP390 on I2C) and magnetometer (IIS2MDC) detected.
- PINIO1 (VTX power) and PINIO2 (camera switch): toggle with the mode switch and confirm 10V and the camera source change.

## 5. Installation notes for users

- Solder the battery leads to the **P1 (VBAT) / P2 (GND)** bottom pads, or check the ESC harness current rating (JST-SH pins are 1 A).
- Fit a low-ESR electrolytic of 470-1000 uF, ≥ 35 V across the ESC battery pads.
- 10 V rail: 1.3 A continuous (DJI O3 / Walksnail / HDZero OK). On 2S, HD VTXs must be powered from VBAT and R41 removed (D-11).
- **J3 (front, silk "VTX 10V") carries 10 V** for the VTX: never plug a GPS or other 5 V device into it (D-15). GPS goes to J4.
- Connect the battery before USB, or reboot after plugging the battery: on USB alone the 5 V/10 V peripherals are unpowered and
  are not detected (D-15).
- LED strip wiring: DIN to P10, 5 V to P11, GND to P4 (the 10 V VTX GND pad, shared; D-21).
- LED strip: limit to 0.8 A (≈ 13 WS2812 at full white) or set `ledstrip_brightness` ≤ 50 %.
