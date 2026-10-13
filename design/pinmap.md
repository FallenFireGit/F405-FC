# F405-FC pin map: STM32F405RGT6 (LQFP-64)

Status: Gate 0, **rev C** (2026-10-11). Rev B applied the Gate 0 audit fixes (`review/gate-0-pinmap-audit.md`) with the lead's decisions. Rev C applies the sourcing/power decisions in `design/decisions.md` (D-01 analog OSD dropped, D-04 VTX switch moved to the 10 V buck EN). Source requirements: `design/requirements.md`.
Firmware targets: Betaflight 4.5 (`design/betaflight_config.txt`, board_name `F405FC`, manufacturer_id `CUST`) and INAV (`design/inav_target.md`).

### Rev C change log (vs rev B)

| Ref | Change |
|---|---|
| D-01 | **AT7456E analog OSD removed** (not sold by DigiKey; MAX7456 obsolete). SPI2 (PB13/PC2/PC3) and OSD_CS (PB12) are now **unused, no connection** (no pads). HD MSP DisplayPort is the primary OSD. DMA1 S4 is now free; S3 goes to M7 |
| D-01 | **M7 (PB7, TIM4_CH2) now has DMA** (DMA1 S3 Ch2, freed by SPI2_RX) and supports DShot + bidir. M8 (PA0) stays PWM/servo only (DMA1 S2 = M2) |
| D-04 | **VTX_PWR_EN (PC15) polarity inverted:** PC15 drives an NX7002AK gate (1k series, 100k pulldown) that pulls the 10 V buck EN low. **High = VTX off.** Low/floating (reset, DFU, boot) = VTX on. BF `pinio_config 1 = 1` |
| G0-09 | CURR/RSSI protection fixed to **10k series + 10 nF + BAT54S** (matches `design/power.md` 10.2) |
| R-01..R-08 | Re-audit minors: stale TPS22810/2N7002/AHCT text fixed; 100k pulldowns on the 4 unused pins; Q2 pulldown on the gate side; DFU-on-USB-only note |

### Rev B change log (vs rev A)

| Audit ID | Change |
|---|---|
| G0-01 | CAM_SEL (PINIO2) PB2 → **PC13**. BEEPER PB7 → **PB2** (the BOOT1 10k pulldown also holds the FET gate off). ESC telemetry PD2 (UART5_RX) → **PA1 (UART4_RX)**. New extra outputs **M7 = PB7 (TIM4_CH2)** and **M8 = PA0 (TIM5_CH1)**, both **PWM/servo only, no DMA**. UART5 (PC12/PD2) becomes a **full spare**. UART4 is now **RX-only** (its TX pin PA0 is M8) |
| G0-02 | VBUS-detect pin **removed** (BF 4.5 ignores the CLI `USB_DETECT` resource anyway). PC13 reused for CAM_SEL |
| G0-05 | HD-VTX connector pin 6 "SBUS/R2" is **not connected by default**. A **DNP 0R** links it to UART5_RX (PD2), with **no inverter** |
| G0-03 | Noted: the GPS is powered from the **buck-only 5 V rail**, not the USB OR-ed rail. On USB-only power during ROM DFU the GPS is dead, so it can't stream into USART3 (PC10/PC11). PB5 stays SPI3_MOSI |
| G0-04 | 10k pull-ups to 3V3 on GYRO1_CS, GYRO2_CS, OSD_CS, FLASH_CS stated as schematic requirements (section 7) |
| G0-06 | INAV target added: `design/inav_target.md` |
| G0-07/08/09/10 | Notes added (LSE must stay off; PC13-15 CMOS-only loads; ADC clamps mandatory; WS2812 level-shifter footprint) |
| - | Section 9 "Net names for schematic" added |

## 0. Sources and how each claim was checked

| What | Source used | Notes |
|---|---|---|
| Pin numbers / names (LQFP-64) | ST CubeMX open pin database `STM32F405RGTx.xml` (`datasheets/st_open_pin_data/`) | Matches DS8626 Table 7. Re-verified by the auditor |
| AF numbers | ST `GPIO-STM32F417_gpio_v1_0_Modes.xml` (same folder) = machine-readable DS8626 Table 9 | Checked by script for every AF used (rev B re-run, including PB7 TIM4_CH2 AF2 and PA0 TIM5_CH1 AF2) |
| DMA request mapping | Betaflight 4.5 `dma_reqmap_mcu.c` + ArduPilot `STM32F405xx.py` + INAV `timer_def_stm32f4xx.h` (the auditor checked these three independent encodings of RM0090 Tables 42/43; they agree) | The RM0090/DS8626 PDFs still couldn't be downloaded (st.com times out) |
| BF allocation order / defaults | BF 4.5 `init.c`, `bus_spi.c`, `target/STM32F405/target.h` (`USE_SPI_DMA_ENABLE_EARLY`), `pg/adc.c`, `light_led.c`, `sound_beeper.c` | |
| Proven patterns | betaflight/config `4.5-config`: SPEEDYBEEF405V4, SPEEDYBEEF405V3, MATEKF405TE, FOXEERF405V2. INAV SPEEDYBEEF405V4 | Noted per pin |

