# F405-FC power architecture (Gate 0 design, rev B; rev C changes from Gate 3 and later; rev D = 6-layer board, D-27)

Source of truth for requirements: `design/requirements.md`. Datasheets are in `datasheets/` (file name in brackets).
Rev B (2026-10-11) replaces both TPS54360B non-synchronous bucks with the synchronous TI **LMR38020FSDDAR**, removes the
TPS22810 load switch (VTX power is now cut by disabling the 10 V buck), and adds VBAT/GND and 10V/GND solder pads.
Rev A is in git history (commit d33a98e). **Rev C (Gate 3, D-19):** 2.1 mm max WE-MAPI 4020 5.6 uH inductors and 2.0 mm 1210
input caps (TDK 4.7 uF 100 V, G2R-01) for the 2.5 mm bottom-height limit; 10 V budget 1.3 A. Section 12 loss/thermal tables still use the rev B 1.5 A / 4030 figures
(conservative: the 10 V load is lower; inductor DCR loss is within 10 mW). All rev B numbers come from `gen/power_calc_lmr.py` (run `python3 -I gen/power_calc_lmr.py`).
Decisions and requirement deviations are logged in `design/decisions.md`.

---

## 0. Summary

| Block | Part | Key numbers |
|---|---|---|
| VBAT TVS | Littelfuse **SMBJ26A** (SMB) | VWM 26 V, VBR 28.9-31.9 V, VC 42.1 V @ 14.3 A |
| 5 V buck (U1) | TI **LMR38020FSDDAR** (HSOIC-8 PowerPAD), 750 kHz, FPWM + spread spectrum | 5.115 V, **1.8 A continuous design budget** (≥ 1.78 A worst-case current-limit floor at 6S incl. L/f tolerances, 1.71 A planned load), L = 5.6 uH (rev C, D-19) |
| 10 V buck (U2) | TI **LMR38020FSDDAR** (same IC) | 10.09 V, **1.3 A continuous** (≥ 1.38 A worst-case floor at 6S), L = 5.6 uH (rev C, D-19); EN also = VTX power switch |
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
  IOUTmax = ILS + dIL/2, ILS = 1.8 A min / 2.3 typ). With nominal inductance and frequency that is 1.96-2.20 A across 2S-6S (5 V) and
  1.97-2.13 A (10 V). Including −20 % inductance, −20 % RT/oscillator spread and the −8 % spread-spectrum dip (audit P0-03), the
  floor was **≥ 1.87 A (5 V)** and **≥ 1.78 A (10 V)** with the rev B 4030 inductors. **Rev C (Gate 3, D-19)** moved to 2.1 mm max WE-MAPI 4020
  5.6 uH parts on both rails for the 2.5 mm bottom-height limit; the larger ripple lowers the high-side peak-limit floor (IHS min 2.6 A − dIL,max/2)
  to **≥ 1.78 A (5 V)** and **≥ 1.38 A (10 V)** at 25.2 V, so the 10 V rail is now derated to **1.3 A continuous**. So the requirement "5 V / 2.5 A" is **derated to 1.8 A continuous** (section 12.1;
  the 1.71 A budget (section 12.1) leaves ≥ 0.16 A to the worst-case limit, so the LED-strip cap in firmware is mandatory, not advisory) and
  "10 V / 2 A" to **1.3 A continuous** (rev C; peaks to ~1.38 A guaranteed at 6S, ~1.9 A typical). The lead accepted these deviations (`design/decisions.md` D-03).
- **Thermals (section 12.5):** the per-IC Tj figures of section 12.2 are large-board values; on this 36 x 36 mm board the board-level
  model of section 12.5 governs, and full budgets are only allowed with in-flight airflow (D-12). In still air the board is limited to ≤ 1 W.
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
           └── CAM1 / CAM2 5V pads,      │      ├── U4 LP38692-3.3 → 3V3 (MCU, flash, baro, mag, LEDs)
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
| VR (stand-off) | 26.0 V | > 25.2 V (6S at 4.20 V/cell). LiHV 6S at 4.35 V/cell = 26.1 V is 0.1 V above VR but still 2.8 V below VBR(min), so leakage stays in the uA range. If LiHV support matters, use the SMBJ28A (VBR 31.1-34.4 V, VC 45.4 V; 45.4 V is still below the 50 V caps and the 85 V LMR38020). |
| VBR @ 1 mA | 28.9 V min, 31.9 V max | A 35 V regen spike is clamped (the TVS starts conducting at 28.9-31.9 V). |
| VC @ IPP = 14.3 A | 42.1 V max | < 50 V ceramic rating, < **85 V** LMR38020 VIN/SW abs max. Only the bucks, input caps, EN dividers, VBAT divider and the ESC connector sit on VBAT. |
| Dynamic resistance (derived) | (42.1 - 31.9) / 14.3 = 0.71 Ohm | Clamp at 5 A is about 31.9 + 5 x 0.71 = **35.5 V**; at 1 A about 32.6 V |

