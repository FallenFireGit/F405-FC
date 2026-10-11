# Gate 0 re-audit: F405-FC pin map rev C, Betaflight config, INAV target

Auditor: fresh, independent Gate 0 re-audit, 2026-10-11. I had no part in writing the files below and did not modify them.
Audited: `design/pinmap.md` (rev C), `design/betaflight_config.txt` (rev C), `design/inav_target.md` (rev C).
Checked against: `design/requirements.md`, `design/decisions.md` (accepted deviations D-01, D-03, D-04, D-09), `design/power.md`
section 4 / 10.2 / 11, `design/agent_brief.md` "Pin map" items 1-6, and the previous audit `review/gate-0-pinmap-audit.md` (G0-01..G0-13).

## Sources used

| Ref | Source | How it was used |
|---|---|---|
| [PIN] | `datasheets/st_open_pin_data/F405RGTx.xml` (ST CubeMX open pin data) | Parsed by script: all 64 positions, pin types, signal lists, ADC channels |
| [AF] | `datasheets/st_open_pin_data/GPIO-STM32F417_gpio_v1_0_Modes.xml` | Parsed by script: `GPIO_AFn_*` for every AF claimed in pinmap section 2 |
| [BF-DMA] | `datasheets/bf_src/dma_reqmap_mcu.c` (F4 section, peripheral + timer tables) | Parsed by script: every `dma` line in the BF config resolved to (DMA, stream, channel) and checked for conflicts |
| [BF-TIM] | `datasheets/bf_src/timer_stm32f4xx.c` `fullTimerHardware[]` (l.63-140) | TIMER_PIN_MAP occurrence indices |
| [AP] | `datasheets/ardupilot_src/STM32F405xx.py` (AF table l.40-525, `DMA_Map` l.574-664) | Independent cross-check of AF and DMA (TIM4_CH2 (1,3,2), TIM5_CH1 (1,2,6), TIM2_CH4 (1,6,3)/(1,7,3) etc.) |
| [INAV] | `datasheets/inav_src/timer_def_stm32f4xx.h` | `DEF_TIM` signature (l.25) and DMA option order (l.33-60) |
| [BF-*] | `cli.c` (cliDmaopt l.5547-5695, cliTimer l.5879-5995), `settings.c`, `parameter_names.h`, `resource.c`, `serial.h`, `x_serial.c`, `init.c`, `bus_spi.c`, `adc_stm32f4xx.c`, `adc.h`, `common_pre.h`, `common_post.h`, `common_defaults_post.h`, `target.h`, `drv_pinio.c`, `piniobox.c`, `sound_beeper.c`, `x_beeper.c`, `light_led.c`, `pwm_output_dshot.c`, `gyro_init.c`, `barometer_bmp388.c`, `compass_lis2mdl.c` | CLI syntax, setting names and lookup values, polarity, init order, defaults |
| [NX] | `datasheets/NX7002AK.pdf` (pdftotext) | Q2 gate load on PC15: Ciss 15 typ / 20 max pF, QG(tot) 0.33-0.43 nC |
| [TS5A] | `datasheets/TS5A3159A_DS.pdf` | IN logic: VIH 2.4 V min at V+ = 5 V, so a 3.3 V PC13 drive is OK |

Scripts (scratchpad, not in the repo): `pins.py` (pin/AF/ADC/net-name check), `bfcheck.py` (set names, resource names, duplicate pins), `dma.py` (DMA resolution + conflicts). All run with `python3 -I`; nothing under `datasheets/` was executed.

**Not available:** RM0090, DS8626 and AN2606 are still not on file (see R-09). `datasheets/bf_src/dshot_bitbang.c` is a GitHub "Not Found" JSON stub, not source. BF `msp_box.c`, `pg/*.c` and `dshot_dpwm.c` are not on file, so the claims that depend on them are marked as unverified below.

## Verification results (checked and passed)