## 1. Design decisions (summary)

* **USART3 on PC10/PC11, I2C1 on PB8/PB9, I2C2 unused.** This frees PB10/PB11 for motors (SpeedyBee F405 V4 / Foxeer F405 V2 pattern).
* **SPI3 on PB3/PB4/PB5 (AF6).** SWD only, so no SWO (SpeedyBee F405 V4 / Foxeer F405 V2).
* **SPI2 unused (rev C).** It was the AT7456E bus (PB13/PC2/PC3, CS PB12); the OSD was dropped (D-01).
* **Motors M1-M4 = PB0, PB1 (TIM3_CH3/CH4), PB10, PB11 (TIM2_CH3/CH4).** All are CHx (not CHxN) and each has a dedicated DMA1 stream, so DShot600 + bidirectional DShot work (SpeedyBee F405 V4 M3/M4; Matek F405-TE M5/M6).
* **Extra outputs:**
  * **M5/M6 = PC8/PC9 (TIM8_CH3/CH4)**, DMA2. Full DShot + bidir (Matek F405-TE M1/M2).
  * **M7 = PB7 (TIM4_CH2): DShot capable (rev C)** on DMA1 S3 Ch2, which was SPI2_RX before the OSD was removed.
  * **M8 = PA0 (TIM5_CH1): PWM/servo only.** Its only request (DMA1 S2 Ch6) collides with M2.
* **LED strip = PA8 (TIM1_CH1), DMA2 S6** (SpeedyBee F405 V4).
* **ADC: VBAT PC0, CURR PC1, RSSI PC5** (SpeedyBee F405 V4 / Foxeer F405 V2).
* **Gyro 1 (ICM-42688-P): CS PA4, INT PC4 (EXTI4)** (SpeedyBee F405 V3/V4, Foxeer F405 V2). **Gyro 2 (BMI270): CS PA15, INT PC14 (EXTI14).**
* **PC13/PC14/PC15 (low-drive) carry only CMOS-level loads:**
  * PC13 = CAM_SEL output into a TS5A3159A IN pin (static, a few pF).
  * PC14 = GYRO2_INT input.
  * PC15 = VTX_PWR_EN output into the gate of Q2 (NX7002AK, Ciss 15-20 pF) through 1k, static; DC load 33 uA into the 100k gate pulldown (rev C, D-04).
  * No LEDs, no chip selects, and no large-gate FETs on PC13-15 (G0-08). A single small-signal FET gate through 1k is a static capacitive load.
* **Beeper on PB2/BOOT1.** BOOT1 needs a 10k pulldown for ROM DFU, and the same resistor holds the N-MOSFET gate low (silent) through reset. BF drives PB2 only after boot, so the strap is sampled correctly.
* **ESC telemetry on UART4_RX (PA1).** UART4 is RX-only; telemetry needs RX only.
* **Betaflight must run `dshot_bitbang = OFF`, `dshot_burst = OFF`.** On F4, bit-bang turns on automatically once bidir is enabled. It needs TIM1/TIM8 and disables SPI DMA on DMA2.

## 2. Full LQFP-64 pin table

AF numbers are from the ST GPIO database (DS8626 Table 9). "DMA" is the stream/channel Betaflight uses with this config.
Rev C: 47 of 51 I/O pins are used. PC2, PC3, PB12, PB13 (ex-SPI2/OSD) are not connected (pulldowns removed in D-24).

