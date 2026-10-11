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
  (e.g. FPV cam and a tilted/rear cam) via PINIO2. It costs one SOT-23-6 and two resistors, and it makes the CAM1/CAM2/VTX-video pads
  meaningful on an analog build. The switch is a pass-through (CAMx → VID_OUT). Without an OSD it could have been dropped; the lead
  kept it because it is cheap and preserves the camera-select requirement. Stock risk: DigiKey snapshot showed it out of stock.

## D-02 GPS powered from the buck-only 5 V rail (pin-map G0-03)

USART3 (PC10/PC11) is a ROM-bootloader port. With the GPS on the USB-OR-ed 5V_SYS, the GPS would stream NMEA into the bootloader
during USB-only DFU. The GPS 5 V pin is on **5V** (battery only), so it is dead on USB power.

## D-03 Bucks: LMR38020FSDDAR on both rails; budgets derated

- Rev A's TPS54360B (non-synchronous) left the 5 V catch diode at an estimated 115-161 C junction at 2.5 A on 6S.
- **LMR38020** (80 V op / 85 V abs max, synchronous, internal compensation) removes both catch diodes and both compensation networks.
  Worst-case Tj is 104 C at the derated budget (`design/power.md` section 12).
- Its 2 A rating and valley current limit (1.8 A min) give a guaranteed 1.96-2.20 A (5 V) and 1.97-2.13 A (10 V).
- **Requirement deviations:** 5 V / 2.5 A → **1.8 A continuous** (LED strip budget 0.8 A instead of 1.0 A); 10 V / 2 A → **1.5 A
  continuous, ~2 A peak**. Typical HD VTXs draw 0.8-1.2 A at 10 V.
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
| USB ESD | ST **USBLC6-2SC6** (497-5235-1-ND); alternate TI TPD2E2U06DRLR (296-38361-1-ND) | stock snapshot was 0 for the ST part; Gate 2 picks the stocked one |
| Blackbox flash | Winbond **W25N01GVZEIG** WSON-8 8 x 6 mm (W25N01GVZEIGCT-ND) | the SOIC-16 variant was not stocked |
| HSE crystal | ECS **ECS-80-8-33-JEN-TR3** (8 MHz, 3225, CL 8 pF, ESR 400 Ω; DigiKey 15282973, ~23.7k stock snapshot; alternate ECS-80-8-33-JGN-TR3, 50-ECS-80-8-33-JGN-TR3CT-ND), 10 pF C0G load caps | 3225 8 MHz crystals have 300-500 Ohm ESR. gm_crit = 4·ESR·(2πf)²·(C0+CL)² ≈ 0.49 mA/V at 400 Ohm, C0 3 pF. **Gain margin depends on DS8626's HSE gm (recalled as 5 mA/V min → margin ≈ 10); DS8626 is not on file, so this is unverified** |
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
