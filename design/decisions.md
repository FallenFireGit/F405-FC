# F405-FC design decisions log

Each entry records a decision, why it was made, and any deviation from `design/requirements.md`. "Lead" = the lead hardware
agent working from `design/agent_brief.md`. Sourcing evidence is in `review/sourcing_research_notes.md` (web-search snippets;
digikey.com itself returns 403 from the build environment, so every stock figure is an undated snapshot to re-check at order time).

## D-01 Analog OSD (AT7456E) dropped; HD MSP DisplayPort is the primary OSD

- **Facts:** The AT7456E (ZHONGKEWEI, MAX7456 clone) has **no DigiKey listing**, including the marketplace. It is sold through LCSC
  (C82351) and marketplace sellers. The only DigiKey item containing it is the DFRobot DFR0515 OSD module (DigiKey 8598401), a separate
  board. The original **MAX7456EUI+ / +T** is listed at DigiKey as **Obsolete** (EOL notice 15 Jan 2016, quantity 0). No other
  MAX7456-compatible analog OSD chip is supported by Betaflight.
- **Rule:** "Every part comes from DigiKey only" and "never substitute a part that isn't sold at DigiKey" outrank the analog OSD
  feature. A module/daughter-board does not fit a 36 x 36 mm board.
- **Decision:** remove the AT7456E, its 27 MHz crystal (also out of stock at DigiKey) and the video in/out network. SPI2
  (PB13/PC2/PC3) and PB12 become unused. HD digital (MSP DisplayPort on UART1) is the primary OSD.
  `osd_displayport_device = MSP`.
- **Side benefit:** DMA1 S3 is freed, so **M7 (PB7, TIM4_CH2) now supports DShot**.
- **Requirement deviation:** "video: analog OSD" is **not met**. Analog-video users get video without an OSD overlay.
- **Camera switch kept:** the TS5A3159A (DigiKey 296-19265-1-ND, active) still lets an analog VTX choose between two analog cameras
  (e.g. FPV cam and a tilted/rear cam) via PINIO2. It costs one SOT-23-6, one 100k pulldown and a 100 nF cap, and it makes the
  CAM1/CAM2/VTX-video pads meaningful on an analog build. The switch is a pass-through (CAM1_VID/CAM2_VID → VTX_VID). Its signal range is
  0-3.3 V, so only DC-coupled cameras (sync tip ≥ 0 V) are supported; check with real cameras at bring-up (Gate 1 G1S-03). Without an OSD it could have been dropped; the lead
  kept it because it is cheap and preserves the camera-select requirement. Stock risk: DigiKey snapshot showed it out of stock.

## D-02 GPS powered from the buck-only 5 V rail (pin-map G0-03)

USART3 (PC10/PC11) is a ROM-bootloader port. With the GPS on the USB-OR-ed 5V_SYS, the GPS would stream NMEA into the bootloader
during USB-only DFU. The GPS 5 V pin is on **5V** (battery only), so it is dead on USB power.

## D-03 Bucks: LMR38020FSDDAR on both rails; budgets derated

- Rev A's TPS54360B (non-synchronous) left the 5 V catch diode at an estimated 115-161 C junction at 2.5 A on 6S.
- **LMR38020** (80 V op / 85 V abs max, synchronous, internal compensation) removes both catch diodes and both compensation networks.
  The board-level thermal envelope is in `design/power.md` section 12.5 (D-12).
- Its 2 A rating and valley current limit (1.8 A min) give 1.96-2.20 A (5 V) and 1.97-2.13 A (10 V) at nominal L/f, and ≥ 1.87 A / ≥ 1.78 A worst case with tolerances.
- **Requirement deviations:** 5 V / 2.5 A → **1.8 A continuous** (LED strip budget 0.8 A instead of 1.0 A); 10 V / 2 A → **1.5 A
  continuous** (≥ 1.78 A worst-case current-limit floor; 2 A peaks are not guaranteed). Typical HD VTXs draw 0.8-1.2 A at 10 V.