| Pin | Name | Net / function | AF | Peripheral / timer ch | DMA (BF) | Notes |
|---|---|---|---|---|---|---|
| 1 | VBAT | 3V3 | - | Backup domain supply | - | No coin cell. Tie to 3V3 with a 100 nF cap to GND |
| 2 | PC13 (RTC_AF1) | CAM_SEL (PINIO2) | GPIO out PP | BF `PINIO 2` | - | Drives TS5A3159A IN (CMOS, static). Low = CAM1 (default), high = CAM2. **100k pulldown** so CAM1 is selected through reset/DFU. Low-drive pin (2 MHz / 30 pF / ≤3 mA sink, no sourcing DC loads): a CMOS input is OK (G0-08) |
| 3 | PC14 (OSC32_IN) | GYRO2_INT (BMI270 INT1) | GPIO in / EXTI14 | EXTI line 14 | - | LSE not used. **Test firmware must never enable LSE** (the backup domain stays powered via VBAT=VDD, so LSEON would survive resets until power-cycled; G0-07) |
| 4 | PC15 (OSC32_OUT) | VTX_PWR_EN (PINIO1) | GPIO out PP | BF `PINIO 1` | - | Drives the gate of Q2 (NX7002AK, via 1k) which pulls the 10 V buck (U2) EN low. **High = VTX off.** **100k gate pulldown** keeps Q2 off, so the VTX is **on** through reset/DFU/boot. Same LSE note as PC14 |
| 5 | PH0-OSC_IN | HSE_IN | - | RCC_OSC_IN 8 MHz | - | 8 MHz crystal. CL1 = CL2 ≈ 2·(CL_xtal − C_stray) |
| 6 | PH1-OSC_OUT | HSE_OUT | - | RCC_OSC_OUT | - | Crystal within ~5 mm, GND guard, no traces under it |
| 7 | NRST | NRST | - | Reset | - | 100 nF to GND. SWD pad |
| 8 | PC0 | VBAT_ADC | analog | ADC123_IN10 | ADC1 → DMA2 S4 | 10k/1k divider (36 V gives 3.27 V), 100 nF at the pin. `vbat_scale = 110` |
| 9 | PC1 | CURR_ADC | analog | ADC123_IN11 | (ADC1) | ESC connector CURR. 10k series + 10 nF (BAT54S clamp removed in D-23: the 10k limits fault current into the pin clamp to < 1 mA) |
| 10 | PC2 | UNUSED_PC2 (was SPI2_MISO) | - | - | - | **Unused** (rev C, OSD removed). no connection (100k pulldown of R-03 removed in D-24) |
| 11 | PC3 | NC (was SPI2_MOSI) | - | - | - | **Unused**, no connection (D-24) |
| 12 | VSSA | GND | - | Analog ground | - | Solid GND plane |
| 13 | VDDA | 3V3A | - | Analog supply / internal VREF+ | - | Ferrite bead from 3V3, 1 µF + 100 nF. **No VREF+ pin on LQFP-64** |
| 14 | PA0-WKUP | MOTOR8 (extra pad S8) | AF2 | TIM5_CH1 | **none** | **PWM/servo only.** TIM5_CH1 → DMA1 S2 Ch6 collides with M2. TIM5 is used by nothing else. (Was UART4_TX, so UART4 is RX-only. Can be given back with `resource MOTOR 8 NONE` + `resource SERIAL_TX 4 A00`) |
| 15 | PA1 | ESC_TLM (UART4_RX) | AF8 | UART4 | - (IRQ) | ESC connector TLM pin → BF `ESC_SENSOR` on UART4 |
| 16 | PA2 | UART2_TX | AF7 | USART2 | - | ELRS RX connector |
| 17 | PA3 | UART2_RX | AF7 | USART2 | - | ELRS RX connector, `SERIAL_RX` |
| 18 | VSS | GND | - | | - | |
| 19 | VDD | 3V3 | - | | - | 100 nF |
| 20 | PA4 | GYRO1_CS | GPIO out | SPI1 CS #1 (ICM-42688-P) | - | **10k pull-up to 3V3** |
| 21 | PA5 | SPI1_SCK | AF5 | SPI1 | - | Both IMUs |
| 22 | PA6 | SPI1_MISO | AF5 | SPI1 | SPI1 RX → DMA2 S0 | |
| 23 | PA7 | SPI1_MOSI | AF5 | SPI1 | SPI1 TX → DMA2 S3 | |
| 24 | PC4 | GYRO1_INT | GPIO in / EXTI4 | EXTI line 4 | - | ICM-42688-P INT1 |
| 25 | PC5 | RSSI_ADC | analog | ADC12_IN15 | (ADC1) | 10k series + 10 nF (clamp removed, D-23) |
| 26 | PB0 | MOTOR1 | AF2 | TIM3_CH3 | DMA1 S7 Ch5 | ESC connector M1 |
| 27 | PB1 | MOTOR2 | AF2 | TIM3_CH4 | DMA1 S2 Ch5 | ESC connector M2 |
| 28 | PB2 (BOOT1) | BEEPER | GPIO out PP | BF `BEEPER` | - | N-MOSFET gate (PMV40UN2, `power.md` section 11) for the 5 V buzzer, active-high. **10k pulldown to GND (BOOT1 strap, also the gate pulldown).** Any series gate resistor (≤100 Ω) goes between the pin node and the gate, never between the pulldown and the pin. `beeper_inversion = ON` |
| 29 | PB10 | MOTOR3 | AF1 | TIM2_CH3 | DMA1 S1 Ch3 | ESC connector M3 |
| 30 | PB11 | MOTOR4 | AF1 | TIM2_CH4 | DMA1 S6 Ch3 (dmaopt 1) | ESC connector M4. opt 0 (S7) would collide with M1 |
| 31 | VCAP_1 | VCAP1 | - | Core regulator | - | 2.2 µF low-ESR (ESR < 2 Ω) to GND |
| 32 | VDD | 3V3 | - | | - | 100 nF |
| 33 | PB12 | NC (was OSD_CS) | - | - | - | **Unused**, no connection (D-24) |
| 34 | PB13 | NC (was SPI2_SCK) | - | - | - | **Unused**, no connection (D-24) |
| 35 | PB14 | STATUS_LED_BLUE (LED0) | GPIO out | BF `LED 1` | - | 3V3 → R → LED → pin (low = on) |
| 36 | PB15 | STATUS_LED_GREEN (LED1) | GPIO out | BF `LED 2` | - | Same as LED0 |
| 37 | PC6 | UART6_TX | AF8 | USART6 | - | Spare UART (full) |
| 38 | PC7 | UART6_RX | AF8 | USART6 | - | Spare UART (full) |
| 39 | PC8 | MOTOR5 (extra pad S5) | AF3 | TIM8_CH3 | DMA2 S2 Ch0 | DShot + bidir |
| 40 | PC9 | MOTOR6 (extra pad S6) | AF3 | TIM8_CH4 | DMA2 S7 Ch7 | DShot + bidir |
| 41 | PA8 | LED_STRIP | AF1 | TIM1_CH1 | DMA2 S6 Ch0 | WS2812 DIN via ~220-330 Ω. **SN74LV1T125 3.3→5 V buffer (VCC = 5 V) with a DNP 0 Ω bypass** (D-07) (WS2812 VIH ≈ 3.5 V; G0-10) |
| 42 | PA9 | UART1_TX | AF7 | USART1 | - | HD VTX connector TX |
| 43 | PA10 | UART1_RX | AF7 | USART1 | - | HD VTX connector RX |
| 44 | PA11 | USB_DM | AF10 | OTG_FS_DM | - | Via ESD array, 90 Ω diff |
| 45 | PA12 | USB_DP | AF10 | OTG_FS_DP | - | Internal pull-up, no external 1.5k |
| 46 | PA13 | SWDIO | AF0 | SWD | - | **Reserved.** Test pad |
| 47 | VCAP_2 | VCAP2 | - | Core regulator | - | 2.2 µF low-ESR (ESR < 2 Ω) to GND |
| 48 | VDD | 3V3 | - | | - | 100 nF |
| 49 | PA14 | SWCLK | AF0 | SWD | - | **Reserved.** Test pad |
| 50 | PA15 | GYRO2_CS | GPIO out | SPI1 CS #2 (BMI270) | - | **10k pull-up to 3V3** (on top of the JTDI internal pull-up at reset) |
| 51 | PC10 | UART3_TX | AF7 | USART3 | - | GPS connector. GPS supply = buck-only 5 V rail, dead during USB-only DFU (G0-03) |
| 52 | PC11 | UART3_RX | AF7 | USART3 | - | GPS connector |
| 53 | PC12 | UART5_TX | AF8 | UART5 | - | Spare UART (full), pad |
| 54 | PD2 | UART5_RX | AF8 | UART5 | - | Spare UART (full), pad. **Optional DNP 0R from HD-VTX connector pin 6 (SBUS/R2), no inverter** (only works for non-inverted R2 signals; inverted SBUS needs an external inverter) |
| 55 | PB3 | SPI3_SCK | AF6 | SPI3 | - | W25N01GV CLK |
| 56 | PB4 | SPI3_MISO | AF6 | SPI3 | SPI3 RX → DMA1 S0 | W25N01GV DO |
| 57 | PB5 | SPI3_MOSI | AF6 | SPI3 | SPI3 TX → DMA1 S5 | W25N01GV DI |
| 58 | PB6 | FLASH_CS | GPIO out | SPI3 CS | - | **10k pull-up to 3V3.** Flash /WP, /HOLD → 3V3 via 10k |
| 59 | PB7 | MOTOR7 (extra pad S7) | AF2 | TIM4_CH2 | DMA1 S3 Ch2 | **DShot + bidir capable (rev C):** DMA1 S3 was SPI2_RX, freed by removing the OSD. TIM4 is used by nothing else |
| 60 | BOOT0 | BOOT0 | - | Boot strap | - | 10k pulldown. BOOT button to 3V3 |
| 61 | PB8 | I2C1_SCL | AF4 | I2C1 | - | Baro, mag, GPS connector. 2.2k pull-up |
| 62 | PB9 | I2C1_SDA | AF4 | I2C1 | - | 2.2k pull-up |
| 63 | VSS | GND | - | | - | |
| 64 | VDD | 3V3 | - | | - | 100 nF + shared 4.7 µF bulk |

