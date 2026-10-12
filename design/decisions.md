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
