# F405-FC power architecture (Gate 0 design, rev B)

Source of truth for requirements: `design/requirements.md`. Datasheets are in `datasheets/` (file name in brackets).
Rev B (2026-10-11) replaces both TPS54360B non-synchronous bucks with the synchronous TI **LMR38020FSDDAR**, removes the
TPS22810 load switch (VTX power is now cut by disabling the 10 V buck), and adds VBAT/GND and 10V/GND solder pads.
Rev A is in git history (commit d33a98e). All rev B numbers come from `gen/power_calc_lmr.py` (run `python3 -I gen/power_calc_lmr.py`).
Decisions and requirement deviations are logged in `design/decisions.md`.

---

## 0. Summary

| Block | Part | Key numbers |
|---|---|---|
| VBAT TVS | Littelfuse **SMBJ26A** (SMB) | VWM 26 V, VBR 28.9-31.9 V, VC 42.1 V @ 14.3 A |
| 5 V buck (U1) | TI **LMR38020FSDDAR** (HSOIC-8 PowerPAD), 750 kHz, FPWM + spread spectrum | 5.115 V, **1.8 A continuous design budget** (2.0 A guaranteed current-limit floor), L = 6.8 uH |
| 10 V buck (U2) | TI **LMR38020FSDDAR** (same IC) | 10.09 V, **1.5 A continuous** (1.97 A guaranteed floor), L = 8.2 uH; EN also = VTX power switch |
| VTX pit switch | U2 EN pulled low by **Q2 NX7002AK** (SOT-23) from PINIO1 (PC15) | GPIO high = VTX **off**; default (reset/DFU/boot) = VTX **on** |
| 3.3 V main | TI **LP38692MP-3.3/NOPB** LDO (SOT-223-5) | 1 A rated, 250 mA budget, from 5V_SYS |
| 3.3 V IMU | TI **LP5907MFX-3.3/NOPB** LDO (SOT-23-5) | 82 dB PSRR @1 kHz, 10 mA budget |
| USB / power OR | Nexperia **PMEG4030ER** x2 (SOD-123W) | dual-diode OR into 5V_SYS (section 9) |
| Buzzer | Nexperia **PMV40UN2** (SOT-23) + PMEG4030ER flyback | 30 V, 44 mOhm @ 4.5 V |
| Power entry | 2 x large SMD pads VBAT/GND (2.5 x 4 mm) + 10V/GND pad pair (2 x 3 mm) | carries the current the JST-SH pins cannot (section 5) |

### Why the LMR38020 (rev A open issue: catch-diode Tj 115-161 C)
- **Synchronous:** no catch Schottky. The rev A hot spot (PMEG6030EP at 0.93 W) disappears; all switching loss is in one PowerPAD
  package with RthJC(bot) 4.3 C/W into the planes.
- **85 V abs max / 80 V operating** ([lmr38020.pdf] 7.1, 7.3): 43 V above the TVS worst-case clamp, versus 23 V for the TPS54360B.
  That also leaves room for an SMBJ28A/30A TVS if LiHV support is ever wanted.
- **Internal compensation, EN abs max = VIN + 0.3 V:** no RC compensation network and no EN zener. Per rail the part count drops from
  about 16 to 10 (IC, L, CIN, CHF, CBOOT, RT, 2 x RFB, 2 x REN, COUT).
- **Cost of the change:** the 2 A device rating. The datasheet guarantees output current through the valley limit (Eq. 7:
  IOUTmax = ILS + dIL/2, ILS = 1.8 A min / 2.3 typ). With our inductors that is **1.96-2.20 A minimum** across 2S-6S (5 V rail) and
  **1.97-2.13 A** (10 V rail). So the requirement "5 V / 2.5 A" is **derated to 1.8 A continuous** (see the budget in section 12.1) and
  "10 V / 2 A" to **1.5 A continuous, 2 A peak**. The lead accepted these deviations (`design/decisions.md` D-03).
- **Thermals (section 12):** worst-case Tj 86-104 C (5 V at 1.8 A, 2S) and 74-88 C (10 V at 1.5 A, 4-6S) at Ta = 50 C, against
  150 C max / 163 C TSD. Rev A's diode reached 161 C.
- I kept the TPS54360B as the documented fallback (rev A design) if the 5 V budget ever has to return to 2.5 A.

Block diagram:

```
 VBAT pads (2.5x4 mm) ─┬─ ESC JST VBAT pin (parallel, 1 A rated)
                       │
                D1 SMBJ26A ── C1 10u/50V (entry)
                       │
        VBAT ──────────┼─────────────────┬────────────────────────┬── R 10k/1k → VBAT_ADC
                       │                 │                        │
          U1 LMR38020 (5V1, 750 kHz)   U2 LMR38020 (10V, 750 kHz) │
             EN ← 301k/100k UVLO          EN ← 301k/100k UVLO      (ESC side: 470-1000 uF low-ESR electrolytic, external)
                       │                    └─ Q2 NX7002AK drain; gate ← PC15 VTX_PWR_EN (high = VTX off)
                       │                 │
                 5V (5.115 V)          10V ── HD VTX JST pin 1, 10V/GND pads (analog VTX)
           │  │  │  │
           │  │  │  └── D5 PMEG4030ER ──┐
           │  │  └── Buzzer (+)          │
           │  └── LED strip 5V pad       ├── 5V_SYS (≈4.76 V on battery, ≈4.65 V on USB)
           └── CAM1 / CAM2 5V pads,      │      ├── U4 LP38692-3.3 → 3V3 (MCU, flash, baro, mag, LEDs[, OSD])
               GPS 5V (buck-only, G0-03) │      ├── U5 LP5907-3.3  → 3V3_IMU (ICM-42688-P, BMI270)
                                         │      └── RX 5V pad (ELRS)
 USB-C VBUS ── D4 PMEG4030ER ────────────┘
```

