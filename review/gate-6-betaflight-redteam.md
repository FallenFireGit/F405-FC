# Gate 6 red team: Betaflight bring-up walkthrough (paper)

Reviewer: fresh, independent, adversarial agent. Date 2026-10-13. Scope: flash, pin/resource map, timers/DMA, gyro alignment,
USB-only power, INAV consistency. This is a review only: no file under design/, gen/, kicad/, lib/, bom/, fab/ or docs/ was changed.

## Verdict: **FAIL** (0 BLOCKER, 2 MAJOR, 7 MINOR, 7 INFO)

I found nothing in the hardware or in the Betaflight resource/timer/DMA map that would stop the board from flashing or flying.
Every `resource` line matches the netlist and the PCB pads. The DMA plan has no conflicts. **Both provisional gyro alignments
come out correct on paper.** The gate fails because of two MAJOR findings in the bring-up and user documentation. One makes the
first DFU flash fail as written. The other is a missing mitigation against hardware damage that `design/decisions.md` (D-15) says
is in place. Both can be fixed in the docs and silkscreen without any schematic change.

## Method (what was actually run)

| Check | How | Result |
|---|---|---|
| Schematic netlist | `kc 'kicad-cli sch export netlist -o /tmp/g6n.net kicad/F405FC.kicad_sch'`, parsed U3 pins 1-64 | All 64 pins match `design/pinmap.md` §9 and `circuit.py:287-298` |
| PCB pad nets | `kc 'python3 gen/padpos.py U3 …'` | U3 pads 1-64 carry the same nets as the schematic |
| Pin numbers | `datasheets/st_open_pin_data/F405RGTx.xml` positions 1-64 | Match the symbol (e.g. PA11=44, PA12=45, BOOT0=60) |
| AF numbers | Script over `GPIO-STM32F417_gpio_v1_0_Modes.xml` | PB0/PB1 AF2 TIM3, PB10/PB11 AF1 TIM2, PC8/PC9 AF3 TIM8, PA8 AF1 TIM1, PB7 AF2 TIM4, PA0 AF2 TIM5_CH1, all USART/SPI/I2C/OTG AFs as listed in pinmap §2 |
| Timer index / DMA options | `bf_src/timer_stm32f4xx.c:63-135`, `bf_src/dma_reqmap_mcu.c:380-470` | The TIMER_PIN_MAP occurrence indexes and every `dma` option in the config resolve to the streams in pinmap §3. No stream is used twice |
| CLI names | Every `set` name grepped in `bf_src/settings.c` / `parameter_names.h`; `dma` names in `cli.c:5322-5327`; resource names in `resource.c` | All exist. `gyro_to_use` / `gyro_2_*` need `USE_MULTI_GYRO`, which is on (`common_pre.h:364`) |
| Polarity | `sound_beeper.c` (systemBeep), `light_led.c:91-92`, `drv_pinio.c:40-80` | Beeper inverted = high for beep. LEDs low = on. PINIO idles low (VTX on), USER1 → high (VTX off) |
| Serial masks | `bf_src/serial.h:36-53` | 131073 = MSP+VTX_MSP, 64 = RX_SERIAL, 2 = GPS, 1024 = ESC_SENSOR |
| Gyro alignment | ICM-42688-P DS-000347 p.19 (Fig. 4) and p.53 (Fig. 15); BMI270 DS000-08 p.134 (pin-out) and p.144 (§8.2 table); U6/U7 pad coordinates from `padpos.py` | See §3: both configured values are correct |
| USB-only power | `circuit.py` nets 5V_SYS / 5V / VBUS / 3V3 / 3V3_IMU (netlist dump) | See §4 |

## 1. Flashing walkthrough