Pin count: 51 I/O + VBAT + NRST + BOOT0 + 2 VCAP + 4 VDD + 2 VSS + VDDA + VSSA = 64. ✓ Rev C: 47 I/O used, 4 unused (PC2, PC3, PB12, PB13: no connection, no pads).

### 2.1 EXTI line allocation

| EXTI line | Pin | User |
|---|---|---|
| 4 | PC4 | GYRO_1 INT (ICM-42688-P) |
| 14 | PC14 | GYRO_2 INT (BMI270) |
| all others | - | unused |

Lines 4 and 14 differ. No other pin numbered 4 or 14 is EXTI-configured (PA4 = CS output, PB14 = LED output). ✓

### 2.2 Peripheral → pin summary

| Peripheral | Pins | AF |
|---|---|---|
| USART1 (HD VTX) | TX PA9, RX PA10 | AF7 |
| USART2 (ELRS) | TX PA2, RX PA3 | AF7 |
| USART3 (GPS) | TX PC10, RX PC11 | AF7 |
| UART4 (ESC telemetry, RX-only) | RX PA1 (TX pin PA0 is M8) | AF8 |
| UART5 (spare) | TX PC12, RX PD2 | AF8 |
| USART6 (spare) | TX PC6, RX PC7 | AF8 |
| SPI1 (IMUs) | SCK PA5, MISO PA6, MOSI PA7, CS PA4 / PA15 | AF5 |
| SPI2 | unused (rev C) | - |
| SPI3 (W25N01GV) | SCK PB3, MISO PB4, MOSI PB5, CS PB6 | AF6 |
| I2C1 | SCL PB8, SDA PB9 | AF4 |
| USB OTG FS | PA11, PA12 (no VBUS-detect pin) | AF10 |
| SWD | PA13, PA14, NRST | AF0 |
| Motors (DShot + bidir) | M1 PB0, M2 PB1 (TIM3 CH3/CH4, AF2), M3 PB10, M4 PB11 (TIM2 CH3/CH4, AF1) | |
| Extra outputs | M5 PC8, M6 PC9 (TIM8 CH3/CH4, AF3, DShot), M7 PB7 (TIM4_CH2, AF2, DShot, rev C), M8 PA0 (TIM5_CH1, AF2, PWM only) | |
| LED strip | PA8 TIM1_CH1 | AF1 |
| ADC1 | PC0 IN10, PC1 IN11, PC5 IN15 | analog |
| GPIO | BEEPER PB2, LEDs PB14/PB15, PINIO1 PC15, PINIO2 PC13, INTs PC4/PC14 | - |