**GPS supply (pin-map decision 3 / G0-03):** the GPS 5 V pin is on **5V (buck only)**, not 5V_SYS, so the GPS is unpowered during
USB-only ROM DFU and cannot stream NMEA into USART3. This moves 0.1 A from 5V_SYS to 5V directly.

---

## 1. VBAT input protection

### 1.1 TVS: Littelfuse SMBJ26A (unidirectional, 600 W, SMB / DO-214AA)

Values are from the JEDEC-standard SMBJ table, which Littelfuse/DigiKey list identically (DigiKey listing for SMBJ26A:
"42.1 V clamp at 14.3 A Ipp (10/1000 us)"). I could not download Littelfuse's own PDF (the site blocks automated
fetches), so pull the PDF before release.

| Parameter | Value | Check |
|---|---|---|
| VR (stand-off) | 26.0 V | > 25.2 V (6S at 4.20 V/cell). LiHV 6S at 4.35 V/cell = 26.1 V is 0.1 V above VR but still 2.8 V below VBR(min), so leakage stays in the uA range. If LiHV support matters, use the SMBJ28A (VBR 31.1-34.4 V, VC 45.4 V; 45.4 V is still below 50 V caps and the 65 V IC). |
| VBR @ 1 mA | 28.9 V min, 31.9 V max | A 35 V regen spike is clamped (the TVS starts conducting at 28.9-31.9 V). |
| VC @ IPP = 14.3 A | 42.1 V max | < 50 V ceramic rating, < **85 V** LMR38020 VIN/SW abs max. Only the bucks, input caps, EN dividers, VBAT divider and the ESC connector sit on VBAT. |
| Dynamic resistance (derived) | (42.1 - 31.9) / 14.3 = 0.71 Ohm | Clamp at 5 A is about 31.9 + 5 x 0.71 = **35.5 V**; at 1 A about 32.6 V |

Margin summary at the worst-case clamp (42.1 V):
- LMR38020 VIN and SW: 85 V abs max, 80 V operating: 42.9 V margin. No catch diode exists any more.
- LMR38020 EN: abs max is VIN + 0.3 V, so the UVLO divider (10.5 V on EN at 42.1 V) needs no zener (section 2.6).
- 50 V X7R input ceramics: 7.9 V margin. 42.1 V is the worst case at full rated pulse current; realistic ESC regen pulses clamp near 32-36 V.
- VBAT ADC pin: 42.1 / 11 = 3.83 V. The pin's ESD diode clamps it, with injection current (42.1 - 3.6)/10k - 3.6/1k = **0.25 mA**, far below the STM32 ±5 mA IINJ limit (DS8626 section 6.2).

Note that there is no reverse-polarity protection. A reversed pack forward-biases the TVS, which will short and probably fail as
the indicator; this is normal for FPV FCs because polarity is set by the ESC harness.

### 1.2 Input ceramics

| Ref | Value | MPN | Placement |
|---|---|---|---|
| C1 | 10 uF 50 V X7R 1210 | Murata GRM32ER71H106KA12L | Board entry, next to D1 |
| C2 / C3 | 10 uF 50 V X7R 1210 | GRM32ER71H106KA12L | U1 / U2 VIN-GND, inside the hot loop |
| C4 / C5 | 100 nF 100 V X7R 0603 | Murata GRM188R72A104KA35D | U1 / U2 VIN pin, closest (datasheet 9.2.2.6: 100-220 nF HF bypass) |

- LMR38020 needs at least **4.7 uF effective** on VIN (9.2.2.6). A 10 uF/50 V 1210 keeps about 4.5 uF at 25 V; together with the shared
  entry cap C1 (also about 4.5 uF, within 10 mm) each IC sees about 9 uF.
- RMS ripple current ≈ IOUT/2 (Eq. 12): 0.9 A (5 V) and 0.75 A (10 V). A 1210 X7R handles 2-3 A at a few mOhm ESR.
- **External bulk:** a low-ESR electrolytic of 470-1000 uF, 35 V min (50 V preferred for 6S) across the ESC battery pads. It damps the
  battery-lead/ceramic LC on hot-plug and absorbs regen energy; the TVS is the backstop.

---

## 2. 5 V buck (U1): LMR38020FSDDAR