| Item | Evidence | Status |
|---|---|---|
| BOOT0 | U3-60 = BOOT0. R16 10k to GND. SW1 pin 2 = BOOT0, pin 1 = 3V3 (netlist) | OK. BOOT1 = PB2 with R17 10k pulldown → system memory when BOOT0 = 1 |
| NRST | U3-7, C35 100 nF, TP3. No external pull-up (the internal one is enough) | OK |
| USB data | J1 A6/B6 (D+) → USB_DP → U13 pins 3/4 → U3-45 PA12. J1 A7/B7 (D−) → USB_DM → U13 pins 1/6 → U3-44 PA11 | OK, not swapped. Internal D+ pull-up, so no 1.5k is needed |
| VBUS sensing | No detect pin (G0-02). `usb_io.c:55-61`: `usbCableIsInserted()` returns false with no pin. VCP is unaffected | OK (accepted) |
| 5 V back-feed | VBUS → D4 (A = VBUS, K = 5V_SYS); 5V → D5 → 5V_SYS. USB cannot reach the buck 5V or VBAT. The battery cannot reach VBUS except as D4 leakage (INFO-5) | OK |
| HSE | Y1 8 MHz, `set system_hse_mhz = 8`, BF generic F405 default 8 MHz | OK. The ROM DFU detects HSE automatically (AN2606, from memory: not on disk, G0-13) |
| SWD | TP1 SWDIO (PA13), TP2 SWCLK (PA14), TP3 NRST, TP4 3V3, TP5 GND. PA13/PA14 are not reused | OK. No SWO (PB3 = SPI3_SCK) |
| ROM-bootloader ports | USART1 RX PA10 = J3 VTX TX. USART3 PC11 = GPS. PB11 (M4) is the other USART3 RX option. CAN2 RX PB5 = SPI3_MOSI (input to the flash) | On USB-only power the VTX, GPS and ESC are unpowered, so the lines are quiet. With a battery connected they are not: see M-1 and m-2 |

## 2. Betaflight config audit (`design/betaflight_config.txt`)

### 2.1 Resources (every line checked against the netlist)

BEEPER B02 = BEEPER. MOTOR 1-8 = B00, B01, B10, B11, C08, C09, B07, A00 = MOTOR1-8. LED_STRIP A08. SERIAL TX/RX 1/2/3/5/6 and RX4 A01 =
UART nets. I2C1 B08/B09. LED 1/2 = B14/B15 (blue/green, sink). SPI1 A05/A06/A07, SPI3 B03/B04/B05 (SDI = MISO, SDO = MOSI, correct).
ADC_BATT C00, ADC_CURR C01, ADC_RSSI C05. PINIO 1 C15 (VTX_PWR_EN), PINIO 2 C13 (CAM_SEL). FLASH_CS B06. GYRO_CS 1/2 = A04/A15.
GYRO_EXTI 1/2 = C04/C14. **All 40 lines match** (netlist dump, U3 pins 2-62).

### 2.2 Timers and DMA

