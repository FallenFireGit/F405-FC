# Gate 6 red team (rev D): Betaflight bring-up walkthrough, paper review

Reviewer: a fresh, adversarial agent that had not worked on the design before. Date 2026-10-15. Repo HEAD `0524b43` (rev D, 6 layers).
Scope: flashing (DFU), both gyros, baro, mag, OSD/MSP, blackbox, DShot timers and DMA, PINIO, LED strip, beeper, UARTs, ADC, INAV
consistency, and a re-check of every finding in `review/gate-6-betaflight-redteam.md` (older snapshot) against rev D.
This is a review only. No repo file other than this report was changed.

## Verdict: **FAIL** (0 BLOCKER, 2 MAJOR, 6 MINOR, 6 INFO)

The electrical design is consistent with the Betaflight config. All 64 MCU pins, every `resource` line, every `timer` AF, and every
`dma` option resolve correctly, and no DMA stream is used twice. Both gyro alignments re-derive to the configured values from the
rev D footprints. The gate fails on two MAJOR findings in the board and the bring-up procedure:
1. Rev D has **no forward marking on the board**. The gyro alignment is defined relative to a "FRONT" silk mark that the config
   and the INAV target say exists, but it was removed.
2. The Stage B part list for the **first DFU flash leaves out R17 (the BOOT1 strap) and R34/R35 (the USB-C CC pull-downs)**. As
   written, DFU can fail or the board gets no power from a C-to-C cable.

## Method (what was actually run)

| Check | How | Result |
|---|---|---|
| Netlist | `kc 'kicad-cli sch export netlist --format kicadxml …'` → parsed (`/opt/kroot/tmp/rt6bf/nl.json`) | U3 pins 1-64 dumped. All nets listed below |
| Pin positions | `datasheets/st_open_pin_data/F405RGTx.xml` positions 1-64 vs. netlist | All 64 match (PA11=44, PA12=45, BOOT0=60, PC14=3 …) |
| AFs | Script over `GPIO-STM32F417_gpio_v1_0_Modes.xml` | PB0/PB1 TIM3 AF2, PB10/PB11 TIM2 AF1, PC8/PC9 TIM8 AF3, PB7 TIM4 AF2, PA0 TIM5 AF2, PA8 TIM1 AF1. USART1/2/3/6 AF7/8, UART4/5 AF8, SPI1 AF5, SPI3 AF6, I2C1 AF4 on PB8/PB9, OTG_FS AF10 on PA11/PA12 |
| PCB | pcbnew script on `kicad/F405FC.kicad_pcb` (side, rotation and pad coordinates of U6/U7/U8/U9/U10/SW1/J1-J5, all silk texts) | See §3 and G6B-01/03 |
| BF CLI | `bf_src/cli.c:5321-5334` (dma device names), `:5560-5680` (dma pin / NONE), `:5900-5985` (timer AFn), `resource.c`, `settings.c` (every `set` name and lookup value) | All 34 `set` names exist. All 18 resource owner names exist. CW270FLIP/CW0FLIP (settings.c:187/190), FIRST, SPIFLASH, DSHOT600, CRSF and MSP are valid lookups |
| Timer/DMA | `bf_src/timer_stm32f4xx.c:63-135`, `bf_src/dma_reqmap_mcu.c:375-458`, `inav_src/timer_def_stm32f4xx.h:33-60` | See §2 |
| Gyro axes | ICM-42688-P DS-000347 Fig. 4 (p.19) and Fig. 15 (p.53); BMI270 BST-BMI270-DS000-08 §7.1 (p.134) and §8.2 table (p.144). Pages rendered to PNG and read | See §3 |
| Baro/mag | BMP390 DS Table 52 (pin 5 = SDO/SA0); `bf_src/barometer_bmp388.c:50-52,277`; `bf_src/compass_lis2mdl.c:35,48-49` | 0x76 with chip ID 0x60 accepted; LIS2MDL 0x1E with WHO_AM_I 0x40 |
| Polarity | `sound_beeper.c:85`, `light_led.c:92`, `drv_pinio.c:40-80`, netlist Q1/Q2/U11 | See §2.3 |
| Gyro detection | `bf_src/gyro_init.c:610-655` | See G6B-12 |

