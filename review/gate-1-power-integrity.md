# Gate 1 schematic review: power integrity (F405-FC rev C)

Reviewer: independent Gate 1 power-integrity review, 2026-10-11. I did not modify any design file.

## Scope

Every power net and power component in `design/circuit.py` (source of truth) and the generated schematic/netlist:
VBAT entry and TVS (D1, C1), both LMR38020 bucks (U1/U2: pins incl. EP, EN/UVLO, RT, FB, BOOT, PG, CIN/CHF/COUT, L1/L2),
VTX power cut (Q2 on EN_10V), 5V_SYS diode-OR (D4/D5), LDOs U4 LP38692 and U5 LP5907 (pinout, EN, caps, stability),
3V3A ferrite/VDDA, VCAP1/2, MCU decoupling, sensor supply decoupling, USB VBUS path, buzzer and LED supplies, PWR_FLAG usage,
voltage/power ratings of every part on a power net, and MPN vs value/rating consistency.

## Method

- Read `design/circuit.py` (lines cited below), `design/power.md`, `design/requirements.md`, `design/decisions.md`.
- Exported the netlist with `kicad-cli sch export netlist` (KiCad 10.0.6) and parsed it with my own script (`python3 -I`, scratchpad)
  to list every node on VBAT, 5V, 10V, 5V_SYS, VBUS, 3V3, 3V3A, 3V3_IMU, EN_*, RT_*, FB_*, SW_*, BST_*, VCAP*, BUZ_*, VTX_OFF_G,
  every unconnected pin, and every BOM line's value/footprint/MPN. I also summed the capacitance on each rail.
- Ran `kicad-cli sch erc --severity-all`: **0 errors, 0 warnings**.
- Datasheets (pdftotext, plus one page render of the LP38692 NDC0005A drawing): `lmr38020.pdf` (SNVSC40E), `lp38692.pdf`
  (SNVS322M), `lp5907.pdf` (SNVS798Q), `NX7002AK.pdf`, `PMV40UN2.pdf`, `PMEG4030ER.pdf`, `ICM-42688-P_DS.pdf`, `BMI270_DS.pdf`,
  `BMP390_DS.pdf`. KiCad library symbols checked: `Regulator_Linear:LP5907MFX-*`, `Transistor_FET:2N7002` (Q_NMOS_GSD),
  footprint `Package_TO_SOT_SMD:SOT-223-5`, custom `F405FC:TI_HSOIC-8-1EP...DDA`.
- Not on file, so **not verified**: Littelfuse SMBJ26A, Würth WE-MAPI 74438357068/082, ST IIS2MDC, ST DS8626 (STM32F405),
  Lite-On LED datasheets, Samsung/Murata DC-bias curves, Yageo RC datasheet (ratings below come from general Yageo RC series knowledge:
  0402 50 V / 1/16 W, 0603 75 V / 1/10 W).

Note: the netlist export overwrote `kicad/F405FC.net` (tracked, already modified in the working tree by someone else). After my
export, its only difference from HEAD is the `(date ...)` line.

## Checks passed