Margin summary at the worst-case clamp (42.1 V):
- LMR38020 VIN and SW: 85 V abs max, 80 V operating: 42.9 V margin. No catch diode exists any more.
- LMR38020 EN: abs max is VIN + 0.3 V, so the UVLO divider (10.5 V on EN at 42.1 V) needs no zener (section 2.6).
- 50 V X7R input ceramics: 7.9 V margin. 42.1 V is the worst case at full rated pulse current; realistic ESC regen pulses clamp near 32-36 V.
- VBAT ADC pin: 42.1 / 11 = 3.83 V. The pin's ESD diode clamps it, with injection current (42.1 - 3.6)/10k - 3.6/1k = **0.25 mA**, far below the STM32 ±5 mA IINJ limit (DS8626 section 6.2).

Note that there is no reverse-polarity protection (audit P0-09). A reversed pack forward-biases the TVS **and** both LMR38020 low-side
body diodes (VIN −0.3 V abs max), so both bucks are likely destroyed along with the TVS. The ESC harness sets polarity; the bring-up guide
requires a current-limited first power-up. The TVS fails short as
the indicator; this is normal for FPV FCs because polarity is set by the ESC harness.

### 1.2 Input ceramics

| Ref | Value | MPN | Placement |
|---|---|---|---|
| C1 | 10 uF 50 V X7R 1210 | Samsung CL32B106KBJNNNE (top side, 2.7 mm max is within 3.5 mm) | Board entry, next to D1 |
| C2+C3 (U1) / C10+C11 (U2) | 2 x 4.7 uF 100 V X7S 1210 per IC (2.0 mm, rev C) | TDK C3225X7S2A475K200AB | U1 / U2 VIN-GND, inside the hot loop (audit P0-06: two per IC so each meets 4.7 uF effective locally) |
| C4 / C5 | 100 nF 100 V X7R 0603 | Murata GRM188R72A104KA35D | U1 / U2 VIN pin, closest (datasheet 9.2.2.6: 100-220 nF HF bypass) |

- LMR38020 needs at least **4.7 uF effective** on VIN (9.2.2.6). A 10 uF/50 V 1210 keeps about 4.5 uF at 25 V, so each IC gets **two**
  (≈ 9 uF effective locally), plus the shared entry cap C1. Murata GRM32ER71H106KA12L was replaced by Samsung CL32B106KBJNNNE
  (DigiKey 1276-3387-1-ND) because one DigiKey listing showed the Murata part as discontinued. **Rev C (D-19):** the Samsung part is
  2.7 mm max, over the 2.5 mm bottom limit, so the four bottom-side caps are now TDK **C3225X7S2A475K200AB** (4.7 uF 100 V X7S, 2.0 ± 0.2 mm). The Murata GRM32DR71H106KA01L
  first chosen could not be found at any distributor (Gate 2 re-check G2R-01). A 100 V part keeps more of its value at 25 V; the TDK DC-bias
  curve was not read (assume ≈ 3.5 uF effective each, ≈ 7 uF per IC, ≥ 4.7 uF required). C1 (top side) keeps CL32B106KBJNNNE.
  **Bring-up check:** measure VIN ripple at the U1/U2 VIN pins at full load on 6S (target < 250 mV p-p).
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
- Low-VIN foldback starts below 6.58 V (Eq. 6, tOFF-MIN 300 ns max). Below that the frequency drops toward about 140 kHz. With the 97 %
  maximum duty cycle the rail regulates down to VIN ≈ **6.25-6.4 V** at 1.8 A (audit P0-04); below that it tracks
  VOUT ≈ 0.97·VIN − IOUT·(RDS,HS,hot + DCR). A 2S pack under load (6.0 V) gives about 4.76-4.87 V at 1.8 A (power re-audit P0-04). `gen/power_calc_lmr.py` models 100 % duty and therefore overstates dropout outputs; the 97 % figures in this document are authoritative.

### 2.2 Inductor: Würth WE-MAPI 4020 74438356056 (5.6 uH, 4.1 x 4.1 x 2.1 mm max) — rev C (D-19); **ordered part since rev C Gate 5: WE-MAIA 78438356056** (DigiKey 732-11317-1-ND; ratings and land pattern not verified against its drawing; the analysis below uses the WE-MAPI figures)
- Rev B used the 4030 74438357068 (6.8 uH, 3.1 mm). Gate 3 (G3-01) found it breaks the **2.5 mm bottom-side limit**; the bucks sit on the
  bottom, so both rails now use the 2.1 mm max WE-MAPI 4020 74438356056. 5.6 uH is the largest 4020 value found in distributor listings.
- Würth figures (from distributor/search snippets quoting the datasheet; the PDF itself could not be downloaded): 5.6 uH ±20 %,
  **RDC 68 mOhm typ / 81 mOhm max**, Isat(10 %) **2.65 A typ**, Isat(30 %) 5.5 A typ, IR 2.8 A (catalog) / 3.85 A (datasheet), AEC-Q200.
  DigiKey PN not confirmed (G2R-02); alternate Würth WE-MAIA 78438356056 (DigiKey 732-11317-1-ND, same size and ratings).
