# F405-FC power architecture (Gate 0 design)

Source of truth for requirements: `design/requirements.md`. All datasheets referenced below are saved in
`datasheets/` (file name given in brackets). Equation numbers refer to the cited datasheet revision.
All calculations were done at the nominal switching frequency (800 kHz; the E96 RT gives 797 kHz, a 0.4 %
difference that does not change any conclusion). The script used is reproduced in Appendix A so every
number can be re-derived.

---

## 0. Summary

| Block | Part | Key numbers |
|---|---|---|
| VBAT TVS | Littelfuse **SMBJ26A** (SMB / DO-214AA) | VWM 26 V, VBR 28.9-31.9 V, VC 42.1 V @ 14.3 A |
| 5 V buck | TI **TPS54360BDDAR** (HSOIC-8 PowerPAD), 797 kHz | 5.11 V, 2.5 A design load, L = 4.7 uH (Coilcraft XGL5030-472MEC), catch diode Nexperia PMEG6030EP |
| 10 V buck | TI **TPS54360BDDAR** (same IC) | 10.0 V, 2 A, L = 8.2 uH (Coilcraft XGL5030-822MEC), PMEG6030EP |
| VTX pit switch | TI **TPS22810DBVR** load switch (SOT-23-6) | 18 V / 2 A, 79 mOhm, slew-controlled, default ON |
| 3.3 V main | TI **LP38692MP-3.3/NOPB** LDO (SOT-223-5) | 1 A rated, 250 mA budget, from 5V_SYS |
| 3.3 V IMU | TI **LP5907MFX-3.3/NOPB** LDO (SOT-23-5) | 82 dB PSRR @1 kHz, < 6.5 uVrms, 10 mA budget |
| USB / power OR | Nexperia **PMEG4030ER** x2 (SOD-123W) | dual-diode OR into a "5V_SYS" sub-rail (see section 8) |
| Buzzer | Nexperia **PMV40UN2** (SOT-23) + PMEG4030ER flyback | 30 V, 44 mOhm @ 4.5 V, Vth <= 0.9 V |

Why the TPS54360B and not the suggested LMR33630: the LMR33630 absolute-maximum VIN is **38 V**
([lmr33630.pdf] section 7.1). A TVS whose stand-off clears 25.2 V (26 V class) clamps at up to **42.1 V** at its rated
pulse current, so a 36/38 V-class buck cannot be protected by any TVS that also leaves a full 6S pack alone. The
TPS54360B is rated 60 V operating / **65 V absolute maximum** ([tps54360b.pdf] section 6.1), which gives 23 V of margin
over the TVS clamp. The trade-off is that it is non-synchronous (it needs an external catch Schottky), which costs about
0.6-0.9 W at worst case (sections 2, 11). I found no 60 V+, >= 3 A **synchronous** TI buck in a leaded package. The TI
LMR16030 (60 V, 3 A, SO-8 PowerPAD) is also non-synchronous. Section 13 lists synchronous upgrade options.

Block diagram:

```
 ESC conn VBAT ─┬─ (VBAT/GND solder pads recommended, see risk R1)
                │
             D1 SMBJ26A ── C 10u/50V (entry)
                │
        VBAT ───┼─────────────┬──────────────────────────┬── R 10k/1k → ADC_VBAT
                │             │                          │
        U1 TPS54360B (5V1)  U2 TPS54360B (10V)           (ESC side: external 470-1000 uF low-ESR electrolytic)
                │             │
          5V_MAIN (5.11 V)   10V ── U3 TPS22810 ── VTX_10V (HD VTX conn / analog VTX pad)
           │  │  │  │                 EN ← 10k pull-up to 3V3, PINIO GPIO pulls low = pit/off
           │  │  │  └── D5 PMEG4030ER ──┐
           │  │  └── Buzzer (+)          │
           │  └── LED strip 5V pad       ├── 5V_SYS (≈4.75 V on battery, ≈4.65 V on USB)
           └── CAM1 / CAM2 5V pads       │      ├── U4 LP38692-3.3 → 3V3 (MCU, flash, OSD, baro, mag, LEDs)
                                         │      ├── U5 LP5907-3.3  → 3V3_IMU (ICM-42688-P, BMI270)
 USB-C VBUS ── D4 PMEG4030ER ────────────┘      ├── RX 5V pad (ELRS)
                                                └── GPS 5V pad
```

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
| VC @ IPP = 14.3 A | 42.1 V max | < 50 V ceramic rating, < 60 V catch-diode VR, < **65 V** TPS54360B VIN abs max. Only the bucks, input caps, EN dividers (zener-clamped), VBAT divider and the ESC connector sit on VBAT. |
| Dynamic resistance (derived) | (42.1 - 31.9) / 14.3 = 0.71 Ohm | Clamp at 5 A is about 31.9 + 5 x 0.71 = **35.5 V**; at 1 A about 32.6 V |

Margin summary at the worst-case clamp (42.1 V):
- TPS54360B VIN: 65 V abs max, 22.9 V margin.
- TPS54360B EN pin: 8.4 V abs max. The UVLO divider would put 8.71 V on EN at 42.1 V, so a **6.2 V zener clamps EN** (section 2.7).
- PMEG6030EP catch diode: VR 60 V, 17.9 V margin.
- 50 V X7R input ceramics: 7.9 V margin. 42.1 V is the worst case at full rated pulse current; realistic ESC regen pulses clamp near 32-36 V.
- VBAT ADC pin: 42.1 / 11 = 3.83 V. The pin's ESD diode clamps it, with injection current (42.1 - 3.6)/10k - 3.6/1k = **0.25 mA**, far below the STM32 ±5 mA IINJ limit (DS8626 section 6.2).

Note that there is no reverse-polarity protection. A reversed pack forward-biases the TVS, which will short and probably fail as
the indicator; this is normal for FPV FCs because polarity is set by the ESC harness.

### 1.2 Input ceramics

| Ref | Value | MPN | Placement | Effective C at 25.2 V |
|---|---|---|---|---|
| C1 | 10 uF 50 V X7R 1210 | Murata GRM32ER71H106KA12L | Board entry, next to D1 | ~4.5 uF (estimate, roughly -55 % DC bias; check with Murata SimSurfing) |
| C2 | 10 uF 50 V X7R 1210 | GRM32ER71H106KA12L | U1 VIN-GND, inside the hot loop with D2 anode | ~4.5 uF |
| C3 | 10 uF 50 V X7R 1210 | GRM32ER71H106KA12L | U2 VIN-GND | ~4.5 uF |
| C4, C5 | 100 nF 50 V X7R 0603 | Murata GRM188R71H104KA93D | U1/U2 VIN pin, closest | HF bypass |

