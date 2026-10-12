# Gate 1 MCU/Digital re-review, round 3

Scope: this is a narrow re-review of G1M2-01 (HSE crystal gain margin) after the lead made two changes:

- C36 and C37 are now 8.2 pF C0G parts, `CL05C8R2CB5NNNC`.
- `design/decisions.md` D-07 (the crystal row) was rewritten and cites C0 = 5 pF.

The review also includes a regression check of the HSE nets. The reviewer is independent and did not use the previous reviews' numbers. No design files were modified.

## 1. Evidence gathered (and its limits)

| Input | Value used | Evidence | Strength |
|---|---|---|---|
| ESR max, ECS-80-8-33-JEN-TR3 | 400 Ω | WebSearch: DigiKey 15282973 listing reads "8 MHz ±20ppm Crystal 8pF 400 Ohms 4-SMD", -40 to 85 °C | Distributor data. The ECS ESR table found in search (the ECA-ECX-32 variant) starts at 10 MHz (100 Ω max for 10-15.999 MHz), so it does not cover 8 MHz. The 400 Ω figure is also the most conservative value in Mouser's quoted "40-400 Ω" range |
| C0, ECX-32 | 5 pF | WebSearch (extended): the ECS ECX-32 datasheet snippet reads "Shunt Capacitance Co 5 pF", and Mouser's ECX-32 page repeats 5 pF | Two consistent snippets. **The PDF itself was not opened:** ecsxtal.com and mouser.com fail DNS in WebFetch, and the proxy returns 403 to curl |
| CL, crystal | 8 pF | DigiKey listing (as above) | Distributor data |
| DS8626 HSE transconductance row | "gm" 5 mA/V min, or "Gm_crit_max" 1 mA/V max | WebSearch (extended): the AN2867 snippet lists the STM32F4 4-26 MHz HSE row as a gm minimum of 5 mA/V and a Gm_crit_max of 1 mA/V. AN2867 also says the same parameter is named "Gm_crit_max or Gm depending on the product documentation", and gives the rule "gain margin = gm/gm_crit > 5" | Snippets only. **DS8626 itself was not opened** (the mouser.com mirror fails DNS, and curl to st.com gets 403). The two readings are mutually consistent (5 mA/V ÷ 5 = 1 mA/V), so the ambiguity matters less if both criteria are checked |

## 2. Recomputation (AN2867: gm_crit = 4·ESR·(2πf)²·(C0+CL)²)

Inputs: ESR = 400 Ω and f = 8 MHz.

The two 8.2 pF caps in series give 4.1 pF. Adding 3-5 pF of stray gives an effective CL of **7.1-9.1 pF**, which is centred on the crystal's 8 pF.

The table was computed with Python in this session.

| C0 | CL_eff | C0 + CL | gm_crit | gm/gm_crit (gm = 5 mA/V) | ≤ Gm_crit_max 1 mA/V? |
|---|---|---|---|---|---|
| 5 pF | 7.1 pF (3 pF stray) | 12.1 pF | 0.592 mA/V | 8.45 | yes |
| 5 pF | 8.1 pF (4 pF stray) | 13.1 pF | 0.694 mA/V | 7.21 | yes |
| 5 pF | 9.1 pF (5 pF stray, worst case) | 14.1 pF | **0.804 mA/V** | **6.22** | **yes (20 % headroom)** |
| 7 pF (sensitivity) | 7.1 pF | 14.1 pF | 0.804 mA/V | 6.22 | yes |
| 7 pF (sensitivity) | 9.1 pF | 16.1 pF | 1.048 mA/V | 4.77 | **no** |

**Result:** with C0 = 5 pF, both readings pass at the worst-case CL_eff of 9.1 pF:

- gm/gm_crit = 6.2 ≥ 5
- gm_crit = 0.80 mA/V < 1 mA/V

This matches D-07's 0.59 / 0.80 mA/V and margin of 6.2. The design fails the Gm_crit_max criterion only if (C0 + CL_eff) exceeds about 15.7 pF. At 5 pF stray that means C0 > 6.6 pF, which is 1.6 pF above the cited datasheet value.

**Part-number check for `CL05C8R2CB5NNNC`** (Samsung code):

| Code | Meaning |
|---|---|
| CL05 | 0402 |
| C | C0G |
| 8R2 | 8.2 pF |
| C | ±0.25 pF |
| B | 50 V |
| 5 | 0.5 mm thickness |
| NNNC | Ni/Sn termination, reel |

A WebSearch distributor listing confirms "8.2 pF, 50 V, C0G (NP0), 0402". The netlist value is "8.2pF C0G 50V" with footprint `C_0402_1005Metric`, and the BOM line matches (`bom/bom_raw.csv:10`).

## 3. Regression check

