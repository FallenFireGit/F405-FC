# Gate 1 schematic review: Sensors / Video / Peripherals (independent reviewer)

Date: 2026-10-11. Reviewer: fresh, independent Gate 1 reviewer (sensors, video, peripherals). Nothing else in the repo was modified.

## Scope

- Sensors sheet: U6 ICM-42688-P, U7 BMI270, U8 BMP390, U9 IIS2MDC (KiCad `Sensor_Magnetic:LIS2MDL` symbol), U10 W25N01GVZEIG.
- Video sheet: U11 TS5A3159A camera switch, U12 SN74LV1T125 LED-strip buffer, video and LED pads.
- Connectors sheet (peripheral part only): J1 USB4105 + U13 USBLC6-2SC6, J2-J5 JST-SH, Q1/D9 buzzer driver.
- Out of scope: power stage, MCU pin-mux/DMA, PCB layout.

## Method

1. Read `design/circuit.py` in full. The custom symbols are at lines 132-161 and the sensor/video/connector instances at lines 336-456.
2. Exported the netlist from `kicad/F405FC.kicad_sch` with `kicad-cli sch export netlist`. I then dumped every pin-to-net mapping for U6-U13, J1-J5, Q1 and D9. The schematic matches `circuit.py` pin for pin. `kicad/erc.rpt` shows 0 errors and 0 warnings.
3. Dumped the stock KiCad symbols (`LIS2MDL`, `74AHCT1G125`→`74LVC1G125`, `USB_C_Receptacle_USB2.0_16P`) to get their pin numbers.
4. Datasheets on disk (pdftotext):
   - ICM-42688-P DS-000347 r1.2: p.19 Table 9 and p.20 Table 10.
   - BMI270 DS000-08: §6.3 p.~120 and §7.1 Table 22 p.135.
   - BMP390 DS002 r1.7: §5.1 p.~37, §5.2 and Table 52 p.46, Fig.25 p.48.
   - TS5A3159A SCDS200F: §5 pin table p.3, §6.1 abs max, the 3.3 V electrical table and Table 1 (function table).
   - USB4105 drawing: the pin-assignment table.
5. Betaflight sources in `datasheets/bf_src/`:
   - `barometer_bmp388.c:50-52`: address 0x76 and chip ID 0x60.
   - `compass_lis2mdl.c:35,48-49,77`: address 0x1E and WHO_AM_I 0x40.
6. IIS2MDC and W25N01GV datasheets are not on disk. For these I used WebSearch snippets: an alldatasheet mirror of the ST IIS2MDC DS, plus ST AN5080 and AN5069. Every item that rests only on those snippets is marked **unverified**.
7. betaflight.com is unreachable (DNS). The Betaflight connector-standard details come from search snippets only and are **unverified**.

## Checks passed