- Eq. 11 sub-harmonic floor: LMIN = 0.25 x 5.1 / 750k = **1.70 uH**; 5.6 uH is 3.3x above.
- Ripple (nominal L/f): 0.38 A (7.4 V), 0.72 A (12.6 V), **0.97 A (25.2 V)** = K 0.54 of the 1.8 A budget (above TI's 20-40 % window; accepted:
  the LMR38020 is internally compensated for this range and the output ripple stays ≈ 6 mV with 42 uF effective).
- Peak at 1.8 A/25.2 V: 2.28 A; at 2.0 A: 2.48 A, below Isat(10 %) 2.65 A (to be confirmed). The HS current limit (2.6-3.8 A) is above
  Isat(10 %): the alloy core saturates softly and the valley limit + hiccup (8.3.8) end a short circuit.
- Worst-case current-limit floor (−20 % L, −20 % RT/oscillator, −8 % spread spectrum, IHS min 2.6 A): **1.78 A at 25.2 V** (HS-limited),
  1.95 A at 8.4 V. The 1.71 A planned load (section 12.1) keeps 0.07 A margin at 6S; the firmware LED-strip cap is mandatory.
- Coilcraft XGL5030 (rev A choice) is not obtainable at DigiKey ("no longer available at DigiKey"), so it is excluded.

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

### 3.1 Inductor: Würth WE-MAPI 4020 74438356056 (5.6 uH, 2.1 mm max) — rev C (D-19)
- Same part as L1 (rev B: 74438357082 8.2 uH 4030, 3.1 mm, over the bottom height limit).
- LMIN (Eq. 11) = 0.25 x 10.09 / 750k = 3.36 uH; 5.6 uH is 1.7x above.
- Ripple (nominal): 0.96 A (16.8 V), **1.44 A (25.2 V)**. Peak at 1.3 A/25.2 V = 2.02 A, below Isat(10 %) 2.65 A (to be confirmed).
- **Worst-case current-limit floor at 25.2 V: 1.38 A** (IHS min 2.6 A − dIL,max 2.45 A / 2); 1.79 A at 16.8 V. Nominal: 1.88 A at 25.2 V.
  Hence the 10 V continuous budget drops from 1.5 A to **1.3 A** (D-19). DJI O3 (≈ 0.9 A) and Walksnail/HDZero (0.8-1 A) fit.

### 3.2 Output capacitors
**3 x 22 uF 25 V X5R 1206** (CL31A226KAHNNNE), about 3 x 9 uF = 27 uF effective at 10 V. Datasheet Table 9-1 (12 V out): 1 x 22 uF
(400 kHz) or 2 x 10 uF (1 MHz). 27 uF is 1.2-2.7x those. Plus a 100 nF **100 V 0603** HF cap (C17; Gate 1 G1P-06).

### 3.3 Feedback
RFBT 100 kOhm, RFBB **11.0 kOhm** → **10.09 V** (9.76-10.43 V).

### 3.4 Dropout on 2S / 3S (requirement deviation D-11)
- Regulation without foldback needs VIN ≥ 13.0 V (Eq. 6). With foldback the frequency drops to ~140 kHz, but the **97 % maximum duty
  cycle** still applies (audit P0-02), so the rail regulates only above **VIN ≈ 11.3-11.5 V** at 1.5 A.
- Below that, VOUT ≈ 0.97·VIN − IOUT·(RDS,HS,hot + DCR): at 1.5 A about **6.2-6.35 V from 7.4 V** (2S nominal) and **7.2-7.3 V from 8.4 V**
  (2S full); 3S at 3.7 V/cell (11.1 V) gives about 9.9 V.
- **Consequence:** an HD VTX with a 7.4 V minimum (DJI O3) does **not** run reliably from the 10 V rail on 2S. Analog VTXs rated 5-36 V
  are fine. **2S HD builds must power the VTX from the VBAT pads** (wire to the VTX directly; pit-mode power cut is then unavailable).
  **Remove R41** (0R in series with J3 pin 1, D-16) on such builds so the HD harness's power pin cannot tie VBAT onto the 10 V node.
  This is logged as deviation D-11 and goes in the user guide. A VBAT/10V solder-jumper option was rejected: tying VBAT onto the
  regulated 10 V node back-drives U2 (FPWM sinks up to 0.9 A of reverse current) and defeats the pit-mode switch.
- The rail can never exceed VBAT.

---

## 4. VTX power switch (pit mode / power cut): buck enable

Rev A used a TPS22810 load switch after the 10 V buck. The audit (rev A R8) found that a shorted U2 high-side FET would put VBAT
(up to 25.2 V) on the TPS22810 (20 V abs max). Rev B **removes the TPS22810** and switches the **10 V buck itself** off through its EN pin:

