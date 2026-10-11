# Gate 1 review: MCU / digital (F405-FC, schematic rev C)

Reviewer: independent Gate 1 MCU/digital reviewer, 2026-10-11. This is a fresh review. It does not rely on the Gate 0 audits' conclusions.

## 1. Scope

* **Pin check:** all 64 STM32F405RGT6 (U3) pins in the exported netlist, checked against `design/pinmap.md` rev C section 2 (pin table) and section 9 (net names). Also checked against the ST open pin database (`datasheets/st_open_pin_data/F405RGTx.xml`).
* **Boot and clock:** BOOT0, PB2/BOOT1 plus the beeper gate path, NRST, the HSE crystal (load caps, gain margin) and the SWD pads.
* **USB:** the path through the USBLC6-2SC6 and J1 (USB-C), CC resistors and shield.
* **Pull resistors:** CS pull-ups, I2C pull-ups and unused-pin pulldowns.
* **Status LEDs and PINIO:** LED polarity, and the PINIO1 (VTX_PWR_EN → Q2 → U2 EN) and PINIO2 (CAM_SEL → TS5A3159A IN) chains.
* **Connectors and pads:** UART naming/crossing at J3/J4/J5, ESC connector J2 order, motor pads.
* **LED strip buffer:** U12 is an SN74LV1T125 placed on the KiCad 74AHCT1G125 symbol.
* **ADC networks:** VBAT, CURR and RSSI.
* **Betaflight config:** whether `design/betaflight_config.txt` matches the hardware exactly. The INAV target was spot-checked only.

Power-stage, sensor-internal and layout topics belong to other Gate 1 reviews. They are mentioned here only where they touch MCU pins.

## 2. Method and evidence base

1. **Netlist export.** I exported a fresh netlist from the committed schematic: `kc 'cd kicad && kicad-cli sch export netlist -o /tmp/g1m.net F405FC.kicad_sch'`. It went to the chroot's /tmp so no repo file changed. Ignoring date/tstamp/source lines, it is identical to the committed `kicad/F405FC.net`.
2. **Pin script.** I parsed it with a script (scratchpad `pincheck.py`):
   * For every U3 node, the netlist net was compared with pinmap §9 and with the first token of the pinmap §2 "Net / function" column.
   * Each symbol pin name (with the `_<n>` suffix removed) was compared with the ST XML `<Pin Name Position>` entry.
3. **Spot checks.**
   * `kicad/erc.rpt`: 0 errors, 0 warnings.
   * `docs/F405FC_schematic.pdf`: text-searched for 7 nets added in rev C. All are present, so the PDF is not stale.
4. **Concurrent edit.** During the review, `design/circuit.py` was changed on disk by another task. The only change is `FP["HOLE"]`, a mounting-hole footprint. It has no electrical effect, so the line numbers cited below are still valid.
5. **Datasheets used** (text-extracted from `datasheets/`; nothing was executed):
   * TS5A3159A_DS.pdf: pin table and VIH.
   * NX7002AK.pdf: pinning and VGSth.
   * PMV40UN2.pdf: pinning.
   * ICM-42688-P_DS.pdf: RESV/INT2 handling.
   * BMI270_DS.pdf: Tables 17 and 21, DNC rules.
6. **Betaflight sources used** (`datasheets/bf_src`):
   * `light_led.c:91-92`, `sound_beeper.c:85,117-120`, `pinio.c:52-82`
   * `settings.c` (every CLI name in the config), `serial.h:37-53,85-96`
   * `timer_stm32f4xx.c:63-135` (TIMER_PIN_MAP occurrence indexes), `dma_reqmap_mcu.c:408,437-464`
   * `x_serial.c:204-208` (MSP DisplayPort default function mask), `cli.c:5247` (`NONE` DMA option)
7. **Not on file, so not verified by me:**
   * DS8626 (STM32F405 datasheet), RM0090, AN2606, AN2867.
   * ECS ECX-32 crystal datasheet, SN74LV1T125, USBLC6-2, BAT54S and IIS2MDC datasheets.
   * BF `voltage.c`, `msp_box.c` and the `vcpf4` USB config.

   Any statement below that depends on these is marked *(from memory, not verified)*.

## 3. Checks passed