- **Variant FS** (forced PWM + spread spectrum): DigiKey showed LMR38020FDDAR out of stock (20-week lead time) and listed
  **LMR38020FSDDAR** as a stocked parametric equivalent (1,401 pcs, Oct 2026 snapshot). FPWM keeps a fixed (dithered) frequency at light load.
- Fallback if 2.5 A is ever mandatory: the rev A TPS54360B design (git d33a98e) with a bench-measured diode temperature.

## D-04 VTX power switch = 10 V buck enable; TPS22810 removed

- A shorted 10 V buck high-side FET would put VBAT (25.2 V) on the TPS22810 (20 V abs max).
- PINIO1 (PC15) drives an NX7002AK that pulls the LMR38020 EN low. **High = VTX off; reset/DFU/boot = VTX on** (100k gate pulldown).
- The requirement "PINIO GPIO high-side switch on the 10 V rail (pit mode / power cut)" is met functionally (the 10 V rail is cut);
  the implementation is the regulator's enable rather than a separate high-side switch. Soft start (4 ms) limits inrush.
- Residual risk: a U2 high-side short passes VBAT to the VTX. HD VTXs accept 2S-6S; analog VTXs vary (documented).

## D-05 Inductors: Würth WE-MAPI 4030 (Coilcraft not available at DigiKey)

Coilcraft XGL5030/XGL4030 parts show "no longer available at DigiKey" or no listing. Chosen: **74438357068** (6.8 uH, 3 A, 74 mOhm,
DigiKey 732-11204-1-ND) for 5 V and **74438357082** (8.2 uH, 2.8 A, 86 mOhm) for 10 V. Both are 4.1 x 4.1 x 3.1 mm max, under the 3.5 mm
height limit. Isat figures disagree between sources (3.5-5.5 A); Gate 2 confirms against the Würth datasheet.

## D-06 Power entry pads

VBAT/GND (2.5 x 4 mm), 10V/GND (2 x 3 mm) and LED-strip 5V/GND pads are added, because the JST-SH VBAT pin is rated 1 A
and the 2S worst case draws ~2.9 A.

## D-07 Small-signal substitutions for DigiKey stock