- `kc 'python3 gen/netcheck.py'` printed `model pins=467 exported pins=467 nets=110 parts=161` and then `netcheck: OK (model == exported netlist)`.
- In `kicad/F405FC.net` (exported Oct 12 00:13, newer than `circuit.py`):
  - **HSE_IN** connects C36 pin 1, U3 pin 5 (PH0) and Y1 pin 1.
  - **HSE_OUT** connects C37 pin 1, U3 pin 6 (PH1) and Y1 pin 3.
  - C36 pin 2, C37 pin 2, Y1 pin 2 and Y1 pin 4 are on **GND**.

  This is correct.

## 4. Disposition of G1M2-01

**CLOSED (resolved, with an evidence caveat).** The three points raised last round are addressed:

1. **C0 is unconfirmed.** It is now sourced as 5 pF, from two independent search snippets of ECS and Mouser material. It is not from a filed PDF.
2. **The DS8626 row wording is ambiguous.** D-07 now evaluates both readings, and both pass at the worst case. AN2867's own text treats "Gm" and "Gm_crit_max" as names for the same row and pairs 5 mA/V with 1 mA/V for the F4. The ambiguity therefore no longer decides the outcome.
3. **D-07 used nominal CL.** D-07 now uses CL_eff of 7.1-9.1 pF with the 8.2 pF caps.

The headroom is real but modest: 20 % under the Gm_crit_max reading, and the margin of 6.2 is only just above the required 5. The residual risk comes from the primary documents not having been read (G1M3-01) and is covered by D-07's bring-up test.

## 5. New findings

| ID | Severity | Finding | Evidence | Recommendation |
|---|---|---|---|---|
| G1M3-01 | INFO | The primary documents (ECS ECX-32 PDF and ST DS8626) are still not filed or read. C0 = 5 pF and the HSE row rest on search snippets. The design would fail Gm_crit_max if C0 > 6.6 pF | §1; ecsxtal.com, mouser.com and st.com are unreachable from this environment | File both PDFs under `datasheets/` from a normal browser. Confirm that C0 is 5 pF **max** (not typ) and confirm the DS8626 row wording. Keep the D-07 bring-up test (20 cold boots, low temperature) |
| G1M3-02 | MINOR (documentation) | D-07 labels 0.59 mA/V as "typ". That value is the **best case** (3 pF stray, CL_eff 7.1 pF). The mid-range value (4 pF stray) is 0.69 mA/V. The worst-case value of 0.80 mA/V and the conclusion are correct | `design/decisions.md:70`; §2 table | Change it to "0.59-0.80 mA/V (3-5 pF stray), 0.69 typ". This does not block the gate |
| G1M3-03 | INFO | The DigiKey SKU `1276-1650-1-ND` for CL05C8R2CB5NNNC could not be confirmed by search. It is already marked "(verify)" | `circuit.py:61`; BOM line 10; WebSearch found no DigiKey page linking the two | Confirm the SKU before ordering (BOM/sourcing gate) |
| G1M3-04 | INFO | The 8 MHz ESR comes from distributor data only. The ECS ESR table found starts at 10 MHz | §1 | Confirm the 8 MHz ESR row when the ECX-32 PDF is filed. 400 Ω is already the conservative assumption |

## 6. Verdict

**PASS.** There are no BLOCKER or MAJOR findings: G1M2-01 is closed, and the round adds one MINOR documentation finding (G1M3-02) and three INFO findings. With C0 = 5 pF and ESR = 400 Ω, the worst-case CL_eff of 9.1 pF gives gm_crit = 0.80 mA/V. That passes both the gm/gm_crit ≥ 5 reading (6.2) and the Gm_crit_max = 1 mA/V reading. Netcheck is OK and the HSE nets are intact.

Sources (search snippets only; no PDF was opened):

- DigiKey ECS-80-8-33-JEN-TR3: https://www.digikey.com/en/products/detail/ecs-inc/ECS-80-8-33-JEN-TR3/15282973
- ECS ECX-32 datasheet: https://ecsxtal.com/store/pdf/ecx-32.pdf
- ECS ECA-ECX-32 datasheet: https://www.ecsxtal.com/store/pdf/ECA-ECX-32.pdf
- Mouser ECX-32 page: https://www.mouser.com/en/new/ecs/ecs-ECX-32-smd-quartz-crystals/
- AN2867 Rev 24: https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm8afals-stm32-mcus-and-mpus-stmicroelectronics.pdf
- ST community thread on the L443 Gm row: https://community.st.com/t5/stm32-mcus-products/to-wich-parameter-refers-hse-oscillator-characteristic-gm-in/td-p/370436
- CL05C8R2CB5NNNC listing: https://www.ibselectronics.in/part/samsung/cl05c8r2cb5nnnc/156603/