**Variant:** `FS` = forced PWM **with** ±8 % pseudo-random spread spectrum ([lmr38020.pdf] Table 5, FSPREAD). FPWM keeps the switching
frequency near 750 kHz at light load instead of bursting (PFM `S` variant); spread spectrum lowers conducted/radiated EMI peaks.
Sourcing drove the choice: DigiKey showed LMR38020FDDAR out of stock (20-week lead time) while listing LMR38020FSDDAR as a stocked
parametric equivalent (1,401 pcs, $4.55, Oct 2026 web snapshot; re-check at order time).

### 2.1 Frequency
- **RT = 34.8 kOhm** (Table 8-1, Eq. 2 gives 34.5 k) → **750 kHz** (EC table: 430-650 kHz at 49.9 k gives roughly ±20 % spread).
- tON at 25.2 V = 270 ns, at the 42.1 V clamp 162 ns. Both exceed tON-MIN max 131 ns, so there is no foldback below 51.9 V (Eq. 5).
- Low-VIN foldback starts below 6.58 V (Eq. 6, tOFF-MIN 300 ns max). Below that the frequency drops toward about 140 kHz and the rail
  stays near 5.1 V down to VIN ≈ 5.9 V at 1.8 A (dropout ≈ IOUT x (RDS,HS,hot + DCR)).

### 2.2 Inductor: Würth WE-MAPI 74438357068 (6.8 uH, 4030: 4.1 x 4.1 x 3.1 mm max)
- Eq. 11 sub-harmonic floor: LMIN = 0.25 x 5.1 / 750k = **1.70 uH**. 6.8 uH is 4x above.
- Ripple (Eq. 10 rearranged): 0.31 A (7.4 V), 0.60 A (12.6 V), **0.80 A (25.2 V)** = K 0.44 of the 1.8 A budget, 0.40 of the 2 A rating.
  That is at the top of TI's 20-40 % window, chosen to keep the guaranteed valley-limit current (Eq. 7) above 1.96 A.
- Peak at 2.0 A/25.2 V: 2.40 A. WE-MAPI 74438357068 (DigiKey 732-11204-1-ND): rated 3.0 A, DCR max 74 mOhm, Isat quoted 3.5-5.5 A
  depending on source (iron-alloy core, soft saturation). The HS current limit (3.8 A max) is at or below Isat, so a short-circuit is
  limited cycle by cycle plus hiccup (8.3.8). **Gate 2 must confirm Isat from the Würth datasheet.**
- Coilcraft XGL5030 (rev A choice) is not obtainable at DigiKey ("no longer available at DigiKey"), so it is excluded.
- Height 3.1 mm max (top-side limit 3.5 mm).

### 2.3 Output capacitors
- Datasheet Table 9-1 (5 V, 1 MHz, 24 V in): 2 x 22 uF nominal / 2 x 15 uF minimum rated. At 750 kHz we use **3 x 22 uF 25 V X5R 1206
  (Samsung CL31A226KAHNNNE)** ≈ 3 x 14 uF = 42 uF effective at 5.1 V, below the "10x design value" ceiling (9.2.2.5).
- Plus 1 x 100 nF 0402 at the output for HF spikes (9.2.2.5).

### 2.4 Feedback (Eq. 1, VREF = 1.000 V, ±1.5 % over temp in FPWM)
- RFBT = 100 kOhm (TI recommended value), RFBB = **24.3 kOhm** 1 % → **5.115 V** (worst case 4.96-5.28 V).
- 5.115 V keeps D5's output (5V_SYS) at about 4.76 V, above USB-through-D4 (about 4.65 V), so the battery path wins whenever both are present.
  The upper tolerance 5.28 V is inside WS2812 VDD max 5.3 V.

### 2.5 Boot capacitor
100 nF X7R, ≥ 16 V (8.3.7, 9.2.2.7): Samsung CL05B104KO5NNNC (0402, 16 V).

### 2.6 EN / UVLO (Eq. 13/14)
- RENT = **301 kOhm**, RENB = **100 kOhm**. VON = 1.25 x (1 + 3.01) = **5.01 V typ** (4.41-5.61 V over VEN-H 1.1-1.4 V), VOFF = **4.41 V typ**
  (3.82-4.90 V). The internal VIN UVLO (4.2 V start / 3.8 V operating) is below that.
- EN at 42.1 V = 10.5 V, below VIN + 0.3 V. No zener is needed.
- Divider current 63 uA at 25.2 V.
- U1's EN has **no** GPIO control. The 5 V rail is always on with the battery.

### 2.7 PG pin
Left floating (8.3.5: "If this function is not needed, the PG pin must be left floating").

---

## 3. 10 V buck (U2): LMR38020FSDDAR

Same IC, RT (34.8 k), UVLO network (301 k / 100 k), boot cap, input caps and PG treatment as U1.

### 3.1 Inductor: Würth WE-MAPI 74438357082 (8.2 uH, 4030)
- LMIN (Eq. 11) = 0.25 x 10.09 / 750k = 3.36 uH.
- Ripple: 0.66 A (16.8 V), 0.98 A (25.2 V), 1.25 A (42.1 V clamp). Peak at 1.5 A/25.2 V = 1.99 A, below the 2.8 A rating
  (aggregator listing: 8.2 uH, 2.8 A, 86 mOhm, 4030, AEC-Q200; Isat quoted 5.2 A). DigiKey PN not yet seen: Gate 2 to confirm.