| Function | Chosen | Reason |
|---|---|---|
| VTX-off FET | Nexperia **NX7002AKR** (DigiKey 1727-1289-1-ND) | 2N7002-7-F had a 40-week lead time |
| LED-strip buffer | TI **SN74LV1T125DBVR** (296-37172-1-ND), VCC = 5 V | SN74AHCT1G125DBVR out of stock; LV1T accepts 3.3 V logic at VCC 5 V (up-translation family). 0R bypass kept (DNP) |
| USB ESD | ST **USBLC6-2SC6** (497-5235-1-ND) | its VBUS clamp is the only VBUS surge protection, so the TI TPD2E2U06 (no VBUS pin) is **not** an acceptable alternate; Gate 2 must find a stocked USBLC6-2SC6 or a pin-compatible part with a VBUS clamp |
| Blackbox flash | Winbond **W25N01GVZEIG** WSON-8 8 x 6 mm (W25N01GVZEIGCT-ND) | the SOIC-16 variant was not stocked |
| HSE crystal | ECS **ECS-80-8-33-JEN-TR3** (8 MHz, ECX-32 3225, CL 8 pF, ESR 400 Ω max per DigiKey listing 15282973, **C0 5 pF** per the ECS ECX-32 datasheet — caveat (Gate 2 G2F-06): DigiKey's series field for this MPN is blank and the "-33" code may denote a different ECS 3225 family, so C0 for this exact part is unverified; the margin only fails the 1 mA/V reading if C0 > 6.6 pF) with **8.2 pF C0G** load caps (effective CL 7.1-9.1 pF for 3-5 pF stray) | AN2867: gm_crit = 4·ESR·(2πf)²·(C0+CL)² = **0.59 mA/V best case (3 pF stray), 0.69 mA/V mid (4 pF), 0.80 mA/V worst case (5 pF)**. DS8626's HSE table is read two ways by the reviews (Gate 1 G1M-01, G1M2-01): as "gm = 5 mA/V min" (third-party mirror) → margin 6.2 ≥ 5; or, as in the sibling F427/F429 datasheet and per an ST forum answer, as "Gm_crit_max = 1 mA/V" → 0.80 < 1. **Both readings pass.** ST's own DS8626 PDF is not reachable from the build environment, so the exact row wording remains unverified; bring-up checks HSE start-up over 20 cold boots and at −10 °C if possible |
| Tact switch (BOOT) | C&K **PTS810 SJM 250 SMTR LFS** (CKN10502CT-ND) | 4.2 x 3.2 x 2.5 mm, top side |
| LEDs | Lite-On LTST-C191 (0603): TBKT blue, KGKT green, KRKT red (power) | DigiKey 160-1647-1-ND / 160-1446-1-ND / 160-1447-1-ND |

## D-08 Onboard magnetometer kept despite INAV/address caveats

IIS2MDC (fixed I2C address 0x1E) is a requirement. INAV has no driver for it (`design/inav_target.md`), and it clashes with
HMC5883-class external mags at 0x1E. Betaflight supports it via the LIS2MDL driver. Kept; documented for users.

## D-09 UART4 RX-only, UART5 full spare (pin-map rev B, G0-01)

Accepted by the lead in rev B; unchanged.

## D-10 Sensor stock risk accepted

ICM-42688-P, BMI270 and BMP390 are named in the requirements. DigiKey snapshots showed them at 0 stock in some regions with 8-26 week
lead times, but all three are Active DigiKey catalogue parts with confirmed PNs. They stay; the summary lists this as a procurement risk.

## D-11 10 V rail does not reach 10 V on 2S / low 3S (power audit P0-02)

The LMR38020's 97 % maximum duty cycle limits the 10 V rail to about 6.2-6.35 V at 1.5 A from a 7.4 V (2S) pack and 7.2-7.3 V from
8.4 V. HD VTXs with a 7.4 V minimum (DJI O3) will not run reliably from it on 2S. **Deviation:** "10 V / 2 A" applies to 3S (≥ 11.5 V)
through 6S. 2S HD builds wire the VTX to the VBAT pads (no pit-mode power cut). A VBAT/10V jumper was rejected because it back-drives
the regulated 10 V node. Documented in `design/power.md` 3.4 and the bring-up guide.

## D-12 Thermal operating envelope (power audit P0-01)

The 36 x 36 mm board cannot shed the ≈ 3.9 W worst-case board dissipation (incl. 3V3 loads) in still air. Full budgets assume in-flight airflow; the bench envelope is
≤ 1 W total dissipation. A fan-cooled full-load thermal test at bring-up is a pass/fail gate (`design/power.md` 12.5). STM32F405RGT7
(105 C) does **not** help, because the IMUs and baro are 85 C parts; the envelope (Ta ≤ 35 C full load, Ta 35-50 C ≤ 3 W, bench ≤ 1 W) is the control.

## D-13 Unused MCU pins pulled down (pin-map re-audit R-03)

PC2, PC3, PB12, PB13 (ex-OSD SPI2) each get a 100k pulldown to GND so they are not floating CMOS inputs.

## D-14 USB attach inrush exceeds USB 2.0 limit (Gate 1 G1P-01, power re-audit P0-05)

Through D4 the host charges ≈ 30 uF / 110 uC (5V_SYS bank plus everything behind the two LDOs, which have no soft start), above USB 2.0's
10 uF / 50 uC attach limit. Accepted: the same holds for practically every FPV FC and hosts current-limit their ports. A VBUS soft-start
switch is the fix if a respin has room.

## D-15 GPS / HD-VTX connector mix-up and GPS back-powering (Gate 1 G1S-02, G1S-08, G1M-02)

J3 (HD VTX, pin 1 = 10 V) and J4 (GPS, pin 1 = 5 V) are both SM06B, as the requirements specify. They sit on different board edges (top /
left) and get clear silkscreen ("VTX 10V" / "GPS 5V"); the user guide warns that a GPS plugged into J3 receives 10 V. On USB-only power the
GPS is unpowered (G0-03) while the I2C pull-ups and UART3 TX are live, so a GPS module can load the shared I2C bus and the onboard baro/mag
may not be detected; the guide says "connect the battery before USB, or reboot after connecting the battery". Series resistors on J4 were
not added (requirement-compliant as is; board area).

## D-16 HD VTX 10 V pin through a 0R link (power re-audit P1-03)

R41 (0R, 0805) sits in series with J3 pin 1. 2S HD builds that power the VTX from the VBAT pads (D-11) must remove R41 so the stock
harness cannot tie VBAT onto the regulated 10 V node. J3's pin is a 1 A JST-SH contact: VTXs above 1 A use the 10V/GND pads (P2-05).

## D-17 Gate 2 sourcing substitutions

`review/gate-2-sourcing.md` found MPNs DigiKey does not sell; drop-in replacements with identical value, tolerance, dielectric and package:

| Refs | Was | Now | DigiKey |
|---|---|---|---|
| C36, C37 (8.2 pF C0G 0402) | Samsung CL05C8R2CB5NNNC | KEMET C0402C829C5GACTU | 399-C0402C829C5GACTUCT-ND |
| C23, C39 (2.2 uF X7R 0603) | Samsung CL10B225KO8NNNC (16 V) | Samsung CL10B225KP8NNNC (10 V; 3V3_IMU rail, 3x margin) | 1276-1134-1-ND |
| R3, R8 (34.8 k 1 % 0402) | Yageo RC0402FR-0734K8L | Panasonic ERJ-2RKF3482X | PN not seen; BOM Manager matches by MPN |
| R5 (24.3 k 1 % 0402) | Yageo RC0402FR-0724K3L | Panasonic ERJ-2RKF2432X | PN not seen; matched by MPN |
| Q2 | "NX7002AKR" (not orderable) | NX7002AK,215 | 1727-1289-1-ND |
| U10 | W25N01GVZEIG | W25N01GVZEIG TR (in-stock listing) | W25N01GVZEIGCT-ND |

Stock-out MINORs kept with a documented alternate (no design change): PMEG4030ER,115 → Taiwan Semi SS34LWH (land pattern to be checked
before substituting), PMV40UN2R → DMG3420U-7, STM32F405RGT6 → -RGT7, ICM-42688-P (D-10). Estimated parts cost for 2 boards + spares:
**$167.56** (qty-1 snippet prices, 2026-10-11/12).

## D-18 Gate 2 footprint findings

- G2F-01 (IIS2MDC on stock LGA-12_2x2mm_P0.5mm): the footprint's pad layout (10-11-12-1 on one edge, 4-5-6-7 on the opposite edge,
  2-3 and 8-9 on the sides, counter-clockwise from pin 1 in top view) matches the LIS2MDL pin-connection figure text, and KiCad's own
  LIS2MDL symbol links to this footprint. The IIS2MDC is ST's pin-compatible industrial twin. Mirror orientation rests on ST's standard
  top-view counter-clockwise LGA numbering; the ST PDF could not be downloaded. Residual risk listed in the summary.