| # | Check | Evidence |
|---|---|---|
| 1 | ICM-42688-P pin numbers: 1 AP_SDO, 2/3 RESV, 4 INT1, 5 VDDIO, 6 GND, 7 RESV, 8 VDD, 9 INT2/FSYNC, 10/11 RESV, 12 AP_CS, 13 AP_SCLK, 14 AP_SDI. All match | circuit.py:132-138 vs DS Table 9 p.19 |
| 2 | ICM unused pins: RESV 2/3/10/11 go to GND (allowed: "NC or GND") and RESV 7 goes to GND (required). FSYNC pin 9 goes to GND ("Connect to GND if FSYNC not used") | circuit.py:338-339; DS Table 9 |
| 3 | ICM caps: 100 nF + 2.2 µF (VDD) and 10 nF (VDDIO) on 3V3_IMU, which matches the DS BOM (C1 0.1 µF, C2 2.2 µF, C3 10 nF). VDD and VDDIO are the same rail, so placement must put C3 at pin 5 | circuit.py:342-344; DS p.20 table |
| 4 | BMI270 pin numbers: 1 SDO, 2 ASDx, 3 ASCx, 4 INT1, 5 VDDIO, 6 GNDIO, 7 GND, 8 VDD, 9 INT2, 10 OCSB, 11 OSDO, 12 CSB, 13 SCx, 14 SDx. All match | circuit.py:139-145 vs Table 22 p.135 |
| 5 | BMI270 unused pins are left unconnected: ASDx/ASCx ("VDDIO or DNC; do not connect to GND"), OCSB/OSDO (DNC), INT2 (DNC if unused). All are compliant | circuit.py:347; Table 22 notes */**/*** |
| 6 | BMI270 decoupling: 2 x 100 nF on 3V3_IMU ("100 nF at pin 5 and pin 8") | circuit.py:350-351; DS §7.2 |
| 7 | BMP390 pin numbers: 1 VDDIO, 2 SCK, 3 VSS, 4 SDI, 5 SDO, 6 CSB, 7 INT, 8/9 VSS, 10 VDD. All match | circuit.py:146-151 vs Table 52 p.46 |
| 8 | BMP390 interface straps: CSB is hard-wired to VDDIO (I2C; the DS also allows a direct tie). SDO goes to GND, giving 0x76, which equals BF `BMP388_I2C_ADDR 0x76`. BF accepts chip ID 0x60 (BMP390). INT is left NC (DS: "host INT input or DNC"). Decoupling is 2 x 100 nF as recommended | circuit.py:353-357; DS §5.1, §5.2, Fig.25 notes; bf_src/barometer_bmp388.c:50-52,277 |
| 9 | IIS2MDC pins (KiCad LIS2MDL symbol): 1 SCL, 2 NC, 3 CS, 4 SDA, 5 C1, 6 GND, 7 DRDY, 8 GND, 9 VDD, 10 VDD_IO, 11/12 NC. These agree with the IIS2MDC pin table snippet, where pins 2/11/12 are internally NC and may be tied anywhere or left open. CS goes to 3V3, which selects I2C (fixed address 0x1E, equal to BF `LIS2MDL_MAG_I2C_ADDRESS`). C1 = 220 nF to GND, as recommended. **Unverified** (snippet only, no DS on disk) | circuit.py:358-363; KiCad lib dump; bf_src/compass_lis2mdl.c:35 |
| 10 | W25N01GV WSON-8: 1 /CS, 2 DO, 3 /WP, 4 GND, 5 DI, 6 CLK, 7 /HOLD, 8 VCC, EP to GND. This matches the standard Winbond 8-pin SPI ordering. /WP and /HOLD each have a 10k pull-up to 3V3, and /CS has a 10k pull-up (circuit.py:318-319). **Pin numbers unverified**: no DS on disk, and the search returned no pin table | circuit.py:152-156,366-373 |
| 11 | Each IMU has its own CS (PA4 / PA15, each with a 10k pull-up) and its own INT on its own EXTI line (PC4 = EXTI4, PC14 = EXTI14), which meets requirements.md:22. AP_SDO and SDO share MISO, and both are tri-state when deselected | circuit.py:284-285,318-319,337-347 |
| 12 | IMU supply: both IMUs are on 3V3_IMU (LP5907), within VDD 1.71-3.6 V. Baro, mag and flash are on 3V3 | circuit.py:257-261 |
| 13 | TS5A3159A pins: 1 NO, 2 GND, 3 NC, 4 COM, 5 V+, 6 IN. These match the DBV pin table. IN low gives COM-NC, so NC = CAM1 and the 100k pulldown selects CAM1 through reset/DFU. This matches pinmap.md:69 (PINIO2 high = CAM2) | circuit.py:157-161,378-382; DS p.3, Table 1 |
| 14 | TS5A3159A at V+ = 3.3 V: IN VIH is 2.4 V min, which a 3.3 V STM32 output meets. Ron is 1.2 Ω typ / 1.5 Ω max at 25 °C, and BW is 100 MHz into 50 Ω. Ron is negligible against a 75 Ω video load, and the bandwidth is far above the 4.2-6 MHz composite video band. Ccom(on) is 55 pF, which is acceptable. A 1 Vpp DC-referenced signal (0-1.3 V) is inside the 0..V+ range. For AC-coupled sources see G1S-03 | DS 3.3 V electrical table |
| 15 | LED-strip buffer: 74LVC1G125 symbol pins 1 ~OE, 2 A, 3 GND, 4 Y, 5 VCC, the same as the SN74LV1T125 DBV pinout. ~OE goes to GND (always enabled, which is the correct polarity). VCC = 5 V, and the output passes through a 330 Ω series resistor to the DIN pad. The 100 nF decoupler is on 5V | circuit.py:392-397; netlist U12 |
| 16 | Buzzer: Q1 (PMV40UN2, SOT-23) is wired as 2N7002 symbol G1/S2/D3, the standard Nexperia SOT-23 FET pinout. The gate is driven through 100 Ω from the PB2 node, which carries the 10k BOOT1 pulldown, so the beeper stays silent through reset (pinmap.md:95). D9 Schottky flyback runs from BUZ_N to 5V with the correct polarity. Pads are P13 (5V) and P14 (BUZ_N) | circuit.py:312,450-458 |
| 17 | USB-C: the netlist pins are A6/B6 = D+, A7/B7 = D-, A5 = CC1, B5 = CC2, A4/A9/B4/B9 = VBUS, A1/A12/B1/B12 = GND, SBU NC, SH = GND. These match the USB4105 drawing table (A6 Dp1, A7 Dn1, B6 Dp2, B7 Dn2, A5 CC1, B5 CC2). Both CC pins have 5.1k to GND. USBLC6-2SC6 is wired I/O1 (1,6) = D-, I/O2 (3,4) = D+, 5 = VBUS, 2 = GND | netlist J1/U13; USB4105_drawing.pdf |
| 18 | JST pinouts match requirements.md:29-31: ESC = VBAT GND CURR M1-M4 TLM, HD VTX = 10V GND TX RX GND SBUS/R2, GPS = 5V GND TX RX SDA SCL, ELRS = 5V GND TX RX. The mounting pins go to GND | netlist J2-J5 |
| 19 | The schematic (kicad_sch) matches circuit.py, and ERC is clean | netlist dump; kicad/erc.rpt |