- Guaranteed output (Eq. 7, ILS min): 2.13 A (16.8 V), 2.11 A (25.2 V).

### 3.2 Output capacitors
**3 x 22 uF 25 V X5R 1206** (CL31A226KAHNNNE), about 3 x 9 uF = 27 uF effective at 10 V. Datasheet Table 9-1 (12 V out): 1 x 22 uF
(400 kHz) or 2 x 10 uF (1 MHz). 27 uF is 1.2-2.7x those. Plus 100 nF 0402 HF.

### 3.3 Feedback
RFBT 100 kOhm, RFBB **11.0 kOhm** → **10.09 V** (9.76-10.43 V).

### 3.4 Dropout on 2S / 3S (documented limitation)
- Regulation without foldback needs VIN ≥ 13.0 V (Eq. 6). With foldback the duty cycle extends toward 100 % at about 140 kHz, so the
  rail holds 10 V down to VIN ≈ 10.8 V at 1.5 A.
- Below that, VOUT ≈ VIN − IOUT x (RDS,HS,hot + DCR) ≈ VIN − 0.7 V at 1.5 A: **6.6 V at 7.4 V (2S nominal)**, 7.7 V at 8.4 V.
- DJI O3 (7.4-26.4 V) and some Walksnail units brown out on sagging 2S. Analog VTXs rated 5-36 V are fine. This is user-documented
  behaviour. The rail can never exceed VBAT.

---

## 4. VTX power switch (pit mode / power cut): buck enable

Rev A used a TPS22810 load switch after the 10 V buck. The audit (rev A R8) found that a shorted U2 high-side FET would put VBAT
(up to 25.2 V) on the TPS22810 (20 V abs max). Rev B **removes the TPS22810** and switches the **10 V buck itself** off through its EN pin:

- **Q2 = Nexperia NX7002AK** (60 V, SOT-23, VGS(th) 1.1-2.1 V [NX7002AK.pdf]) drain on U2 EN, source to GND.
- Gate driven from **PC15 / VTX_PWR_EN** through **R 1 kOhm**, with **100 kOhm gate pulldown** (gate side).
- **GPIO high → Q2 on → EN < 0.95 V → U2 off → VTX off.** GPIO low or floating (reset, ROM DFU, early boot) → Q2 off → U2 runs → VTX on.
  Losing video because firmware is mid-flash or misconfigured is worse than lacking pit mode; this matches commercial practice.
- EN with Q2 on at the 42.1 V clamp: 42.1 V / 301 k x RDS(on) (< 5 Ohm at VGS = 3.0 V) ≈ 0.7 mV, far below VEN-L min 0.95 V.
- Turn-on uses the LMR38020's internal 4 ms soft start (8.3.9) plus 18 ms OCP blanking, so inrush into a VTX's input caps is limited and
  start-up into a large capacitive load does not hiccup.
- PC15 is a low-drive pin (G0-08): the load is one SOT-23 gate (Ciss ≈ 30-50 pF) through 1 kOhm, static, so the 2 MHz/30 pF/3 mA limits
  don't bind. The pinmap rule "CMOS-only loads on PC13-15" is met in spirit (a MOSFET gate is a capacitive CMOS-like load).
- **Betaflight:** `set pinio_config = 1,...` (output, not inverted), `pinio_box = 40` (USER1). USER1 inactive → pin LOW → VTX on.
  USER1 active → pin HIGH → VTX off. Pinmap section 6 is updated to match.
- **Double fault:** if U2's high-side FET fails short, the VTX sees VBAT. Nothing else on the 10 V rail can be damaged (the TPS22810
  is gone), and HD VTXs (DJI O3/O4, Walksnail, HDZero) accept 2S-6S directly. This is the residual risk (section 14).

---

## 5. Power entry pads

The ESC JST-SH VBAT pin is rated 1 A (JST SH, AWG 28). Rev B adds:

| Pads | Size | Net | Purpose |
|---|---|---|---|
| VBAT, GND | 2.5 x 4.0 mm SMD each, top side, at the board edge next to the ESC connector | VBAT / GND | Primary power entry, solder 20-22 AWG. JST VBAT pin stays in parallel |
| 10V, GND | 2.0 x 3.0 mm SMD each | 10V / GND | Analog VTX (> 1 A) or HD VTX by wire |
| 5V, GND (LED strip) | 1.5 x 2.0 mm | 5V / GND | WS2812 strip power |

Current check: 6S worst-case board input is about 1.3 A (section 12.4), 2S worst case about 3.6 A. A 2.5 x 4 mm pad with 20 AWG carries
that easily. Copper from the pads to D1/C1 uses ≥ 1.5 mm traces or pours on L1 + L3.

---

## 6. Camera and peripheral 5 V supply

- CAM1/CAM2 5V pads: on **5V** (5.115 V, battery only), about 0.2 A each.
- GPS 5V pin: on **5V** (battery only, G0-03).
- RX 5V pin: on **5V_SYS** (so the receiver works on USB for binding/config).
- LED strip 5V pad: on **5V** (never powered from USB).

