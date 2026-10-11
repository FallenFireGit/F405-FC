# Gate 0 re-audit: F405-FC power design (rev B, post P0 fixes)

Auditor: independent Gate 0 power re-audit, 2026-10-11 (fresh reviewer, not the author of `gate-0-power-audit.md`).
Audited: `design/power.md` (rev B as revised), `design/decisions.md` (D-03, D-04, D-11, D-12, D-13), `design/circuit.py`
(Power, MCU-power, Video and Connectors parts), the generated netlist `kicad/F405FC.net` (power nets only), and
`gen/power_calc_lmr.py`. I did not modify any other file and did not commit.

Method: I extracted the datasheets with `pdftotext -layout` into the scratchpad. Nothing from `datasheets/` was executed.
I ran `python3 -I gen/power_calc_lmr.py` and my own script (`scratchpad/calc/re.py`, not committed, run with `python3 -I`).
Every number marked "recomputed" comes from that script. Anything I could not check against a document on file is
marked **unverified**.

## Sources

| Ref | Source | Used for |
|---|---|---|
| [LMR] | TI LMR38020 SNVSC40E (Sep 2023), `datasheets/lmr38020.pdf` | Fig. 6-1 / Table 6-1 pinout (GND 1, EN 2, VIN 3, RT/SYNC 4, FB 5, PG 6, BOOT 7, SW 8, EP); 7.1 abs max (VIN/SW 85 V, EN VIN+0.3, FB 5.5 V); 7.3 (VOUT must not go below 0 V); 7.4 (RθJA 42.9, RθJB 13.6, ψJB 13.8); 7.5 (VEN-H/L, ILS 1.8 min, IHS 2.6-3.8, IL-NEG −0.9 A FPWM, tOFF-MIN 300 ns max, tON-MAX 5 µs); 7.6 note 2 (DMAX = tON-MAX/(tON-MAX+tOFF-MIN)); orderable table (FSDDAR = FPWM + SS); 9.2.2.6 (≥ 4.7 µF); 9.2.2.9 (thermal-info values "not valid for design purposes") |
| [LP38] | TI LP38692 SNVS322M, `datasheets/lp38692.pdf` | SOT-223 pinout (EN 1, NC 2, OUT 3, IN 4, GND 5); 6.1 12 V abs max; 6.3 VIN ≤ 10 V, Tj ≤ 125 C; 6.4 RθJA 68.5, ψJB 12.8; 8.1.1 reverse voltage |
| [LP59] | TI LP5907 SNVS798Q, `datasheets/lp5907.pdf` | 5.1 VIN/VEN abs max 6 V, VOUT ≤ VIN+0.3; 5.3 VIN 2.2-5.5 V |
| [NX] | Nexperia NX7002AK, `datasheets/NX7002AK.pdf` | VGS(th) 1.1-2.1 V; RDSon 4.5 Ω max at 10 V, 5.2 Ω max at 5 V; Ciss 15/20 pF |
| [PMV] | Nexperia PMV40UN2, `datasheets/PMV40UN2.pdf` | Table 2 pinning (G 1, S 2, D 3) |
| [PMEG] | Nexperia PMEG4030ER, `datasheets/PMEG4030ER.pdf` | Table 2 pinning (K 1, A 2); Rth(j-a) 130 K/W; VF 295/330 mV at 0.1 A |
| [ICM] | TDK ICM-42688-P DS, `datasheets/ICM-42688-P_DS.pdf` | operating temperature −40..+85 C (DS line "Operating Temperature Range") |
| [TS5A] | TI TS5A3159A, `datasheets/TS5A3159A_DS.pdf` | V+ supply (P0-13 check) |
| Not on file | SMBJ26A PDF, USBLC6-2 PDF, SN74LV1T125 PDF, DS8626 (STM32F405), Würth WE-MAPI PDFs, Samsung DC-bias curves | Claims that depend on these are marked unverified |

## Checks that passed (recomputed or traced)