- **Q2 = Nexperia NX7002AK** (60 V, SOT-23, VGS(th) 1.1-2.1 V [NX7002AK.pdf]) drain on U2 EN, source to GND.
- Gate driven from **PC15 / VTX_PWR_EN** through **R 1 kOhm**, with **100 kOhm gate pulldown** (gate side).
- **GPIO high → Q2 on → EN < 0.95 V → U2 off → VTX off.** GPIO low or floating (reset, ROM DFU, early boot) → Q2 off → U2 runs → VTX on.
  Losing video because firmware is mid-flash or misconfigured is worse than lacking pit mode; this matches commercial practice.
- EN with Q2 on at the 42.1 V clamp: Q2 sinks 42.1 V / 301 k = 140 uA. Any RDS(on) below 6.8 kOhm keeps EN under VEN-L min 0.95 V;
  the NX7002AK datasheet specifies 3/4.5 Ohm at VGS = 10 V and shows tens of ohms at most at VGS = 2.5-3 V (Fig. 8), so the margin is
  several orders of magnitude.
- Turn-on uses the LMR38020's internal 4 ms soft start (8.3.9) plus 18 ms OCP blanking, so inrush into a VTX's input caps is limited and
  start-up into a large capacitive load does not hiccup.
- PC15 is a low-drive pin (G0-08): the load is one SOT-23 gate (NX7002AK Ciss 15/20 pF typ/max, datasheet) through 1 kOhm, static, so the 2 MHz/30 pF/3 mA limits
  don't bind. The pinmap rule "CMOS-only loads on PC13-15" is met in spirit (a MOSFET gate is a capacitive CMOS-like load).
- **Betaflight:** `set pinio_config = 1,...` (output, not inverted), `pinio_box = 40` (USER1). USER1 inactive → pin LOW → VTX on.
  USER1 active → pin HIGH → VTX off. Pinmap section 6 is updated to match.
- **Double fault:** if U2's high-side FET fails short, the VTX sees VBAT and the 25 V output capacitors may be overstressed (R7). (The TPS22810
  is gone), and HD VTXs (DJI O3/O4, Walksnail, HDZero) accept 2S-6S directly. This is the residual risk (section 14).

---

## 5. Power entry pads

The ESC JST-SH VBAT pin is rated 1 A (JST SH, AWG 28). Rev B adds:

| Pads | Size | Net | Purpose |
|---|---|---|---|
| VBAT, GND (P1, P2) | 2.5 x 4.0 mm SMD each, **bottom side** (rev C, D-19), at the bottom edge; D1 (TVS) and C1 straddle them on the top | VBAT / GND | Primary power entry, solder 20-22 AWG. JST VBAT pin stays in parallel |
| 10V, GND (P3, P4) | 2.0 x 3.0 mm SMD each, top, right edge | 10V / GND | Analog VTX (> 1 A) or HD VTX by wire |
| 5V (P11) + GND (P4) | 1.5 x 2.0 mm | 5V / GND | WS2812 strip power; the LED strip shares P4 for GND (rev C, D-21) |

Current check: 6S worst-case board input is about 1.06 A (section 12.4), 2S worst case about 2.95 A. A 2.5 x 4 mm pad with 20 AWG carries
that easily. Rev C: P1 is stitched by 4 vias to D1/C1 on the top and to a VBAT copper zone on In2 (rev D: on In3; 8 mm wide from P1 to the U1 input
caps, a 1.6 mm drawn riser (about 1.5 mm filled) to three vias on the U2 input track C10-C12-U2 VIN, `gen/route.py` and
`gen/critical.py`, Gate 3 G3R-02 and Gate 6 G6S-01 review), plus the 0.8 mm B.Cu hot-loop copper at each buck. Routed power branches
(VBAT, 5V, 10V, VTX_PWR) stay on the 1 oz outer layers (Gate 6 G6S-04: 0.45 mm on 0.5 oz In2 would rise ~60-80 °C at 1 A per
IPC-2221). The M3 hole keepouts exclude all copper including pours (G6S-03). The BAT54S ADC clamps of section 10 were removed (D-23).

---

## 6. Camera and peripheral 5 V supply

- CAM1/CAM2 5V pads: on **5V** (5.115 V, battery only), about 0.2 A each.
- GPS 5V pin: on **5V** (battery only, G0-03).
- RX 5V pin: on **5V_SYS** (so the receiver works on USB for binding/config).
- LED strip 5V pad: on **5V** (never powered from USB).

---

## 7. 3.3 V main rail: TI LP38692MP-3.3/NOPB (SOT-223-5)

The analog OSD (AT7456E) was removed in rev C (`design/decisions.md` D-01); its 72.5 mA no longer loads 3V3.

**3V3 load budget:**