### 2.3 Timer usage

| Timer | Channels | Function | Notes |
|---|---|---|---|
| TIM1 | CH1 (PA8) | LED strip | alone on TIM1 |
| TIM2 | CH3 (PB10), CH4 (PB11) | M3, M4 DShot | motors only |
| TIM3 | CH3 (PB0), CH4 (PB1) | M1, M2 DShot | motors only |
| TIM4 | CH2 (PB7) | M7 (DShot capable, rev C) | alone on TIM4, so its rate is independent |
| TIM5 | CH1 (PA0) | M8 PWM/servo | alone on TIM5, so its rate is independent |
| TIM8 | CH3 (PC8), CH4 (PC9) | M5, M6 | M5/M6 share one protocol/rate |
| TIM9-14 | - | unused | |

## 3. DMA allocation (proof of no conflicts)

BF 4.5 allocation order: `motorDevInit` → `adcInit` → `ledStripInit` → `spiInitBusDMA` (EARLY variant on F405). UART DMA is off by default, and I2C never uses DMA. All streams are pinned explicitly in the config. Mappings are RM0090 Tables 42/43 (as encoded by BF/ArduPilot/INAV and confirmed by the audit).

### 3.1 DMA1

| Stream | Channel | Request | User | BF setting |
|---|---|---|---|---|
| S0 | Ch0 | SPI3_RX | SPI3 RX (flash) | `dma SPI_SDI 3 0` |
| S1 | Ch3 | TIM2_UP / TIM2_CH3 | M3 PB10 | `dma pin B10 0` |
| S2 | Ch5 | TIM3_CH4 / TIM3_UP | M2 PB1 | `dma pin B01 0` |
| S3 | Ch2 | TIM4_CH2 | M7 PB7 (rev C) | `dma pin B07 0` |
| S4 | - | - | free (rev C) | - |
| S5 | Ch0 | SPI3_TX | SPI3 TX (flash) | `dma SPI_SDO 3 0` |
| S6 | Ch3 | TIM2_CH2 / TIM2_CH4 | M4 PB11 | `dma pin B11 1` |
| S7 | Ch5 | TIM3_CH3 | M1 PB0 | `dma pin B00 0` |