Checks against the TPS54360B datasheet section 8.2.2.6:
- At least 3 uF effective per IC is required: about 4.5 uF each from C2/C3, plus the shared C1.
- Voltage rating must exceed VIN max: 50 V > 42.1 V clamp.
- RMS ripple current (Eq. 38, worst at D = 0.5): 5 V rail 1.25 A at VIN about 10.2 V; 10 V rail 1.00 A at VIN = 20 V. A 1210 X7R with ESR of a few mOhm dissipates only milliwatts.
- Input ripple (Eq. 39, ΔVIN = IOUT x 0.25 / (CIN x fSW)) with 4.5 uF: 174 mV p-p (5 V rail), 139 mV p-p (10 V rail). Both acceptable.

**External bulk:** require a **low-ESR electrolytic of 470-1000 uF, 35 V minimum (50 V preferred for 6S)** across the ESC
battery pads. Most 4-in-1 ESCs ship one. It damps the LC formed by the battery leads and the ceramics on hot-plug, and it
absorbs most of the regen energy. The TVS is the backstop, not the primary absorber.

---

## 2. 5 V / 2.5 A buck (U1): TPS54360BDDAR

**Why this part:** 4.5-60 V operating input, 65 V abs max, 3.5 A continuous, 4.5 A minimum current limit, 92 mOhm high-side
FET, 100 kHz-2.5 MHz RT-set frequency, internal soft-start, adjustable UVLO, Eco-mode at light load
([tps54360b.pdf] SNVSB93, page 1). It is a leaded 8-pin HSOIC (4.9 x 3.9 mm) with a PowerPAD, which hand/hot-air
assembly can manage with a stencil. TI lists it as active. DigiKey lists TPS54360BDDA as 296-53086-ND, and
aggregators show DigiKey stock of the DDAR reel. Using the same IC for both bucks reduces the BOM.

Output setpoint: **5.11 V**, not 5.00 V. With 5.11 V on 5V_MAIN, 5V_SYS through D5 sits at about 4.75 V. That is roughly
equal to or above USB-through-D4 (4.65 V typ), so the battery path dominates whenever both are present (section 8).
5.11 V is within WS2812 VDD max (5.3 V) and the 5 V tolerance of RX/GPS/camera loads.

### 2.1 Switching frequency and RT
- Target 800 kHz. This keeps the 4.7 uH / 3.1 mm-tall inductor at K about 0.43, and switching loss stays moderate (0.35 W at 25.2 V).
- RT (Eq. 7) = 101756 / f(kHz)^1.008 = 101756 / 800^1.008 = **120.6 kOhm**, so use **121 kOhm 1 %**, which gives f = 92417 / 121^0.991 = **797 kHz** (Eq. 8).
- Pulse-skip limit (Eq. 9; datasheet Eq. 25 is the worked example), with tON(min) = 135 ns, RDS = 0.15 Ohm (hot), Rdc = 24.5 mOhm, Vd = 0.45 V:
  - at VIN 25.2 V: (2.5 x 0.0245 + 5.1 + 0.45) / (135n x (25.2 - 2.5 x 0.15 + 0.45)) = **1645 kHz**
  - at 42.1 V: **986 kHz**
  - Both are above 797 kHz, so there is no pulse skipping even at the TVS clamp. Minimum on-time at 25.2 V is D/f = 0.2024/800k = 253 ns, above 135 ns.
- Frequency-foldback limit (Eq. 10; worked example Eq. 26), with ICL = 6.8 A (max), VOUT(sc) = 0.1 V, fDIV = 8: **1724 kHz** at 25.2 V and **1023 kHz** at 42.1 V. Both are above 797 kHz, so short-circuit current stays controlled.
- Soft-start (Eq. 6): tSS = 1024 / 797 kHz = **1.28 ms**. Inrush to charge 28 uF to 5.1 V in 1.28 ms is 0.11 A.

### 2.2 Inductor: Coilcraft XGL5030-472MEC (4.7 uH, shielded composite, 5.48 x 5.28 x 3.1 mm)
Coilcraft table values at 25 °C: DCR 21.9 mOhm typ / 24.5 mOhm max; Isat 3.1 A at -10 %, 4.8 A at -20 %, 6.7 A at -30 %;
Irms 6.3 A for a 20 °C rise; rated 80 V.

- LO(min) (Eq. 28) = (VIN,max - VOUT) / (IOUT x K) x VOUT / (VIN,max x fSW). At 25.2 V, 2.5 A: K = 0.3 needs 6.78 uH, K = 0.4 needs 5.08 uH, K = 0.5 needs 4.07 uH.
  - 4.7 uH gives **K = 0.43**. That is above TI's 0.3 suggestion, but acceptable with ceramic output caps, and the ripple checks below pass.
  - The 6.8 uH XGL5030 part would give K = 0.3, but it saturates sooner (Isat10 % 2.5 A) and has a higher DCR.
- Ripple (Eq. 29) and peak (Eq. 31) at 2.5 A:

| VIN | D | ΔIL | Ipk | IL,rms (Eq. 30) |
|---|---|---|---|---|
| 6.0 V | 0.850 | 0.203 A | 2.60 A | 2.50 A |
| 8.4 V | 0.607 | 0.533 A | 2.77 A | 2.51 A |
| 12.6 V | 0.405 | 0.807 A | 2.90 A | 2.51 A |
| 16.8 V | 0.304 | 0.945 A | 2.97 A | 2.52 A |
| 25.2 V | 0.202 | 1.082 A | 3.04 A | 2.52 A |

- ΔIL is at least 150 mA (TI section 8.2.2.3 minimum for stable PWM) across the whole 2S-6S range.
- Peak current: 3.04 A against Isat(-10 %) = 3.1 A at full load. During overload the switch current limit (4.5-6.8 A) stays at or below Isat(-30 %) = 6.7 A. Composite cores saturate softly, so cycle-by-cycle limiting still works: the extra overshoot from the 60 ns limit delay is VIN/L x 60 ns ≈ 0.4 A at 30 V with L derated to 4.7 uH x 0.7.
- Height 3.1 mm is within the 3.5 mm top-side limit. The footprint is 5.5 mm, slightly over the 5 x 5 mm wish; XGL4030 (4 x 4 x 3.1 mm) is the fallback if space forces it, at the cost of higher DCR.

### 2.3 Output capacitors
Requirements (TPS54360B section 8.2.2.4):
- Load-step droop (Eq. 32), 1 A step (LED strip), 4 % (0.204 V): COUT > 2 x 1 / (800k x 0.204) = **12.25 uF**
- Unload overshoot (Eq. 33), 2.0 A to 0.5 A, 4 %: COUT > 4.7u x (2.0² - 0.5²) / (5.304² - 5.1²) = **8.30 uF**
- Ripple (Eq. 34), 0.5 % (25.5 mV), ΔIL = 1.082 A: COUT > **6.63 uF**. ESR (Eq. 35) must be < 25.5 mV / 1.082 A = **23.6 mOhm**.
- RMS ripple current (Eq. 36): **312 mA**