| Output | Timer | DMA (BF option) | Conflict? |
|---|---|---|---|
| M1 PB0 | TIM3_CH3 AF2 | DMA1 S7 Ch5 (only option) | - |
| M2 PB1 | TIM3_CH4 AF2 | DMA1 S2 Ch5 (only option) | - |
| M3 PB10 | TIM2_CH3 AF1 | DMA1 S1 Ch3 | - |
| M4 PB11 | TIM2_CH4 AF1 | opt 1 = DMA1 S6 Ch3 (opt 0 = S7 would collide with M1) | - |
| M5 PC8 | TIM8_CH3 AF3 | DMA2 S2 Ch0 | - |
| M6 PC9 | TIM8_CH4 AF3 | DMA2 S7 Ch7 | - |
| M7 PB7 | TIM4_CH2 AF2 | DMA1 S3 Ch2 | - (SPI2 unused) |
| M8 PA0 | TIM5_CH1 AF2 | NONE (only option, DMA1 S2 Ch6, is M2's) | PWM/servo only (documented) |
| LED PA8 | TIM1_CH1 AF1 | DMA2 S6 Ch0 | - |
| SPI1 TX/RX | - | DMA2 S3 / S0 Ch3 | - |
| SPI3 TX/RX | - | DMA1 S5 / S0 Ch0 | - |
| ADC1 | - | opt 1 = DMA2 S4 Ch0 | - |

`dshot_bitbang = OFF` and `dshot_burst = OFF` are right for one DMA stream per motor. Timer-DMA bidirectional DShot is compiled for F4
(`pwm_output_dshot.c:39-112`, under `USE_DSHOT_TELEMETRY`). DMA2 serves only APB2 peripherals (SPI1, ADC1, TIM1, TIM8), so the F40x DMA2
concurrent AHB/APB2 erratum does not apply. The LED strip is alone on TIM1 and DMA2 S6, with no motor conflict.

### 2.3 Other subsystems

| Subsystem | Finding |
|---|---|
| ADC | PC0 IN10 / PC1 IN11 / PC5 IN15 are ADC1-capable (`adc_stm32f4xx.c:89-110`), with 480-cycle sampling. VBAT 10k/1k (R14/R15) gives ×11, and `vbat_scale = 110` with the default `vbat_divider = 10` gives 3.3 V × 11 = 36.3 V full scale. Correct. CURR and RSSI have 10k series + 10 nF. `ibata_scale` is a placeholder |
| UARTs | No inversion needed (CRSF, MSP, NMEA, KISS/BLHeli telemetry are all non-inverted). UART4 RX-only is accepted by BF |
| I2C | BMP390 CSB = 3V3, SDO = GND → 0x76 (BMP388 driver default). IIS2MDC CS pin 3 = 3V3 → I2C 0x1E (LIS2MDL driver). R25/R26 2.2k to 3V3, and `i2c1_pullup = OFF` is consistent. 400 kHz is OK for both parts |
| SPI gyros | Both on SPI1 with CS pull-ups R18/R19 and EXTI lines 4 and 14 (distinct). Shared-bus caveat: m-4 |
| Flash | W25N01GV on SPI3, CS PB6 with R20 pull-up, /WP and /HOLD pulled up. BF supports it (`USE_FLASH_W25N01G`, `common_pre.h:140`). `flash_spi_bus = 3`, `blackbox_device = SPIFLASH` |
| OSD | No analog OSD chip (D-01). `feature OSD` + `osd_displayport_device = MSP` + UART1 MSP|VTX_MSP is the supported HD combination (`x_serial.c:204-207, 368`) |
| PINIO | `pinio_config = 1` (output, not inverted); `drv_pinio.c` drives it LOW at init → VTX on, CAM1. `pinio_box 40,41` = USER1/USER2 |
| Beeper / LEDs | Polarity correct (see Method). Buzzer + is on the buck 5V, so it is silent on USB (INFO-3) |

## 3. Gyro alignment (both provisional values derived and found correct)

**Chip frames (top view, pin 1 at top-left, pins 1-4 down the left side, 12-14 along the top):**
- ICM-42688-P (DS-000347 Fig. 4 p.19 + Fig. 15 p.53). The "ICM-42688-P" marking and +X run along the same edge, and +Y runs
  along the pin-1 → back edge. So **+X points toward pins 8-11 (right) and +Y toward pins 12-14 (top)**, with +Z out of the lid.
- BMI270 (DS000-08 §8.2 p.144 table). Dot top-left → X = +1 g, so **+X points toward pins 12-14 (top)**. Dot top-right → Y = +1 g,
  so **+Y points toward pins 1-4 (left)**. +Z points out of the lid. The pin-out on p.134 uses the same pin-1 position and ring order as the ICM.

**Placement (`padpos.py`, board coordinates seen from the top, y increasing toward the ESC edge):**
U6 and U7 are on side B at rotation 0. Pad 1 is at the lower-left, pads 2-4 go up the left column, 5-7 run left to right along
the upper row (y 16.09), 8-11 go down the right column and 12-14 run right to left along the lower row (y 17.91). That is the
datasheet bottom view rotated 180°, which is the correct mirror for a bottom-side part. The silkscreen "FRONT" at (18, 3.1) is
J3, so forward = −y.

**Result in board terms (F = forward, L = left, U = up):**

| IMU | chip +X | chip +Y | chip +Z | body (X fwd, Y left, Z up) from chip | BF alignment | Config |
|---|---|---|---|---|---|---|
| U6 ICM-42688-P | right | back | down | X = −y, Y = −x, Z = −z | **CW270FLIP** | `gyro_1_sensor_align = CW270FLIP` ✓ |
| U7 BMI270 | back | left | down | X = −x, Y = +y, Z = −z | **CW0FLIP** | `gyro_2_sensor_align = CW0FLIP` ✓ |

Cross-check: BMI-X = ICM-Y and BMI-Y = −ICM-X. Both derivations give the same body frame. The INAV sketch uses the same
values (same Cleanflight convention). Assumptions: the BF body frame is X forward, Y left, Z up. Level gives acc Z = +1 g, and
positive pitch is nose-down, which matches the rcCommand sign. The BF alignment mapping is CW270FLIP: (x,y,z) → (−y,−x,−z) and
CW0FLIP: (−x,y,−z). That table comes from memory of `common/sensor_alignment.c`, which is **not on disk**. Keep the bench tilt test
in `docs/assembly_and_bringup.md` §4. The magnetometer has no alignment set (m-3).

## 4. USB-only power (battery disconnected)

VBUS → D4 → 5V_SYS (≈ 4.65 V) → U4 LP38692 (3V3) + U5 LP5907 (3V3_IMU), both EN tied to 5V_SYS, and J5 pin 1 (ELRS).

| Works on USB | Dead on USB (5V/10V are buck-only) |
|---|---|
| MCU, USB VCP/DFU, both IMUs (3V3_IMU), BMP390, IIS2MDC, W25N01GV (3V3), status/power LEDs, ELRS RX (5V_SYS), camera-switch IC (3V3) | GPS (J4 pin 1 = 5V), LED strip and buffer U12 (VCC = 5V), buzzer, camera power pads P8, VTX (10V/VTX_PWR), ESC; VBAT reads 0 V |

Back-power paths checked: D5 blocks 5V_SYS → 5V, and D4 blocks 5V_SYS → VBUS (apart from leakage, INFO-5). U12 SN74LV1T125 inputs are
partial-power-down tolerant. Live 3V3 signals do reach unpowered peripherals: the I2C pull-ups and UART3_TX into a GPS (D-15),
UART1_TX into the VTX, and the DShot lines into the ESC. These currents are small and harmless to the FC, but a GPS-mag can hold
down I2C1 (see M-2).

## 5. INAV (`design/inav_target.md`)

The pins, the DMA variants (PB11 dmavar 1, PB7 S3, PA0 servo-only, PA8 S6), ADC1 on DMA2 S4, PINIO1/2, the UART map, the flash CS
and the gyro alignments all match the BF config and the netlist. `VBAT_SCALE_DEFAULT 1100` fits the 10k/1k divider. Only a stale
comment was found (m-1). As the document says, it has not been compiled.

## Findings

### MAJOR

**M-1: The first-flash DFU step in the bring-up guide fails as written, and it contradicts the design's own "DFU on USB power only" rule.**
- Evidence: `docs/assembly_and_bringup.md:84-85`. Step 2 powers the board from the bench at 8.4 V. Step 3 then says "DFU: hold BOOT,
  plug USB". BOOT0 is sampled only at a reset (power-on or NRST). With 3V3 already up from the bench, plugging USB is not a reset,
  so the blank MCU stays where it is. A virgin F405 has no empty-flash check, so it does not fall into the bootloader by itself
  (AN2606 behaviour, from memory: not on disk). `design/pinmap.md:292` (R-08) requires ROM DFU on **USB power only**, because with a
  battery the VTX (on by default, D-04) drives PA10 = USART1_RX, a bootloader port. The guide never says this.
- Fix: rewrite step 3 as "Switch the bench supply **off**, hold BOOT, plug USB (USB-only power) → 0483:DF11". Alternatively, hold
  BOOT and short TP3 (NRST) to TP5. Add the R-08 rule to the guide for every later flash: no battery, or at least no VTX/GPS
  connected, during any DFU (see m-2 for software DFU).

**M-2: The D-15 mitigations against GPS/HD-VTX mix-ups and GPS back-powering are not on the board or in the guide.**
- Evidence: `design/decisions.md` D-15 says J3/J4 "get clear silkscreen ("VTX 10V" / "GPS 5V"); the user guide warns that a GPS
  plugged into J3 receives 10 V" and "connect the battery before USB, or reboot after connecting the battery". In
  `gen/build_pcb.py:144`, `LABELS["J3"] = "FRONT"`. The PCB has `gr_text "FRONT"` at (118, 103.1) and no "VTX 10V" text (full gr_text
  list grepped from `kicad/F405FC.kicad_pcb`). `docs/assembly_and_bringup.md` contains no J3/J4/GPS warning (grep for J3, J4,
  GPS, "before USB" and reboot finds only lines 68 and 87). J3 and J4 are both SM06B. Plugging a GPS into J3 puts 10 V on a 5 V GPS
  (VBAT if U2's high-side FET fails, D-04). A bench session that starts on USB with a GPS-mag attached can come up without
  baro/mag (G1M-02), and a bring-up technician would chase a phantom sensor fault.
- Fix: put "VTX 10V" (or "10V VTX") next to J3 and keep "FRONT" as a separate arrow/text, for example on the other side of the
  connector or on B.SilkS. Add both D-15 warnings to `docs/assembly_and_bringup.md` §4/§5.

### MINOR

**m-1: Stale "BAT54S clamp mandatory" text contradicts D-23.** Places: `design/pinmap.md:13`, `:76`, `:92`, `:287` ("Mandatory");
the `inav_target.md` comment `ADC_CHANNEL_2_PIN PC1 // CURR (10k + 10 nF + BAT54S)`. D7/D8 were removed (`circuit.py:452-456`; netlist
CURR_ADC = R38, C52, U3-9 only). Fix: update the text to "10k + 10 nF, no clamp (D-23)".

**m-2: The R-08 claim "BF's `bl` command (software DFU) is unaffected" is wrong.** Evidence: `design/pinmap.md:292`. BF's
`bl` / Configurator "reboot to bootloader" resets and jumps into the same ROM system bootloader. That bootloader polls
USART1/USART3/CAN2 just as it does with BOOT0. With a battery connected, the VTX (UART1, on by default) and the GPS (UART3 PC10/PC11, on
the battery 5V) are powered and talking. An MSP poll or NMEA stream can catch the bootloader on a USART, and USB DFU then never
enumerates. Fix: in pinmap §7 and the guide, say "for any firmware flash (BOOT button or Configurator), unplug the battery".

**m-3: No magnetometer alignment.** Evidence: `betaflight_config.txt:160-163` sets bus and hardware but no `align_mag`. U9 is on
top at rotation 0 (`padpos.py`: T (9.55, 7.70) rot 0). The IIS2MDC axis drawing is not on disk (no `iis2mdc.pdf`), so I could not
derive it. Fix: derive `align_mag` from the IIS2MDC datasheet (Fig. "pin connections / axes") and add it, or add a bench step
(rotate the board, check the heading in the Setup tab). Mirror it in the INAV notes.

**m-4: The shared SPI1 bus and BF's cached gyro-detection mask can leave gyro 2 permanently undetected after one bad cold boot.**
Evidence: both IMUs start in I2C mode while their CS is high. The ICM-42688-P datasheet Table 9 says "AP_CS … connect to VDDIO if
using I2C", and the BMI270 switches to SPI only on a CS rising edge. Both therefore see the other part's SCK/MOSI traffic as I2C
until they are switched. pinmap §7 already notes this. Separately, `gyro_init.c` (around `gyrosToScan` / `gyrosDetected`) stores
the detected mask on the first successful detection and scans only those gyros afterwards. Fix: in the guide, (a) power-cycle 10-20
times and check that `status` lists both gyros every time; (b) if a gyro was refitted or was missing on the first boot, run
`defaults nosave` and re-paste the config so detection runs again.

**m-5: The assembly order contradicts itself for the bottom-side LGAs.** Evidence: `docs/assembly_and_bringup.md:42-44` says
"Keep hot air away from the bottom side once it is populated". But U10 (Stage B, :80) and U6/U7 (Stage C, :91, "hot air") are
bottom-side parts (`padpos.py`: U6 B, U7 B, U10 B), fitted after the bottom-side bucks, inductors and 1210s. Fix: reflow U6/U7/U10
with the Stage A bottom-side hot-plate pass, and then test them later. Otherwise the guide has to describe a shielded local hot-air
procedure for the IMUs.

**m-6: The config.h appendix does not compile as written, and the firmware source is vague.** Evidence:
`betaflight_config.txt:302-303` ends `#define GYRO_1_ALIGN CW270_DEG_FLIP   (provisional)`, which expands with the trailing
text. `DEFAULT_DSHOT_BURST` / `DEFAULT_DSHOT_TELEMETRY` could not be found in the BF excerpts on disk (other names may apply,
not verified). The guide says only "Flash Betaflight (STM32F405 target)". A 4.5 Configurator cloud build sets `CLOUD_BUILD`,
and then the driver block in `common_pre.h:72-169` (ICM42688P, BMI270, BMP388, W25N01G) is **not** auto-included. Fix: state
the exact source (the generic `STM32F405` baseline hex from the BF release assets, or a local `make STM32F405`, both built without
`CLOUD_BUILD`). Move the "(provisional)" notes to separate comment lines and check the macro names against the 4.5 `pg/motor.c`.

**m-7: Stage C sensor checks can be made deterministic.** With `baro_hardware = AUTO` / `mag_hardware = AUTO`, detection probes
other drivers at 0x76/0x1E first, and an external GPS-mag on the same bus can confuse it. Fix: set `baro_hardware = BMP388` and
`mag_hardware = LIS2MDL` (names per the BF lookup tables; not verified on disk). In the guide, note that `status` reports the BMP390
as "BMP388".

### INFO

- **INFO-1:** Both gyro alignments are verified on paper (§3). The bench tilt test still has to confirm them, because the BF
  alignment table was used from memory.
- **INFO-2:** M8 (PA0) cannot run DShot. A DShot octo mixer will fail motor init. This is documented (pinmap §3.3, §5).
- **INFO-3:** On USB only, the buzzer, LED strip, GPS, cameras and VTX are dead (by design, D-02). The beeper cannot be
  bench-tested without a battery.
- **INFO-4:** HD OSD canvas. For DJI O3 / Walksnail, consider `set vcd_video_system = HD` (`settings.c:1570`), or rely on the VTX's
  canvas negotiation.
- **INFO-5:** `design/power.md:330` says the 100k VBUS bleeder stops D4 leakage from floating VBUS. PMEG4030ER IR is 5 µA typ at
  10 V / 25 °C (`PMEG4030ER.pdf` p.5, and higher when hot), so a hot board with a battery and no cable can still float VBUS to
  several volts. This is harmless because nothing senses VBUS. A USB-C cable to an unpowered host gets µA-level back-feed.
- **INFO-6:** On USB the 5V_SYS load (MCU + IMUs + flash + an ELRS RX in WiFi mode) approaches 0.45 A against the USB 500 mA
  budget (`power.md` §9). Attach inrush over the limit is accepted (D-14). A port that trips will make DFU look flaky. Use a
  powered hub if that happens.
- **INFO-7:** BF `usbCableIsInserted()` is always false without a detect pin (`usb_io.c:55-61`). Features gated on it (for
  example the MSC auto-boot path) behave as "no cable". Accepted in G0-02.

## Not verified

- No physical board. Everything above is a paper walkthrough.
- BF `common/sensor_alignment.c` (alignment matrices), `drivers/accgyro/accgyro_spi_icm426xx.c` (whether it disables the I2C
  interface), `bmi270.c`, `flash_w25n01g.c`, `barometer.c` detection order, `pg/motor.c` macro names and the F4 SPI pin table
  (`bus_spi_stdperiph.c`) are not on disk. Behaviour attributed to them is from memory.
- AN2606 (bootloader ports, DFU HSE detection, empty-flash behaviour) and RM0090 are not on disk. The DMA tables were checked only
  against the BF/INAV/ArduPilot encodings.
- IIS2MDC datasheet (axis orientation, pinout): not on disk. W25N01GV datasheet: not on disk.
- PTS810 contact pairing (G2F-07). If the KiCad pad pairing were wrong, BOOT0 would be tied high permanently and BF would never
  boot. The guide's pre-power continuity check (§3 step 1) is the only safeguard.
- Whether the BF 4.5 Configurator offers a generic STM32F405 build, and with which drivers.
- DJI/Walksnail 6-pin harness TX/RX orientation on J3 pins 3/4 (FC-side TX on pin 3 assumed).
- The INAV target was not compiled. The INAV macro and driver names (ICM42605, BMP388 accepting chip id 0x60, `TIM_USE_SERVO`
  DMA handling) are unverified.
- Footprint-to-die pad mapping of the U6/U7 LGA footprints was taken as verified by Gate 2. The alignment result depends on it.