## 1. Flashing walkthrough (rev D)

| Item | Evidence | Status |
|---|---|---|
| BOOT0 | U3-60 BOOT0, R16 10k to GND, SW1 pads "2" (BOOT0) / "1" (3V3) at (24.42/28.57, 7.47 / 5.33) | OK |
| BOOT1 | PB2 (U3-28): R17 10k to GND, and R40 → Q1 gate | Circuit OK. **R17 is a top-side part that the guide fits only in Stage C (G6B-02)** |
| NRST | U3-7, C35 100 nF (bottom), TP3 (bottom, label "RST") | OK |
| USB | J1 A6/B6 → USB_DP → U13 3/4 → U3-45 PA12; A7/B7 → USB_DM → U13 1/6 → U3-44 PA11. CC1/CC2 → R34/R35 5.1k → GND. VBUS → D4 → 5V_SYS → U4/U5 | OK (not swapped). **R34/R35 are top-side and are not in the Stage B list (G6B-02)** |
| VBUS sensing | VBUS goes only to D4, R36, C51, U13-5. No MCU pin. `usb_io.c:55-66`: `usbCableIsInserted()` is always false without `USE_USB_DETECT` (only used for debug, `x_tasks.c:136`) | OK (accepted G0-02) |
| DFU on USB only | Guide §3 step 3 (`assembly_and_bringup.md:125-127`): bench off, hold BOOT, plug USB, or BOOT + NRST short | Fixed vs. old M-1 |
| `bl` on USB only | Guide :128-129, `pinmap.md:292` | Fixed vs. old m-2 |
| HSE | Y1 8 MHz + C36/C37 fitted in Stage B; `system_hse_mhz = 8` | OK |
| SWD | TP1 PA13 "DIO", TP2 PA14 "CLK", TP3 NRST "RST", TP4 3V3, TP5 GND, all bottom. Silk labels are 1.4 mm from their own pad | OK after the rev D test-pad move |

## 2. Betaflight config audit (`docs/F405FC_betaflight_config.txt` = `design/betaflight_config.txt`, byte-identical)

### 2.1 Resources: all 40 lines match the netlist

BEEPER B02 = BEEPER (U3-28). MOTOR1-8 = B00/B01/B10/B11/C08/C09/B07/A00 = nets MOTOR1-8 (U3-26/27/29/30/39/40/59/14). J2 pins 4-7 carry
M1-M4; P19-P22 carry M5-M8. LED_STRIP A08 (U3-41 → U12-2). SERIAL TX/RX 1 = A09/A10 (J3-3/4), 2 = A02/A03 (J5-3/4), 3 = C10/C11
(J4-3/4), RX4 = A01 (J2-8 ESC_TLM), 5 = C12/D02 (P15/P16), 6 = C06/C07 (P17/P18). I2C1 B08/B09 (U8, U9, J4-5/6, R25/R26 2.2k).
LED 1/2 = B14/B15 (D11 blue / D12 green, cathode to pin). SPI1 A05/A06/A07 and SPI3 B03/B04/B05 (SDI = MISO, SDO = MOSI, correct).
ADC_BATT C00, ADC_CURR C01, ADC_RSSI C05. PINIO1 C15 (VTX_PWR_EN), PINIO2 C13 (CAM_SEL). FLASH_CS B06. GYRO_CS A04/A15.
GYRO_EXTI C04/C14.

### 2.2 Timers and DMA (re-derived from `dma_reqmap_mcu.c:375-458`)