7 used once each, S4 free. ✓

### 3.2 DMA2

| Stream | Channel | Request | User | BF setting |
|---|---|---|---|---|
| S0 | Ch3 | SPI1_RX | SPI1 RX (IMUs) | `dma SPI_SDI 1 0` |
| S1 | - | - | free | - |
| S2 | Ch0 | TIM8_CH1/CH2/CH3 | M5 PC8 | `dma pin C08 0` |
| S3 | Ch3 | SPI1_TX | SPI1 TX (IMUs) | `dma SPI_SDO 1 0` |
| S4 | Ch0 | ADC1 | ADC1 | `dma ADC 1 1` |
| S5 | - | - | free | - |
| S6 | Ch0 | TIM1_CH1/CH2/CH3 | LED strip PA8 | `dma pin A08 0` |
| S7 | Ch7 | TIM8_CH4/TRIG/COM | M6 PC9 | `dma pin C09 0` |

6 used once each, S1/S5 free. ✓

### 3.3 Per-requester view

| Requester | Pin | Options (BF opt index) | Chosen | Reason |
|---|---|---|---|---|
| M1 TIM3_CH3 | PB0 | 0: DMA1 S7 Ch5 | S7 | only option |
| M2 TIM3_CH4 | PB1 | 0: DMA1 S2 Ch5 | S2 | only option |
| M3 TIM2_CH3 | PB10 | 0: DMA1 S1 Ch3 | S1 | only option |
| M4 TIM2_CH4 | PB11 | 0: DMA1 S7 Ch3, 1: DMA1 S6 Ch3 | **opt1 S6** | opt0 collides with M1 |
| M5 TIM8_CH3 | PC8 | 0: DMA2 S2 Ch0, 1: DMA2 S4 Ch7 | S2 | opt1 collides with ADC1 |
| M6 TIM8_CH4 | PC9 | 0: DMA2 S7 Ch7 | S7 | only option |
| **M7 TIM4_CH2** | **PB7** | 0: DMA1 S3 Ch2 | **S3 (rev C)** | SPI2 removed, S3 free |
| **M8 TIM5_CH1** | **PA0** | 0: DMA1 S2 Ch6 | **NONE** | S2 = M2, so PWM/servo only |
| LED strip TIM1_CH1 | PA8 | 0: DMA2 S6 Ch0, 1: S1 Ch6, 2: S3 Ch6 | S6 | |
| SPI1 TX / RX | PA7 / PA6 | TX 0: S3, 1: S5 · RX 0: S0, 1: S2 (DMA2 Ch3) | S3 / S0 | RX opt1 collides with M5 |
| SPI3 TX / RX | PB5 / PB4 | TX 0: S5, 1: S7 · RX 0: S0, 1: S2 (DMA1 Ch0) | S5 / S0 | opt1s collide with M1/M2 |
| ADC1 | PC0/PC1/PC5 | 0: DMA2 S0, 1: DMA2 S4 (Ch0) | **opt1 S4** | opt0 collides with SPI1 RX. Must be explicit (default is unused) |
| UART1-6, I2C1 | - | - | none | BF defaults |

Every stream appears at most once in "Chosen". **No DMA conflict.** ✓

* With a quad mixer, BF only claims M1-M4 DMA. M5/M6 streams are reserved anyway.
* **M8 can never run DShot in Betaflight** (rev C: M7 can). A 7-motor DShot mixer works; an 8-motor DShot mixer fails to initialise M8. Use M8 as a servo (`resource SERVO n A00`) or with PWM/Oneshot.
* Bidir DShot reuses each motor's stream. `dshot_burst = OFF`. DMA2 only targets APB2 peripherals (bit-bang off), so it stays clear of the F40x DMA2 AHB/APB2 erratum.

## 4. Serial port plan

| BF port | Pins | Use | BF function |
|---|---|---|---|
| UART1 (0) | PA9/PA10 | HD VTX connector TX/RX | MSP + VTX_MSP |
| UART2 (1) | PA2/PA3 | ELRS RX | SERIAL_RX (CRSF) |
| UART3 (2) | PC10/PC11 | GPS (+ I2C1 on the same connector) | GPS |
| UART4 (3) | PA1 RX only | ESC connector TLM | ESC_SENSOR |
| UART5 (4) | PC12/PD2 | **spare, full** (PD2 optionally gets HD SBUS/R2 via DNP 0R) | - |
| USART6 (5) | PC6/PC7 | **spare, full** | - |
| VCP (20) | USB | | MSP |