**Chosen: 2 x 22 uF 25 V X5R 1206 (Samsung CL31A226KAHNNNE)**, about **28 uF effective** at 5.1 V (assumes about -36 % DC bias per cap).
That is more than twice the most stringent requirement (12.25 uF). ESR is about 2-3 mOhm. A 25 V rating was chosen over
10 V/16 V so the same MPN serves the 10 V rail (BOM reduction).

### 2.4 Feedback divider (Eq. 3: RHS = RLS x (VOUT - 0.8)/0.8)
RLS = 10.2 kOhm gives RHS = 54.83 kOhm, so use **54.9 kOhm**.
- VOUT = 0.8 x (1 + 54.9/10.2) = **5.106 V**.
- Tolerance stack with VREF 0.792-0.808 V and 1 % resistors: 4.97-5.25 V.
- Divider current 78 uA, well above the 1 uA minimum (section 8.2.2.9).

### 2.5 Compensation (section 8.2.2.11, Type 2A: R4 + C5 from COMP to GND, C8 in parallel)
Inputs: COUT,eff = 28 uF, ESR = 2.5 mOhm, gmps = 12 A/V, gmea = 350 uA/V, VREF = 0.8 V.
- fp(mod) (Eq. 44) = IOUT / (2π VOUT COUT) = 2.5 / (2π x 5.1 x 28u) = **2786 Hz**
- fz(mod) (Eq. 45) = 1 / (2π ESR COUT) = **2274 kHz**
- fco: Eq. 46 √(fp fz) = 79.6 kHz; Eq. 47 √(fp x fsw/2) = **33.4 kHz**. Use the lower value, 33.4 kHz (about fsw/24).
- R4 (Eq. 48) = (2π fco COUT / gmps) x (VOUT / (VREF gmea)) = 8915 Ohm, so use **8.87 kOhm**
- C5 (Eq. 49) = 1 / (2π R4 fp) = 6.44 nF, so use **6.8 nF** X7R. The zero lands at 2.64 kHz, just below fp.
- C8 = max(Eq. 50: COUT x ESR / R4 = 7.9 pF; Eq. 51: 1/(R4 fsw π) = 44.9 pF), so use **47 pF** C0G.

The datasheet notes that this method ignores slope compensation, so the real crossover is lower than calculated. Verify
with a load-step test (or WEBENCH) on the first build.

### 2.6 Bootstrap capacitor
**100 nF X7R, at least 10 V** (section 7.3.4 and 8.2.2.7). Use the same 0603 50 V part as the bypass caps (GRM188R71H104KA93D).

### 2.7 EN / UVLO divider (Eqs. 4 and 5) and EN clamp
Target: start about 5.6 V, stop about 4.4 V. A deliberately low stop threshold keeps the FC alive through deep 2S sag:
at VIN = 4.4 V, 5V_MAIN is about 3.9 V and 5V_SYS about 3.5 V, which is just enough for the 3.3 V LDO.
- RUVLO1 (Eq. 4) = (VSTART - VSTOP) / IHYS = 1.2 V / 3.4 uA = 353 kOhm, so use **357 kOhm**
- RUVLO2 (Eq. 5) = VENA / ((VSTART - VENA)/RUVLO1 + I1) = 1.2 / ((5.6 - 1.2)/357k + 1.2u) = 88.73 kOhm, so use **88.7 kOhm**
- Nominal thresholds: VSTART = VEN + R1 (VEN/R2 - I1) = **5.60 V**; VSTOP = VSTART - R1 x IHYS = **4.39 V**
- Worst-case stack using the datasheet min/max for VEN (1.1-1.3 V), I1 (0.58-1.8 uA) and IHYS (2.2-4.5 uA): start 4.88-6.33 V, stop 3.28-5.54 V.
  - The spread comes from the EN current sources, not the resistors.
  - Even the worst-case start (6.33 V) is below a resting 2S pack (>= 7.0 V). The worst-case stop (5.54 V) is still below a 2S pack at 3.0 V/cell under load.
- Divider current at 25.2 V: 56.5 uA.
- **EN overvoltage:** the EN node is (VIN/R1 + I1 + IHYS) / (1/R1 + 1/R2). That gives 5.34 V at 25.2 V, 7.29 V at 35 V, and **8.71 V at 42.1 V**, above the 8.4 V EN abs max.
  - Section 7.3.7 recommends a zener. Add **D3 = BZT52C6V2-7-F (Diodes Inc, SOD-123), cathode on EN**.
  - At 25.2 V, EN = 5.34 V is below the zener's 5.8 V minimum VZ, so no current flows in normal operation and the UVLO is unaffected (EN is only 1.2 V near the thresholds).
  - At 42.1 V the zener carries about 35 uA and holds EN at about 6.2-6.6 V.

The same R1/R2/zener values are used on U2 (10 V buck), which keeps the BOM to one set of values.

### 2.8 Catch diode: Nexperia PMEG6030EP (60 V, 3 A, SOD128 / CFP5, Tj max 150 °C) [PMEG6030EP.pdf, 20 Feb 2023]
- VR 60 V, which is at least 42.1 V clamp (section 8.2.2.5 recommends a 60 V diode).
- IF(AV) 3 A, above the average diode current (1 - D) x IOUT = 0.8 x 2.5 = 2.0 A. IFSM is 50 A.
- VF (Table 8): 0.43 V typ / 0.50 V max at 2 A; 0.46 / 0.53 at 3 A. Cd is 120 pF at 10 V.
- Leakage at 60 V and 25 °C is 80 uA typ (the low-leakage "EP" grade). I rejected the lower-VF PMEG6045ETP because it leaks 70 mA typ / 300 mA max at 60 V and 125 °C, a thermal-runaway risk.
- Loss (Eq. 37) at 25.2 V, 2.5 A: (25.2 - 5.1)/25.2 x 2.5 x 0.45 + 120p x 800k x (25.2 + 0.45)² / 2 = 0.897 + 0.032 = **0.93 W**. Thermal analysis is in section 11 (this is the hottest part on the board at worst-case load).
- Rejected alternative: PMEG060V050EPD (5 A, CFP15, 3 K/W) has a better package but is **NRND at DigiKey**.

### 2.9 Minimum input voltage (Eq. 1) and dropout
VIN(min) = (VOUT + VF + Rdc x IOUT)/0.99 + RDS x IOUT - VF:
- at 2.5 A: **5.59 V**
- at 1.2 A: 5.37 V

So the 5 V rail regulates down to about 5.6 V on 2S (2.8 V/cell). Below that it tracks VBAT: at VIN = 5.0 V, VOUT ≈ 4.51 V at 2.5 A
and 4.77 V at 1 A, until UVLO stop (4.39 V nominal).