| Load | Typ | Budget (max) | Source |
|---|---|---|---|
| STM32F405RGT6 @168 MHz, all peripherals on | ~90 mA | 120 mA | DS8626 run-mode table (verify exact row) |
| W25N01GV (read/program) | 25 mA | 35 mA | Winbond DS |
| BMP390 + IIS2MDC | <1 mA | 1 mA | Bosch/ST DS |
| 3 x LEDs @ about 2 mA | 6 mA | 6 mA | |
| Pull-ups, misc | 2 mA | 5 mA | |
| **Total** | **~125 mA** | **~170 mA** | |

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
- CIN = 1 uF 25 V X5R 0603 within 1 cm (section 8.2.2.2.1), plus the 4.7 uF 5V_SYS bulk.
- COUT = **one 2.2 uF X5R 0603** (C20, Samsung CL10A225KO8NNNC) at the OUT pin. Datasheet 8.2.2.2: the output capacitor's ESR must be
  5-500 mOhm; a 1-2.2 uF ceramic is typically 10-40 mOhm, so the local cap itself is compliant, and the large 10 uF 0805 was removed.
  **Open risk (power re-audit P2-03):** at the regulator's loop bandwidth (< 100 kHz) trace inductance is negligible, so the loop also sees
  the rest of the 3V3 bank (≈ 12.6 uF incl. C29/C47 4.7 uF and the 100 nF decaps; C26 is 2.7 mm from U4), whose parallel ESR is below
  5 mOhm. TI also states (8.2.2.2) the LP38692 is "designed to work with very small ceramic capacitors" and is stable with no load; whether
  the distributed bank causes ringing is unproven. **Control:** bring-up load step 10 → 150 mA on 3V3 with a scope at U4 OUT: pass if
  ringing settles within 2 cycles and overshoot < 100 mV. **Fallback if it fails:** replace C29 and C47 (4.7 uF) with 1 uF parts and/or
  fit a 0.5-1 Ohm 0603 resistor in series with C29 (cut-and-bodge on rev C; a footprint in the next revision).

---

## 8. Low-noise 3.3 V for the IMUs: TI LP5907MFX-3.3/NOPB (SOT-23-5)

- Specs: 250 mA, 2.2-5.5 V input (6 V abs max), PSRR **82 dB at 1 kHz**, noise < 6.5 uVrms (10 uVrms at 1 mA, 10 Hz-100 kHz), dropout 120 mV typ, IQ 12 uA ([lp5907.pdf] SNVS798Q, Jul 2025, active).
- Fed from 5V_SYS (4.75 V max, within the 5.5 V limit). Its PSRR attenuates the buck ripple, which reaches 5V_SYS already filtered through D5.
- Load: ICM-42688-P (about 0.9 mA, 6-axis LN mode) + BMI270 (about 1 mA). Budget **10 mA**.
- P = (4.756 - 3.3) x 0.01 = 15 mW, so Tj rise is about 3 °C.
- Capacitors: CIN = 1 uF 25 V X5R 0603, COUT = **2.2 uF 16 V X7R 0603** (about 1.8 uF effective at 3.3 V; the allowed effective range is 0.7-10 uF, datasheet section 5.6). Each IMU keeps its own 100 nF local decoupling, which sums well under 10 uF.
- EN tied to IN.
- TI now points to TPS7A20 as the "more updated portfolio device". The LP5907 is still in production, so this is not an obsolescence flag.

---

## 9. USB VBUS path and 5V_SYS OR-ing

**Topology (deviation from a single diode, deliberate):** two PMEG4030ER Schottkys form a diode-OR into a sub-rail **5V_SYS**.
- **D4:** VBUS to 5V_SYS.
- **D5:** 5V (buck output) to 5V_SYS.
- 5V_SYS feeds only the two LDOs and the RX 5V pin. LED strip, cameras, GPS (G0-03) and buzzer stay on 5V (battery only).

Why:
1. **USB never powers the LED strip or the cameras.** Worst-case USB load is 5V_SYS = 0.17 (3V3) + 0.01 (IMU) + 0.15 (RX) = **0.33 A**, typically about 0.2 A. That is close to the USB 2.0 500 mA budget without the LED strip's 1 A blowing it. The single-diode version would let a connected LED strip pull up to 1 A more from the laptop.
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
- Place 1 uF 25 V on VBUS. USB 2.0 limits the capacitance a device presents at attach to 10 uF / 50 uC. Through D4 the host charges
  the whole 5V_SYS bank and, because neither LDO has a soft start, everything behind them: ≈ 30 uF, ≈ 110 uC (Gate 1 G1P-01, power
  re-audit P0-05). **This exceeds the USB inrush limit; accepted deviation D-14** (the same is true of essentially every FPV FC; hosts
  current-limit and tolerate it in practice). A VBUS soft-start load switch would fix it at the cost of board area.
- VBUS surge: the USBLC6-2SC6 VBUS pin is a clamp to GND (its internal Zener) and is the only VBUS surge protection; the LP5907 (6 V abs
  max) sits behind D4 (−0.35 V) and the 1 uF + 6.7 uF capacitance. The TPD2E2U06 alternate has **no** VBUS clamp, so it is **not** an
  acceptable substitute (Gate 2).