---

## 7. 3.3 V main rail: TI LP38692MP-3.3/NOPB (SOT-223-5)

**AT7456E supply check** ([AT7456E.pdf], ZHONGKEWEI datasheet, DC characteristics):
- AVDD, DVDD and PVDD are each specified **3.15-5.25 V**.
- Supply current: IAVDD 2.2 typ / 2.5 max, IDVDD 43.1 typ / 60 max, IPVDD 6.0 typ / 10 max (100 % white field). That is **51.3 mA typ / 72.5 mA max**.
- SPI VIH is 0.65 x VDVDD. At 5 V that is 3.25 V, which a 3.3 V MCU only marginally meets. So the AT7456E is powered from **3V3** (supported range, and logic levels match). The MAX7456 it clones is 5 V-only ([MAX7456_DS.pdf]), so check any reference schematic before copying.

**3V3 load budget:**

| Load | Typ | Budget (max) | Source |
|---|---|---|---|
| STM32F405RGT6 @168 MHz, all peripherals on | ~90 mA | 120 mA | DS8626 run-mode table (verify exact row) |
| W25N01GV (read/program) | 25 mA | 35 mA | Winbond DS |
| AT7456E | 51 mA | 72.5 mA | above |
| BMP390 + IIS2MDC | <1 mA | 1 mA | Bosch/ST DS |
| 3 x LEDs @ about 2 mA | 6 mA | 6 mA | |
| Pull-ups, misc | 2 mA | 5 mA | |
| **Total** | **~175 mA** | **~240 mA, use 250 mA** | |

**Why the LP38692:**
- 1 A rated, 2.7-**10 V** input (12 V abs max). The headroom over the 5 V rail tolerates load-dump transients that a 5.5 V-max LDO (TLV757P, AP2112, TLV1117LV) would not.
- Stable with 1 uF+ ceramic (ESR 5-500 mOhm). TI lists it active.
- SOT-223 thermal resistance about **68.5 °C/W** (High-K JEDEC; Thermal Information section 6.4 of [lp38692.pdf] SNVS322M; the pdftotext column order is ambiguous, so re-read the table).
- A SOT-23-5 LDO (θJA about 200-250 °C/W) would run Tj above 125 °C at 0.36 W.

**Input:** 5V_SYS (4.75 V on battery, about 4.65 V on USB).
- Dropout at 3.3 V: 65 mV typ / 110 mV max at 0.1 A and 650/1000 mV at 1 A, so about 0.15-0.3 V at 250 mA.
- Minimum input is therefore about 3.6 V. The rail holds on USB as low as VBUS = 4.0 V, and on battery down to VBAT about 4.4 V.

**Dissipation:** (4.756 - 3.3) x 0.25 A = **0.364 W**, so Tj = 50 + 0.364 x 68.5 = **75 °C** at 50 °C ambient. Typical: 0.255 W, Tj 67 °C.

**Components:**
- EN tied to IN. VEN(on) must be at least 1.8 V at VIN = 4 V and 3 V at VIN = 6 V; tying to VIN satisfies this.
- CIN = 1 uF 25 V X5R 0603 within 1 cm (section 8.2.2.2.1), plus the 10 uF 5V_SYS bulk.
- COUT = 10 uF 10 V X5R 0805 (Murata GRM21BR61A106KE19L) plus 100 nF. ESR about 5 mOhm is inside the 5-500 mOhm window.

---

## 8. Low-noise 3.3 V for the IMUs: TI LP5907MFX-3.3/NOPB (SOT-23-5)

- Specs: 250 mA, 2.2-5.5 V input (6 V abs max), PSRR **82 dB at 1 kHz**, noise < 6.5 uVrms (10 uVrms at 1 mA, 10 Hz-100 kHz), dropout 120 mV typ, IQ 12 uA ([lp5907.pdf] SNVS798Q, Jul 2025, active).
- Fed from 5V_SYS (4.75 V max, within the 5.5 V limit). Its PSRR attenuates the buck ripple, which reaches 5V_SYS already filtered through D5.
- Load: ICM-42688-P (about 0.9 mA, 6-axis LN mode) + BMI270 (about 1 mA). Budget **10 mA**.
- P = (4.756 - 3.3) x 0.01 = 15 mW, so Tj rise is about 3 °C.
- Capacitors: CIN = 1 uF 25 V X5R 0603, COUT = **2.2 uF 16 V X7R 0603** (about 1.8 uF effective at 3.3 V; the allowed effective range is 0.7-10 uF, section 5.4). Each IMU keeps its own 100 nF local decoupling, which sums well under 10 uF.
- EN tied to IN.
- TI now points to TPS7A20 as the "more updated portfolio device". The LP5907 is still in production, so this is not an obsolescence flag.

---

## 9. USB VBUS path and 5V_SYS OR-ing