| Item | Evidence | Result |
|---|---|---|
| LMR38020 symbol pin numbers vs datasheet | circuit.py:123-127; [LMR] Fig. 6-1/Table 6-1. Netlist: VBAT→U1.3/U2.3, EN_x→pin 2, RT→4, FB→5, PG 6 unconnected (allowed: "Can be left open"), BOOT 7, SW 8, GND 1 + EP | PASS |
| LP38692 SOT-223 pinout | circuit.py:128-131 vs [LP38] pin table (EN 1, NC 2, OUT 3, IN 4, GND 5). Netlist: U4.4 IN and U4.1 EN on 5V_SYS, U4.3 on 3V3 | PASS |
| LP5907, USBLC6, PMEG4030ER, BAT54S, PMV40UN2, NX7002AK pin mapping | Netlist: U5.1 IN, U5.3 EN, U5.5 OUT; U13 I/O1 = 1/6 (DM), I/O2 = 3/4 (DP), VBUS 5; D4/D5/D9 pin 1 = K ([PMEG] Table 2); D7/D8 pin 1 A to GND, pin 2 K to 3V3, pin 3 COM to ADC; Q1/Q2 G1 S2 D3 ([PMV] Table 2) | PASS |
| Power-part values: circuit.py vs power.md | TVS SMBJ26A; C1 + 2 × 10 µF/50 V 1210 + 100 nF/100 V per IC (circuit.py:209, 221-223); RENT 301 k 0603 / RENB 100 k; RT 34.8 k; RFBT 100 k / RFBB 24.3 k and 11.0 k; L 6.8 / 8.2 µH WE-MAPI; 3 × 22 µF 25 V + 100 nF per rail; Q2 with 1 k series + 100 k on the gate side (circuit.py:237-241); 5V_SYS 4.7 µF + 2 × 1 µF; VBAT 10 k (0603) / 1 k / 100 nF; CURR/RSSI 10 k + 10 nF + BAT54S; buzzer 100 Ω + PB2 10 k pulldown + PMV40UN2 + flyback to 5V; J4 GPS on 5V, J5 RX on 5V_SYS, J3 pin 1 on 10V; TS5A V+ = 3V3 | PASS (except the items in P1-04) |
| Design script reproduces power.md 12.2 | `python3 -I gen/power_calc_lmr.py`: Pic 1.26/1.01/0.99 W (5 V 1.8 A at 7.4/16.8/25.2 V), 0.89/0.83 W (10 V), FB 5.115 V (4.96-5.28), 10.091 V (9.76-10.43), UVLO on 4.41/5.01/5.61 V, off 3.81/4.41/4.89 V, EN 10.50 V at 42.1 V | PASS (dropout model in the script is still wrong, see P0-04) |
| Abs max, battery-only (2S-6S, TVS clamp 42.1 V) | LMR VIN/SW 85 V; EN = 0.249·VIN ≤ VIN+0.3; FB ≤ 5.5 V (U2 HS-short case 42.1 × 11/111 = 4.17 V); ceramics 50/100 V; Q2 VDS ≤ 10.5 V (60 V); LP38692 IN ≤ 5.03 V (12 V abs); LP5907 IN ≤ 5.03 V (6 V abs) | PASS |
| USB-only | VBAT = 0 → both EN = 0 (resistive); D5 blocks 5V_SYS → 5V → L1 → HS body diode → VBAT; GPS/LED/cam/buzzer unpowered; 5V_SYS ≤ 5.5 − VF(D4) ≈ 5.2-5.3 V at vSafe5V max, inside LP5907 5.5 V op | PASS (transient: P0-05) |
| Battery + USB | D4 blocks battery → VBUS; both diodes forward at near-equal voltage is harmless | PASS |
| Hot-plug (battery) | EN tracks VIN through the divider (no EN > VIN+0.3 case); TVS + 50 V ceramics; 4 ms soft start. PC0 injection ≤ 2.5 mA during the 3V3 ramp (P0-15) | PASS |
| VTX off / reset / DFU | PC15 floating at reset → 100 k gate pulldown → Q2 off → U2 on (VTX on, D-04). Q2 on: 42.1 V/301 k = 140 µA; NX7002AK at VGS ≈ 3 V is far below the 6.8 kΩ needed. PB2 10 k → buzzer silent; CAM_SEL 100 k → CAM1 | PASS |
| Reversed battery | power.md:92-95 now states TVS + both LMR38020 body-diode paths fail; [LMR] 7.1 VIN ≥ −0.3 V | Documented (PASS as documentation) |
| TVS coverage | One SMBJ26A at the VBAT entry covers U1, U2, C1-C3b, EN dividers, VBAT divider and J2 pin 1. 10V/5V rails are only reachable through the bucks | PASS (SMBJ26A values unverified, no PDF) |
| ADC protection | VBAT_ADC 0.25 mA injection at 42.1 V via 10 k; CURR/RSSI 10 k + BAT54S to 3V3/GND (2.16 mA at 25.2 V) | PASS (STM32 IINJ limit unverified, DS8626 not on file) |
| Buzzer driver | PMV40UN2 fully on from 3.3 V; drain ≤ 5.28 + VF ≪ 30 V; gate held low by the 10 k BOOT1 pulldown through 100 Ω | PASS |
| Inductor / cap selection (unchanged since the first audit) | LMIN 1.70/3.36 µH (Eq. 11) vs 6.8/8.2 µH; Table 9-1 output C met; 2 × 10 µF/50 V per IC (P0-06) | PASS (Isat and DC-bias unverified) |
| 12.5 arithmetic | R_board-air = 1/(h · 2 × 12.96 cm²): h 10/15/40/80 → 38.6/25.7/9.6/4.8 K/W. Rows recomputed: flight worst 92-108 C (U1) / board 66-82 C; flight typical 69-76 / 57-64 C; bench worst 136-178 / 110-152 C; bench envelope 59-72 / 51-64 C | PASS: within ±2 C of power.md:417-420 (rounding) |
| U2 dropout loss on 2S | 1.5² × 0.303 × 1.45 = 1.02 W (power.md:422 says ≈ 1.0 W) | PASS |