**Notes for users:**
- On USB only, LEDs, cameras, buzzer, GPS and the VTX are unpowered (no 10 V either). RX, MCU, sensors and flash run.
- The RX sees about 4.76 V on battery and about 4.65 V on USB; ELRS receivers (onboard LDOs) are fine. The GPS sees 5.115 V.

---

## 10. Analog inputs

### 10.1 VBAT divider
- R_top = **10.0 kOhm 1 %**, R_bot = **1.00 kOhm 1 %** (0402; it only sees ≤ 3.8 V), ratio 11, so Betaflight **vbat_scale = 110** (and `vbat_divider/multiplier` defaults).
- Full scale is 3.3 V x 11 = 36.3 V, comfortably above 25.2 V.
- C = **100 nF** across R_bot. Source impedance is 10k || 1k = 909 Ohm, so fc = 1/(2π x 909 x 100n) = **1.75 kHz**. The cap also supplies the ADC sample charge.
- Divider current 2.29 mA at 25.2 V. R_top dissipates 52 mW, within a 0.1 W 0603 rating.
- Protection: R_top itself limits injection at the 42.1 V clamp to 0.25 mA (section 1.1).
- Leakage at 4S idle (16.8 V / 11k): 1.5 mA. That is a known storage drain; unplug packs.

### 10.2 Current sense (ESC CURR pin) and RSSI input (pin-map G0-09: mandatory protection)
- Series **10.0 kOhm** + **10 nF** to GND at the ADC pin (fc = 1.59 kHz), plus a **BAT54S** clamp (common node on the ADC pin, one diode
  to 3V3, one to GND). **Removed in rev C (D-23): no clamp is fitted; the BAT54S text below is history.**
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
| 3V3 (LP38692) | MCU 120, flash 35, baro+mag 1, LEDs 6, misc 5 | 170 mA | 1 A | ≥ 5x |
| 3V3_IMU (LP5907) | 2 IMUs | 10 mA | 250 mA | 25x |
| 5V_SYS (via D5 / D4) | 3V3 + IMU + RX 150 mA | 0.33-0.41 A | D 3 A | USB budget 0.5 A OK |
| 5V (U1) | 5V_SYS 0.33 + LED strip **0.80** + 2 cams 0.40 + GPS 0.10 + buzzer 0.08 | **1.71 A** | ≥ 1.78 A worst case at 6S (rev C) | 0.07 A |
| 10V (U2) to VTX | HD VTX (O3 about 0.9 A, Walksnail/HDZero about 0.8-1 A) / analog | **1.3 A cont.** (rev C) | ≥ 1.38 A worst case at 6S | 0.08 A |

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
| U4 LP38692 (170 mA) | (4.76 − 3.3) x 0.17 = 0.25 W | 68.5 | 67 C (+ board rise, 12.5) |
| D5 PMEG4030ER (0.41 A) | 0.14 W | 130 | 68 C |
| VBAT divider | 0.06 W | | |

Power-stage total worst case ≈ 1.3 + 0.95 + 0.6 (inductors) + 0.25 + 0.14 + 0.06 ≈ **3.3 W** (rev A: 4.2 W); with the 3V3 loads
(≈ 0.5-0.6 W) the board total is ≈ **3.9 W** (section 12.5). Typical 4S ≈ 2.0 W including 3V3 loads.
Bench-testing at full LED + VTX load without airflow will still overheat the board; this goes in the user notes.

Thermal layout rules: each LMR38020 PowerPAD gets ≥ 6 x 0.3 mm thermal vias into L2 GND (TI layout 9.5); VIN/GND pins 1/3 with the
input caps on the same layer; SW copper kept minimal (no diode tab any more).

### 12.5 Board-level thermal model (audit P0-01 / re-audit P1-01) and operating envelope

**All numbers in this section are unvalidated engineering estimates** (no thermal simulation or measurement exists yet); the bring-up
thermal gate below is what validates them.

The per-IC Tj numbers in 12.2 use RθJA values measured on large boards (JEDEC 76 x 114 mm; TI EVM). On a 36 x 36 mm board all the heat
leaves through the board itself:

**T_board ≈ Ta + P_board · R_board-air**, **Tj(U1) ≈ T_board + P_U1 · R_ic-board**, with
- R_board-air: both faces of the board, 2 x 13 cm². Still air (h ≈ 10-15 W/m²K incl. radiation): **25-38 K/W**. In flight, prop wash of
  3-10 m/s (h ≈ 40-80 W/m²K): **5-10 K/W**.
- R_ic-board ≈ 20 C/W (LMR38020 RθJB 13.6 C/W, datasheet 7.4, plus spreading).
- P_board includes **every** dissipator: both bucks and inductors, D5, the VBAT divider, the LP38692 and the 3V3 loads themselves
  (MCU ≈ 0.3 W at 168 MHz, flash/sensors/LEDs ≈ 0.05 W) and the LDO drop (0.25 W): the 3V3 domain adds **≈ 0.5-0.6 W** (re-audit P1-01b).