**Topology (deviation from a single diode, deliberate):** two PMEG4030ER Schottkys form a diode-OR into a sub-rail **5V_SYS**.
- **D4:** VBUS to 5V_SYS.
- **D5:** 5V (buck output) to 5V_SYS.
- 5V_SYS feeds only the two LDOs and the RX 5V pin. LED strip, cameras, GPS (G0-03) and buzzer stay on 5V (battery only).

Why:
1. **USB never powers the LED strip or the cameras.** Worst-case USB load is 5V_SYS = 0.25 (3V3, with OSD) + 0.01 (IMU) + 0.15 (RX) = **0.41 A** (0.33 A without OSD), typically about 0.25 A. That is close to the USB 2.0 500 mA budget without the LED strip's 1 A blowing it. The single-diode version would let a connected LED strip pull up to 1 A more from the laptop.
2. **No back-feed into VBAT on USB.** With a single diode onto the buck output, USB current flows back through the LMR38020 high-side FET body diode (SW to VIN) and raises VBAT to about 3.9 V. That powers the ESC MCUs and the VBAT divider from USB and makes VBAT read about 3.9 V. D5 blocks this path.
3. **No back-feed into the USB host.** D4 blocks the battery-side rail from VBUS.
4. With battery and USB both present, 5V_SYS ≈ 5.115 - 0.35 = 4.76 V from the battery and 5.0 - 0.35 = 4.65 V from USB, so the battery path carries essentially all the current. Sharing near equality is harmless.

**Diode: Nexperia PMEG4030ER** (40 V, 3 A, SOD-123W 2.6 x 1.7 mm, Tj 150 °C) [PMEG4030ER.pdf, 23 Jan 2023]:
- VF: 0.295 typ / 0.330 max at 0.1 A; 0.38/0.44 at 1 A. About **0.35 V at 0.5 A**.
- IR: 5 uA typ at 10 V, 25 °C. Chosen over the lower-VF PMEG3030EP, which leaks 190 uA at 5 V.
- D5 loss at 0.41 A: 0.14 W. With Rth(j-a) = 130 K/W on a 1 cm² pad, Tj = 50 + 18 = 68 °C.
- D4 on USB: 0.14 W. Rated 3 A, against a requirement of at least 1 A.

**VBUS details:**
- Add a **100 kOhm bleeder from VBUS to GND** (after the USB ESD device). D4's reverse leakage (5V_SYS to VBUS, uA at 25 °C, up to about 0.5 mA hot) would otherwise float an unplugged VBUS up toward 4-5 V and confuse anything that looks at VBUS. (Rev B has no VBUS-detect pin; the bleeder is kept for a clean unplugged state.)
- Place 1 uF 25 V on VBUS. USB-C sinks must keep VBUS capacitance at or below 10 uF.

**Notes for users:**
- On USB only, LEDs, cameras, buzzer, GPS and the VTX are unpowered (no 10 V either). RX, MCU, sensors, flash (and OSD if fitted) run.
- The RX sees about 4.76 V on battery and about 4.65 V on USB; ELRS receivers (onboard LDOs) are fine. The GPS sees 5.115 V.

---

## 10. Analog inputs

### 10.1 VBAT divider
- R_top = **10.0 kOhm 1 %**, R_bot = **1.00 kOhm 1 %** (0603), ratio 11, so Betaflight **vbat_scale = 110** (and `vbat_divider/multiplier` defaults).
- Full scale is 3.3 V x 11 = 36.3 V, comfortably above 25.2 V.
- C = **100 nF** across R_bot. Source impedance is 10k || 1k = 909 Ohm, so fc = 1/(2π x 909 x 100n) = **1.75 kHz**. The cap also supplies the ADC sample charge.
- Divider current 2.29 mA at 25.2 V. R_top dissipates 52 mW, within a 0.1 W 0603 rating.
- Protection: R_top itself limits injection at the 42.1 V clamp to 0.25 mA (section 1.1).
- Leakage at 4S idle (16.8 V / 11k): 1.5 mA. That is a known storage drain; unplug packs.

### 10.2 Current sense (ESC CURR pin) and RSSI input (pin-map G0-09: mandatory protection)
- Series **10.0 kOhm** + **10 nF** to GND at the ADC pin (fc = 1.59 kHz), plus a **BAT54S** clamp (common node on the ADC pin, one diode
  to 3V3, one to GND).
- The 10 kOhm alone limits injection to (25.2 − 3.6)/10k = 2.16 mA if VBAT is mis-wired onto CURR/RSSI. The BAT54S keeps the pin within
  about −0.3 / 3.6 V so the injection goes through the Schottky rather than the MCU's ESD structure.
- BAT54S leakage (≤ 2 uA at 25 V, far less at 3.3 V) x 10 kOhm < 20 mV error. The 10 nF is 2500x the ADC sample cap.
- The same network is used on RSSI (PC5).

---

## 11. Buzzer driver

- Low-side **Nexperia PMV40UN2** (30 V, 3.7 A, SOT-23) [PMV40UN2.pdf]:
  - VGS(th) 0.4-0.9 V.
  - RDS(on) 36/44 mOhm at 4.5 V, 43/53 mOhm at 2.5 V. So it is fully enhanced from a 3.3 V GPIO.
  - VGS ±12 V.