| Area | Evidence | Result |
|---|---|---|
| LMR38020 pin map | Symbol circuit.py:123-127 vs SNVSC40E Fig. 6-1/Table 6-1 (1 GND, 2 EN, 3 VIN, 4 RT/SYNC, 5 FB, 6 PG, 7 BOOT, 8 SW, EP). Netlist: U1/U2 pin 1 and 9 on GND, pin 3 on VBAT | PASS |
| PG | Unconnected (`unconnected-(U1-PG-Pad6)`); Table 6-1: "Can be left open when not used" | PASS |
| EP | Pad 9 on GND; footprint has EP pad 9 + 8 thermal vias. Table 6-1: "Connect to system ground" | PASS |
| RT | 34.8 k (R3, R8) = Table 8-1 value for 750 kHz; Eq. 2 gives 34.5 k | PASS |
| FB | 100 k / 24.3 k → 5.115 V; 100 k / 11.0 k → 10.09 V (Eq. 9, VREF 1.000 V). RFBT 100 k = TI recommended | PASS |
| EN/UVLO | 301 k / 100 k (RENB within 10-100 k, 9.2.2.8). VON 5.01 V typ, VOFF 4.41 V typ (VEN-H 1.25 V, VEN-L 1.10 V). EN = 0.249 x VIN ≤ VIN (abs max VIN + 0.3 V). EN at 42.1 V = 10.5 V | PASS |
| BOOT | 100 nF 16 V X7R BOOT-SW (C5, C13); 9.2.2.7 requires 100 nF ≥ 16 V | PASS (exactly at the 16 V minimum) |
| CIN / CHF | Per IC 2 x 10 uF 50 V X7R 1210 + 100 nF 100 V X7R 0603 (circuit.py:221-223) + shared C1. 9.2.2.6: ≥ 4.7 uF effective, rated ≥ VIN max (pref. 2x), 100-220 nF HF at 100 V X7R. 50 V ≈ 2 x 25.2 V | PASS |
| COUT | 3 x 22 uF 25 V X5R 1206 + 100 nF each rail (circuit.py:232-234). Table 9-1: 5 V 2-3 x 22 uF; 12 V 1 x 22 uF (400 kHz) / 2 x 10 uF (1 MHz). Total 66 uF nominal, well under the 10x ceiling (9.2.2.5) | PASS |
| Inductors | 6.8 uH / 8.2 uH vs Eq. 11 LMIN 1.7 / 3.4 uH; footprint `L_Wuerth_MAPI-4030` 2 pads | PASS (Isat not verifiable, no Würth PDF) |
| VBAT ratings | VBAT nodes: C1/C2/C3/C10/C11 50 V, C4/C12 100 V, R1/R6 301 k 0603, R14 10 k 0603, D1, U1/U2 VIN (85 V abs max), J2, P1. No 0402 resistor and no < 50 V cap on VBAT | PASS vs 42.1 V clamp |
| Resistor power | R14 (VBAT divider top): 52 mW at 25.2 V in a 0.1 W 0603 (≈ 85 mW available at 83 C board after derating); 147 mW only during a TVS-clamp transient. R1/R6: 1.2 mW at 25.2 V | PASS |
| TVS | SMBJ26A uni, K = VBAT, A = GND (circuit.py:206). VWM 26 V > 25.2 V | PASS (Littelfuse PDF not on file) |
| Q2 VTX cut | NX7002AK SOT-23 1 G / 2 S / 3 D (datasheet pinning table) = KiCad 2N7002 (Q_NMOS_GSD); netlist Q2.3 on EN_10V, Q2.1 on VTX_OFF_G. VGS(th) 1.1-2.1 V vs 3.27 V gate (1 k / 100 k); VDS 60 V vs ≤ 10.5 V; needs only 140 uA sink | PASS |
| LP38692 pinout | SNVS322M pin table SOT-223: 1 EN, 2 N/C, 3 OUT, 4 IN, 5 GND (tab). Symbol circuit.py:128-131 matches; NDC0005A drawing (p. 31): 4 leads at 1.5 mm pitch, tab at 6.3 mm row spacing = KiCad SOT-223-5 pads | PASS |
| LP38692 EN/caps | EN tied to IN (VEN ON ≥ 1.8 V at 4 V, ≥ 3 V at 6 V); CIN 1 uF 25 V (C19) ≥ 1 uF; COUT 10 uF 25 V 0805 (C20) + bank. VIN 4.4-5.3 V within 2.7-10 V | PASS (see G1P-02) |
| LP5907 pinout | SNVS798Q Table 4-2 SOT-23: 1 IN, 2 GND, 3 EN, 4 N/C, 5 OUT = KiCad symbol pins | PASS |
| LP5907 EN/caps | EN = IN; VIN ≤ 5.3 V (≤ 5.5 V op, 6 V abs). CIN 1 uF (C22). COUT total 4.71 uF nominal (≈ 3.5-4 uF effective) within 0.7-10 uF (5.6) | PASS |
| 5V_SYS OR | D4 A = VBUS, K = 5V_SYS; D5 A = 5V, K = 5V_SYS (netlist). Symbol pin 1 = K = SOD-123W pad 1. PMEG4030ER 40 V / 3 A | PASS |
| USB VBUS | J1 A4/A9/B4/B9 → VBUS; C51 1 uF 25 V; R36 100 k bleeder; USBLC6 pin 5 on VBUS; 5.1 k Rd on CC1/CC2 | PASS (inrush: G1P-01) |
| 3V3A / VDDA | FB1 BLM18KG601SN1D 3V3 → 3V3A, 1 uF + 100 nF, only U3.13 VDDA on 3V3A | PASS |
| VCAP | C33/C34 2.2 uF on U3.31/U3.47 (each net only the pin + its cap) | PASS (ST DS not on file; 2 x 2.2 uF is the ST requirement for LQFP-64) |
| MCU decoupling | 4 x 100 nF (VDD 19/32/48/64) + 4.7 uF bulk + 100 nF on VBAT pin 1 (tied to 3V3) | PASS |
| ICM-42688-P | DS-000347 table (lines C1 0.1 uF, C2 2.2 uF on VDD, C3 10 nF on VDDIO): C38/C39/C40 on 3V3_IMU (VDD = VDDIO) | PASS (dielectric: G1P-05) |
| BMI270 | DS: 100 nF on VDD and VDDIO: C41, C42 | PASS |
| BMP390 | DS: C1 = C2 = 100 nF: C43, C44; CSB = 3V3 (I2C) | PASS |
| W25N01GV, TS5A3159A, SN74LV1T125 | 100 nF each (C48, C49, C50); U12 VCC on 5V | PASS |
| Buzzer | 5V → pad P13; P14 = BUZ_N = Q1 drain = D9 anode; D9 cathode on 5V; Q1 PMV40UN2 30 V, 44 mΩ at 4.5 V; gate 100 R + 10 k pulldown | PASS |
| LEDs | Red 1 k from 3V3 (≈ 1.3 mA); blue 330 R / green 1 k from 3V3 sinking into PB14/PB15 | PASS (Lite-On VF not on file) |
| PWR_FLAG | On VBAT, GND, 5V, 10V, 5V_SYS, VBUS, 3V3A (circuit.py:274-275): every one is a net fed only by passive pins (pads, inductors, diodes, ferrite, connector). 3V3 and 3V3_IMU are driven by power_out pins and carry no flag. ERC 0/0 | PASS |
| Other cap ratings | 5V caps ≥ 16 V; 10V COUT 25 V vs 10.43 V max; 5V_SYS/VBUS ≥ 16 V; VBAT_ADC 16 V vs 3.83 V max | PASS |
| MPN vs value | All Samsung codes decoded (dielectric A = X5R, B = X7R, C = C0G; voltage O = 16 V, A = 25 V, B = 50 V); all Yageo RC MPNs match value/size; GRM188R72A104 = 100 nF 100 V X7R | PASS except G1P-03 |

## Findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| G1P-01 | MINOR | **USB inrush claim in power.md is wrong.** power.md says the host sees only ≈ 7.7 uF because the LDO outputs "charge through the LDOs' current limit after start-up". Neither LDO has a soft start; once 5V_SYS rises past ~2-3 V both LDOs pass current up to their current limit, so the host charges the whole downstream bank at plug-in. Nominal: VBUS 1 uF (5 uC) + 5V_SYS 6.7 uF (31.5 uC) + 3V3 16.8 uF (55.4 uC) + 3V3A 1.1 uF (3.6 uC) + 3V3_IMU 4.71 uF (15.5 uC) ≈ **30 uF / ≈ 111 uC** (≈ 80 uC after DC bias), plus the ELRS receiver's own input caps. That exceeds the USB 2.0 10 uF / 50 uC inrush allowance. Practical risk is low (most FCs do this), but the doc claims compliance it lacks | power.md:309-311; circuit.py:247, 252-254, 260-261, 297-306, 342-371, 416; netlist cap sums; lp38692.pdf/lp5907.pdf (no soft-start feature) | Correct power.md 9 and log the non-compliance as a decision (D-xx), or add a soft-start/current-limited switch in the VBUS path |
| G1P-02 | MINOR | **LP38692 output ESR floor not met by the 3V3 bank as built.** SNVS322M 8.2.2.2.2: output cap ESR must be 5-500 mΩ "for stability". 3V3 carries 14 ceramic caps (10 uF 0805 + 4.7 uF + 12 x 100 nF / 1 uF), so the aggregate ESR is well below 5 mΩ. power.md claims the 10 uF's ESR "about 5 mOhm is inside the window", which ignores the parallel bank. TI's own EC conditions use 10 uF ceramic, so instability is unlikely but unproven | lp38692.pdf 8.2.2.2.2 and EC header (CIN = COUT = 10 uF); power.md:272; circuit.py:253-254, 296-306 | Correct power.md 7. Add a 3V3 load-step (0 → 200 mA) ringing check to the bring-up guide. Optionally provide a 0402 footprint for a 0.1-0.47 Ω series R with a separate ≥ 1 uF at U4 OUT if the check fails |
| G1P-03 | MINOR | **Catalog value does not match the MPN rating.** `C4u7` is labelled "4.7uF X5R 10V" but CL10A475K**O**8NNNC is the 16 V Samsung code (O = 16 V). The BOM/schematic value of C18 and C29 is wrong (harmless direction, but BOM and MPN disagree) | circuit.py:68; netlist C18, C29 | Change the value string to "4.7uF X5R 16V" (or pick a 10 V MPN) |
| G1P-04 | MINOR | **power.md has drifted from the schematic** (source of truth): LP38692 COUT is "Murata GRM21BR61A106KE19L 10 V" in power.md but CL21A106KAYNNNE 25 V in circuit; LP5907 COUT is "X7R" in power.md but X5R (CL10A225KO8NNNC); VBAT R_bot is "0603" in power.md but 0402; section 1.2 / 13 refdes are wrong (HF caps are C4/C12 not C4/C5; PMEG4030ER are D4/D5/D9 not D4/D5/D8; BAT54S are D7/D8 not D9/D10, and D10 is the red LED) | power.md:101-103, 272, 282, 325, 458-473; circuit.py:67, 69, 223, 253, 261, 271, 418-456 | Regenerate power.md 1.2/7/8/10.1/13 from circuit.py |
| G1P-05 | INFO | ICM-42688-P bypass table specifies **X7R** for C2 (2.2 uF on VDD); C39 is X5R (CL10A225KO8NNNC). Fine at 3.3 V / ≤ 85 C; datasheet deviation only | ICM-42688-P_DS (bypass capacitor table: C1 X7R 0.1 uF, C2 X7R 2.2 uF, C3 X7R 10 nF); circuit.py:67, 343 | Optional: use an X7R 2.2 uF 0603 (e.g. CL10B225KO8NNNC) |
| G1P-06 | INFO | 10 V rail HF cap C17 is 100 nF **16 V** 0402 at up to 10.43 V (65 % of rating); 0402 X7R at that bias keeps only a fraction of its value. It also fails short first in the accepted U2 HS-short double fault (R7) | circuit.py:234 (`C100n` on vout for both rails); power.md:487-489 | Use a 50 V 0402 X7R 100 nF (CL05B104KB5NNNC) on the 10 V output |
| G1P-07 | INFO | **Single fault in U1** (HS FET short) puts VBAT onto 5V, then through D5 onto 5V_SYS: LP5907 (6 V abs max), U12, cameras, GPS, LED strip all see up to 25 V. power.md R7 covers only the U2 case | power.md:487-489; lp5907.pdf 5.1 | Add to the risk list (accepted, same as most FCs) |
| G1P-08 | INFO | **Unverified, no datasheet on file:** SMBJ26A VC/VBR; Würth Isat/DCR (L1/L2); IIS2MDC supply pins (3/9/10) and decoupling (C46 100 nF + C47 1 uF; I recall ST recommending 100 nF + 4.7 uF, not verified); STM32 VCAP/VDDA recommendations; blue LED VF at 3.3 V with 330 R | circuit.py:206, 212-213, 358-365, 324-327 | Add the PDFs to `datasheets/` and close at Gate 2 |

## Verdict

**PASS**: 0 BLOCKER, 0 MAJOR, 4 MINOR (G1P-01 to G1P-04), 4 INFO. The pin connections, enable, frequency, feedback, boot,
input/output capacitance, voltage ratings and PWR_FLAG usage of the power schematic are correct against the datasheets on file.
The MINOR items are a documentation error (USB inrush), a missing stability check (LP38692 ESR), one BOM value string and doc drift.