---

## 3. 10 V / 2 A buck (U2): TPS54360BDDAR

Same IC, RT (121 kOhm, 797 kHz), UVLO network, zener, boot cap, input cap and catch diode as U1.

### 3.1 Inductor: Coilcraft XGL5030-822MEC (8.2 uH, 5.48 x 5.28 x 3.1 mm)
Coilcraft table values: DCR 36.5 mOhm typ / 41.0 mOhm max; Isat 2.3 A at -10 %, 3.6 A at -20 %, 5.0 A at -30 %; Irms 4.8 A for a 20 °C rise.
- LO(min) (Eq. 28) at 25.2 V, 2 A: K = 0.3 needs 12.6 uH, K = 0.4 needs 9.42 uH, K = 0.5 needs 7.54 uH. 8.2 uH gives **K = 0.46**.
- 8.2 uH is a compromise between two limits:
  - Larger L keeps ripple above the 150 mA minimum closer to dropout, and gives more slope-compensation margin at D > 0.5 (VIN < 20 V).
  - The 10 uH part's Isat(-10 %) is only 2.1 A.

| VIN | D | ΔIL | Ipk @2 A |
|---|---|---|---|
| 11.0 V | 0.909 | 0.139 A (below 150 mA only within 0.5 V of dropout) | 2.07 A |
| 12.6 V | 0.794 | 0.315 A | 2.16 A |
| 16.8 V | 0.595 | 0.617 A | 2.31 A |
| 20.0 V | 0.500 | 0.762 A | 2.38 A |
| 25.2 V | 0.397 | 0.919 A | 2.46 A |

- Eq. 9 / Eq. 10 at 42.1 V: 1847 / 1183 kHz, both above 797 kHz.
- **Slope compensation:** the TPS54360B ramp is internal and not specified numerically (section 7.3.2). D > 0.5 happens on 3S and low 4S. Check for sub-harmonic oscillation on the bench at VIN = 12-16 V with a 2 A load. If any appears, go to 10 uH (XGL5030-103MEC).

### 3.2 Output capacitors
- Eq. 32 (1 A step, 4 % = 0.4 V): **6.25 uF**
- Eq. 33 (2.0 A to 0.5 A, 4 %): 3.77 uF
- Eq. 34 (50 mV ripple, ΔIL 0.919 A): 2.87 uF
- ESR < 54.4 mOhm; ICOUT,rms (Eq. 36) = 265 mA

**Chosen: 3 x 22 uF 25 V X5R 1206 (CL31A226KAHNNNE)**, about **27 uF effective** at 10 V (assumes about -59 % DC bias per cap).
That is 4.3x the requirement. The VTX's own input capacitance follows the load switch.

### 3.3 Feedback divider
RLS = 10.0 kOhm, RHS = 10k x 9.2/0.8 = **115 kOhm** (exact E96 value). VOUT = **10.00 V** (9.72-10.29 V over VREF and 1 % tolerances).

### 3.4 Compensation (COUT,eff = 27 uF, ESR 2.5 mOhm)
- fp(mod) = 2/(2π x 10 x 27u) = **1179 Hz**
- fz(mod) = 2358 kHz
- fco = min(52.7 kHz, **21.7 kHz**) = 21.7 kHz
- R4 (Eq. 48) = 10.96 kOhm, so use **11.0 kOhm**
- C5 (Eq. 49) = 12.27 nF, so use **12 nF**
- C8 = max(6.1 pF, 36.2 pF), so use **39 pF** C0G

### 3.5 Dropout behaviour on 2S and low 3S (documented limitation)
- Eq. 1 says the 10 V rail needs VIN at least **10.49 V at 2 A** (10.30 V at 1 A). So it regulates on 4S-6S and on 3S above about 3.5 V/cell.
- Below that, the TPS54360B goes to 100 % duty (section 7.3.4). The high-side FET stays on while BOOT-SW > 2.1 V, and the integrated BOOT recharge FET briefly pulls SW low to refresh the boot cap, so the effective duty is about 99 %.
- The output then follows VOUT ≈ 0.99 (VIN - RDS IOUT + VF) - VF - Rdc IOUT:

| VBAT | VTX rail @ 2 A | @ 1 A |
|---|---|---|
| 6.0 V (2S empty) | 5.56 V | 5.75 V |
| 7.4 V (2S nominal) | 6.94 V | 7.13 V |
| 8.4 V (2S full) | 7.93 V | 8.12 V |
| 11.1 V (3S nominal) | about 10 V, edge of regulation | regulating |

- **Consequence for 2S builds:** the VTX gets VBAT minus about 0.4 V. DJI O3 (7.4-26.4 V input) and some Walksnail units will brown out on 2S sag. Analog VTXs rated 5-36 V are fine.
- This is documented user-facing behaviour, not a fault. There is no over-voltage concern because the rail can never exceed VBAT.

---

## 4. VTX power switch (pit mode): TI TPS22810DBVR