Requirement "6 UARTs: ELRS, GPS, HD VTX, ESC telemetry RX, 2 spare" is met: 2 full spares (UART5, USART6), and ESC telemetry gets the RX it needs.

## 5. Extra outputs: requirement met (4 pads)

| Pad | Pin | Timer | DShot / bidir | Servo/PWM |
|---|---|---|---|---|
| S5 | PC8 | TIM8_CH3 | yes (DMA2 S2) | yes |
| S6 | PC9 | TIM8_CH4 | yes (DMA2 S7) | yes |
| S7 | PB7 | TIM4_CH2 | **yes (DMA1 S3, rev C)** | yes |
| S8 | PA0 | TIM5_CH1 | **no (no DMA)** | yes |

The requirement reads "4 extra motor/servo pads", so S7/S8 satisfy it. Rev C: hepta-DShot is possible, octo-DShot is **not** (M8 has no DMA). If a pilot needs an 8th DShot output, the LED_STRIP pad (PA8, TIM1_CH1, DMA2 S6) can be remapped in the CLI.

Deviation from the original architect brief: the brief asked for "all 6 UARTs TX+RX". **UART4 is RX-only** in this map, because its TX pin is M8. The lead accepted this by choosing the G0-01 remap. The CLI can swap it back.

## 6. Polarity / default-state table

| Signal | Pin | Hardware polarity | Reset state (hardware) | BF setting | Behaviour |
|---|---|---|---|---|---|
| BEEPER | PB2 | High = buzzer on (N-FET gate) | 10k pulldown (BOOT1 strap) → silent | `beeper_inversion = ON`, `beeper_od = OFF` | BF writes HIGH for beep when inverted (`sound_beeper.c:85`) |
| LED0 / LED1 | PB14 / PB15 | Low = on (sink) | off | `led_inversion = 0` | BF writes LOW for on (`light_led.c:92`) |
| VTX_PWR_EN (PINIO1) | PC15 | **High = VTX off** (Q2 pulls 10 V buck EN low) | 100k gate pulldown → VTX **on** | `pinio_config 1 = 1`, `pinio_box 1 = 40` (USER1) | VTX on through reset and after boot. USER1 active → pin high → VTX off |
| CAM_SEL (PINIO2) | PC13 | Low = CAM1 | 100k pulldown → CAM1 | `pinio_config 2 = 1`, `pinio_box 2 = 41` (USER2) | USER2 active → CAM2 |

## 7. Schematic requirements: boot, power and pull resistors

* **VDD (19, 32, 48, 64):** 100 nF each + one 4.7 µF bulk.
* **VDDA (13):** ferrite bead from 3V3, 1 µF + 100 nF. **VSSA (12)** to GND. **No VREF+ pin** (bonded to VDDA inside). A 1% 3V3 regulator is recommended for ADC accuracy.
* **VBAT (1):** tie to 3V3 with 100 nF.
* **VCAP_1 (31), VCAP_2 (47):** 2.2 µF each, low-ESR ceramic (ESR < 2 Ω), X5R/X7R, ≥6.3 V, right at the pin. Mandatory.
* **BOOT0 (60):** 10k pulldown. BOOT button to 3V3.
* **PB2/BOOT1 (28):** 10k pulldown to GND (ROM DFU strap). This is also the BEEPER FET gate pulldown.
* **NRST (7):** 100 nF to GND. SWD pad.
* **HSE:** 8 MHz crystal on PH0/PH1. Load caps per crystal CL.
* **Chip-select pull-ups (G0-04): 10k to 3V3 on GYRO1_CS (PA4), GYRO2_CS (PA15), FLASH_CS (PB6).** (OSD_CS removed in rev C.) These keep every SPI device deselected until firmware drives the CS lines. Bring-up check from the audit: cold-boot repeatedly and confirm both IMUs always detect. The BMI270 starts in I2C mode until its first CS rising edge. If detection is flaky, swap the gyro_1/gyro_2 order so the BMI270 is probed first.
* **Default-state pulldowns:** 100k on CAM_SEL (PC13) and 100k on the Q2 **gate side** of the 1k series resistor (matches `power.md` section 4; PC15 still reads low through the 1k).
* **I2C1:** 2.2k pull-ups to 3V3 on SCL/SDA.
* **Flash:** /WP and /HOLD to 3V3 via 10k.
* **ADC inputs from off-board (CURR, RSSI):** series 10k + 10 nF. The BAT54S clamps of G0-09 were removed in D-23 (series resistor limits the injected current).
* **LED strip:** SN74LV1T125 powered from 5 V, DNP 0 Ω bypass, then 330 Ω series.
* **HD-VTX connector pin 6 (SBUS/R2):** not connected by default. DNP 0R to UART5_RX (PD2). No inverter.
* **GPS 5 V:** from the buck-only 5 V rail (not the USB OR-ed rail), so the GPS is off during USB-only DFU and can't disturb the ROM bootloader on USART3 (G0-03).
* **Test firmware:** never enable LSE/RTC (PC14/PC15 are GPIO).
* **ROM DFU:** enter DFU on **USB power only**. With a battery connected the VTX is on by default and drives PA10 (USART1_RX, a bootloader port), which can capture the ROM bootloader (re-audit R-08). BF's `bl` command enters the same ROM bootloader, so it needs USB power only as well (Gate 6 m-2).