- G2F-02: USB-C moved so the PCB edge sits 2.60 mm from the rear shell slots per the GCT drawing.
- G2F-03/04: LMR38020 paste split into three windows clear of the inner vias; pad and vias set to solid zone connection.
- G2F-05/06/07 (WSON-8, crystal pads, PTS810 pad pairing) are stock KiCad footprints whose vendor drawings could not be downloaded:
  bring-up check for SW1 = continuity test of BOOT0–3V3 before power-up (must be open when not pressed).

## D-19 Gate 3 rework (placement rev C)

Gate 3 (`review/gate-3-placement.md`) failed with 3 BLOCKER / 9 MAJOR. Changes:

- **Bottom height (G3-01):** L1/L2 4030 (3.1 mm) → Würth WE-MAPI 4020 **74438356056** 5.6 uH (2.1 mm max) on both rails; 1210 input
  caps CL32B106KBJNNNE (2.7 mm max) → Murata **GRM32DR71H106KA01L** (2.0 mm). Putting the inductors on top was rejected: the bucks'
  PowerPAD via fields block top-side parts over the ICs, and the SW node would need vias.
- **Consequence (requirement deviation, extends D-03):** the HS peak-limit floor with −20 % L, −20 % RT and −8 % spread spectrum falls to
  1.78 A (5 V) and **1.38 A (10 V)** at 6S. The 10 V continuous budget is now **1.3 A** (typical HD VTX 0.8-1.2 A); the 5 V margin over the
  1.71 A planned load is 0.07 A, so the LED-strip firmware cap stays mandatory. `gen/power_calc_lmr.py` and `design/power.md` §0/2.2/3.1/12.1 updated.