**Why this part:**
- Single-chip load switch: 2.7-18 V operating, 20 V abs max, 79 mOhm typ / 115 mOhm max (-40..105 °C).
- 2 A continuous in SOT-23-6 (DBV) at TA = 65 °C.
- CT-programmable slew rate (limits inrush into an HD VTX's bulk caps).
- Thermal shutdown at 160 °C, quick output discharge, and an EN/UVLO pin with 1.13 V falling / 1.23 V rising thresholds, so it is directly 3.3 V-GPIO compatible ([tps22810.pdf] SLVSDH0C).
- Leaded SOT-23 package.

A discrete PMOS plus level shifter would need 3-4 parts plus an RC for inrush control and has no thermal protection.

**Default state decision: VTX ON at boot, GPIO actively pulls it OFF.**
- Circuit: EN has a 10 kOhm pull-up to 3V3, and the PINIO GPIO connects directly to EN.
- During MCU reset, DFU bootloader and early boot, the pin is a floating input, so the pull-up holds the VTX on.
- Reason: losing video because firmware is misconfigured, mid-flash, or in a brown-out reset is far worse than lacking pit mode. This matches common commercial practice ("VTX power default on, PINIO to cut").
- Betaflight: `resource PINIO 1 <pin>`, `set pinio_config = 129` (output, inverted), `set pinio_box = 40` (USER1).
  - USER1 inactive drives the pin HIGH (VTX on). Activating USER1 drives it LOW (VTX off, pit/power-cut).
  - GPIO low sinks 3.3 V/10k = 0.33 mA, and VOL is far below the 1.08 V minimum falling threshold.
  - EN "must not float" (section 9.3.1). The pull-up satisfies that.

**Values:**
- CIN = 1 uF 25 V X5R 0603 at the VIN pin (section 7.3 requires at least 1 uF). The 10 V buck output caps are adjacent.
- CT = **10 nF**: slew rate (Eq. 3) SR = 46.62 / CT(pF) = 4.66 V/ms, so 10-90 % of 10 V takes **1.72 ms** (Table 2 interpolates to 1.5-2.1 ms between 9 V and 12 V). Inrush into a 100 uF VTX input is 0.47 A; into 470 uF it is 2.2 A, briefly, inside the buck's current limit.
- QOD: left unconnected (discharge disabled). The VTX load discharges its own caps. A DNP 0402 pad from QOD to VOUT is optional.
- COUT at the VTX pad: 1 x 22 uF 25 V X5R 1206 (same MPN as the buck caps).

**Thermal:**
- P = I² RON. At 1 A that is 0.079 W typ / 0.115 W max; at 2 A, 0.32 W typ / **0.46 W max**.
- With the JEDEC θJA of 182 °C/W, the 2 A worst case gives Tj = 50 + 84 = 134 °C. With wide pours on the VIN/VOUT pins (θ about 110 °C/W estimated) it is about 101 °C. At 1 A (DJI O3 is about 0.9 A at 10 V) Tj ≈ 71 °C.
- Thermal shutdown protects it. Pour copper on pins 1 and 6.

**Risk:** the 20 V abs max VIN is fine for 10 V and for 2S dropout (8.4 V max). If U2's high-side FET ever failed short, the VTX
rail would rise to VBAT (up to 25.2 V) and destroy U3, and probably the VTX too. A 30 V discrete PMOS would survive
that particular double fault. I judged the slew control and thermal protection more valuable.

---

## 5. Camera supply

Both camera inputs (CAM1/CAM2) get a **5V_MAIN** pad (5.11 V, battery-only). Each analog camera draws about 150-200 mA, so the
budget is 0.4 A for both. No VBAT/10 V jumper (kept simple as instructed). Most analog FPV cameras accept 5-36 V, so 5 V is
universally safe. HD cameras are powered by the HD VTX itself.

---

## 6. 3.3 V main rail: TI LP38692MP-3.3/NOPB (SOT-223-5)

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

## 7. Low-noise 3.3 V for the IMUs: TI LP5907MFX-3.3/NOPB (SOT-23-5)

- Specs: 250 mA, 2.2-5.5 V input (6 V abs max), PSRR **82 dB at 1 kHz**, noise < 6.5 uVrms (10 uVrms at 1 mA, 10 Hz-100 kHz), dropout 120 mV typ, IQ 12 uA ([lp5907.pdf] SNVS798Q, Jul 2025, active).
- Fed from 5V_SYS (4.75 V max, within the 5.5 V limit). Its PSRR attenuates the buck ripple, which reaches 5V_SYS already filtered through D5.
- Load: ICM-42688-P (about 0.9 mA, 6-axis LN mode) + BMI270 (about 1 mA). Budget **10 mA**.
- P = (4.756 - 3.3) x 0.01 = 15 mW, so Tj rise is about 3 °C.
- Capacitors: CIN = 1 uF 25 V X5R 0603, COUT = **2.2 uF 16 V X7R 0603** (about 1.8 uF effective at 3.3 V; the allowed effective range is 0.7-10 uF, section 5.4). Each IMU keeps its own 100 nF local decoupling, which sums well under 10 uF.
- EN tied to IN.
- TI now points to TPS7A20 as the "more updated portfolio device". The LP5907 is still in production, so this is not an obsolescence flag.

---

## 8. USB VBUS path and 5V_SYS OR-ing

**Topology (deviation from a single diode, deliberate):** two PMEG4030ER Schottkys form a diode-OR into a sub-rail **5V_SYS**.
- **D4:** VBUS to 5V_SYS.
- **D5:** 5V_MAIN (buck output) to 5V_SYS.
- 5V_SYS feeds only the two LDOs, the RX 5V pad and the GPS 5V pad. LED strip, cameras and buzzer stay on 5V_MAIN.

Why:
1. **USB never powers the LED strip or the cameras.** Worst-case USB load is 5V_SYS = 0.25 (3V3) + 0.01 (IMU) + 0.15 (RX) + 0.10 (GPS) = **0.51 A**, typically about 0.32 A. That is close to the USB 2.0 500 mA budget without the LED strip's 1 A blowing it. The single-diode version would let a connected LED strip pull up to 1 A more from the laptop.
2. **No back-feed into VBAT on USB.** With a single diode onto the buck output, USB current flows back through the TPS54360B high-side FET body diode (SW to VIN) and raises VBAT to about 3.9 V. That powers the ESC MCUs and the VBAT divider from USB and makes VBAT read about 3.9 V. D5 blocks this path.
3. **No back-feed into the USB host.** D4 blocks the battery-side rail from VBUS.
4. With battery and USB both present, 5V_SYS ≈ 5.106 - 0.35 = 4.75 V from the battery and 5.0 - 0.35 = 4.65 V from USB, so the battery path carries essentially all the current. Sharing near equality is harmless.

**Diode: Nexperia PMEG4030ER** (40 V, 3 A, SOD-123W 2.6 x 1.7 mm, Tj 150 °C) [PMEG4030ER.pdf, 23 Jan 2023]:
- VF: 0.295 typ / 0.330 max at 0.1 A; 0.38/0.44 at 1 A. About **0.35 V at 0.5 A**.
- IR: 5 uA typ at 10 V, 25 °C. Chosen over the lower-VF PMEG3030EP, which leaks 190 uA at 5 V.
- D5 loss at 0.51 A: 0.18 W. With Rth(j-a) = 130 K/W on a 1 cm² pad, Tj = 50 + 23 = 73 °C.
- D4 on USB: 0.18 W. Rated 3 A, against a requirement of at least 1 A.

**VBUS details:**
- Add a **100 kOhm bleeder from VBUS to GND** (after the USB ESD device). D4's reverse leakage (5V_SYS to VBUS, uA at 25 °C, up to about 0.5 mA hot) would otherwise float an unplugged VBUS up toward 4-5 V and confuse VBUS sensing if it is used (PA9).
- Place 1 uF 25 V on VBUS. USB-C sinks must keep VBUS capacitance at or below 10 uF.

**Notes for users:**
- On USB only, LEDs, cameras, buzzer and the VTX are unpowered (no 10 V either). RX, GPS, MCU, sensors, flash and OSD run.
- RX and GPS see about 4.75 V on battery and about 4.65 V on USB. ELRS receivers and u-blox M10 modules (3.0/3.3-5.5 V inputs with onboard LDOs) are fine.
- If a GPS specified for 5.0 V ±5 % is used, power it from 5V_MAIN through a jumper instead.

---

## 9. Analog inputs

### 9.1 VBAT divider
- R_top = **10.0 kOhm 1 %**, R_bot = **1.00 kOhm 1 %** (0603), ratio 11, so Betaflight **vbat_scale = 110** (and `vbat_divider/multiplier` defaults).
- Full scale is 3.3 V x 11 = 36.3 V, comfortably above 25.2 V.
- C = **100 nF** across R_bot. Source impedance is 10k || 1k = 909 Ohm, so fc = 1/(2π x 909 x 100n) = **1.75 kHz**. The cap also supplies the ADC sample charge.
- Divider current 2.29 mA at 25.2 V. R_top dissipates 52 mW, within a 0.1 W 0603 rating.
- Protection: R_top itself limits injection at the 42.1 V clamp to 0.25 mA (section 1.1).
- Leakage at 4S idle (16.8 V / 11k): 1.5 mA. That is a known storage drain; unplug packs.

### 9.2 Current sense (ESC CURR pin)
- Series **10.0 kOhm** plus **10 nF** to GND at the ADC pin, fc = **1.59 kHz**.
- The 10 kOhm limits injection to (25.2 - 3.6)/10k = **2.16 mA** if VBAT is mis-wired onto CURR. That is below the ±5 mA IINJ rule; a 1 kOhm would allow 21.6 mA.
- The 10 nF is 2500x the 4 pF ADC sample cap, so sampling error is negligible.

### 9.3 RSSI / analog input
Same as 9.2: 10 kOhm series plus 10 nF.

---

## 10. Buzzer driver

- Low-side **Nexperia PMV40UN2** (30 V, 3.7 A, SOT-23) [PMV40UN2.pdf]:
  - VGS(th) 0.4-0.9 V.
  - RDS(on) 36/44 mOhm at 4.5 V, 43/53 mOhm at 2.5 V. So it is fully enhanced from a 3.3 V GPIO.
  - VGS ±12 V.
- I rejected 2N7002/NX7002AK: VGS(th) up to 2.1-2.5 V and RDS(on) 3.7-5.2 Ohm at 5 V, so marginal from 3.3 V.
- Circuit:
  - 5V_MAIN to buzzer+ pad; buzzer- pad to the PMV40UN2 drain; source to GND.
  - Gate: **100 Ohm** series from GPIO, **100 kOhm** gate-to-source pull-down. The low threshold means the gate must not float during reset.
  - Flyback **PMEG4030ER** (reusing the D4/D5 MPN) across the buzzer, cathode on 5V_MAIN. A magnetic buzzer's inductive kick is clamped to 5.1 + 0.4 V.
- Dissipation at 100 mA: 0.53 mW.
- Betaflight: GPIO high means the beeper sounds, so use `BEEPER_INVERTED` / `beeper_inversion = ON` as on most transistor-driven targets.
- Silent on USB-only (5V_MAIN is battery-only).

---

## 11. Current, dissipation and thermal budget

### 11.1 Rail loads (design budget)

| Rail | Loads | Budget | Capability | Margin |
|---|---|---|---|---|
| 3V3 (LP38692) | MCU, flash, OSD, baro, mag, LEDs | 250 mA | 1 A | 4x (thermally limited about 0.6 A) |
| 3V3_IMU (LP5907) | 2 IMUs | 10 mA | 250 mA | 25x |
| 5V_SYS (via D5 / D4) | 3V3 + IMU + RX 150 mA + GPS 100 mA | 0.51 A | D 3 A | ok; USB about 0.5 A |
| 5V_MAIN (U1) | 5V_SYS 0.51 + LED strip 1.0 + 2 cams 0.40 + buzzer 0.10 | **2.01 A** | 2.5 A design / 3.5 A IC | 0.49 A |
| 10V (U2) to VTX | HD VTX (O3 about 0.9 A, Walksnail/HDZero about 0.8-1 A) / analog | 2.0 A | 3.5 A IC; TPS22810 2 A | 0 A at 2 A (switch-limited) |

LED strip: a WS2812 draws about 60 mA at full white, so 1 A is about 16 LEDs at full white. Set a brightness cap in firmware.

### 11.2 Buck losses (TPS54360B section 8.2.2.13, Eqs. 52-55 for the IC; Eq. 37 for the diode)

Parameters: RDS = 0.15 Ohm (hot; 92 mOhm typ at 25 °C, Fig. 1), trise = VIN x 0.16 ns/V + 3 ns, QG = 3 nC, IQ = 146 uA,
VF = 0.45 V, Cj = 120 pF, inductor loss = (IL,rms²) x DCRmax + 0.05 W core-loss allowance.

**Worst case (5 V rail at 2.5 A, 10 V rail at 2.0 A):**

| VIN | 5V: IC (cond/sw/gd) | 5V: diode | 5V: L | 5V total | η5 | 10V: IC | 10V: diode | 10V: L | 10V total | η10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 6.0 V | 0.860 (0.797/0.048/0.014) | 0.171 | 0.203 | 1.234 W | 91.2 % | dropout | - | - | - | - |
| 8.4 V | 0.664 | 0.446 | 0.204 | 1.313 W | 90.7 % | dropout | | | | |
| 12.6 V | 0.538 | 0.678 | 0.204 | 1.420 W | 90.0 % | 0.609 | 0.194 | 0.214 | 1.018 W | 95.2 % |
| 16.8 V | 0.518 | 0.798 | 0.205 | 1.521 W | 89.3 % | 0.553 | 0.379 | 0.215 | 1.147 W | 94.6 % |
| 25.2 V | 0.608 (0.190/0.354/0.060) | 0.929 | 0.206 | **1.743 W** | 88.0 % | 0.586 | 0.574 | 0.217 | **1.377 W** | 93.6 % |

**Typical (5 V at 1.2 A, 10 V at 1.0 A):**

| VIN | 5V total | η5 | 10V total | η10 |
|---|---|---|---|---|
| 12.6 V | 0.596 W | 91.1 % | 0.394 W | 96.2 % |
| 16.8 V (4S) | 0.678 W | 90.0 % | 0.497 W | 95.3 % |
| 25.2 V (6S) | 0.828 W | 88.1 % | 0.662 W | 93.8 % |

These are loss-model estimates. The datasheet efficiency curve is for 12 V in. The 10 V figures exclude core loss beyond the
0.05 W allowance, so treat η10 as optimistic by about 1 %.

### 11.3 Junction temperature estimates (TA = 50 °C inside the frame, worst-case load at 25.2 V)

| Part | P | θ used | Tj | Limit |
|---|---|---|---|---|
| U1 TPS54360B | 0.61 W | 42 °C/W (JEDEC) to 55 °C/W (small board) | 76-83 °C | 150 °C |
| U2 TPS54360B | 0.59 W | 42-55 | 75-82 °C | 150 °C |
| D2 PMEG6030EP (5 V) | 0.93 W | 70 (4-layer, 1 cm² SW pour both sides, estimate) to 120 (datasheet, 1 cm² single-sided) | **115-161 °C** | **150 °C** |
| D2 at 2.0 A (realistic budget) | 0.75 W | 70-120 | 103-140 °C | 150 °C |
| D2 typical (1.2 A, 4S) | 0.39 W | 70 | 77 °C | |
| D6 PMEG6030EP (10 V) | 0.57 W | 70-120 | 90-119 °C | 150 °C |
| U4 LP38692 | 0.36 W | 68.5 | 75 °C | 125 °C (op) |
| U3 TPS22810 @2 A | 0.46 W | 110-182 | 101-134 °C | 150 °C (TSD 160) |
| U3 @1 A | 0.12 W | 182 | 71 °C | |
| D5 PMEG4030ER | 0.18 W | 130 | 73 °C | 150 °C |

Board totals:
- **Worst case about 4.2 W:** 1.74 + 1.38 + 0.36 + 0.46 + 0.18 + 0.06 divider + 0.02.
- **Typical 4S about 1.7 W.**
- In still air a 36 x 36 mm board cannot shed 4 W (natural convection gives θ(board-air) of the order of 30-40 K/W). In flight, prop wash brings that to about 5-8 K/W.
- **Bench-testing at full LED + VTX load without airflow will overheat the board.** This is normal for FPV FCs, but should be in the user notes.

Thermal design rules:
- U1/U2 PowerPAD: at least 9 thermal vias (0.3 mm) into the inner GND planes (section 10.1).
- D2 cathode tab is the SW node. Give it about 1 cm² on top plus a matching inner-layer island stitched with vias. This trades a little SW-node EMI area for diode Tj, so keep the island tight to the inductor.
- If measured Tj(D2) exceeds 130 °C at a sustained 2.5 A on 6S, apply section 13 option A.

### 11.4 Battery-side current

| Case | IVBAT |
|---|---|
| 6S worst (5 V 2.5 A + 10 V 2 A) | 1.43 A |
| 4S typical | 1.03 A |
| 2S worst (VIN 6 V, 5 V rail 2.33 A in + VTX constant-power 9 W at 5.6 V ≈ 1.6 A) | **about 3.9 A** |

See risk R1: the JST-SH VBAT pin is rated 1 A.

---

## 12. Bill of materials (power section)

DigiKey part numbers marked "verify" use DigiKey's usual pattern for the vendor but were not confirmed (digikey.com blocks
automated lookups). Before ordering, search the MPN on DigiKey, confirm the part is Active, and copy the cut-tape PN.