## 8. Open questions

1. **IIS2MDC fixed address 0x1E** collides with HMC5883L-class GPS mags on the external I2C pads. Also, **INAV has no IIS2MDC/LIS2MDL driver** (see `inav_target.md`). Do we keep the onboard mag?
2. **SBUS from DJI/Walksnail is inverted.** The DNP-0R path to PD2 has no inverter, so it only suits non-inverted R2 use. Is an inverter footprint wanted later?
3. Gyro alignment and `ibata_scale` are placeholders until placement and ESC are fixed.
4. RM0090 and AN2606 PDFs should be filed under `datasheets/` from another network before Gate 1 (G0-13).

## 9. Net names for schematic

MCU-side net name for every pin. Off-board-side nets (after series resistors, buffers or connectors) may get suffixes such as `_PAD` or `_CONN`, but the MCU pin net uses exactly these names.

| Pin | MCU pin | Net name |
|---|---|---|
| 1 | VBAT | 3V3 |
| 2 | PC13 | CAM_SEL |
| 3 | PC14 | GYRO2_INT |
| 4 | PC15 | VTX_PWR_EN |
| 5 | PH0 | HSE_IN |
| 6 | PH1 | HSE_OUT |
| 7 | NRST | NRST |
| 8 | PC0 | VBAT_ADC |
| 9 | PC1 | CURR_ADC |
| 10 | PC2 | UNUSED_PC2 |
| 11 | PC3 | UNUSED_PC3 |
| 12 | VSSA | GND |
| 13 | VDDA | 3V3A |
| 14 | PA0 | MOTOR8 |
| 15 | PA1 | ESC_TLM |
| 16 | PA2 | UART2_TX |
| 17 | PA3 | UART2_RX |
| 18 | VSS | GND |
| 19 | VDD | 3V3 |
| 20 | PA4 | GYRO1_CS |
| 21 | PA5 | SPI1_SCK |
| 22 | PA6 | SPI1_MISO |
| 23 | PA7 | SPI1_MOSI |
| 24 | PC4 | GYRO1_INT |
| 25 | PC5 | RSSI_ADC |
| 26 | PB0 | MOTOR1 |
| 27 | PB1 | MOTOR2 |
| 28 | PB2 | BEEPER |
| 29 | PB10 | MOTOR3 |
| 30 | PB11 | MOTOR4 |
| 31 | VCAP_1 | VCAP1 |
| 32 | VDD | 3V3 |
| 33 | PB12 | UNUSED_PB12 |
| 34 | PB13 | UNUSED_PB13 |
| 35 | PB14 | STATUS_LED_BLUE |
| 36 | PB15 | STATUS_LED_GREEN |
| 37 | PC6 | UART6_TX |
| 38 | PC7 | UART6_RX |
| 39 | PC8 | MOTOR5 |
| 40 | PC9 | MOTOR6 |
| 41 | PA8 | LED_STRIP |
| 42 | PA9 | UART1_TX |
| 43 | PA10 | UART1_RX |
| 44 | PA11 | USB_DM |
| 45 | PA12 | USB_DP |
| 46 | PA13 | SWDIO |
| 47 | VCAP_2 | VCAP2 |
| 48 | VDD | 3V3 |
| 49 | PA14 | SWCLK |
| 50 | PA15 | GYRO2_CS |
| 51 | PC10 | UART3_TX |
| 52 | PC11 | UART3_RX |
| 53 | PC12 | UART5_TX |
| 54 | PD2 | UART5_RX |
| 55 | PB3 | SPI3_SCK |
| 56 | PB4 | SPI3_MISO |
| 57 | PB5 | SPI3_MOSI |
| 58 | PB6 | FLASH_CS |
| 59 | PB7 | MOTOR7 |
| 60 | BOOT0 | BOOT0 |
| 61 | PB8 | I2C1_SCL |
| 62 | PB9 | I2C1_SDA |
| 63 | VSS | GND |
| 64 | VDD | 3V3 |

Power net names `3V3`, `3V3A` and `GND` are upper-case alphanumerics (no `+` sign) so they meet the UPPER_SNAKE rule. If the schematic tool needs names starting with a letter, use `VCC_3V3` / `VCC_3V3A` consistently instead.