* **Pin numbers (all 64), by script against [PIN]:** every row of pinmap section 2 and every row of section 9 matches the CubeMX position and name. `Type="I/O"` count = 51. LQFP-64 has no VREF+ pin. The "47 used + 4 NC = 51" count is correct: the BF config uses 41 distinct pins, plus PH0/PH1/PA11/PA12/PA13/PA14 = 47. The unused pins are PC2, PC3, PB12, PB13.
* **AF numbers (all 32 AF claims in section 2), by script against [AF]:** all correct. PA0 TIM5_CH1 AF2, PA1 UART4_RX AF8, PA2/PA3 USART2 AF7, PA5/6/7 SPI1 AF5, PB0/PB1 TIM3_CH3/CH4 AF2, PB10/PB11 TIM2_CH3/CH4 AF1, PC6/PC7 USART6 AF8, PC8/PC9 TIM8_CH3/CH4 AF3, PA8 TIM1_CH1 AF1, PA9/PA10 USART1 AF7, PA11/PA12 OTG_FS AF10, PA13/PA14 SWD AF0, PC10/PC11 USART3 AF7, PC12/PD2 UART5 AF8, PB3/4/5 SPI3 AF6, PB7 TIM4_CH2 AF2, PB8/PB9 I2C1 AF4. [AP] agrees for every timer AF (e.g. `"PB7:TIM4_CH2": 2`, `"PA0:TIM5_CH1": 2`).
* **ADC channels:** PC0 = ADC123_IN10, PC1 = ADC123_IN11, PC5 = ADC12_IN15 [PIN]. BF F405 map agrees (`adc_stm32f4xx.c:106-111`). ADC1 is the default instance (`adc.h:28-29`).
* **Section 9 net names vs section 2:** checked by script for all 64 pins with no mismatch. Net names are unique except the power nets (3V3, GND) and "(NC)".
* **Duplicate pins:** none. Each of the 41 pins in the BF `resource` list appears exactly once. No pin in section 2 carries two functions.
* **EXTI:** only PC4 (EXTI4) and PC14 (EXTI14) are EXTI-configured. Every other pin numbered 4 or 14 is an output (PA4 CS, PB14 LED). PC13 and PC15 are outputs, so EXTI15_10 has a single user.
* **DMA (BF), by script against [BF-DMA]:** all 14 `dma` lines resolve to the stream/channel in their comments. DMA1 uses S0, S1, S2, S3, S5, S6, S7 and DMA2 uses S0, S2, S3, S4, S6, S7, **with no stream used twice**. PA0 (TIM5_CH1) has a single option, (1,2,6), which collides with M2 (1,2,5) on DMA1 S2, so `dma pin A00 NONE` is correct. PB7 TIM4_CH2 → DMA1 S3 Ch2 is free now that SPI2_RX is gone. [AP] and [INAV] encode the same streams. Pinmap tables 3.1/3.2/3.3 match.
* **CLI ordering/semantics:** `timer <pin> AFn` resets that pin's dmaopt to `DMA_OPT_UNUSED` (`cli.c:5983`). The config puts every `dma pin` line **after** the `timer` lines, so the dma options survive. `dma pin` needs a configured timer (`cli.c:5606`), and every DMA pin has one. 9 timer-map entries ≤ `MAX_TIMER_PINMAP_COUNT` 21 (`common_defaults_post.h:93`). `timer A00 AF2` selects TIM5_CH1 rather than TIM2_CH1 (AF1), which keeps TIM2 (M3/M4) free of an extra channel.
* **TIMER_PIN_MAP occurrence indices (config.h appendix) vs [BF-TIM]:** PB0 TIM1_CH2N(1)/TIM3_CH3(2)/TIM8_CH2N(3) → 2 ✓. PB1 → 2 ✓. PB10 1 ✓. PB11 1 ✓ with dma 1 ✓. PC8 TIM3(1)/TIM8(2) → 2 ✓. PC9 → 2 ✓. PA8 1 ✓. PB7 TIM4_CH2 only → 1 ✓. PA0 TIM2_CH1(1, l.63)/TIM5_CH1(2, l.75) → 2 ✓, dma -1.
* **Set names and values:** every `set` name exists in `settings.c`/`parameter_names.h` (script). Lookup values are valid: `MSP` (`settings.c:492`), `FIRST` (l.196), `SPI`/`I2C` (l.331), `SPIFLASH` (l.226), `OFF` (l.480), `CW0` (l.183), `DSHOT600` (l.304), `CRSF` (l.249). Every resource name exists in `resource.c`.
* **Serial:** function masks MSP 1, GPS 2, RX_SERIAL 64, ESC_SENSOR 1024, VTX_MSP 131072 (`serial.h:37-53`). UART4 is identifier 3 and VCP is 20 (`serial.h:85-96`). An RX-only UART is valid because a port is kept if **TX or RX** has a pin (`x_serial.c:571`). `MSP_DISPLAYPORT_UART` exists and sets VTX_MSP|MSP (`x_serial.c:204-208`).
* **Polarity, checked against the BF sources and `design/power.md`:**
  * BEEPER (PB2): `beeperInit` configures OUT_PP (ODR = 0), then `systemBeep(false)` writes `inverted ? false : true` = LOW (`sound_beeper.c:85,117-122`). With `beeper_inversion = ON`, a beep drives HIGH. That matches the active-high PMV40UN2 gate (power.md section 11), and the 10k BOOT1 pulldown keeps it silent through reset.
  * LEDs: `led_inversion = 0` gives "on" = LOW (`light_led.c:92`), which is correct for 3V3 → R → LED → pin.
  * PINIO: with config 1 (OUT_PP, not inverted), `pinioInit` configures OUT_PP and drives LOW (`drv_pinio.c:52-71`). The box task runs only when a mode range exists (`piniobox.c:73`). So PC15 is LOW by default: Q2 off, 10 V buck EN released, VTX on, which matches power.md section 4 and pinmap section 6. USER1 active drives PC15 HIGH, Q2 turns on, VTX off. PC13 is LOW = CAM1 by default and USER2 selects CAM2. `PINIO1_BOX` in the appendix auto-enables `USE_PINIO`/`USE_PINIOBOX` (`common_post.h:642-648`).
  * The PC15 load is within the low-drive limits: NX7002AK Ciss is 15-20 pF [NX] (power.md's 30-50 pF is conservative), there is 1 k in series, and the DC source current through the 100k pulldown is 33 µA.
* **ADC DMA:** `ADC1_DMA_OPT` defaults to unused (`common_defaults_post.h:155-156`), and `adc_stm32f4xx.c:302-304` then gets no DMA, so the explicit `dma ADC 1 1` (DMA2 S4) is required and correct.
* **Init order:** `motorDevInit` (`init.c:545`) → `adcInit` (673) → `ledStripInit` (774) → `spiInitBusDMA` (988, `USE_SPI_DMA_ENABLE_EARLY`, `target.h:76`). Every option is pinned and there is no conflict, so the order can't cause a failed allocation.
* **Drivers/addresses:** BMP388 driver default address 0x76 (`barometer_bmp388.c:50,265-267`), consistent with "SDO to GND". LIS2MDL address 0x1E (`compass_lis2mdl.c:35`).
* **INAV target:** the `DEF_TIM(tim, ch, pin, usage, flags, dmavar)` signature matches [INAV] l.25. DMA, resolved with [INAV] l.33-60: DMA1 S7 M1, S2 M2, S1 M3, **S6 M4 (dmavar 1, brief item 5)**, S3 M7. DMA2 S2 M5, S7 M6, S6 LED, S4 ADC1. No conflict. M8 (TIM5) is `TIM_USE_SERVO`, so no DShot DMA is started on DMA1 S2. `TARGET_IO_PORTD BIT(2)` covers PD2. The ADC1 stream (DMA2 S4) does not clash with M5 (dmavar 0 = S2).
* **Brief "Pin map" items 1-6:**
  1. Remap applied (CAM_SEL PC13, BEEPER PB2, ESC TLM PA1/UART4_RX, M7 PB7, M8 PA0, M5/M6 PC8/PC9, UART5 full spare, VBUS detect dropped). M7 now has DShot (a superset, justified by D-01).
  2. SBUS/R2 is NC by default, with a DNP 0R to PD2 and no inverter (pinmap rows 54, section 7).
  3. GPS is on the buck-only 5V (power.md l.64, l.222).
  4. CS pull-ups are on PA4/PA15/PB6. OSD_CS no longer exists.
  5. The INAV target exists, with PB11 dmavar 1.
  6. DMA, EXTI, duplicates and net names were re-verified above, and section 9 exists with UPPER_SNAKE names.

## Previous findings (G0-01..G0-13): disposition

| ID | Status | Evidence |
|---|---|---|
| G0-01 (MAJOR) | **Resolved.** 4 extra pads: M5/M6/M7 DShot, M8 PWM/servo | pinmap section 5; BF `resource MOTOR 5-8`; DMA verified above |
| G0-02 | Resolved: VBUS-detect pin removed, PC13 reused | pinmap rev B log; no `USB_DETECT` in config |
| G0-03 | Dispositioned (D-02): GPS on buck-only 5V. AN2606 is still unverified (R-09) | power.md l.64, l.222 |
| G0-04 | Resolved: 10k CS pull-ups plus the bring-up check | pinmap section 7 |
| G0-05 | Resolved: NC by default, DNP 0R to PD2, 2 full spares (UART5, USART6) | pinmap rows 53/54, section 4 |
| G0-06 | Resolved: `design/inav_target.md` | see above; residual INAV notes R-07 |
| G0-07 | Resolved: LSE note | pinmap rows 3/4, section 7 |
| G0-08 | Electrically OK, but the **text regressed**: section 1 still says "TPS22810 EN" and "no FET gates on PC13-15", while PC15 now drives a FET gate | **R-01** |
| G0-09 | Resolved: 10k + 10 nF + BAT54S, matching power.md 10.2 | pinmap rows 9/25, section 7 |
| G0-10 | Resolved (footprint). Part name is stale vs D-07 | R-05 |
| G0-11 | Resolved: `osd_displayport_device = MSP`. Placeholders are still flagged | config l.205, l.152, l.182 |
| G0-12 | No action needed. Still true (bit-bang OFF) | |
| G0-13 | **Still open:** RM0090/DS8626/AN2606 not on file (pinmap section 8 Q4) | R-09 |

## Findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| R-01 | MINOR | **Pinmap section 1 contradicts rev C / D-04 on PC15.** It says "PC15 = VTX_PWR_EN output into the **TPS22810 EN pin** (static CMOS)" and "**No LEDs, no FET gates**, no chip selects on PC13-15 (G0-08)". In rev C, PC15 drives the NX7002AK (Q2) gate through 1k, and the TPS22810 is removed. A schematic author reading section 1 gets the wrong load and a rule the design itself breaks. Electrically the load is acceptable: Ciss 15-20 pF, 33 µA DC into the 100k, static. | pinmap.md l.54-55 vs l.70, l.12; power.md l.188-196; decisions.md D-04; NX7002AK.pdf Ciss | Rewrite section 1: "PC15 = VTX_PWR_EN into the Q2 (NX7002AK) gate via 1k, 100k pulldown; static capacitive load ≤ 20 pF, ≤ 35 µA DC". Restate the rule as "no DC current-sourcing loads (LEDs, bipolar bases)". |
| R-02 | MINOR | **Beeper FET type is inconsistent.** Pinmap row 28 says "N-MOSFET gate (**2N7002 class**)". power.md section 11 chose the **PMV40UN2** and explicitly **rejected 2N7002/NX7002AK** as marginal from 3.3 V (VGS(th) up to 2.1-2.5 V, RDS(on) of several Ω). | pinmap.md l.94; power.md l.328-333 | Change row 28 to "PMV40UN2 (logic-level N-MOSFET), 100 Ω series, 10k BOOT1 pulldown". |
| R-03 | MINOR | **Unused pins PC2, PC3, PB12, PB13 are left floating, and the claim "firmware leaves it as analog input" is unsupported.** After reset, STM32F4 GPIOs are floating inputs (except the JTAG pins). Nothing in BF init reconfigures unused pins (no analog/unused-pin handling in `init.c` or `io.c`). PC2/PC3 sit next to VSSA/VDDA (pins 12/13), so a floating Schmitt input there adds leakage and noise beside the analog supply. | pinmap.md l.76-77, l.99-100, l.132 ("no pads"); `grep -i analog init.c io.c` finds nothing; ST guidance on unused I/O (AN4899, from memory, not on file) | Tie each unused pin to GND through 10k-100k (or directly to GND), or give them test pads with a pulldown. Fix the text: "BF leaves unused pins as floating inputs". |
| R-04 | MINOR | **Q2 gate pulldown position is specified two different ways.** Pinmap section 7 says "100k on the Q2 gate (**VTX_PWR_EN side of the 1k**, so PC15 also reads low)". power.md section 4 says "100 kOhm gate pulldown (**gate side**)". Both work, since PC15 sees 101k to GND either way, but the schematic needs one answer. The gate side is the better choice because Q2 stays off even if the 1k is open. | pinmap.md l.283 vs power.md l.189 and pinmap.md l.70 | Make section 7 say "gate side of the 1k" (PC15 still reads low through 1k + 100k). |
| R-05 | INFO | LED-strip buffer part is stale. Pinmap rows 41 and section 7 name 74AHCT1G125 / 74LVC1T45, but D-07 chose **SN74LV1T125DBVR** (VCC 5 V). | pinmap.md l.107, l.287; decisions.md D-07 | Update the part name. |
| R-06 | INFO | **Stale/understated DShot notes.** (a) Section 5 says "If a pilot needs a **7th** DShot output, the LED_STRIP pad can be remapped". Since rev C, M7 is DShot, so this would be the 8th. (b) Section 3.3 and the config (l.114) say an 8-motor DShot mixer "fails to initialise M8". In BF 4.5, `dshotPwmDevInit` returns NULL when any motor's `pwmDshotMotorHardwareConfig` fails, which disables **all** motors, not just M8. `pwm_output_dshot.c:246-247` confirms the false return. The caller (`dshot_dpwm.c`) is not on file, so the NULL return is auditor knowledge. | pinmap.md l.233, l.259; config l.114; `pwm_output_dshot.c:246` | Reword: "octo DShot is not possible; selecting an 8-motor mixer with DShot leaves no motor output (use PWM/Oneshot for octo, or remap LED_STRIP for an 8th DShot motor)". |
| R-07 | INFO | **INAV wording and residual risk.** `inav_target.md` l.173 says "INAV's `DEF_TIM` macro always records the dmavar-0 stream". In fact it records the stream chosen by the `dmavar` argument ([INAV] l.25); here dmavar 0 = D(1,2,6). If a user forces TIM5 to motors (INAV `timer_output_mode`), S8 would take DMA1 S2 and break M2. INAV driver and macro names (`USE_MAG_ALL`, `UART4_TX_PIN NONE`, `ADC1_DMA_STREAM`, ICM42605 driver detecting the 42688-P) are unverified; the doc says so. | inav_target.md l.17, l.173-175, l.189-190 | Correct the sentence. Add "do not set TIM5 to MOTORS". Compile in an INAV tree before release (already noted). |
| R-08 | INFO | **ROM DFU with battery connected.** With D-04, the HD VTX is **on** by default whenever the battery is present, and its TX drives PA10 (USART1_RX, a bootloader pin per the previous audit). On USB-only power the VTX is unpowered, so DFU is clean. On battery, VTX traffic on PA10 could capture the ROM bootloader. AN2606 is not on file, so this is unverified. | pinmap.md rows 43, 70; decisions.md D-04; previous audit G0-03 | Bring-up/user guide: "enter ROM DFU on USB power only (battery disconnected)". |
| R-09 | INFO | **G0-13 is still open.** RM0090, DS8626 and AN2606 are not on file. As a result, these remain unverified against ST documents: the PC13-15 output restrictions (including whether DS8626 limits PC13-15 to one output at a time; that wording is from F1 datasheets and the auditor believes it is absent for F4, but PC13 and PC15 are both outputs here), the bootloader pin list, and the FT status of PA0/PA1. DMA tables are covered by three independent encodings ([BF-DMA], [AP], [INAV]), which agree. | pinmap.md section 8 Q4 | File the three PDFs before Gate 1 and re-check the PC13-15 note. |
| R-10 | INFO | **The config.h appendix is not fully equivalent to the CLI, and some macro names can't be verified locally.** The appendix has no `DEFAULT_FEATURES` (OSD, LED_STRIP, TELEMETRY, ESC_SENSOR), no I2C pull-up/clock settings, and no OSD displayport default. `DEFAULT_DSHOT_*`, `GYRO_n_SPI_INSTANCE`, `GYRO_n_ALIGN`, `FLASH_SPI_INSTANCE`, `PINIO1_CONFIG`, `DEFAULT_RX_FEATURE` and `SERIALRX_PROVIDER` are not in the BF files on file (the `pg/*.c` sources are absent); the auditor recognises them as BF 4.5 config.h names. USER1/USER2 permanent IDs 40/41 are not on file either (`msp_box.c` absent); the auditor's knowledge agrees. `datasheets/bf_src/dshot_bitbang.c` is a 404 JSON stub. | config l.207-314; `grep` over `datasheets/bf_src` | Add `DEFAULT_FEATURES` etc. if the appendix is to be submitted to betaflight/config. Build once and run `diff all` against the CLI. Re-fetch `dshot_bitbang.c`. |
| R-11 | INFO | Pinmap section 8 Q1 (keep onboard mag?) was answered by D-08. Brief item 1 said M7 was PWM/servo only, and rev C upgraded it to DShot (consistent with D-01). | pinmap.md l.294; decisions.md D-08 | Mark Q1 closed with a reference to D-08. |

No BLOCKER or MAJOR findings.

## Requirement coverage

| Requirement | Status |
|---|---|
| STM32F405RGT6 LQFP-64; BF + INAV | Covered: BF CLI + config.h; INAV target sketch (uncompiled, R-07) |
| USB-C FS device | Covered: PA11/PA12 AF10, no VBUS pin (not required) |
| Two IMUs on SPI, own CS, own INT on separate EXTI | Covered: SPI1, CS PA4/PA15 (10k pull-ups), INT PC4 EXTI4 / PC14 EXTI14 |
| BMP390 + IIS2MDC on I2C, external I2C pads | Covered: I2C1 PB8/PB9, 2.2k pull-ups. INAV mag unsupported (D-08) |
| W25N01GV on own SPI | Covered: SPI3 PB3/4/5, CS PB6, DMA1 S0/S5 |
| Analog OSD AT7456E on own SPI | **Not met: accepted deviation D-01.** MSP DisplayPort on UART1 instead |
| Camera select via PINIO | Covered: PC13 PINIO2 → TS5A3159A (now a CAM1/CAM2 → VTX video switch, D-01) |
| VTX 10 V switch via PINIO | Covered: PC15 PINIO1 → Q2 → 10 V buck EN (**accepted deviation D-04**: EN control instead of a high-side switch) |
| HD VTX JST-SH 6-pin on a full UART, SBUS/R2 | Covered: USART1 PA9/PA10. R2 is NC with a DNP 0R to PD2 (brief item 2) |
| ESC connector incl. CURR, TLM | Covered: CURR PC1 (protected), M1-M4 PB0/PB1/PB10/PB11, TLM PA1 |
| 6 UARTs (ELRS, GPS, HD, ESC TLM, 2 spare) | Covered: UART4 is RX-only (**accepted D-09**), 2 full spares (UART5, USART6) |
| 4 motors + 4 extra motor/servo pads | Covered: M1-M4 and M5/M6/M7 DShot + bidir; M8 PWM/servo (octo DShot not possible, R-06) |
| WS2812 output | Covered: PA8 TIM1_CH1, DMA2 S6, buffer footprint (R-05 part name) |
| Buzzer, low-side N-MOSFET | Covered: PB2, active-high, BOOT1 pulldown (R-02 text) |
| ADC VBAT / CURR / RSSI | Covered: PC0 IN10 / PC1 IN11 / PC5 IN15, ADC1 on DMA2 S4 |
| 2 status LEDs + power LED | Covered: PB14/PB15 (sink). Power LED is not on the MCU |
| BOOT button, SWD pads | Covered: BOOT0 10k pulldown + button. PA13/PA14/NRST pads |
| 8 MHz HSE | Covered: PH0/PH1, `system_hse_mhz = 8` |
| 5 V / 10 V current ratings | Out of pin-map scope. Accepted deviation D-03 |

## Verdict

**PASS** (0 BLOCKER, 0 MAJOR, 4 MINOR: R-01..R-04, 7 INFO).

I re-verified pin numbers, AF numbers, ADC channels, EXTI lines, duplicate pins, section 9 net names, the full BF DMA plan, the TIMER_PIN_MAP indices, the CLI syntax/semantics and the INAV DMA plan against the primary sources on file, and found no errors. PINIO, beeper and LED polarity match the hardware described in pinmap section 6 and power.md sections 4 and 11. The MINOR findings are document inconsistencies (R-01, R-02, R-04) and one unused-pin treatment (R-03). Fix them before schematic capture so the schematic is not drawn from stale text.