| Case | P_board | P_U1 | Ta | Board rise | U1 Tj | T_board (MCU, IMU ambient) |
|---|---|---|---|---|---|---|
| In flight, worst case 6S/2S (5 V 1.8 A, 10 V 1.5 A, LED 0.8 A) | 3.9 W | 1.3 W | 50 C | 20-39 C | 96-115 C | **70-89 C** |
| In flight, hot-day envelope (≤ 3.0 W, see below) | 3.0 W | 1.0 W | 50 C | 15-30 C | 85-100 C | 65-80 C |
| In flight, typical 4S (5 V 1.0 A, 10 V 1.0 A) | 2.0 W | 0.6 W | 50 C | 10-20 C | 72-82 C | 60-70 C |
| Bench, still air, bench envelope (below) | 1.0 W | 0.25 W | 25 C | 25-38 C | 55-68 C | 50-63 C |
| Bench, still air, HD VTX at 1 A + LED off | 1.9 W | 0.35 W | 25 C | 48-72 C | 80-104 C | 73-97 C: **not allowed** |

The MCU (STM32F405RGT6) and both IMUs are rated to 85 C ambient. The upper estimate of the worst-case in-flight row (89 C) exceeds that,
so the envelope is restricted:

**Operating envelope (also in the bring-up/user guide):**
- **Flight, Ta ≤ 35 C:** full design budget (5 V 1.8 A, 10 V 1.5 A): T_board ≤ 74 C at the upper estimate.
- **Flight, Ta 35-50 C:** P_board ≤ 3.0 W, i.e. LED strip ≤ 0.4 A (or VTX ≤ 1.2 A): T_board ≤ 80 C.
- **Bench / still air:** **VTX off or in pit mode (PINIO USER1), LED strip off.** With RX + GPS + MCU + sensors only, P_board ≈ 0.9 W (typical);
  with two cameras added at budget current it rises to ≈ 1.4 W (power re-audit P2-01), board 61-79 C at 25 C ambient (upper estimate) and
  85 C at ≈ 31 C ambient. So: **bench work above ~25 C ambient, or with cameras powered for long sessions, needs a fan.** An HD VTX at
  normal power on the bench always needs a fan (standard practice for HD VTXs anyway).
- The STM32F405RGT7 (105 C ambient) would not raise the envelope, because the IMUs and baro are 85 C parts; it is therefore **not** offered
  as a thermal fix (re-audit P1-01d).

**Pass/fail thermal gate at bring-up (ambient-referenced, two-point, power re-audit P1-01c/P2-02):** fan at ~3 m/s, ambient Ta measured,
10 min per run, at (a) 2S 7.4 V and (b) 6S 25.2 V (on 2S the 10 V rail is in dropout):
- **Point 1, full budget** (5 V 1.8 A, 10 V 1.5 A, i.e. the Ta ≤ 35 C envelope): pass if **(MCU case − Ta) ≤ 45 K** and **(U1/U2 case − Ta)
  ≤ 65 K** → MCU ≤ 80 C, U1 ≤ 100 C at Ta = 35 C.
- **Point 2, hot-day budget** (≤ 3.0 W: LED strip 0.4 A, rest as point 1, i.e. the Ta 35-50 C envelope): pass if **(MCU case − Ta) ≤ 30 K**
  and **(U1/U2 case − Ta) ≤ 50 K** → MCU ≤ 80 C, U1 ≤ 100 C at Ta = 50 C.