- I rejected 2N7002/NX7002AK: VGS(th) up to 2.1-2.5 V and RDS(on) 3.7-5.2 Ohm at 5 V, so marginal from 3.3 V.
- Circuit:
  - 5V to buzzer+ pad; buzzer- pad to the PMV40UN2 drain; source to GND.
  - Gate: **100 Ohm** series from the PB2 node; the PB2 node carries the **10 kOhm BOOT1 pulldown** to GND (pinmap section 7), which also holds the gate off through reset. The series resistor sits between the PB2/pulldown node and the gate, never between the pulldown and the pin.
  - Flyback **PMEG4030ER** (reusing the D4/D5 MPN) across the buzzer, cathode on 5V. A magnetic buzzer's inductive kick is clamped to 5.1 + 0.4 V.
- Dissipation at 100 mA: 0.53 mW.
- Betaflight: GPIO high means the beeper sounds, so use `BEEPER_INVERTED` / `beeper_inversion = ON` as on most transistor-driven targets.
- Silent on USB-only (5V is battery-only).

---


## 12. Current, dissipation and thermal budget

### 12.1 Rail loads (design budget)

| Rail | Loads | Budget | Capability | Margin |
|---|---|---|---|---|
| 3V3 (LP38692) | MCU 120, flash 35, baro+mag 1, LEDs 6, misc 5 (+ OSD 72.5 only if fitted) | 170 mA (250 mA with OSD) | 1 A | ≥ 4x |
| 3V3_IMU (LP5907) | 2 IMUs | 10 mA | 250 mA | 25x |
| 5V_SYS (via D5 / D4) | 3V3 + IMU + RX 150 mA | 0.33-0.41 A | D 3 A | USB budget 0.5 A OK |
| 5V (U1) | 5V_SYS 0.41 + LED strip **0.80** + 2 cams 0.40 + GPS 0.10 + buzzer 0.08 | **1.79 A** | 1.96 A guaranteed (Eq. 7) | 0.17 A |
| 10V (U2) to VTX | HD VTX (O3 about 0.9 A, Walksnail/HDZero about 0.8-1 A) / analog | **1.5 A cont.** | 1.97 A guaranteed | 0.47 A |

LED strip: 0.8 A ≈ 13 WS2812 at full white; set `ledstrip_brightness` ≤ 50 % for longer strips. This replaces rev A's 1.0 A.

### 12.2 Loss model (from `gen/power_calc_lmr.py`)
Assumptions: RDS(on) at 25 C 303/133 mOhm (7.5) x 1.45 hot; switching edge total 10 ns (not specified by TI: an estimate); 30 mW
drive/IQ allowance; inductor loss = IRMS² x DCRmax + 50 mW core.

| Case | IC loss | Inductor | η | Tj at Ta 50 C (RθJA 29 EVM / 43 JEDEC) |
|---|---|---|---|---|
| 5 V 1.8 A, VIN 7.4 V (2S) | 1.26 W | 0.29 W | 85.6 % | 86 / 104 C |
| 5 V 1.8 A, 16.8 V (4S) | 1.01 W | 0.29 W | 87.6 % | 79 / 93 C |
| 5 V 1.8 A, 25.2 V (6S) | 0.99 W | 0.29 W | 87.8 % | 79 / 92 C |
| 5 V 2.0 A, 8.4 V (overload case) | 1.46 W | 0.35 W | 85 % | 92 / 113 C |
| 10 V 1.5 A, 16.8 V | 0.89 W | 0.25 W | 93.0 % | 76 / 88 C |
| 10 V 1.5 A, 25.2 V | 0.83 W | 0.25 W | 93.4 % | 74 / 86 C |
| 10 V 2.0 A, 16.8 V (peak) | 1.52 W | 0.40 W | 91.3 % | 94 / 115 C |

The board is 36 x 36 mm with two 1 W sources about 10 mm apart, so the effective RθJA will be nearer the JEDEC 43 C/W than the EVM's 29.
Every case stays below 150 C, and the hottest (2.0 A overload on 2S) is 113 C.

### 12.3 Other dissipators

| Part | P | θ | Tj |
|---|---|---|---|
| U4 LP38692 (170 mA, no OSD) | (4.76 − 3.3) x 0.17 = 0.25 W | 68.5 | 67 C |
| U4 with OSD (250 mA) | 0.36 W | 68.5 | 75 C |
| D5 PMEG4030ER (0.41 A) | 0.14 W | 130 | 68 C |
| VBAT divider | 0.06 W | | |

Board total worst case ≈ 1.3 + 0.95 + 0.6 (inductors) + 0.25 + 0.14 + 0.06 ≈ **3.3 W** (rev A: 4.2 W). Typical 4S ≈ 1.3 W.
Bench-testing at full LED + VTX load without airflow will still overheat the board; this goes in the user notes.

Thermal layout rules: each LMR38020 PowerPAD gets ≥ 6 x 0.3 mm thermal vias into L2 GND (TI layout 9.5); VIN/GND pins 1/3 with the
input caps on the same layer; SW copper kept minimal (no diode tab any more).

