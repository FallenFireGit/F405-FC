# Gate 2: Footprint audit (independent re-audit)

Scope: every footprint in the `FP` map in `design/circuit.py`, plus the passives, as placed in `kicad/F405FC.kicad_pcb`. I did not reuse the earlier builder's conclusions in `review/footprint_build_notes.md`. I re-checked each footprint myself.

How I checked:
- **Pad geometry.** I dumped the pads with KiCad 10.0.6 `pcbnew.FootprintLoad()`, which gives library coordinates in top view with y pointing down.
- **Pad-to-net mapping.** I read it from the placed board. This is the result of the symbol-pin to pad mapping.
- **Datasheets.** I compared the pads against the datasheets in `datasheets/`, rendered with `pdftoppm` and viewed page by page.
- **Missing datasheets.** For parts with no datasheet on disk I used WebSearch snippets. WebFetch failed on DNS for st.com, sparkfun, alldatasheet and mikroe, and curl got a proxy 403, so no PDF could be opened. Any statement below that rests only on a snippet says so.

## Verdict: **NOT PASSED**: 1 MAJOR open (G2F-01, a verification gap only), 0 BLOCKER

- No footprint was found to be wrong.
- Every pad-to-net mapping that could be checked against a primary document is correct.
- The one MAJOR is the IIS2MDC LGA-12. Its pin names are confirmed, but its numbering direction and pad size could not be checked against ST's drawing. A mirrored LGA scraps the board, so this must be closed before fab.
- Once G2F-01 is closed, the gate is a PASS with MINORs.

## Per-footprint results

Coordinates are in mm, from the footprint origin, top view. Each pin map below gives symbol pin → pad → net as found on the board.