| # | Check | Result / evidence |
|---|---|---|
| P1 | **64/64 U3 pins vs pinmap §9 and §2** | Script output: `U3 pins in netlist: 64 missing: [] bad: 0`. Every pin's net equals the §9 name, and §2 agrees. ST XML vs symbol pin names: `ST pins 64 diffs 0`. Source is the `mcu_conn` dict at `circuit.py:280-292` |
| P2 | **BOOT0** | R16 10k BOOT0→GND (`circuit.py:308`). SW1 between 3V3 and BOOT0 (`:309`). PTS810 footprint pads are 1,1,2,2, matching the symbol's 1/2 |
| P3 | **PB2 / BOOT1 + beeper** | R17 10k BEEPER→GND (`:312`). R40 100 Ω goes BEEPER→BUZ_G (`:450`), so the series resistor sits on the gate side and the strap node keeps the 10k. Q1 PMV40UN2 is G=1, S=2, D=3 on the 2N7002 symbol, which matches the PMV40UN2.pdf pinning table. D9 flyback BUZ_N→5V, buzzer pads P13/P14. BF: `beeper_inversion = ON` → `IOWrite(io, inverted ? onoff : !onoff)` (`sound_beeper.c:85`) drives HIGH for beep. `beeper_od = OFF` → OUT_PP (`:120`) |
| P4 | **NRST** | C35 100 nF to GND and TP3 (net NRST: C35, TP3, U3.7). Internal pull-up only, which is acceptable |
| P5 | **SWD pads** | TP1 SWDIO (U3.46), TP2 SWCLK (U3.49), TP3 NRST, TP4 3V3, TP5 GND (`:468-471`). Matches the requirement |
| P6 | **HSE wiring and load caps** | Y1 pin 1 = HSE_IN = PH0 (pin 5); pin 3 = HSE_OUT = PH1 (pin 6); pins 2/4 = GND. The 3225-4Pin footprint has pads 1-4. C36/C37 are 10 pF C0G. CL_eff = 10·10/20 + C_stray(3-5 pF) = 8-10 pF, against CL 8 pF, consistent with pinmap's CL1 = 2·(CL − C_stray). **Gain margin: see G1M-01** |
| P7 | **USB D+/D-** | J1 A6/B6 (D+) → USB_DP → U3.45 PA12. J1 A7/B7 (D-) → USB_DM → U3.44 PA11. Not swapped, and both rows of the receptacle are joined. USBLC6-2SC6: I/O1 (pins 1, 6) on USB_DM, I/O2 (pins 3, 4) on USB_DP, pin 2 GND, pin 5 VBUS. Flow-through pairing is consistent |
| P8 | **USB CC / VBUS / shield** | R34 and R35 are separate 5.1k resistors from CC1/CC2 to GND (`:410-411`). VBUS on A4/A9/B4/B9. GND on A1/A12/B1/B12. J1.SH (4 shield pads) to GND. No external 1.5k on D+; the OTG_FS internal pull-up is used |
| P9 | **CS pull-ups** | 10k to 3V3 on GYRO1_CS (R18, PA4), GYRO2_CS (R19, PA15) and FLASH_CS (R20, PB6) (`:318-319`). Flash /WP and /HOLD each have their own 10k to 3V3 (R29, R30) |
| P10 | **I2C1** | R25/R26 2.2k to 3V3 on I2C1_SCL/SDA (`:322-323`). Bus: U3 PB8/PB9, BMP390 SCK/SDI, IIS2MDC SCL/SDA, J4 pins 6/5. BMP390 CSB = 3V3 (I2C mode) and SDO = GND (0x76). BF `i2c1_pullup = OFF` is consistent |
| P11 | **Status LEDs** | 3V3 → R27 330 Ω → D11 (blue) → PB14, and 3V3 → R28 1k → D12 (green) → PB15. Cathode is at the pin, so low = on. BF `ledSet`: `IOWrite(leds[led], on ? inverted : !inverted)` (`light_led.c:91-92`). With `led_inversion = 0`, on writes LOW. Matches |
| P12 | **PINIO1 VTX_PWR_EN** | PC15 → R11 1k → VTX_OFF_G. R12 100k is on the gate side to GND. Q2 is NX7002AK (G=1, S=2, D=3 per NX7002AK.pdf Table 2). Drain is on EN_10V = U2.EN (`:237-241`). VGSth max is 2.1 V (datasheet), so a 3.3 V drive turns it on and pulls EN low (VTX off). BF `pinio_config 1 = 1`, non-inverted: `pinioInit` drives `IOLo` (`pinio.c:67-70`), so the VTX is on after boot. USER1 active → high → VTX off. Matches pinmap §6 |
| P13 | **PINIO2 CAM_SEL** | PC13 → U11 pin 6 (IN). R31 100k to GND. NC (pin 3) = CAM1_VID, NO (pin 1) = CAM2_VID, COM (pin 4) = VTX_VID. TS5A3159A_DS p.3: "High = COM connected to NO; Low = COM connected to NC", so low = CAM1 as documented. VIH is 2.4 V at 3.3 V supply, which PC13 meets. Load on PC13/PC15 is a CMOS gate plus a 100k pulldown (33 µA), within the backup-domain I/O limits (but see G1M-06) |
| P14 | **Unused pins** | PC2, PC3, PB12, PB13 each have a 100k pulldown (R21-R24, `:320-321`). No U3 pin is left unconnected. Unused peripheral pins: BMI270 INT2/ASDX/ASCX/OCSB/OSDO are NC (allowed by BMI270_DS Tables 17 and 21: DNC). ICM-42688-P INT2/FSYNC and RESV2/3/7/10/11 are on GND (ICM DS pin table: "Connect to GND if FSYNC not used", "RESV: No connect or connect to GND", pin 7 "Connect to GND") |
| P15 | **ELRS J5** | 1 = 5V_SYS, 2 = GND, 3 = UART2_TX (PA2), 4 = UART2_RX (PA3), MP = GND. FC-side naming (see G1M-05) |
| P16 | **GPS J4** | 1 = 5V (buck-only, D-02), 2 = GND, 3 = UART3_TX (PC10), 4 = UART3_RX (PC11), 5 = I2C1_SDA, 6 = I2C1_SCL |
| P17 | **HD VTX J3** | 1 = 10V, 2 = GND, 3 = UART1_TX (PA9), 4 = UART1_RX (PA10), 5 = GND, 6 = HD_R2. HD_R2 links to UART5_RX only through R37, DNP 0R (`:431`). Matches the requirements order (10V, GND, TX, RX, GND, SBUS/R2) |
| P18 | **ESC J2** | 1 VBAT, 2 GND, 3 ESC_CURR, 4 MOTOR1 (PB0), 5 MOTOR2 (PB1), 6 MOTOR3 (PB10), 7 MOTOR4 (PB11), 8 ESC_TLM (PA1, UART4_RX). Matches requirements.md:30 exactly |
| P19 | **Motor / extra pads** | P19 S5 = PC8, P20 S6 = PC9, P21 S7 = PB7, P22 S8 = PA0, plus a GND pad (P24) and a 5V pad (P25). UART5 (P15/P16) and UART6 (P17/P18) pads are present |
| P20 | **LED-strip buffer U12** | The KiCad 74LVC1G125 base symbol (which 74AHCT1G125 extends) has pin 1 inverted input (OE#), pin 2 A, pin 3 GND, pin 4 tri-state Y, pin 5 VCC. Netlist: pin 1 = GND (always enabled), pin 2 = LED_STRIP (PA8), pin 4 = LED_DIN_BUF, pin 5 = 5V. This matches the SN74LV1T125 DBV pinout (1 OE, 2 A, 3 GND, 4 Y, 5 VCC) *(from memory; datasheet not on file)*. R33 330 Ω → LED_DIN pad P10. R32 is a DNP 0R bypass (see G1M-03) |
| P21 | **VBAT divider** | R14 10k (0603) from VBAT to VBAT_ADC, R15 1k to GND, C24 100 nF (`:270-272`). Ratio is 11, so 36 V gives 3.27 V. BF full scale with `vbat_scale 110`, divider 10, multiplier 1 is 4095·110·3300/(4095·10·10) = 363 → 36.3 V = 11 × 3.3 V, which matches. *(BF formula from memory; `voltage.c` not on file. `settings.c:919-921` confirms the parameter names.)* INAV `VBAT_SCALE_DEFAULT 1100` is consistent |
| P22 | **CURR / RSSI protection** | For each: 10k series (R38, R39), 10 nF to GND (C52, C53), BAT54S with A = GND, K = 3V3, COM = ADC node (D7, D8) (`:442-447`). The KiCad BAT54S symbol is 1 = A, 2 = K, 3 = COM. This clamps the node below GND − Vf and above 3V3 + Vf, and limits injection to (5 V − 3.6 V)/10k = 0.14 mA. The clamp/filter sits on the MCU side of the 10k, as required by G0-09 |
| P23 | **BF resources vs hardware** | Every `resource` line (`betaflight_config.txt:16-56`) names the same pin the netlist connects to that function: BEEPER B02, MOTOR 1-8, LED_STRIP A08, SERIAL_TX/RX 1/2/3/5/6, RX 4 = A01 (no TX 4), I2C B08/B09, LED B14/B15, SPI1/SPI3 pins, ADC C00/C05/C01, PINIO C15/C13, FLASH_CS B06, GYRO_EXTI C04/C14, GYRO_CS A04/A15. The config.h appendix matches the CLI section |
| P24 | **BF timers / DMA** | AF numbers match pinmap §2. TIMER_PIN_MAP occurrence indexes match `timer_stm32f4xx.c`: PB0 and PB1 are 2nd (after TIM1 CHxN), PC8 and PC9 are 2nd (after TIM3), PA0 is 2nd (after TIM2), and PB10/PB11/PA8/PB7 are 1st. DMA options match `dma_reqmap_mcu.c`: ADC1 opt 1 = DMA2 S4; TIM2_CH4 opt 1 = DMA1 S6; TIM4_CH2 = DMA1 S3 Ch2; TIM5_CH1 has only DMA1 S2 (M2), so `NONE` is right (`cli.c:5247` accepts NONE). No stream is used twice |
| P25 | **BF serial / functions** | `serial 0 131073` = MSP (1) + VTX_MSP (1 << 17) (`serial.h:37,53`). This is the same mask BF sets for `MSP_DISPLAYPORT_UART` (`x_serial.c:207`). SERIAL_RX 64, GPS 2 and ESC_SENSOR 1024 are correct. `SERIAL_PORT_UART4` is a valid identifier (`serial.h:88`). Every `set` name exists in `settings.c` / `parameter_names.h`. `pinio_box 40,41` = USER1/USER2 *(permanent IDs from memory; `msp_box.c` not on file)* |
| P26 | **ERC / PDF currency** | `kicad/erc.rpt`: 0 errors, 0 warnings. The PDF contains the rev C nets (VTX_OFF_G, LED_DIN_BUF, BUZ_G, HD_R2, UNUSED_PB13, USB_CC2, ESC_TLM) |

## 4. Findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| G1M-01 | **MAJOR** | **HSE gain margin is not demonstrated, and on one plausible reading of the MCU spec it fails.** The design assumes ESR 400 Ω, C0 3 pF, CL 8 pF, giving gm_crit = 4·ESR·(2πf)²·(C0+CL)² = **0.49 mA/V** (0.68 mA/V if C0 = 5 pF). The margin depends on the STM32F405 HSE gm(min), which decisions.md "recalled as 5 mA/V" and marks "unverified". I also cannot verify it. My own recollection of DS8626 is "gm = 1 mA/V (startup) min", and AN2867 requires gm/gm_crit ≥ 5. At 1 mA/V the margin is **2.0** (1.5 at C0 = 5 pF): a cold-start/ageing risk across the build. If the 1 mA/V figure is instead AN2867's "gm_crit_max" for F4, 0.49 < 1 passes. The crystal's ESR and C0 come from decisions.md, not from a datasheet on file | `circuit.py:313-317` (Y1 ECS-80-8-33-JEN-TR3, 10 pF loads); `decisions.md:69` ("DS8626 is not on file, so this is unverified"); pinmap §8 item 4 (RM0090/AN2606 still not filed) | File DS8626 and the ECX-32 datasheet (ESR max and C0 at 8 MHz) under `datasheets/`, then recompute against the DS8626 HSE gm / gm_crit_max row. If gm(min) = 1 mA/V, change Y1 to an 8 MHz part with ESR ≤ 150 Ω and C0 ≤ 3 pF (gm_crit ≤ 0.18 mA/V → margin ≥ 5.5), or use a larger package with lower ESR. No other schematic change is needed. Closing this is documentation only if the datasheet confirms ≥ 5 margin |
| G1M-02 | MINOR | **External I2C/UART devices on the GPS connector are back-powered on USB-only power, which can stall the on-board I2C1 bus.** J4 pin 1 is the buck-only 5V (dead on USB, D-02), but J4 SDA/SCL carry 3V3 2.2k pull-ups, and PC10 (UART3_TX) idles high, both live on USB. A plugged-in GPS/mag module is fed through its ESD diodes into its unpowered 3.3 V rail. That can clamp SDA/SCL near 0.5-0.7 V while the BMP390 and IIS2MDC share the bus. BF detects baro/mag only at boot, so a USB-first, battery-later bench session can come up without baro/mag until reboot. Flight boots (battery first) are unaffected | `circuit.py:322-323` (pull-ups to 3V3); `:432-435` (J4: pin 1 = "5V", 5/6 = I2C1); `:212` (5V = U1 buck output); decisions.md D-02 | Accept and document in the bring-up/user notes ("connect the battery before USB, or reboot after connecting the battery, when a GPS-mag is attached"). Alternatively, fit a series resistor (≈100-220 Ω) on J4 SDA/SCL/TX to limit back-feed current. The D-02 trade-off (GPS dead in DFU) should stay |
| G1M-03 | INFO | The LED-strip bypass R32 (DNP 0R) connects PA8 directly to the U12 output (LED_DIN_BUF). Fitting R32 with U12 populated causes output contention (push-pull vs push-pull) | `circuit.py:392-397` | Assembly note / silkscreen: "R32 only with U12 not fitted" |
| G1M-04 | INFO | The BMI270 starts in I2C mode (BMI270_DS: "After reset / power-up, device's primary interface is in I2C mode") and shares SCK/MOSI with the ICM-42688-P. BF probes gyro_1 (ICM) first, so ICM traffic is seen by a BMI270 still in I2C mode. Already flagged by Gate 0 | `circuit.py:336-349`; `betaflight_config.txt:144-150`; pinmap §7 | Keep the pinmap §7 bring-up check (repeated cold boots, both IMUs detected). If flaky, swap the gyro order |
| G1M-05 | INFO | All JST connectors use FC-side signal names (pin 3 = FC TX, pin 4 = FC RX). The TX→RX crossing therefore happens in the cable or peripheral. This matches requirements.md:29-31 and the common DJI/ELRS/GPS FC convention, but no cable pinout standard is on file to prove it for a specific DJI/Walksnail/ELRS/GPS harness | J3/J4/J5 at `circuit.py:427-439` | At bring-up, check each supplied harness end to end (FC TX reaches the peripheral RX). Put T/R labels on silkscreen |
| G1M-06 | INFO | PC13 and PC15 are both GPIO outputs in the backup (power-switch) domain. DC loads are 33 µA each, static, no sourcing of LED-type loads, so the 2 MHz / 30 pF / 3 mA rules are met. I could not check DS8626 for any "only one of PC13-15 as output at a time" restriction (that wording is from the F1 family; I believe it is absent from F4) | `circuit.py:240-241, 379-382`; pinmap G0-08 | Confirm against DS8626 Table 7 footnote when the PDF is filed |
| G1M-07 | INFO | The BAT54S clamps on CURR/RSSI feed reverse leakage through the 10k series resistor. Error is about ±mV at 25 °C, rising to tens of mV when hot. This is an offset on CURR (about 0.5 A at ibata_scale 400 when hot) | `circuit.py:442-447` | Calibrate `ibata_offset` warm. Optionally choose a low-leakage clamp at Gate 2 |
| G1M-08 | INFO | USB: the shield goes straight to GND (acceptable; an RC/ferrite is optional). There is no VBUS-sense pin, and PA9 (OTG_FS_VBUS) is used as UART1_TX. This relies on BF F4 VCP not enabling VBUS sensing *(from memory; `vcpf4/usb_conf.h` not on file)*, which is the same pattern as SPEEDYBEEF405V4 per pinmap §0 | `circuit.py:406-409`, `mcu_conn` PA9 | Confirm USB enumeration at bring-up with UART1 connected to a VTX |
| G1M-09 | INFO | The BF config still has hardware placeholders: `gyro_1/2_sensor_align = CW0`, `ibata_scale = 400`. The INAV target is uncompiled | `betaflight_config.txt:146-149,183`; `inav_target.md:3` | Set alignments after placement is frozen. Calibrate the scale per ESC |
| G1M-10 | INFO | U12 uses the 74AHCT1G125 symbol with value/MPN SN74LV1T125. Pin functions are identical (P20), but the lib_id name may confuse BOM/schematic readers. The LV1T VIH at 5 V (2.0 V) is from memory | `circuit.py:392-394` | Optional: add a symbol Description note. Gate 2 confirms VIH from the TI datasheet |
| G1M-11 | INFO | The blue status LED (LTST-C191TBKT) uses 330 Ω from 3.3 V, giving about 0.5-2 mA depending on Vf. It may be dim but is functional | `circuit.py:324-327` | Bench check. Optionally 150-220 Ω |

## 5. Verdict

**FAIL (1 MAJOR: G1M-01).** Pin assignment, nets, boot straps, USB, pull resistors, polarity chains, connectors, ADC networks and the Betaflight configuration all match the pin map and hardware. The only open item that blocks sign-off is the unverified HSE oscillator gain margin (G1M-01). It closes as PASS if DS8626 plus the crystal datasheet show a margin ≥ 5; otherwise Y1 must change to a lower-ESR crystal. G1M-02 (MINOR) needs a documentation decision.