### 12.4 Battery-side current

| Case | IVBAT |
|---|---|
| 6S worst (5 V 1.8 A + 10 V 1.5 A) | (9.21/0.889 + 15.1/0.94)/25.2 ≈ **1.05 A** |
| 4S typical (5 V 1.0 A, 10 V 1.0 A) | ≈ 1.0 A |
| 2S worst (VIN 7.4 V; 5 V 1.8 A; VTX in dropout at 6.7 V x 1.5 A) | ≈ 1.43 + 1.5 ≈ **2.9 A** |

So the JST VBAT pin alone is not enough on 2S/4S with an HD VTX: the VBAT pads (section 5) are the primary input.

---

## 13. Bill of materials (power section)

DigiKey PNs and evidence: `design/parts_signal.md`, `review/sourcing_research_notes.md`, and the Gate 2 BOM (`bom/F405FC_digikey_bom.csv`).

| Ref | Qty | Value / function | MPN (manufacturer) | Package |
|---|---|---|---|---|
| D1 | 1 | TVS 26 V uni 600 W | SMBJ26A (Littelfuse) | SMB |
| U1, U2 | 2 | 80 V 2 A sync buck, FPWM + SS | LMR38020FSDDAR (TI) | HSOIC-8 PowerPAD |
| L1 | 1 | 6.8 uH 3 A 74 mOhm | 74438357068 (Würth WE-MAPI) | 4030 |
| L2 | 1 | 8.2 uH 2.8 A 86 mOhm | 74438357082 (Würth WE-MAPI) | 4030 |
| C1-C3 | 3 | 10 uF 50 V X7R | GRM32ER71H106KA12L (Murata) | 1210 |
| C4, C5 | 2 | 100 nF 100 V X7R | GRM188R72A104KA35D (Murata) | 0603 |
| Cout | 6 | 22 uF 25 V X5R (3 per rail) | CL31A226KAHNNNE (Samsung) | 1206 |
| Cboot, HF out | 4 | 100 nF 16 V X7R | CL05B104KO5NNNC (Samsung) | 0402 |
| RT | 2 | 34.8 k 1 % | RC0402FR-0734K8L (Yageo) | 0402 |
| RFBT | 2 | 100 k 1 % | RC0402FR-07100KL (Yageo) | 0402 |
| RFBB (5 V) | 1 | 24.3 k 1 % | RC0402FR-0724K3L (Yageo) | 0402 |
| RFBB (10 V) | 1 | 11.0 k 1 % | RC0402FR-0711KL (Yageo) | 0402 |
| RENT | 2 | 301 k 1 % | RC0603FR-07301KL (Yageo) | 0603 (sees up to 42 V) |
| RENB | 2 | 100 k 1 % | RC0402FR-07100KL (Yageo) | 0402 |
| Q2 | 1 | VTX-off N-FET 60 V | NX7002AKR (Nexperia) | SOT-23 |
| R (Q2 gate) | 1 + 1 | 1 k series, 100 k pulldown | RC0402FR-071KL / -07100KL | 0402 |
| U4 | 1 | LDO 3.3 V 1 A | LP38692MP-3.3/NOPB (TI) | SOT-223-5 |
| U5 | 1 | LDO 3.3 V low-noise | LP5907MFX-3.3/NOPB (TI) | SOT-23-5 |
| D4, D5, D8 | 3 | Schottky 40 V 3 A | PMEG4030ER (Nexperia, orderable PMEG4030ERX) | SOD-123W |
| D9, D10 | 2 | ADC clamp | BAT54S (Nexperia BAT54S,215 or onsemi) | SOT-23 |
| Q1 | 1 | Buzzer N-FET | PMV40UN2R (Nexperia) | SOT-23 |

---

## 14. Risks and open items

- **R1 (closed by rev B): JST-SH power contacts.** VBAT/GND and 10V/GND pads added (section 5). Users must solder battery leads to the pads
  (or confirm their ESC harness current); the bring-up guide says so.
- **R2 (closed by rev B): catch-diode temperature.** No catch diode. Worst-case IC Tj 104 C at the design budget (section 12.2).
- **R3 (decision): AT7456E sourcing.** See `design/decisions.md` D-01.
- **R4 (low): ceramic DC-bias derating.** Effective capacitance figures are estimates. Every requirement keeps ≥ 1.5x margin.
- **R5 (low): LP38692 θJA from a column-scrambled text extraction.** Re-read Table 6.4 from the PDF.
- **R6 (medium): requirement deviation** 5 V 2.5 A → 1.8 A continuous, 10 V 2 A → 1.5 A continuous (D-03). The LED strip budget is the
  item that absorbs it.
- **R7 (low): U2 high-side short** puts VBAT on the VTX output (section 4). No on-board part can be damaged by it.
- **R8 (low): switching-edge losses** use a 10 ns estimate (TI publishes no rise/fall time). Confirm the 5 V rail's case temperature
  on the bench at 1.8 A on 2S and 6S (bring-up guide).
- **R9 (low): WE-MAPI Isat** values disagree between sources (3.5-5.5 A); verify against the Würth datasheet at Gate 2.