| Ref | Part | Footprint | Status | Evidence |
|---|---|---|---|---|
| U6 | ICM-42688-P | `Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y` | **VERIFIED** | See [ICM-42688-P (U6)](#icm-42688-p-u6) |
| U7 | BMI270 | `F405FC:Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270` | **VERIFIED** | See [BMI270 (U7)](#bmi270-u7) |
| U8 | BMP390 | `F405FC:Bosch_LGA-10_2x2mm_P0.5mm_BMP390` | **VERIFIED** | See [BMP390 (U8)](#bmp390-u8) |
| U9 | IIS2MDC | `Package_LGA:LGA-12_2x2mm_P0.5mm` | **UNVERIFIED** (G2F-01) | See [IIS2MDC (U9)](#iis2mdc-u9) |
| J1 | USB4105-GF-A | `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | **VERIFIED-WITH-NOTES** (G2F-02) | See [USB4105-GF-A (J1)](#usb4105-gf-a-j1) |
| U1, U2 | LMR38020FSDDAR | `F405FC:TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA` | **VERIFIED-WITH-NOTES** (G2F-03, -04, -10) | See [LMR38020FSDDAR (U1, U2)](#lmr38020fsddar-u1-u2) |
| U10 | W25N01GVZEIG | `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm` | **UNVERIFIED** geometry (G2F-05) | See [W25N01GVZEIG (U10)](#w25n01gvzeig-u10) |
| U4 | LP38692MP-3.3 | `Package_TO_SOT_SMD:SOT-223-5` | **VERIFIED** | See [LP38692MP-3.3 (U4)](#lp38692mp-33-u4) |
| U5 | LP5907MFX-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | **VERIFIED** | lp5907.pdf Table 4-2 (SOT-23): IN 1, GND 2, EN 3, N/C 4, OUT 5. Board: 1/3 = 5V_SYS, 2 = GND, 4 = NC, 5 = 3V3_IMU. The stock pin 1 is top-left and numbering is counter-clockwise (JEDEC MO-178), matching the DBV top view. |
| U11 | TS5A3159A (DBV) | `Package_TO_SOT_SMD:SOT-23-6` | **VERIFIED** | TS5A3159A_DS.pdf Pin Functions: NO 1, GND 2, NC 3, COM 4, V+ 5, IN 6. Board: 1 CAM2_VID (NO), 2 GND, 3 CAM1_VID (NC), 4 VTX_VID, 5 3V3, 6 CAM_SEL. This agrees with "low = CAM1". |
| U12 | SN74LV1T125 on the `74AHCT1G125` symbol | `Package_TO_SOT_SMD:SOT-23-5` | **VERIFIED-WITH-NOTES** | No datasheet on disk. A WebSearch snippet of the TI DS Table 5-1 (DBV) gives 1 OE̅, 2 A, 3 GND, 4 Y, 5 VCC. Board: 1 GND (always enabled), 2 LED_STRIP, 3 GND, 4 LED_DIN_BUF, 5 5V. The 74AHCT1G125 symbol numbering matches. |
| U13 | USBLC6-2SC6 | `Package_TO_SOT_SMD:SOT-23-6` | **VERIFIED-WITH-NOTES** | No datasheet on disk. Pin 1 = I/O1 is confirmed by a snippet. The rest (2 GND, 3/4 I/O2, 5 VBUS, 6 I/O1) comes from the KiCad symbol and my memory of the ST DS. Board: 1+6 USB_DM, 3+4 USB_DP, 2 GND, 5 VBUS. Because the part is flow-through and each I/O pair sits on one net, a swap inside a pair is harmless. |
| Q1, Q2 | PMV40UN2, NX7002AK | `Package_TO_SOT_SMD:SOT-23` | **VERIFIED** | PMV40UN2.pdf and NX7002AK.pdf Table 2: 1 G, 2 S, 3 D (TO-236AB). Board: Q1 1 BUZ_G, 2 GND, 3 BUZ_N. Q2 1 VTX_OFF_G, 2 GND, 3 EN_10V. |
| D7, D8 | BAT54S | `Package_TO_SOT_SMD:SOT-23` | **VERIFIED-WITH-NOTES** | ds11005 is not on disk. Snippets give 1 = A1, 2 = K2, 3 = K1/A2 (common). Board: 1 GND, 2 3V3, 3 CURR_ADC / RSSI_ADC, which is the correct rail clamp. |
| D4, D5, D9 | PMEG4030ER | `Diode_SMD:Nexperia_CFP3_SOD-123W` | **VERIFIED** | See [PMEG4030ER (D4, D5, D9)](#pmeg4030er-d4-d5-d9) |
| D1 | SMBJ26A | `Diode_SMD:D_SMB` | **VERIFIED-WITH-NOTES** (polarity), geometry UNVERIFIED (G2F-09) | Device:D_Zener has K = 1. KiCad D_SMB pad 1 is the cathode, with the fab bar at pad 1 and the silk bracket on the pad-1 side. Board: pad 1 VBAT, pad 2 GND, which is correct for a unidirectional TVS. Pads are 2.5 x 2.3 at ±2.15. The Littelfuse land pattern was not available. |
| D10–D12 | LTST-C191 0603 LEDs | `LED_SMD:LED_0603_1608Metric` | **VERIFIED-WITH-NOTES** (polarity), land UNVERIFIED (G2F-09) | Device:LED has K = 1. In the KiCad LED_0603 footprint pad 1 is the cathode, with the silk bracket and fab chamfer on the pad-1 side. Board: D10 1 = GND. D11 1 = STATUS_LED_BLUE (MCU sink). D12 1 = STATUS_LED_GREEN. All anodes go through resistors to 3V3. The Lite-On land drawing was not available. |
| Y1 | ECS-80-8-33-JEN-TR3 (8 MHz) | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | **UNVERIFIED** (G2F-06) | See [ECS-80-8-33-JEN-TR3 (Y1)](#ecs-80-8-33-jen-tr3-y1) |
| J2–J5 | JST SH SM08B / SM06B / SM04B-SRSS-TB | `Connector_JST:JST_SH_SM0xB-SRSS-TB_..._Horizontal` | **VERIFIED-WITH-NOTES** | See [JST SH (J2–J5)](#jst-sh-j2j5) |
| SW1 | C&K PTS810 SJM 250 | `Button_Switch_SMD:SW_SPST_PTS810` | **UNVERIFIED** pair mapping (G2F-07) | Pads "1" sit at (±2.075, −1.075) and pads "2" at (±2.075, +1.075). The footprint therefore assumes the two pads on the same long edge are bussed internally. The C&K PDF is not on disk and the snippets do not show the schematic. Board: 1 = 3V3, 2 = BOOT0. |
| H1–H4 | M3 grommet hole | `F405FC:MountingHole_3.2mm_M3_Grommet4.6mm` | **VERIFIED** | NPTH Ø3.2. Courtyard Ø4.6 on F and B. The board has positions at 102.75 / 133.25, which is a 30.5 mm square. `gen/build_pcb.py` `hole_keepouts()` adds the 4.6 mm track/via rule areas, and I saw 4 rule-area zones on the board. This matches requirements.md lines 7–8. |
| P1–P25 | Solder pads | `F405FC:Pad_SMD_{2.5x4.0,2.0x3.0,1.5x2.0,1.2x1.6}mm` | **VERIFIED** | Single roundrect pad "1", mask margin 0, F.Cu/Mask/Paste, excluded from BOM and pos. Every one carries its net. |
| TP1–TP5 | SWD test pads | `TestPoint:TestPoint_Pad_D1.0mm` | **VERIFIED** | Stock Ø1.0 pad. Nets are SWDIO, SWCLK, NRST, 3V3 and GND. |
| L1, L2 | WE-MAPI 4030 | `Inductor_SMD:L_Wuerth_MAPI-4030` | **UNVERIFIED** land (G2F-09) | Pads 0.98 x 3.7 at ±1.185, fab body 4.1 x 4.1. The WE datasheet could not be fetched and snippets give no land data. The part is a 2-terminal non-polar inductor, so there is no mapping risk. |
| U3 | STM32F405RGT6 | `Package_QFP:LQFP-64_10x10mm_P0.5mm` | **VERIFIED-WITH-NOTES** | Pad 1 is at (−5.675, −3.75), counter-clockwise, 0.3 x 1.55 at P0.5. That is the standard JEDEC LQFP-64 10x10. The ST land drawing (DS8626) is not on disk, so this relies on ST's published 0.30 x 1.20 land at an 11.5 mm row pitch, which the footprint covers, as I recall it. The pin-function mapping was audited at Gates 0 and 1. |
| R, C, FB1 | 0402 / 0603 / 0805 / 1206 / 1210 | `Resistor_SMD:*`, `Capacitor_SMD:*`, `Inductor_SMD:L_0603_1608Metric` | **VERIFIED** | Stock IPC-7351 nominal. 0402 is the smallest size used, which meets requirements.md line 14. |

### ICM-42688-P (U6)

Evidence: ICM-42688-P_DS.pdf rev 1.2.

- **Package (p.54 Fig. 10.2).** The top view has pin 1 at the top-left: 1–4 run down the left side, 5–7 along the bottom, 8–11 up the right side and 12–14 along the top from right to left. The bottom view shows side-pad centres at 2x 1.1625 and top/bottom pad centres at 2x 0.9125.
- **Dimensions (p.55 table).** W 0.25 (0.20–0.30), L 0.475 (0.425–0.525), e 0.5, D 2.5, E 3.0.
- **Footprint.** Pad centres are at ±1.1625 / ±0.9125 at P0.5, with the same numbering, pin 1 at (−1.1625, −0.75) and pad 14 at (−0.5, −0.9125). Pads are 0.35 x 0.625, which is W+0.10 and L+0.15. The pad-to-pad gap is 0.15 and the copper edge sits at 1.475 / 1.225, inside the body.
- **Pin map (p.19 Table 9).**

  | Pad | Function | Board net |
  |---|---|---|
  | 1 | AP_SDO | SPI1_MISO |
  | 2, 3 | RESV | GND |
  | 4 | INT1 | GYRO1_INT |
  | 5 | VDDIO | 3V3_IMU |
  | 6 | GND | GND |
  | 7 | RESV ("connect to GND") | GND |
  | 8 | VDD | 3V3_IMU |
  | 9 | INT2/FSYNC (FSYNC unused, so "connect to GND") | GND |
  | 10, 11 | RESV | GND |
  | 12 | AP_CS | GYRO1_CS |
  | 13 | AP_SCLK | SPI1_SCK |
  | 14 | AP_SDI | SPI1_MOSI |

  All match.
- **Silk.** A pin-1 triangle sits left of pad 1.

### BMI270 (U7)

Evidence: BMI270_DS.pdf DS000-08.

- **Landing pattern (p.145 §8.3).** Pads 0.475 x 0.25. The side-pad inner edge is 0.925 from centre, so the centre is at ±1.1625. The top-pad inner edge is 0.675 from centre, so the centre is at ±0.9125. Pin 1 is top-left, with 14/13/12 along the top and 5/6/7 along the bottom.
- **Footprint.** Identical to §8.3: the same centres, 0.475 x 0.25 pads, and pad 1 at (−1.1625, −0.75).
- **Pin map (p.134 §7.1 top view).**

  | Pad | Function | Board net |
  |---|---|---|
  | 1 | SDO | SPI1_MISO |
  | 4 | INT1 | GYRO2_INT |
  | 5 | VDDIO | 3V3_IMU |
  | 6 | GNDIO | GND |
  | 7 | GND | GND |
  | 8 | VDD | 3V3_IMU |
  | 12 | CSB | GYRO2_CS |
  | 13 | SCX | SPI1_SCK |
  | 14 | SDX | SPI1_MOSI |
  | 2, 3, 9, 10, 11 | ASDX, ASCX, INT2, OCSB, OSDO | not connected |

### BMP390 (U8)

Evidence: BMP390_DS.pdf rev 1.7.

- **Outline (p.49 Fig. 26).** Side pads are 0.275 x 0.250 (6x) with column centres 1.525 apart. Top/bottom pads are 0.250 x 0.275 (4x), 0.500 apart. All pads are 0.100 from the edge. The vent is Ø0.25 at 0.6/0.6 from the pin-1 corner.
- **Landing pattern (§7.2).** Bosch's recommended land is the bottom-view outline, i.e. 1:1.
- **Pin-out (p.46 Fig. 23 top view).** Pin 1 is top-right on the top edge, pin 2 top-left, 3/4/5 down the left side, 6/7 along the bottom from left to right, and 8/9/10 up the right side.
- **Footprint.**

  | Pads | Centre (x, y) |
  |---|---|
  | 1 | (+0.25, −0.7625) |
  | 2 | (−0.25, −0.7625) |
  | 3, 4, 5 | (−0.7625, −0.5 / 0 / +0.5) |
  | 6 | (−0.25, +0.7625) |
  | 7 | (+0.25, +0.7625) |
  | 8, 9, 10 | (+0.7625, +0.5 / 0 / −0.5) |

  Pad sizes are 1:1. The fab vent sits at (+0.4, −0.4), on the pin-1 corner side. The silk triangle is above pad 1.
- **Board nets.**

  | Pad | Function | Board net |
  |---|---|---|
  | 1 | VDDIO | 3V3 |
  | 2 | SCK | I2C1_SCL |
  | 3 | VSS | GND |
  | 4 | SDI | I2C1_SDA |
  | 5 | SDO | GND (address 0x76) |
  | 6 | CSB | 3V3 (I²C) |
  | 7 | INT | not connected |
  | 8, 9 | VSS | GND |
  | 10 | VDD | 3V3 |

  These match Table 52.

### IIS2MDC (U9)

- **Pin names.** These are confirmed by WebSearch snippets of IIS2MDC DS Table 2 and LIS2MDL AN5069. The KiCad `Sensor_Magnetic:LIS2MDL` symbol agrees.

  | Pin | Name | Board net |
  |---|---|---|
  | 1 | SCL/SPC | I2C1_SCL |
  | 2 | NC | not connected |
  | 3 | CS | 3V3 (I²C mode) |
  | 4 | SDA | I2C1_SDA |
  | 5 | C1 | MAG_C1 (220 nF) |
  | 6 | GND | GND |
  | 7 | INT/DRDY | not connected |
  | 8 | GND | GND |
  | 9 | VDD | 3V3 |
  | 10 | VDD_IO | 3V3 |
  | 11, 12 | NC | not connected |

- **Footprint.** Pad 1 is at (−0.7625, −0.75), which is top-left. 1–4 run down the left side, 5–6 along the bottom, 7–10 up the right side and 11–12 along the top. All pads are 0.375 x 0.35, with a 0.15 gap. The silk triangle is at the top-left. The footprint description is only "LGA12", with no source.
- **What is missing.** The **numbering direction and pad size have not been checked against ST's Fig. 2 or the package drawing**. No PDF could be opened.

### USB4105-GF-A (J1)

Evidence: USB4105_drawing.pdf p.1 "Recommended PCB Layout (component side)".

- **Signal pads.** 4x 0.60 and 8x 0.30 by 1.15. The x-positions are ±0.25, ±0.75, ±1.25, ±1.75, ±2.40 and ±3.20 (spans 0.50 / 3.50 / 4.80 / 6.40).
- **Locating holes.** 2x Ø0.65, 5.78 apart, 3.68 from the rear-slot line.
- **Shell slots.** Front slots are 2.10 / 1.70 and rear slots 1.80 / 1.40, both 1.00 / 0.60 wide and 8.64 apart. The pad inner edge is 4.18 from the rear slots.
- **Stock footprint.** Pads are at y −3.68 (1.15 long), holes at (±2.89, −2.605), front slots at (±4.32, −3.105) with a 0.6 x 1.7 drill in a 1.0 x 2.1 pad, and rear slots at (±4.32, +1.075) with a 0.6 x 1.4 drill in a 1.0 x 1.8 pad. Every dimension matches.
- **Pin names.** From the drawing's front view: A1 is top-left, B12 bottom-left, A12 top-right and B1 bottom-right. Looking into the mouth with the PCB edge at +y, A1 is at −x. The stock footprint has A1/B12 stacked at −3.2 and A12/B1 at +3.2, and the order is A1/B12, A4/B9, B8, A5, B7, A6, A7, B6, A8, B5, B4/A9, B1/A12. This is consistent with the drawing's pin table.
- **Board nets.**

  | Pins | Function | Board net |
  |---|---|---|
  | A6 / B6 | Dp1 / Dp2 | USB_DP |
  | A7 / B7 | Dn1 / Dn2 | USB_DM |
  | A5 | CC1 | USB_CC1 |
  | B5 | CC2 | USB_CC2 |
  | A4 / A9 / B4 / B9 | VBUS | VBUS |
  | A1 / A12 / B1 / B12 | GND | GND |
  | SH (4 slots) | Shell | GND |
  | A8 / B8 | SBU1 / SBU2 | not connected |

- **Board edge.** The drawing puts the PCB edge 2.60 mm from the rear-slot line. The board has 2.025 mm (see G2F-02).

### LMR38020FSDDAR (U1, U2)

Evidence: lmr38020.pdf.

- **Pin functions (Table 6-1).** 1 GND, 2 EN, 3 VIN, 4 RT/SYNC, 5 FB, 6 PG, 7 BOOT, 8 SW, plus the thermal pad.
- **Example board layout (p.38 DDA0008B).**
  - Pads 8x 1.55 x 0.6 with R0.05.
  - Row centres 5.4 apart, P1.27.
  - Metal 2.95 x 4.9, solder-mask defined, with a mask opening of 2.71 x 3.4.
  - Vias Ø0.2 on a 1.3 grid.
  - Note 10: vias under paste should be filled, plugged or tented.
- **Stencil (p.39).** 2.71 x 3.4 at 0.125 mm.
- **Footprint.**
  - Signal pads: 1.55 x 0.6 roundrect at ±2.7. Pad 1 is at (−2.7, −1.905), pads 1–4 run down the left side and 5–8 up the right side.
  - Pad 9: a 2.71 x 3.4 F.Cu/Mask/Paste pad, plus 2.95 x 4.9 F.Cu metal with no mask.
  - Vias: 8 PTH, 0.3 drill / 0.6 pad on F.Cu+B.Cu at (±0.65, ±0.65 / ±1.95), with no mask or paste on the via pads.
  - **There is no B.Cu copy of the EP, and that is intentional.**
- **Board nets.**

  | Pad | Function | U1 net | U2 net |
  |---|---|---|---|
  | 1 | GND | GND | GND |
  | 2 | EN | EN_5V | EN_10V |
  | 3 | VIN | VBAT | VBAT |
  | 4 | RT/SYNC | RT_5V | RT_10V |
  | 5 | FB | FB_5V | FB_10V |
  | 6 | PG | not connected | not connected |
  | 7 | BOOT | BST_5V | BST_10V |
  | 8 | SW | SW_5V | SW_10V |
  | 9 | EP | GND | GND |

  I checked U2 by its symbol map; U1 was dumped from the board.
- **Via holes.** The outer-row via holes (y 1.8–2.1) sit outside the 1.7 mask/paste edge. The inner four sit inside the paste.

### W25N01GVZEIG (U10)

- **Datasheet.** The Winbond datasheet is not on disk, and searches returned no ZE dimension table.
- **Stock footprint.** It comes from a GigaDevice 8x6 WSON drawing.
  - Pads 0.65 x 0.5 at ±3.75, P1.27.
  - EP 3.4 x 4.3, mask = copper, with 4 paste windows of 1.37 x 1.73.
  - Pad 1 is at (−3.75, −1.905), and numbering is counter-clockwise.
- **Pin map.** The standard Winbond SPI-flash pin-out is 1 /CS, 2 DO, 3 /WP, 4 GND, 5 DI, 6 CLK, 7 /HOLD, 8 VCC. The board matches it: FLASH_CS, SPI3_MISO, FLASH_WP, GND, SPI3_MOSI, SPI3_SCK, FLASH_HOLD, 3V3, with EP = GND.

### LP38692MP-3.3 (U4)

Evidence: lp38692.pdf.

- **Pin Functions (SOT-223).** EN 1, NC 2, OUT 3, IN 4, GND = 5 (tab).
- **Package (p.31 NDC0005A / MP05A).**
  - Land: 4 pads 1.0 wide x 1.5 long at P1.5.
  - Tab land: 3.3 x 1.5.
  - Row-to-tab centre distance: 6.3.
  - Top view: pin 1 at the left, tab at the top.
- **Stock footprint.**
  - Pads 2.2 x 1.0 at x −3.05.
  - Tab 1.8 x 3.4 at x +3.25, so the centre distance is 6.30.
  - Pin 1 is at y −2.25. That is the TI view rotated 90° clockwise, not mirrored.
- **Board nets.** 1 = 5V_SYS (EN), 2 = not connected, 3 = 3V3, 4 = 5V_SYS, 5 (tab) = GND.

### PMEG4030ER (D4, D5, D9)

Evidence: PMEG4030ER.pdf.

- **Pinning (Table 2).** Pin 1 = K (marking bar), pin 2 = A.
- **Reflow footprint (p.9 Fig. 15).** Lands 1.2 x 1.2 with a 2.8 centre distance; the occupied area is 4.4.
- **Stock footprint.** 1.2 x 1.2 at ±1.4, which is an exact match. The fab cathode bar is at pad 1.
- **Board nets.**

  | Ref | Pad 1 (K) | Pad 2 (A) |
  |---|---|---|
  | D4 | 5V_SYS | VBUS |
  | D5 | 5V_SYS | 5V |
  | D9 | 5V | BUZ_N |

  The symbol's K = 1 matches the device's pin 1.

### ECS-80-8-33-JEN-TR3 (Y1)

- **Footprint.** Pads 1.4 x 1.2 at (±1.1, ±0.85). Pad 1 is bottom-left, and numbering runs counter-clockwise (the TXC source).
- **Board nets.** 1 = HSE_IN, 3 = HSE_OUT (diagonal), 2 and 4 = GND.
- **What is missing.** The ECS ECX-32 drawing is not on disk and no snippet gave the pad assignment.

### JST SH (J2–J5)

- **Datasheet.** JST_SH_eSH.pdf renders with no text because its fonts are missing, so I could not read any dimensions from it.
- **Stock footprint.** Signal pads 0.6 x 1.55 at P1.0 (y −2.0). MP pads 1.2 x 1.8 at y +1.875. The body runs from −1.675 to 2.575, and pin 1 is at −x with a fab triangle.
- **Placement.** On the board the MP side faces the edge for all four connectors, so the mating face is 0.5 mm inside the edge. For example, J2 has MP at y 134.775 with the edge at 136.
- **Pin 1 nets.** J2 VBAT, J3 VTX_PWR, J4 5V, J5 5V_SYS. These follow the circuit pin order.

## Findings

| ID | Severity | Item | Finding | Fix |
|---|---|---|---|---|
| G2F-01 | **MAJOR** | U9 IIS2MDC, `Package_LGA:LGA-12_2x2mm_P0.5mm` | The pin **names** are confirmed (1 SCL … 12 NC). The **numbering direction** (counter-clockwise from top-left in top view) and the **pad size** (0.375 x 0.35) are not. The ST package drawing and the "Pin connections" figure could not be opened: there is no PDF on disk, WebFetch hit DNS failures and curl got a 403. The stock footprint has no source in its description. A mirrored LGA gives a dead mag at best, and VDD on an I/O pin at worst. | Put `iis2mdc.pdf` (DocID030986) in `datasheets/`. Then check Fig. 2 (top view, pin-1 mark) and the LGA-12 2.0x2.0x0.7 outline (terminal L/W). Confirm that pads 1–4 run down the left side and 7–10 up the right side when seen from the top. Size the pads per TN0018 (land ≈ terminal + 0.1 L / + 0.05 W). If anything differs, make a custom footprint. |
| G2F-02 | MINOR | J1 USB4105, board edge | Per the GCT drawing, the PCB edge belongs 2.60 mm in front of the rear-slot centre line (footprint y = +3.675). `design/placement.py:32` puts J1 at 36 − 3.1, so the edge is only **2.025 mm** from the rear slots (slot x = 133.975, edge x = 136.0). The shell therefore overhangs the edge by 0.575 mm more than designed, and the body is less supported over the PCB. The footprint itself is correct. | Move J1 0.575 mm toward the edge (`put("J1", 36 - 3.675, ...)`). Alternatively, confirm that the plug-to-frame clearance needs the extra overhang and record that as a deliberate decision. Recheck DRC for the rear slots at 0.475 mm from the edge (the copper edge sits about 1.1 mm from it now). |
| G2F-03 | MINOR | U1/U2 LMR38020 thermal vias | Four 0.3 mm PTH vias, at (±0.65, ±0.65), sit inside the 2.71 x 3.4 paste opening, which has 100 % coverage. TI note 10 says vias under paste should be filled, plugged or tented. There is no mask on the via pads at either end, so solder will wick through to the far side. The far side is the top side, because U1/U2 are on B.Cu. That costs joint volume and can leave solder balls on the top. | Do one of two things. Specify via filling (IPC-4761 Type VII) for these vias in the fab notes. Or split the EP paste into windows that avoid the via rings (for example 4 windows of about 1.1 x 1.4, giving roughly 65 % coverage at 0.12 mm stencil) and add F.Mask tenting on the far-side via pads. |
| G2F-04 | MINOR | U1/U2 LMR38020 EP heat path | The bottom-side copy of the pad was removed on purpose. The via pads have no `zone_connect` override, and the board currently has no GND pour (only the 4 keepout rule areas). If the opposite-layer GND pour uses the default thermal relief for PTH pads, the 8 vias reach the plane through spokes and the θJA used in power.md will not be met. | In the footprint, set `(zone_connect 2)` (solid) on the 8 via pads and on pad 9. Alternatively, set the GND zones to solid for PTH, and check this at Gate 3 routing. |
| G2F-05 | MINOR | U10 W25N01GV WSON-8 8x6 | The Winbond package drawing is unavailable: there is no PDF on disk, downloads failed, and snippets carry no ZE table. EP 3.4 x 4.3, terminal L/b and the EP connection rule are unverified. The pin-out (1 /CS … 8 VCC) is the standard Winbond SPI order. The footprint's 0.65 pad gives only about 0.075 mm toe beyond the body, which is marginal for iron rework. Also, WSON is a leadless package outside the "LGA/QFN only for sensors" rule; this was accepted in decisions.md line 69. | File the W25N01GV datasheet and check D2/E2, L and b, and the "EP: GND or float" note. If you want hand rework, lengthen the pads outward by 0.3 mm (pad 0.95 x 0.5 centred at ±3.9). |
| G2F-06 | MINOR | Y1 crystal 3225-4 pin | The pad assignment (1/3 = crystal, 2/4 = case GND) is unverified for this ECS part. That is the industry convention, but some 3225 crystals use 1/2 or no-connect pads. There is also an inconsistency: the MPN is `ECS-80-8-33-JEN-TR3` (series code "-33"), while the datasheet field points to `ECX-32.pdf`. | Confirm the series and the drawing for this MPN, with its pad numbering and land (ECS typically gives 1.4 x 1.15 pads). Update the datasheet URL to match. |
| G2F-07 | MINOR | SW1 PTS810 | The stock footprint buses the pads by long edge: "1" at y −1.075 and "2" at +1.075. If C&K actually buses the pads by short side, BOOT0 is tied permanently to 3V3 and the MCU always boots into the DFU bootloader. The C&K PDF was not available. | Check the pts810.pdf schematic and footprint. A quick continuity check on a loose switch also settles it. |
| G2F-08 | INFO | LMR footprint metadata | The footprint `descr` / Description still says "8x 0.2mm vias", but the actual vias are 0.3 / 0.6. `review/footprint_build_notes.md` §5 still describes 0.2 / 0.4 vias and a B.Cu EP copy. | Update the description and the notes. Do this cosmetically, without changing the pads. |
| G2F-09 | INFO | D1 SMB, D10–D12 0603 LEDs, L1/L2 WE-MAPI 4030 | Polarity and mapping are verified. The land dimensions are stock and were not checked against the vendor drawings (Littelfuse SMB, Lite-On LTST-C191, WE-MAPI 4030), because none was available. All are generous IPC-nominal lands for these body sizes. | Optional: file the datasheets and spot-check them. |
| G2F-10 | INFO | Hand assembly | The LGA parts (BMP390 1:1 pads of 0.25 x 0.275, BMI270 1:1, ICM, IIS2MDC) and the HSOIC EP need hot air or reflow with a stencil (≤ 0.1 mm for the BMP390). That is allowed by requirements.md line 15. There is no BGA or WLCSP, and every passive is 0402 or larger. | Put this in the assembly guide. Keep the BMP390 vent (top lid) free of flux and conformal coat. |

## Not covered

- Footprint 3D models and courtyard overlaps: these belong to Gate 3 DRC.
- The STM32 pin-function map, which was audited at Gates 0 and 1.