## Disposition of previous findings (P0-xx)

| ID | Prev. sev | Disposition | Evidence |
|---|---|---|---|
| P0-01 | MAJOR | **OPEN (partly resolved), residual raised as P1-01 (MAJOR)** | Resolved: board-level model added (power.md:405-424); airflow assumption stated; still-air case shown as not allowed; U2 dropout and edge-time sensitivity named; pass/fail gate defined; D-12 logged (decisions.md:94-98). Not resolved: the bench envelope breaks its own 1 W limit, on-board load dissipation is left out, the gate criteria are not tied to ambient and do not cover 2S, and the old "worst-case Tj 104 C" claim is still the headline in power.md:38, decisions.md:34 (D-03) and power.md:481 (R2). Details in P1-01 |
| P0-02 | MAJOR | **ACCEPTED-DEVIATION** (D-11) | decisions.md:87-92 logs that the 10 V rail regulates only for VIN ≥ 11.5 V, that 2S HD VTXs are wired to the VBAT pads, and why the jumper was rejected (back-drive, loss of pit mode). power.md:182-191 and R10 (power.md:493) match. Recomputed: 6.21-6.35 V at 7.4 V/1.5 A (DMAX 0.943-0.963). Residual wiring hazard in P1-03 |
| P0-03 | MINOR | **OPEN (MINOR)** | Worst-case floors (≥ 1.87 A / ≥ 1.78 A) are now stated at power.md:34-37 and 369-370, but the old "guaranteed" figures remain at power.md:16 ("2.0 A guaranteed current-limit floor"), :17 ("1.97 A guaranteed floor"), :131 ("above 1.96 A"), :173 ("Guaranteed output … 2.13 A, 2.11 A"), decisions.md:35 ("guaranteed 1.96-2.20 A … 1.97-2.13 A") and decisions.md:37 ("~2 A peak"). power.md:36 still says "the 1.79 A budget leaves ≥ 0.08 A", but 12.1 (power.md:369) now has 1.71 A with a 0.16 A margin |
| P0-04 | MINOR | **OPEN (MINOR)** | The 2.1/3.4 text now uses DMAX, but power.md:126 says "A 2S pack under load (≥ 6.0 V) gives ≥ 4.9 V". Recomputed: **4.76-4.87 V** at 6.0 V/1.8 A (DMAX 0.943-0.963, hot RDS, DCR). `gen/power_calc_lmr.py:22-25` still assumes 100 % duty: it prints 6.61 V (10 V rail at 7.4 V) and 10.09 V at 11.1 V, against power.md's 6.2-6.35 V and 9.9 V. power.md:6 still says "All rev B numbers come from gen/power_calc_lmr.py". The script's last lines (`R~5 ohm`, "3.3 ohm-ish at VGS 3.3 V") are not datasheet values ([NX] gives 5.2 Ω max at 5 V only) |
| P0-05 | MINOR | **OPEN (MINOR)** | Partly resolved: 5V_SYS bulk cut to 4.7 µF (circuit.py:247), and power.md:313 says TPD2E2U06 is not acceptable. Still open: (a) decisions.md:67 (D-07) still lists **TPD2E2U06DRLR as the alternate, "Gate 2 picks the stocked one"**, and the ST part had 0 stock, so the forbidden substitution is the logged fallback. (b) The VBUS surge claim rests on the USBLC6 internal Zener (power.md:312), but the USBLC6-2 datasheet is not on file (**unverified**), and nothing shows that the clamp keeps 5V_SYS below the LP5907's 6 V abs max ([LP59] 5.1). A Zener that starts conducting near 6 V cannot do that by itself. (c) The inrush argument at power.md:310-311 is wrong: the LDOs do not limit inrush (the LP38692 has no soft start), so the host also charges about 17.7 µF on 3V3 and about 4.7 µF on 3V3_IMU, nominal, counted from circuit.py. Estimate: ≈ 3.3 V × 22 µF + 4.7 V × 7.7 µF ≈ 110 µC, against the USB 2.0 50 µC / 10 µF limit. This is common FC practice, but it should be logged as accepted rather than claimed compliant |
| P0-06 | MINOR | **RESOLVED** | 2 × 10 µF/50 V 1210 per IC in circuit.py:221-222 and power.md:102, plus 100 nF/100 V and C1. ≈ 9 µF effective per IC against 4.7 µF ([LMR] 9.2.2.6). DC-bias figure unverified (no Samsung curve) |
| P0-07 | MINOR | **RESOLVED (text); verification deferred to Gate 2** | power.md:133-135 now states HS-limit > Isat(10 %) with the soft-saturation rationale; tracked as R9 (power.md:492) and D-05. Leftover: power.md:132/455-456 and D-05 still give "3 A"/"2.8 A" without saying which rating (IR or Isat) they are (INFO) |
| P0-08 | MINOR | **RESOLVED (R7 corrected)**, stale sentence in P1-02 | power.md:487-489 now names the 25 V output caps as at risk and accepts the double fault. But power.md:213-214 still says "Nothing else on the 10 V rail can be damaged" |
| P0-09 | MINOR | **RESOLVED** | power.md:92-95 now names both LMR38020 body-diode paths ([LMR] 7.1 VIN ≥ −0.3 V) |
| P0-10 | MINOR | **RESOLVED** | AT7456E gone from the 3V3 budget (power.md:244-255); "65 V" gone; 2S current is 2.95/2.9 A throughout; Ciss 15/20 pF (power.md:209); RDS text matches [NX] (power.md:205); pinmap.md:55, :71, :95 match D-04 and PMV40UN2 |
| P0-11 | INFO | Accepted (no action needed) | K = 0.49/0.62 on the 10 V rail; peak stays below Isat |
| P0-12 | INFO | OPEN (INFO), bring-up check | LP38692 ESR 5-500 mΩ ([LP38] 8.2.2.2); 10 µF 0805 ceramic on 3V3 (circuit.py:253) |
| P0-13 | INFO | **RESOLVED** | TS5A3159A V+ = 3V3 (circuit.py:379) |
| P0-14 | INFO | OPEN (INFO), not addressed | No GPS series resistors; optional |
| P0-15 | INFO | No action needed | — |
| P0-16 | INFO | OPEN (INFO) | power.md:147 still states 5.28 V is "inside WS2812 VDD max 5.3 V" with no transient margin; power.md:109 still says "35 V min" bulk while the clamp is 42.1 V |
| P0-17 | INFO | OPEN (INFO) | The U1 high-side short (VBAT on 5V → LP5907 6 V / every 5 V load) is still missing from §14 |