## Findings

| ID | Sev | Finding | Evidence | Fix |
|---|---|---|---|---|
| G1S-01 | MINOR | **Shared SPI1 bus with the BMI270 in I2C mode until its first CSB rising edge.** After power-up the BMI270 primary interface is I2C. SCx/SDx are on SPI1_SCK/MOSI, and SDO (its I2C address bit) is on the floating/ICM-driven MISO. ICM-42688-P traffic issued before BF toggles GYRO2_CS can be decoded as I2C. A START condition appears whenever MOSI falls while SCK idles high (SPI mode 3). If a first byte of 0xD0/0xD2 (0x68/0x69 + W) then follows, the BMI270 ACKs and pulls MOSI low against the MCU. The reverse also applies: the ICM-42688-P keeps its I2C slave enabled (addr 0x68/0x69 via AP_AD0 = MISO) until UI_SIFS_CFG = 11. The probability is low but not zero, and it is firmware-ordering dependent. I did not verify BF's detection order. | BMI270 DS §6.3 ("CSB rising edge is needed before starting SPI"); ICM DS INTF_CONFIG0 UI_SIFS_CFG 11 = disable I2C; circuit.py:337-347 | No schematic change required. Gate-3/bring-up: confirm BF toggles both CS lines (dummy CHIP_ID read) before any burst traffic, and that the icm426xx driver sets UI_SIFS_CFG = 11. Optionally set BMI270 NV_CONF.spi_en. If a respin happens, putting the BMI270 on its own SPI bus removes the issue |
| G1S-02 | MINOR | **6-pin GPS and 6-pin HD VTX connectors are physically identical (SM06B-SRSS-TB), and pin 1 is 10V on J3 vs 5V on J4.** Plugging a GPS into J3 puts 10 V (and VBAT on a U2 high-side failure, see D-04) on the GPS 5 V input, which will likely destroy it. The Betaflight connector standard v2.0 reportedly deprecated the 6-pin UART+I2C GPS connector for exactly this reason (**unverified**: search snippet only, betaflight.com unreachable). | circuit.py:427-435; requirements.md:29,31 | Minimum: large, unambiguous silkscreen ("VTX 10V" / "GPS 5V") and placement on different board edges. Better: move the GPS to a 4-pin (UART) connector plus I2C pads, or use a different pin count for the GPS. This is a requirement deviation, so the lead must log it |
| G1S-03 | MINOR | **Camera switch analog range is 0..V+ (3.3 V). Negative video excursions are not passed.** A DC-referenced composite signal (sync tip ≥ 0 V, 1 Vpp) is fine. But if a camera output is AC-coupled into a VTX input terminated to GND, the sync tips swing below 0 V. Below about -0.3 to -0.5 V the switch's port diodes conduct, which clips the sync and violates abs max VCOM/VNC/VNO ≥ -0.5 V (IK limit -50 mA). There is also no ESD protection on the exposed CAM1/CAM2/VTX video pads. | TS5A3159A DS §6.1 abs max and the 3.3 V table (analog range 0..V+); circuit.py:378-386 | Bench-check with representative analog cameras and VTXs at Gate 3. If the sync is clipped, add a DC-restore/bias (e.g. a series cap plus a bias to about 0.5-1 V on each input) or document "DC-coupled cameras only". Consider a low-cap ESD diode on the video pads |
| G1S-04 | MINOR | **IIS2MDC decoupling is lighter than ST's guidance.** The design has 100 nF + 1 µF on 3V3 at the mag. The ST app-note snippet recommends 100 nF ceramic + 10 µF close to pin 9 (Vdd), because the set/reset pulses through C1 draw high current. **Unverified** (snippet from AN5069/AN5080 via search, no DS on disk). | circuit.py:363-365 | Change the 1 µF to a 4.7-10 µF 0603/0805 X5R, or confirm against the IIS2MDC DS before Gate 2. Place C220n (C1 pin) next to pins 5/6 |
| G1S-05 | INFO | IIS2MDC and W25N01GV pin numbers were checked only against search snippets and the standard Winbond ordering (see checks 9 and 10). The stock `Package_LGA:LGA-12_2x2mm_P0.5mm` pad numbering vs the IIS2MDC land pattern is likewise unverified. | review/footprint_build_notes.md (W25N footprint marked UNVERIFIED) | Gate 2 must confirm both pinouts and footprints against the official ST and Winbond datasheets |
| G1S-06 | INFO | ICM-42688-P pin 9 (INT2/FSYNC/CLKIN) is tied to GND. This is DS-compliant, but it rules out the external 32 kHz CLKIN option that some newer BF versions support. INT2 must never be enabled as an output in firmware, or it will drive against GND. | circuit.py:338; DS Table 9 | Accept. Optionally route pin 9 to GND through a 0 Ω resistor so CLKIN can be added later |
| G1S-07 | INFO | When the DNP R0 bypass (LED_STRIP to LED_DIN_BUF) is fitted, U12 must be removed. Otherwise PA8 and the buffer output fight. | circuit.py:396 | Add an "R0 fitted ⇒ U12 DNP" note on the Video sheet |
| G1S-08 | INFO | On USB-only power the GPS (5V, battery-only, D-02) is unpowered while I2C1 is pulled to 3V3 through 2.2k and UART3_TX may idle high. Current flows back into the GPS through its I/O clamp diodes (a few mA), which can partially power the module and load the I2C bus (baro/mag reads may fail on USB). | circuit.py:322-323,433 | Accept and document, or bench-check that baro/mag still enumerate on USB-only with a GPS plugged in |
| G1S-09 | INFO | The ESC pin order matches requirements.md:30. However, the requirement's claim that this is the "Betaflight/BLHeli standard order" could not be confirmed. One board snippet (AirBrain H743 BF wiki) shows VBAT GND CUR **TLM** M1-M4. | requirements.md:30; circuit.py:422-426 | Confirm against the target ESC pinout before PCB release, and silkscreen the order |
| G1S-10 | INFO | Documentation mismatch: decisions.md D-01 says the camera switch costs "two resistors" and routes "CAMx → VID_OUT". The schematic has one 100k pulldown, and the net is named VTX_VID. | decisions.md D-01; circuit.py:378-386 | Update the D-01 wording |
| G1S-11 | INFO | SN74LV1T125 VIH at VCC = 5 V and its Ioff (unpowered input tolerance on USB-only power, when the 5 V rail is off but PA8 can drive high) were not verified, because the TI DS is not on disk. | circuit.py:392-394 | Gate 2: confirm in the SN74LV1T125 DS that VIH ≤ 2.0 V at 5 V and that Ioff / input tolerance hold with VCC = 0 |

No BLOCKER and no MAJOR findings. No custom-symbol pin number was found wrong against an on-disk datasheet (ICM-42688-P, BMI270, BMP390, TS5A3159A, USB4105).

## Verdict

**PASS** (no BLOCKER or MAJOR findings). There are 4 MINOR findings (G1S-01 to G1S-04) and 7 INFO items. G1S-02 and G1S-03 need a lead decision. G1S-04, G1S-05 and G1S-11 must be closed at Gate 2, where the official IIS2MDC, W25N01GV and SN74LV1T125 datasheets are needed.