| RefDes class | Qty | Value / function | MPN (manufacturer) | Package (imperial) | V rating | DigiKey PN |
|---|---|---|---|---|---|---|
| D1 | 1 | TVS 26 V uni 600 W | SMBJ26A (Littelfuse) | SMB / DO-214AA | VWM 26 V | SMBJ26ALFCT-ND (verify; DigiKey product 285998) |
| U1, U2 | 2 | 60 V 3.5 A buck | TPS54360BDDAR (TI) | HSOIC-8 PowerPAD (DDA) | 60 V (65 abs) | 296-TPS54360BDDARCT-ND (verify); tube TPS54360BDDA = 296-53086-ND |
| D2, D6 | 2 | Catch Schottky 60 V 3 A | PMEG6030EP,115 (Nexperia) | SOD128 (CFP5) | 60 V | verify |
| L1 | 1 | 4.7 uH, 24.5 mOhm max, Isat 3.1/4.8/6.7 A | XGL5030-472MEC (Coilcraft) | 5.48 x 5.28 x 3.1 mm (2221) | 80 V | verify (DigiKey carries Coilcraft XGL) |
| L2 | 1 | 8.2 uH, 41 mOhm max, Isat 2.3/3.6/5.0 A | XGL5030-822MEC (Coilcraft) | 2221 | 80 V | verify |
| C1, C2, C3 | 3 | 10 uF X7R | GRM32ER71H106KA12L (Murata) | 1210 | 50 V | 490-GRM32ER71H106KA12L (verify suffix) |
| C (VIN HF, BOOT x2, 3V3 HF, VBAT ADC) | 6 | 100 nF X7R | GRM188R71H104KA93D (Murata) | 0603 | 50 V | verify |
| C (5V out x2, 10V out x3, VTX out x1) | 6 | 22 uF X5R | CL31A226KAHNNNE (Samsung) | 1206 | 25 V | 1276-CL31A226KAHNNNE (verify suffix) |
| C (5V_SYS bulk, LP38692 out) | 2 | 10 uF X5R | GRM21BR61A106KE19L (Murata) | 0805 | 10 V | verify |
| C (TPS22810 IN, LP38692 IN, LP5907 IN, VBUS) | 4 | 1 uF X5R | GRM188R61E105KA12D (Murata) | 0603 | 25 V | verify |
| C (LP5907 out) | 1 | 2.2 uF X7R | GRM188R71C225KE15D (Murata) | 0603 | 16 V | verify |
| C (CT, CURR, RSSI) | 3 | 10 nF X7R | GRM188R71H103KA01D (Murata) | 0603 | 50 V | verify |
| C5 (U1 comp) | 1 | 6.8 nF X7R | GRM188R71H682KA01D (Murata) | 0603 | 50 V | verify |
| C5' (U2 comp) | 1 | 12 nF X7R | GRM188R71H123KA01D (Murata) | 0603 | 50 V | verify |
| C8 (U1) | 1 | 47 pF C0G | GRM1885C1H470JA01D (Murata) | 0603 | 50 V | verify |
| C8' (U2) | 1 | 39 pF C0G | GRM1885C1H390JA01D (Murata) | 0603 | 50 V | verify |
| D3, D7 | 2 | EN clamp zener 6.2 V | BZT52C6V2-7-F (Diodes Inc) | SOD-123 | 6.2 V | BZT52C6V2-FDICT-ND (verify) |
| R (UVLO top) | 2 | 357 k 1 % | RC0603FR-07357KL (Yageo) | 0603 | 75 V | 311-357KHRCT-ND (verify) |
| R (UVLO bottom) | 2 | 88.7 k 1 % | RC0603FR-0788K7L (Yageo) | 0603 | | 311-88.7KHRCT-ND (verify) |
| R (RT) | 2 | 121 k 1 % | RC0603FR-07121KL (Yageo) | 0603 | | verify |
| R (U1 FB top) | 1 | 54.9 k 1 % | RC0603FR-0754K9L (Yageo) | 0603 | | verify |
| R (U1 FB bottom) | 1 | 10.2 k 1 % | RC0603FR-0710K2L (Yageo) | 0603 | | verify |
| R (U2 FB top) | 1 | 115 k 1 % | RC0603FR-07115KL (Yageo) | 0603 | | verify |
| R (U2 FB bottom, U3 EN pull-up, VBAT top, CURR, RSSI) | 5 | 10.0 k 1 % | RC0603FR-0710KL (Yageo) | 0603 | 75 V | 311-10.0KHRCT-ND (verify) |
| R4 (U1 comp) | 1 | 8.87 k 1 % | RC0603FR-078K87L (Yageo) | 0603 | | verify |
| R4' (U2 comp) | 1 | 11.0 k 1 % | RC0603FR-0711KL (Yageo) | 0603 | | verify |
| R (VBAT bottom) | 1 | 1.00 k 1 % | RC0603FR-071KL (Yageo) | 0603 | | verify |
| R (VBUS bleeder, buzzer gate pull-down) | 2 | 100 k 1 % | RC0603FR-07100KL (Yageo) | 0603 | | verify |
| R (buzzer gate series) | 1 | 100 Ohm 1 % | RC0603FR-07100RL (Yageo) | 0603 | | verify |
| U3 | 1 | Load switch 18 V 2 A | TPS22810DBVR (TI) | SOT-23-6 | 18 V (20 abs) | verify (296-...-ND) |
| U4 | 1 | LDO 3.3 V 1 A | LP38692MP-3.3/NOPB (TI) | SOT-223-5 | 10 V | LP38692MP-3.3/NOPBCT-ND (verify; aggregator shows DigiKey ...DKR-ND stock) |
| U5 | 1 | LDO 3.3 V low-noise | LP5907MFX-3.3/NOPB (TI) | SOT-23-5 | 5.5 V | verify |
| D4, D5, D8 | 3 | Schottky 40 V 3 A (USB OR x2, buzzer flyback) | PMEG4030ER (Nexperia; orderable suffix per DigiKey, e.g. PMEG4030ERX) | SOD-123W | 40 V | verify |
| Q1 | 1 | N-MOSFET 30 V logic-level | PMV40UN2R (Nexperia) | SOT-23 | 30 V | verify |