## New findings (P1-xx)

| ID | Sev | Finding | Evidence | Fix |
|---|---|---|---|---|
| P1-01 | **MAJOR** | **The thermal operating envelope and its pass/fail gate (the P0-01 fix) are internally inconsistent and would not catch a rating violation.** (a) **The bench envelope breaks its own ≤ 1 W limit.** power.md:430 allows "VTX in pit mode **or ≤ 1 A**, LED strip ≤ 0.2 A, cameras OK". Recomputed at 4S with the doc's own loss model: 5 V at 1.03 A (5V_SYS 0.33 + LED 0.2 + cams 0.4 + GPS 0.1) gives U1 0.38 + L1 0.13 + LDO 0.19 + D5 0.11 = 0.81 W. Adding the VTX at 1 A (U2 0.43 + L2 0.14) gives **1.38 W**. (b) **On-board load dissipation is left out of P_board:** the 3V3 loads (MCU, flash, sensors, LEDs) dissipate 3.3 V × 0.13-0.17 A ≈ 0.43-0.56 W on the board, but power.md:399 sums only converter/LDO/diode losses. With it, the bench "VTX ≤ 1 A" case is **≈ 1.8 W → board rise 47-70 C → 72-95 C at Ta 25 C**, above the STM32F405RGT6's 85 C ambient rating and the ICM-42688-P's 85 C operating limit ([ICM]). In flight the 2S worst case becomes 3.2 + 0.56 ≈ 3.8 W (20 ns edges at 6S: 3.7 W), which puts the board upper bound at about 86-87 C at Ta 50 C, not ≤ 83 C (power.md:417, 427). (c) **The gate criteria are not tied to ambient.** power.md:432-433 tests at room ambient with a 3 m/s fan and passes at "MCU case ≤ 80 C, U1/U2 ≤ 105 C". That allows a 55 C MCU rise, against the model's 17-33 C. Moved to the design ambient of 50 C, a passing board could have the MCU at about 105 C (the -T6 Tj limit, DS8626 unverified) and the IMUs well above 85 C. The gate also runs only at 6S, while U1's loss is highest on 2S (1.26 W vs 0.99 W, script output); the first audit asked for 2S and 6S. (d) The **STM32F405RGT7 mitigation** (D-12, power.md:427-429) does not cover the IMUs (85 C) or the W25N/BMP390, so the "hot-climate" fallback is incomplete. (e) The headline "worst-case Tj 104 C" from the per-IC JEDEC model is still the justification text in power.md:38, decisions.md:34 (D-03) and power.md:481 (R2). It contradicts 12.5 (93-109 C in flight). | power.md:399, 405-433, 38, 481; decisions.md:34, 94-98; recomputed in scratchpad `calc/re.py`; [LMR] 9.2.2.9; [ICM] operating range | Restate the bench envelope so it fits ≤ 1 W including the 3V3 loads (e.g. VTX in pit mode **and** LED ≤ 0.2 A; no VTX on the 10 V rail without a fan). Add the 3V3 load (~0.5 W) to P_board in 12.3/12.5. Express the gate as **rise above ambient** (e.g. MCU case − Ta ≤ 30 C so that it holds ≤ 80 C at Ta 50 C; U1/U2 case − Ta ≤ 55 C), or run it in a 50 C enclosure, at **both 2S and 6S**. Replace the "104 C" text in the power.md summary, D-03 and R2 with the 12.5 figures. Name the 85 C sensors in D-12 |
| P1-02 | MINOR | **Stale statement contradicting R7:** power.md:213-214 "Nothing else on the 10 V rail can be damaged" vs R7 (power.md:487-489), which now says the 25 V output caps may crack or fail short under a U2 HS short | power.md:213 vs 487 | Align §4 with R7 |
| P1-03 | MINOR | **The D-11 2S workaround can recreate the back-drive it rejects.** D-11 tells 2S HD users to power the VTX from the VBAT pads. The standard HD harness (J3, circuit.py:427-430) carries power on pin 1 = 10V. If the user keeps that harness and adds a VBAT feed, or uses a VTX whose two power inputs are common, VBAT is tied to the 10V node. U2 (FPWM, enabled by default through reset/boot, D-04) then runs in DMAX dropout against an output it cannot raise. The inductor current ramps negative to IL-NEG (−0.9 A, [LMR] 7.5) and circulates through U2/L2. That is the same back-drive the lead cites as the reason to reject the jumper (decisions.md:91-92; power.md:189-190). Not destructive by estimate (≈ 0.9² × 0.44 ≈ 0.36 W in U2), but it adds heat and noise, and the documentation does not warn against it | decisions.md:87-92; power.md:187-190; circuit.py:427-430; [LMR] 7.5 IL-NEG | In the user guide, tell 2S HD builds to remove or cut the J3 pin-1 power wire (or use a VBAT-only harness), or to set USER1 so U2 is held off. Optionally add a DNP 0R in series with J3 pin 1 so 2S builds can open the 10 V path |
| P1-04 | MINOR | **circuit.py (the schematic source) and the power.md BOM disagree on references and parts:** (a) refdes: power.md:471-472 says D4/D5/**D8** = PMEG4030ER and **D9/D10** = BAT54S. circuit.py:244, 418, 454 have D4/D5/**D9** = PMEG4030ER, circuit.py:442-447 have **D7/D8** = BAT54S, and D10 is the power LED (circuit.py:265). (b) BAT54S MPN: power.md "Nexperia BAT54S,215 or onsemi" vs circuit.py:446 "BAT54S-7-F, Diodes Inc". (c) 3V3 LDO output cap: power.md:272 "GRM21BR61A106KE19L 10 V" vs circuit.py:69/253 "CL21A106KAYNNNE 25 V X5R". (d) LP5907 COUT: power.md:282 "2.2 µF 16 V **X7R**" vs circuit.py:67 "CL10A225KO8NNNC **X5R**". (e) The 5V_SYS bulk C4u7 is 10 V X5R 0603 (circuit.py:68) at 4.8-5.3 V DC bias. power.md:310 counts it as 4.7 µF in the inrush sum; its effective value is lower (unverified, no curve) | as cited | Make circuit.py and the power.md §13 BOM match (refdes and MPN); state one choice per position |
| P1-05 | INFO | **USB-only: the LED-strip buffer may back-power 5V.** U12 SN74LV1T125 has VCC = 5V (circuit.py:392-394), which is unpowered on USB, while PA8 can drive LED_STRIP high when the LED strip feature runs on USB. If the input has no Ioff protection, current flows through the input clamp into 5V (and on through L1/HS body diode to VBAT). Limited to GPIO mA. Ioff/partial-power-down capability is **unverified** (datasheet not on file) | circuit.py:392-397 | Confirm "Ioff" in the SN74LV1T125 datasheet at Gate 2, or note it in bring-up |
| P1-06 | INFO | **12.5 assumptions should be labelled as estimates.** The model assumes an isothermal board (fin efficiency 1 over both faces), still-air h 10-15 W/m²K and a chosen R_ic-board of 20 C/W (RθJB 13.6 + "local spreading"). These are reasonable (my natural-convection + radiation estimate agrees; laminar forced-convection h ≈ 35-64 W/m²K at 3-10 m/s for L = 36 mm, + ~6 radiation, which supports 40-80), but the text never says the numbers are unvalidated estimates whose only validation is the bring-up gate | power.md:407-413 | Add one sentence: "estimates, validated only by the bring-up gate (P1-01)" |

## Not verified (explicitly)

- SMBJ26A electrical values (no PDF). USBLC6-2 VBUS clamp voltage (no PDF). SN74LV1T125 Ioff (no PDF).
- STM32F405 IINJ, PC13-15 drive and the T6/T7 temperature ratings (DS8626 not on file).
- Würth WE-MAPI Isat/IR (no PDF). MLCC DC-bias effective capacitance (no curves).
- LMR38020 switching edge times, Coss, and the real board thermal resistance (only the bring-up gate can confirm these).
- I did not run KiCad ERC or regenerate the schematic. I only read the existing `kicad/F405FC.net` for the power nets.
- While this audit ran, uncommitted work-in-progress changed `design/circuit.py` (mounting-hole footprint only; the line
  numbers cited above are unchanged) and removed the B.Cu pad 9 from the LMR38020 DDA footprint
  (`lib/F405FC.pretty/TI_HSOIC-8-1EP_..._DDA.kicad_mod`; the thermal vias remain). That is layout (Gate 1) and out of
  scope here. The Gate 1 reviewer should check that the bottom-side heat-spreading copper under U1/U2 is still present,
  because the 12.5 model assumes the whole board spreads the heat.

## Verdict

**FAIL**: 1 MAJOR open (P1-01, the P0-01 residual: thermal envelope and gate). P0-02 is closed as an accepted deviation
(D-11). The remaining open items are MINOR: P0-03, P0-04, P0-05, P1-02, P1-03 and P1-04. INFO: P0-12, P0-14, P0-16,
P0-17, P1-05 and P1-06. No BLOCKER: I found no abs-max violation or back-feed path in battery-only, USB-only, both,
battery hot-plug, VTX-off or reset/DFU states, and circuit.py's power nets match the datasheet pinouts. P1-01 can be
fixed in the text (envelope, P_board term, gate criteria tied to ambient and run at 2S + 6S, stale 104 C claims) without
changing the circuit.