If a point fails, lower that envelope's LED-strip budget until it passes and update this section.

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
| L1, L2 | 2 | 5.6 uH (rev C; figures of the WE-MAPI) | 78438356056 (Würth WE-MAIA; was 74438356056 WE-MAPI) | 4020 |
| C1 (VBAT entry) | 1 | 10 uF 50 V X7R | CL32B106KBJNNNE (Samsung) | 1210 |
| C2 C3 C10 C11 (2 per IC) | 4 | 4.7 uF 100 V X7S | C3225X7S2A475K200AB (TDK, rev C) | 1210 (2.0 mm) |
| C4, C12, C17 | 3 | 100 nF 100 V X7R (VIN HF ×2, 10 V out HF) | GRM188R72A104KA35D (Murata) | 0603 |
| Cout | 6 | 22 uF 25 V X5R (3 per rail) | CL31A226KAHNNNE (Samsung) | 1206 |
| Cboot, HF out | 4 | 100 nF 16 V X7R | CL05B104KO5NNNC (Samsung) | 0402 |
| RT | 2 | 34.8 k 1 % | ERJ-2RKF3482X (Panasonic; Yageo RC0402FR-0734K8L is not at DigiKey) | 0402 |
| RFBT | 2 | 100 k 1 % | RC0402FR-07100KL (Yageo) | 0402 |
| RFBB (5 V) | 1 | 24.3 k 1 % | ERJ-2RKF2432X (Panasonic; Yageo not at DigiKey) | 0402 |
| RFBB (10 V) | 1 | 11.0 k 1 % | RC0402FR-0711KL (Yageo) | 0402 |
| RENT | 2 | 301 k 1 % | RC0603FR-07301KL (Yageo) | 0603 (sees up to 42 V) |
| RENB | 2 | 100 k 1 % | RC0402FR-07100KL (Yageo) | 0402 |
| Q2 | 1 | VTX-off N-FET 60 V | NX7002AK,215 (Nexperia) | SOT-23 |
| R41 | 1 | 0R link, J3 pin 1 (remove for 2S HD builds) | RC0805JR-070RL (Yageo) | 0805 |
| R (Q2 gate) | 1 + 1 | 1 k series, 100 k pulldown | RC0402FR-071KL / -07100KL | 0402 |
| U4 | 1 | LDO 3.3 V 1 A | LP38692MP-3.3/NOPB (TI) | SOT-223-5 |
| U5 | 1 | LDO 3.3 V low-noise | LP5907MFX-3.3/NOPB (TI) | SOT-23-5 |
| D4, D5, D9 | 3 | Schottky 40 V 3 A (USB OR, 5V OR, buzzer flyback) | PMEG4030ER,115 (Nexperia) | SOD-123W |
| ~~D7, D8~~ | 0 | ADC clamp, removed (D-23) | ~~BAT54S-7-F~~ | - |
| Q1 | 1 | Buzzer N-FET | PMV40UN2R (Nexperia) | SOT-23 |

---

## 14. Risks and open items

- **R1 (closed by rev B): JST-SH power contacts.** VBAT/GND and 10V/GND pads added (section 5). Users must solder battery leads to the pads
  (or confirm their ESC harness current); the bring-up guide says so.
- **R2 (closed by rev B): catch-diode temperature.** No catch diode. Board-level thermal envelope in section 12.5.
- **R3 (closed): AT7456E sourcing.** Analog OSD removed (`design/decisions.md` D-01).
- **R4 (low): ceramic DC-bias derating.** Effective capacitance figures are estimates. Every requirement keeps ≥ 1.5x margin.
- **R5 (low): LP38692 θJA from a column-scrambled text extraction.** Re-read Table 6.4 from the PDF.
- **R6 (medium): requirement deviation** 5 V 2.5 A → 1.8 A continuous, 10 V 2 A → 1.5 A continuous (D-03), and 1.3 A since rev C (D-19). The LED strip budget is the
  item that absorbs it.
- **R7 (low, double fault): U2 high-side short** puts VBAT on the 10 V net (audit P0-08). The VTX sees VBAT, and the 25 V-rated 10 V
  output capacitors see up to 25.2 V (42 V during TVS-clamped transients) and may crack or fail short, which would then load VBAT through
  the failed FET. Accepted as a double fault (a shorted FET first); it is not a first-power-up risk.
- **R8 (low): switching-edge losses** use a 10 ns estimate (TI publishes no rise/fall time). Confirm the 5 V rail's case temperature
  on the bench at 1.8 A on 2S and 6S (bring-up guide).
- **R9 (low): WE-MAPI 4020 Isat(10 %)** 2.65 A **typical** (Würth figures via snippets, Gate 2 re-check), Isat(30 %) 5.5 A, is below the 2.6-3.8 A HS current limit; soft saturation and the valley limit + hiccup make this acceptable (section 2.2). The worst normal-load peak is 2.28 A (5 V, 1.8 A, 25.2 V).
- **R10 (medium): 10 V rail on 2S / low 3S** cannot reach 10 V (section 3.4, D-11). HD VTXs needing ≥ 7.4 V brown out on 2S.
- **R11 (medium): thermal in still air** (section 12.5). Bench running at full load without airflow is not allowed; the bring-up thermal test is a pass/fail gate.
- **R12 (medium, single fault): U1 high-side FET short** (Gate 1 G1P-07) puts VBAT (up to 25.2 V) on 5V and, through D5, on 5V_SYS: the
  LP38692 (10 V operating / 12 V abs max), LP5907 (6 V abs max), SN74LV1T125, cameras, GPS, RX and LED strip would be destroyed. There is
  no crowbar/OVP on 5V. Accepted for rev C (same as most FPV FCs); a 6.2 V TVS + fuse or an OVP switch on 5V is a respin option.
- **R13 (low): JST-SH pin current** (power re-audit P2-05): J3 pin 1 (10 V via R41) is a JST-SH contact rated 1 A. HD VTXs drawing > 1 A
  (or analog VTXs at high power) must use the 10V/GND pads, not the connector. R41 (0805 0R jumper, Yageo rating 2 A — datasheet not on
  file) dissipates < 0.1 W at 1.5 A.
- **R14 (low): LP38692 output network stability** (section 7, P2-03): bring-up load-step test with a documented fallback.