| Output | Timer (BF table line) | DMA | Conflict |
|---|---|---|---|
| M1 PB0 | TIM3_CH3 AF2 (l.102, 2nd PB0 entry) | DMA1 S7 Ch5 | - |
| M2 PB1 | TIM3_CH4 AF2 | DMA1 S2 Ch5 | - |
| M3 PB10 | TIM2_CH3 AF1 (l.96) | DMA1 S1 Ch3 | - |
| M4 PB11 | TIM2_CH4 AF1 (l.97) | opt 1 = DMA1 S6 Ch3 | - (opt 0 = S7 is M1's) |
| M5 PC8 | TIM8_CH3 AF3 (l.134) | DMA2 S2 Ch0 | - |
| M6 PC9 | TIM8_CH4 AF3 (l.135) | DMA2 S7 Ch7 | - |
| M7 PB7 | TIM4_CH2 AF2 (l.107) | DMA1 S3 Ch2 | - |
| M8 PA0 | TIM5_CH1 AF2 (l.75) | NONE (the only option, DMA1 S2 Ch6, is M2's) | PWM/servo only (documented) |
| LED PA8 | TIM1_CH1 AF1 (l.69) | DMA2 S6 Ch0 | - |
| SPI1 TX/RX | - | DMA2 S3 / S0 Ch3 | - |
| SPI3 TX/RX | - | DMA1 S5 / S0 Ch0 | - |
| ADC1 | - | opt 1 = DMA2 S4 Ch0 | - (opt 0 = DMA2 S0 is SPI1 RX) |

DMA1 S4 and DMA2 S1/S5 are free. No UART DMA is configured, and a generic F405 build has no UART DMA by default (`target.h`).
DMA2 serves only APB2 peripherals (SPI1, ADC1, TIM1, TIM8). The CLI order is valid: `timer` resets the dmaopt (`cli.c:5983`) and
the `dma pin` lines come after the `timer` lines. `dma pin A00 NONE` is accepted (`cli.c:5647-5649`).

### 2.3 Other subsystems

| Subsystem | Evidence | Status |
|---|---|---|
| Gyros | U6 ICM-42688-P: AP_CS=12 ← PA4 (R18 10k pull-up), INT1=4 → PC4 (EXTI4), SDO=1/SCLK=13/SDI=14 on SPI1, pins 2/3/6/7/9/10/11 GND (DS Table 9 OK). U7 BMI270: CSB=12 ← PA15 (R19), INT1=4 → PC14 (EXTI15_10), ASDx/ASCx/INT2/OCSB/OSDO open (DS Table 22 allows this: "do not connect to GND"). Both on 3V3_IMU | OK. EXTI lines 4 and 14 are distinct, with no other EXTI user |
| Baro | U8 BMP390: CSB(6)=3V3 → I2C, SDO(5)=GND → 0x76 (DS Table 52), INT open. BF BMP388 driver: addr 0x76, accepts chip ID 0x60 (`barometer_bmp388.c:50-52,277`) | OK |
| Mag | U9 IIS2MDC: CS(3)=3V3 → I2C, C1(5) = C45 220 nF. BF LIS2MDL driver 0x1E, WHO_AM_I 0x40 (`compass_lis2mdl.c:35,48-49`) | OK. Alignment open (G6B-05) |
| I2C | R25/R26 2.2k to 3V3 → `i2c1_pullup = OFF`, 400 kHz | OK |
| Flash | U10 W25N01GV: /CS(1)=PB6 with R20, DO(2)=PB4, DI(5)=PB5, CLK(6)=PB3, /WP and /HOLD 10k up. `flash_spi_bus = 3`, `blackbox_device = SPIFLASH`, `USE_FLASH_W25N01G` (`common_pre.h:140`, non-cloud) | OK |
| OSD | No OSD chip. UART1 mask 131073 = MSP(1) + VTX_MSP(131072) (`serial.h:36-53`), `osd_displayport_device = MSP` | OK |
| DShot | `dshot_bitbang OFF`, `dshot_burst OFF`, `dshot_bidir ON`; the F4 timer path includes telemetry (`pwm_output_dshot.c:39-142`) | OK |
| PINIO | Q2 NX7002AK: G ← R11 1k ← PC15, R12 100k gate pull-down, D = EN_10V → high = 10 V off. U11 TS5A3159A: IN(6) ← PC13 with R31 100k pull-down, NC(3) = CAM1, NO(1) = CAM2. `drv_pinio.c:52-71`: non-inverted outputs are driven low at init | OK (VTX on and CAM1 through reset and at boot) |
| Beeper | PB2 → R40 100Ω → Q1 gate, R17 10k pull-down, buzzer to 5V with D9 flyback. `beeper_inversion = ON` → high for beep (`sound_beeper.c:85`) | OK |
| LEDs | 3V3 → R27/R28 → anode, cathode → PB14/PB15. `led_inversion = 0` → low = on (`light_led.c:92`) | OK |
| LED strip | PA8 → U12 SN74LV1T125 A(2), OE(1)=GND, Y(4) → R33 330 → P10; VCC = 5V (buck only) | OK. Dead on USB-only power (by design) |
| ADC | PC0 IN10 / PC1 IN11 / PC5 IN15 on ADC1 (`adc_stm32f4xx.c:89-111`). VBAT R14 10k / R15 1k → ×11, `vbat_scale = 110` → 36.3 V full scale (25.2 V reads 2.29 V at the pin) | OK. `ibata_scale` is a placeholder |
| UARTs | CRSF, MSP, NMEA and KISS telemetry are all non-inverted, so no inverter is needed. RX4-only for ESC_SENSOR (1024) | OK. R37 SBUS option: G6B-11 |

## 3. Gyro alignment, re-derived from the rev D PCB

**PCB (pcbnew):** U6 at (15.4, 17.0) and U7 at (19.2, 17.0) are both on **B.Cu, rotation 0** (unchanged by rev D, D-27). Board-top
view, y increasing toward J2: pad 1 at the lower left (14.237, 17.75), pads 1→4 up the left column, 5→7 left to right along the upper row
(y 16.088), 8→11 down the right column, 12→14 right to left along the lower row (y 17.912). U7 uses the same pattern. This is the datasheet
**top view mirrored in y**, which is correct for a part on the bottom side.

**Chip frames (top view, pin 1 at the top left):**
- ICM-42688-P (Fig. 4 + Fig. 15): the iso view has the dot at the (−X, +Y) corner, and X runs along the long (3 mm) edge that carries
  the marking. So **+X points right (pins 8-11), +Y points up (pins 12-14)** and +Z points out of the lid.
- BMI270 (§8.2 table): dot at the top left → X = +1 g, so **+X points up (pins 12-14)**. Dot at the top right → Y = +1 g, so **+Y
  points left (pins 1-4)**. X×Y = out of the lid.

**In board terms (front = J3 edge, y = 0):**

| IMU | chip +X | chip +Y | chip +Z | body (X fwd, Y left, Z up) | BF value | Config |
|---|---|---|---|---|---|---|
| U6 ICM-42688-P | right | back | down | X = −cy, Y = −cx, Z = −cz | CW270FLIP | `gyro_1_sensor_align = CW270FLIP` ✓ |
| U7 BMI270 | back | left | down | X = −cx, Y = +cy, Z = −cz | CW0FLIP | `gyro_2_sensor_align = CW0FLIP` ✓ |

The INAV values match (`inav_target.md:41,47`). Caveats: the BF rotation table (CW270FLIP = (−y, −x, −z), CW0FLIP = (−x, y, −z)) and
the body frame are taken from memory, because `common/sensor_alignment.c` is not on disk. The result is only meaningful if the user
knows which edge is the front, and **the board no longer shows it (G6B-01)**.

## 4. INAV consistency (`docs/F405FC_inav_target.md` = `design/inav_target.md`, identical)

The pins, UARTs, SPI/I2C buses, CS/EXTI, ADC1 on DMA2 S4, VBAT 1100, PINIO1/2, beeper inversion, LED pins, and the per-channel DMA
variants all match the BF config and the netlist. M4 uses dmavar 1 (`D(1,6,3)`). M7 uses `D(1,3,2)`. S8 TIM5_CH1 is servo-only
(its only DMA, `D(1,2,6)`, collides with M2, as documented). The LED is `D(2,6,0)`. The alignments are identical. The INAV file on
disk has no TIMx_UP (burst) entries, so per-channel DMA is the right model. Not compiled (the document says so).

## Findings

### MAJOR

**G6B-01: Rev D has no forward or orientation marking. The config, INAV target and bring-up tilt test depend on a "FRONT" silk mark that no longer exists.**
- Evidence: `docs/F405FC_betaflight_config.txt:155` says "board front = J3 (VTX) edge, **marked "FRONT" on silk**". `inav_target.md:41`
  says "front = J3 edge". The guide (`assembly_and_bringup.md:144-146`) says "tilt the board nose-down and roll right" without
  defining the nose anywhere in §4. The rev D PCB has 34 `gr_text` items and none of them is "FRONT" or an arrow. It has no other
  board-level silk graphics and no visible footprint silk text (pcbnew scan). The mark was dropped in commit `29ee39c`
  (`gen/build_pcb.py:148`, `LABELS["J3"]` "FRONT" → "VTX 10V") as part of the old M-2 fix, and the rev D label "J3 VTX 10V" is on
  B.Silk (18.0, 2.85). The only remaining hint is the prose "J3 (front; …)" in guide §5 (:161).
- Impact: the alignment values are correct only with J3 forward. A builder who mounts the board by the usual cues (USB to the side,
  ESC plug to the rear) has a 1-in-4 chance of a correct yaw. A 90° yaw error passes a casual Setup-tab glance and the "nose-down /
  roll right" test only if the tester knows where the nose is. Wrong yaw alignment means an immediate flip or flyaway on the first arm.
- Fix: add a "FRONT ▲" arrow (or "↑ FRONT") on F.SilkS at the J3 edge (there is room near (9-12, 4) or (24-27, 9); check the
  silk-over-copper DRC) and a second one on B.SilkS. Correct config :155 and the INAV comment. In guide §4, add "nose = J3 (VTX
  connector) edge, arrow on the silk". Optionally document `board_align_yaw` for other mountings.

**G6B-02: The Stage B part list for the first DFU flash leaves out R17 (BOOT1 strap) and R34/R35 (USB-C CC Rd). Stage A step 10 needs J1 before it is fitted.**
- Evidence: Stage B (`assembly_and_bringup.md:114-116`) fits "U3, Y1 + C36/C37, C25-C29, C31-C34, C53, R14/R15, R16, FB1, U13, J1, SW1".
  On the rev D PCB, **R17 (PB2/BOOT1 10k pull-down), R34/R35 (CC1/CC2 5.1k to GND), R36 and C51 are top-side parts** (pcbnew side scan).
  They are therefore fitted only by "the remaining top passives" in Stage C (:133-134), which comes after the DFU flash (:125-127).
  - Without R17, PB2 is a floating input at reset (Q1/R40 are also Stage C). With BOOT0 = 1, the F405 boots the system bootloader
    only if BOOT1 = 0, and BOOT1 = 1 selects SRAM. DFU entry then depends on a floating pin (RM0090 boot table, from memory, not on
    disk).
  - Without R34/R35, a USB-C source (a C-to-C cable from a laptop or charger) never turns on VBUS, because a sink must present Rd.
    The board stays dead and "STM32 BOOTLOADER" never enumerates. Only an A-to-C cable works.
  - Stage A step 2.1.10 (:101-102, "plug USB-C … 5V_SYS ≈ 4.6-4.7 V via D4") runs before J1/U13 are fitted in Stage B. As written
    it cannot be done.
- Fix: add R17, R34, R35, R36 and C51 to the Stage B list. Move step 2.1.10 to Stage B (after J1, before DFU). Add a pre-DFU check:
  "PB2 (R17) to GND ≈ 10k; CC1/CC2 to GND ≈ 5.1k".

### MINOR

**G6B-03: Silk labels are stale, misplaced or missing after the rev D placement freeze.**
- Evidence (pcbnew text scan vs. footprint positions): "BOOT" at (20.59, 10.33) is 7.1 mm from SW1 (26.5, 6.4), outside its bbox
  (23.6-29.4 × 4.5-8.3). "USB" at (24.44, 22.3) is about 3 mm left of and below J1's bbox (27.5-36.5 × 9.2-19.8). Both were next to
  their parts at `cce9f56` ((26.5, 8.78) and (26.64, 14.5)). **P6 "C2" (camera 2 input) and J5 "RX" have no label at all.** "C1" and
  "VID" do. `gen/build_pcb.py:159` skips re-labelling whenever labels already exist, so moved parts keep their old labels.
- Impact: the Stage C PINIO2 check (:154, "confirm … the camera source change") needs the CAM2 pad identified. A "BOOT" label next
  to U8/R16 invites probing the wrong part.
- Fix: regenerate the labels (`--fresh`) on the frozen placement. Add a check that every LABELS ref has a label within N mm of its
  own part.

**G6B-04: The guide's sensor-detection expectations do not match BF output, and AUTO detection is still used (old m-7, open; now verifiable).**
- Evidence: guide :153 "`status` lists BMP390 … magnetometer (IIS2MDC)". BF reports driver names: the lookup tables are
  `… "BMP388" …` (`settings.c:154`) and `… "LIS2MDL" …` (`settings.c:160`). Config :12 still says the enum names "were not verified".
  They are on disk now.
- Fix: set `baro_hardware = BMP388` and `mag_hardware = LIS2MDL` (deterministic, and avoids probing HMC5883 at the shared 0x1E
  address). In the guide, write "`status`: BARO=BMP388, MAG=LIS2MDL". Update config :12.

**G6B-05: No magnetometer alignment (old m-3, open).** `betaflight_config.txt:164-167` sets no `align_mag`. U9 is F.Cu, rotation 0,
pad 1 at (8.787, 6.95) top left. The IIS2MDC datasheet is still not in `datasheets/`. The guide (:150-151) now tells the user to set it
on the bench, which is a mitigation. Fix: add `IIS2MDC.pdf`, derive `align_mag` from its axis figure, and put it in the BF config and
the INAV notes.

**G6B-06: The BF bring-up section skips most functional checks, and the firmware source is still vague (old m-6, partly open).**
- Evidence: §4 (:141-154) checks gyros, resources, alignment, cold boot, mag, baro and PINIO. It does **not** check: blackbox
  (`flash_info` / erase + log), motors (Motors tab without props: DShot600 with bidir RPM shows, M5-M7 if used, M8 servo only),
  ESC telemetry on UART4, OSD over MSP on the HD VTX, LED strip, beeper (needs battery: buzzer + is on the 5 V buck), VBAT/current
  calibration (`vbat_scale`, `ibata_scale` against a meter), or assigning USER1/USER2 in the Modes tab (needed before "toggle with
  the mode switch" at :154). Step :126 says only "Flash Betaflight (STM32F405 target)" and "paste, save". The `defaults nosave`
  prerequisite and the cloud-build driver list are only in the config header (:9-11).
- Fix: add these steps, with pass criteria, to §4. In §3 step 3, name the exact firmware (BF 4.5.x, generic STM32F405, or a cloud
  build with ICM42688P, BMI270, BMP388, LIS2MDL, W25N01G, LED_STRIP, PINIO, DSHOT telemetry) and the `defaults nosave` → paste →
  `save` sequence.

**G6B-07: The pre-power BOOT0 check has a wrong pass criterion.** Guide :123 says "measure BOOT0 to 3V3: open circuit unless the button is
pressed". BOOT0 has R16 10k to GND, and 3V3 has the LDO, the MCU and decoupling to GND, so the DMM reads a finite, drifting value,
not "open". Fix: "Across SW1 (pad 1 = 3V3 to pad 2 = BOOT0): open when released, < 1 Ω when pressed. BOOT0 (R16) to GND ≈ 10 kΩ."

**G6B-08: Guide numbering and reference errors.** §2.1 steps go 1-8 and then 10 (:93, :101). :62 says "A2 (step 2.1.9)", but A2 is step 8.
:115 lists C53 as "MCU decoupling", but C53 is the 10 nF RSSI_ADC filter (netlist: C53 on RSSI_ADC). :139 says to dispense paste on
Y1, which was fitted in Stage B. Fix: renumber and correct.

### INFO

- **G6B-09:** The config (:3), `inav_target.md:1` and `pinmap.md:3` still say "rev C". The pin map did not change in rev D (netlist
  identical to pinmap §9), but add "valid for rev D" so a builder does not doubt it.
- **G6B-10:** All three status LEDs (D10-D12) are on the **bottom** side ((3.17, 7.14), (12.6, 1.45), (9.44, 2.8)). Once the board
  is in a stack, they are hidden. Mention this in the guide.
- **G6B-11:** The R37 option (HD_R2 → UART5_RX, no inverter) only works with a non-inverted SBUS source. The F405 USARTs cannot
  invert, and the usual air-unit SBUS is inverted. This is documented at :136 as "non-inverted SBUS option only". Keep CRSF on UART2.
- **G6B-12:** Shared SPI1 with both IMUs starting in I2C mode (old m-4): in BF, `gyro_init.c:610-631` scans both gyros on every boot
  when the cached mask holds both. The BMI270 therefore gets its SPI-switching CS edge each boot, and the guide now has the
  cold-boot / `defaults` re-detect step (:147-149). That part is mitigated. Under INAV only the first IMU found (the ICM) is accessed, so
  the BMI270 stays in I2C mode and sees all ICM traffic. A false address match (first byte 0xD0-0xD3) is unlikely with ICM register
  reads, but this has not been bench-tested.
- **G6B-13:** U8 (BMP390) moved in rev D to F.Cu (16.0, 8.9), about 3 mm from the MCU body and unshielded. Add "cover the baro
  with open-cell foam (prop wash / light)" to §5.
- **G6B-14:** HD OSD canvas: consider `set vcd_video_system = HD` (`settings.c:1570`) for O3/Walksnail (old INFO-4, still open).

## Re-check of the earlier Gate 6 findings (`review/gate-6-betaflight-redteam.md`)

| Old | Topic | Rev D status | Evidence |
|---|---|---|---|
| M-1 | DFU step with bench powered | **Fixed** | Guide :125-127 (bench off, hold BOOT, plug USB, or BOOT + NRST) |
| M-2 | J3 10 V silk / GPS warnings | **Fixed, but caused G6B-01** | B.Silk "J3 VTX 10V" (18.0, 2.85); F.Silk "GPS 5V" (3.1, 5.42); guide :161-163. "FRONT" was removed |
| m-1 | Stale BAT54S text | **Fixed** | `pinmap.md:76,287`, `inav_target.md:115` (the :13/:26 rows are historical change-log entries) |
| m-2 | `bl` needs USB-only | **Fixed** | `pinmap.md:292`, guide :128-129 |
| m-3 | Mag alignment | **Open** → G6B-05 | Bench mitigation in guide :150-151 |
| m-4 | Shared SPI / cached gyro mask | **Mitigated** → G6B-12 | Guide :147-149 |
| m-5 | Bottom-side LGA order | **Fixed** | Guide :43-63 (all bottom parts in one hot-plate pass A1) |
| m-6 | config.h appendix / firmware source | **Partly fixed** → G6B-06 | The "provisional" text is now a `//` comment (:302-303). Firmware source in the guide is still vague |
| m-7 | AUTO baro/mag, names | **Open** → G6B-04 | Names are now verifiable in `settings.c:154,160` |
| INFO-1..7 | | Unchanged (INFO-4 → G6B-14) | Not re-derived beyond the netlist (D4/R36/C51 path unchanged) |

## Checked and OK (rev D)

- All 64 U3 pins vs. the ST pin data and the netlist. All 40 `resource` lines. All 9 `timer` AFs vs. the ST AF table and the BF timer table.
- All 14 `dma` lines vs. `dma_reqmap_mcu.c`. No stream is used twice, DMA1 S4 and DMA2 S1/S5 are free, and DMA2 carries only APB2 peripherals.
- CLI syntax for `timer`, `dma`, `dma pin … NONE`, every `set` name and every lookup value used. Serial function masks.
- EXTI4 / EXTI15_10 for the gyro INTs. CS pull-ups R18/R19/R20. JTAG pins PA15/PB3/PB4 reused (BF reconfigures them; PA15 resets with a pull-up).
- BMP390 at 0x76 (SDO = GND, CSB = 3V3) with chip ID 0x60 accepted. IIS2MDC in I2C mode (CS = 3V3) at 0x1E. I2C pull-ups 2.2k.
- W25N01GV pinout and SPI3. LED strip buffer pinout and OE. Beeper FET, pull-down placement and inversion. LED sink polarity.
- PINIO1/2 hardware polarity and reset state vs. `drv_pinio.c` (VTX on, CAM1 through reset, DFU and boot).
- VBAT scale 110 against the 10k/1k divider. ADC channels.
- ICM-42688-P / BMI270 unused-pin handling vs. DS Table 9 / Table 22.
- **Gyro alignment CW270FLIP (U6) / CW0FLIP (U7) re-derived from the rev D footprints (B.Cu, rotation 0) and the datasheet figures.**
- USB D+/D− not swapped. CC Rd values. VBUS not sensed (accepted). BOOT0 R16 / SW1 nets. Stage A part sides (all A1 parts are on B.Cu; D1/C1/R41/D4 are on F.Cu).
- INAV target vs. BF config, netlist and the INAV F4 DMA table.

## Not verified

- No physical board: everything here is on paper.
- BF `common/sensor_alignment.c` (rotation matrices), the body-frame convention, `bus_spi_stdperiph.c` pin tables, `pg/motor.c`
  macro names, the BMI270 and ICM-426xx drivers (I2C-disable behaviour), and the USER1/USER2 permanent box IDs 40/41: none of these
  are on disk, so they are from memory.
- AN2606 (ROM DFU behaviour, HSE detection, USART polling) and RM0090 (the BOOT1 = 1 → SRAM table) are not on disk.
- IIS2MDC datasheet (axes, pinout), W25N01GV datasheet, C&K PTS810 contact pairing (KiCad pad numbering assumed). If the pairing
  were wrong, BOOT0 would be stuck high.
- DJI/Walksnail J3 pin order, the GPS J4 pin order and the ESC J2 pin order against real harnesses.
- The INAV target was not compiled. INAV driver availability (ICM42605 handling the 42688-P, BMP390 ID, any LIS2MDL driver) and the INAV IMU detection order are unverified.
- Whether the BF 4.5 Configurator offers a generic STM32F405 build, and which drivers a cloud build includes by default.
- Footprint pad-to-die mapping of the custom BMI270/BMP390 footprints (taken from Gate 2). The alignment result depends on it.