- **Hot loops (G3-02/03):** every buck, LDO, MCU, IMU and crystal support part is now placed relative to its IC pad (`ANCHOR` in
  `design/placement.py`), legalized with a 1.5 mm search radius first, and checked by `gen/placecheck.py` (pad-to-pad limits, exits non-zero).
  Limits of 2.1 mm for BST/HF-input caps and 6.5-7.5 mm for the third 10 V output cap and the U2 EN network are the courtyard-limited
  minimum on this board (the EN node is a DC divider; the third output cap is bulk).
- **Battery pads** P1/P2 moved to the bottom edge (they sat over U1's PowerPAD vias on the top); C1 stays on top next to D1.
- **ADC clamps:** D8 (RSSI) sits near the MCU on the bottom; D7 (CURR_ADC) had no free spot there and moved to the bottom-right corner
  (32.0, 7.25). The ADC nets are slow; trace length is not critical.

## D-20 Gate 2 re-check (`review/gate-2-recheck.md`)

- **G2R-01 BLOCKER:** GRM32DR71H106KA01L was not found at any distributor. Bottom-side input caps C2/C3/C10/C11 are now TDK
  **C3225X7S2A475K200AB** (4.7 uF 100 V X7S 1210, 2.0 mm; DigiKey 445-6042-1-ND to verify at order time). C1 (top side) returns to
  Samsung CL32B106KBJNNNE (1276-3387-1-ND). Per-IC effective input capacitance ≈ 7 uF at 25 V (estimate; curve not read).
- **G2R-02 MAJOR:** no DigiKey PN seen for 74438356056. Kept (Würth figures confirmed: 81 mOhm max, Isat(10 %) 2.65 A typ, 2.1 mm max);
  alternate WE-MAIA **78438356056** (732-11317-1-ND). Confirm in DigiKey BOM Manager before ordering.
- **G2R-03 MAJOR:** `bom/F405FC_digikey_bom.csv` and `bom/digikey_bom_costed.csv` regenerated from circuit.py; ERJ-2RKF PNs filled
  (P34.8KLCT-ND / P24.3KLCT-ND), U10 → 256-W25N01GVZEIGTRCT-ND (G2R-05), KEMET price corrected. Estimated total **$175.73**.
- **G2R-07 MINOR (LMR38020 paste 45 %, 8 vias):** kept; with hand assembly the paste is applied by stencil and the three windows avoid
  wicking into the open vias. Bring-up thermal test (power.md §12.5) is the check.
- **G2R-08 INFO:** no tracks or vias under the L1/L2 bodies on B.Cu (rule areas added before routing).

## D-21 Gate 3 re-review fixes and routing-capacity rework (`review/gate-3-placement-rereview.md`)

- **G3-11 (labels):** user pads are fixed on regular grids (top: S8/LED/5V/RSSI row, T5/R5, G/S7/5V; bottom: one 5V/G/C1/C2/VID column,
  a UART6/S5/S6 2x2 block, two SWD/power test-point rows). `gen/build_pcb.py` places every label by rule: no silk on copper, inside the
  board, and for pads/test points the label's nearest labelled pad is its own by >= 0.6 mm. Label areas are reserved in the legalizer.
  The LED-strip GND pad P12 was removed: the LED strip shares P4 (GND, next to P3 10V).
- **G3R-01 (top parts near thermal vias):** the U1/U2 thermal-via pads have no F/B mask openings (verified: pad layer set has no mask
  layers), so the top annulus is tented; top-side parts are additionally kept >= 0.6 mm from the via fields by the legalizer.
- **G3R-02 (VBAT copper):** VBAT from the battery pads to both buck inputs is an In2 copper zone (priority above the GND pour), stitched
  by 4 vias at P1, 3 at the U1 input caps and 2 at the U2 input caps; the 0.8 mm edge trace and the 1.0 mm In2 trunk are gone.
- **G3R-10 (MCU escape):** a 0.8 mm keep-clear ring around the MCU pad field for non-anchored top parts; MCU decaps moved from 2.05 to
  2.75 mm from their pins (VCAP2/3V3 caps C34/C26 to the MCU top-right corner, VCAP2 ~4 mm), and 25 MCU signal pins are fanned inward to
  vias under the package (`FANOUT=mcu gen/gndfan.py`). D9 (buzzer flyback) moved next to the buzzer pads in the top-left corner; U13
  (USB ESD) is fixed between J1 and the MCU with its flow-through axis perpendicular to D+/D− (G3R-07 accepted as MINOR: no other spot).
- In1 stays a solid GND plane: the Specctra export restricts every net class to F/In2/B (`gen/route.py`). Making In1 a Specctra "power"
  layer instead (G3R-12 note) left GND pads unrouted, so that approach was dropped.

## D-22 Routing method and routing-driven changes

- **Router.** Freerouting 2.5.0 (the brief's tool) was run on every placement revision and plateaued at 56-93 unrouted connections
  on this 36 x 36 mm, 4-layer, 161-part board. The production routing therefore comes from `gen/pathfinder.py`, a negotiated-
  congestion (PathFinder) grid router written for this board, after the scripted critical routes (`gen/critical.py`) and the MCU
  inward fanout (`gen/gndfan.py`, FANOUT=mcu). Reproduce with `bash gen/route_pipeline.sh`. Freerouting trial logs are not kept.
- **Clearance model.** Pairwise clearance = max of the two net classes; holes keep the 0.19 mm hole clearance; a 0.035 mm grid
  safety margin to fixed copper and a 0.015 mm margin between routed nets cover the 0.05 mm rasterization. KiCad DRC is the judge.
- **Net classes.** Signal tracks 0.127 mm (the brief's minimum) to gain routing capacity; PWR_MID (VBAT/5V branches) 0.35 mm with
  0.127 mm clearance; PWR_HI (10V, SW, VTX_PWR) 0.45 mm with 0.15 mm clearance (both ample for ≤ 25.2 V). Buck hot loops and the main
  VBAT/5V copper are the scripted 0.8 mm tracks and the In2 VBAT zone.
- **In1.** The GND plane is never routed by default. A final PathFinder pass may use short In1 hops (cost 6x) only where no other
  layer has room; their count and length are reported in `review/summary.md` and checked at Gate 4.
- **Routing-driven placement moves:** U5 (3V3_IMU LDO) and C23 moved from under the MCU top pin row, C53 (RSSI filter cap) moved next
  to its series resistor R39, R21/R22 (unused-pin pulldowns) moved to the bottom, fanout vias kept 0.8 mm outside the IMU courtyards.
  These free via sites under the MCU body for the SPI1/SPI3 pin escapes.

## D-23 ADC clamp diodes D7/D8 removed (Gate 3 re-review G3R-09 option)

The BAT54S clamps on CURR_ADC and RSSI_ADC occupied the last free routing space under the MCU corner. Each ADC input keeps its
10 k series resistor and 10 nF filter cap. A fault source of 5 V then injects (5 - 3.3 - 0.3) / 10 k ≈ 0.14 mA into the STM32 pin clamp
(limit 5 mA per pin, 25 mA total); even 12 V gives ≈ 0.85 mA. The external clamp was redundant with the series resistor.