---

## 13. Risks and open items

**R1 (high): JST-SH power contacts.**
- JST SH contacts are rated **1 A** (AWG #28). The ESC connector carries all board power on one VBAT pin:
  - 6S worst case 1.43 A; 4S typical 1.03 A; 2S worst about 3.9 A.
- The HD VTX connector's single 10 V pin carries up to 2 A by design. DJI O3 at about 0.9 A is OK.
- **Recommendation:** add VBAT+GND solder pads (2 mm) as the primary power input, with the SH VBAT pin in parallel. Add a 10V/GND pad pair for analog VTXs above 1 A.
- This affects requirements.md.

**R2 (medium): catch-diode temperature at sustained 2.5 A on 6S** (D2 Tj estimate 115-161 °C against a 150 °C limit).
- Mitigation in place: copper/vias on the SW island; the realistic budget is 2.0 A (Tj 103-140 °C).
- Option A, if the bench measurement is bad: replace U1 with a 65 V synchronous buck such as ADI **LT8641** (65 V, 3.5 A, 3 x 4 mm LQFN). It needs no catch diode, and total 5 V loss drops to about 1.1 W. Cost: a fine-pitch QFN and about $6.
- Option B: limit the LED strip to 0.5 A.

**R3 (medium): AT7456E sourcing.** The AT7456E is a ZHONGKEWEI clone of the obsolete MAX7456 and is **not a DigiKey catalogue
part** as far as I could find (LCSC C82351). This conflicts with the "every part at DigiKey" rule and needs a decision at the
requirements level. Power-wise it fits on 3V3 (72.5 mA max).

**R4 (low): ceramic DC-bias derating.** Effective capacitances (22 uF/25 V 1206: about 14 uF at 5.1 V, about 9 uF at 10 V;
10 uF/50 V 1210: about 4.5 uF at 25 V) are engineering estimates. Confirm with the Samsung/Murata tools. Every requirement has
at least 2x margin, so even a 30 % miss is safe.

**R5 (low): datasheet text-extraction ambiguity.** The LP38692 SOT-223 θJA (68.5 °C/W) came from a column-scrambled text
extraction of Table 6.4. Re-read it from the PDF.

**R6 (low): slope compensation on the 10 V rail at D > 0.5.** See section 3.1. Bench-check at 12-16 V and 2 A.

**R7 (low): UVLO spread.** EN current-source tolerances give a start of 4.9-6.3 V and a stop of 3.3-5.5 V (section 2.7). It is
functional across the full spread.

**R8 (low): TPS22810 double fault.** If U2's high side shorts, the VTX rail sees VBAT, above U3's 20 V abs max (section 4).

---

## Appendix A: calculation script (Python, standard library only)

Full script: `gen/power_calc.py` (run `python -I gen/power_calc.py`). Note: its first UVLO block uses the superseded 6.0/5.2 V targets; the final values (357 k / 88.7 k, 5.60 / 4.39 V) are in section 2.7. The core formulas are below.

```python
fsw=800e3; ton=135e-9; gmps=12; gmea=350e-6; vref=0.8; VFd=0.45; RDS=0.15; Cj=120e-12
# Eq.7  RT_k = 101756/(fsw_k**1.008);   Eq.8 fsw_k = 92417/(RT_k**0.991)
# Eq.9  fskip  = (Io*Rdc+Vo+Vd)/(ton*(Vin-Io*RDS+Vd))
# Eq.10 fshift = 8*(ICL*Rdc+Vosc+Vd)/(ton*(Vin-ICL*RDS+Vd))      ICL=6.8, Vosc=0.1
# Eq.28 Lmin = (Vin-Vo)/(Io*K)*Vo/(Vin*fsw);  Eq.29 dIL = Vo*(Vin-Vo)/(Vin*L*fsw)
# Eq.32 C>2*dIstep/(fsw*dV); Eq.33 C>L*(Ioh^2-Iol^2)/(Vf^2-Vi^2); Eq.34 C>dIL/(8*fsw*Vrip); Eq.35 ESR<Vrip/dIL
# Eq.44 fp=Io/(2pi*Vo*C); Eq.45 fz=1/(2pi*ESR*C); Eq.46/47 fco=min(sqrt(fp*fz), sqrt(fp*fsw/2))
# Eq.48 R4=(2pi*fco*C/gmps)*(Vo/(vref*gmea)); Eq.49 C5=1/(2pi*R4*fp); Eq.50/51 C8=max(C*ESR/R4, 1/(R4*fsw*pi))
# Eq.4  R1=(Vstart-Vstop)/3.4u;  Eq.5 R2=1.2/((Vstart-1.2)/R1+1.2u)
# Eq.1  Vinmin=(Vo+Vf+Rdc*Io)/0.99+RDS*Io-Vf
# Eq.37 Pd=(Vin-Vo)*Io*Vf/Vin + Cj*fsw*(Vin+Vf)^2/2
# Eq.52-55 Pic = Io^2*RDS*Vo/Vin + Vin*fsw*Io*(Vin*0.16n+3n) + Vin*3n*fsw + Vin*146u
```
