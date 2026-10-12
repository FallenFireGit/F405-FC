# Gate 1 re-review: MCU / digital (F405-FC, schematic rev C, HEAD bf896ee)

Reviewer: fresh, independent Gate 1 MCU/digital re-reviewer, 2026-10-11. This is a re-review of `review/gate-1-mcu-digital.md` (FAIL on MAJOR G1M-01) after the lead's responses in `design/decisions.md` (D-07 crystal row, D-15) and the `design/circuit.py` changes in bf896ee.

## 1. Evidence base and limits

* **Netlist.** Freshly exported from the current schematic with `kc 'cd kicad && kicad-cli sch export netlist -o /work/kicad/F405FC.net F405FC.kicad_sch'`. That file is git-ignored (`.gitignore:7`).
* **Scripts** (scratchpad, not committed):
  * `pc.py` parses every net and node in the netlist and compares all 64 U3 pins with pinmap §2 (first token of "Net / function") and §9.
  * A second script maps each `resource` line in `betaflight_config.txt` through pinmap §9 (port → pin) to the netlist net.
* **ERC.** `kicad/erc.rpt` (19:25): 0 errors, 0 warnings. The schematic PDF (`docs/F405FC_schematic.pdf`, bf896ee) contains R41 / VTX_PWR, so it reflects the Gate 1 fixes.
* **Web.**
  * WebSearch result snippets only.
  * Direct downloads of the ST DS8626 copy (cdn.sparkfun.com) and of `ecsxtal.com/store/pdf/ECX-32.pdf` failed with proxy `CONNECT 403`.
  * **Not seen by me:** DS8626 Table 30 itself, the ECX-32 datasheet, and AN2867.
  * DS8626 and ECX-32 are still **not on file** in `datasheets/`.

## 2. Disposition of the previous findings

| ID | Prev. | Lead response | Re-review disposition |
|---|---|---|---|
| G1M-01 | MAJOR | D-07: "DS8626 Table 30 lists HSE gm 5 mA/V min (third-party mirror ic37.com)", giving a margin of about 10 | **OPEN, stays MAJOR** (restated as G1M2-01) |
| G1M-02 | MINOR | D-15: accepted. User-guide note "connect battery before USB, or reboot"; no series resistors | **RESOLVED (accepted risk, documented).** Consistent with the previous review's first fix option. Residual: the "user guide" D-15 cites does not exist in the repo yet (no hit for the wording outside decisions.md and reviews), so see G1M2-02 (INFO) |
| G1M-03 | INFO | R32 comment and video sheet note "fit ONLY with U12 removed" (`circuit.py` VID note) | Closed (schematic note present). A silkscreen note is a Gate 2 item |
| G1M-04..11 | INFO | No change needed | Unchanged, carried as INFO |

## 3. G1M-01 recomputed independently

**Crystal data (ECS-80-8-33-JEN-TR3).** DigiKey listing snippet (product 15282973): "8 MHz ±20ppm Crystal 8pF 400 Ohms 4-SMD", -40 to 85 °C. The JGN variant has the same 400 Ω / 8 pF. **ESR max 400 Ω is confirmed by distributor data. C0 could NOT be confirmed:** no search result gave it, and the ECX-32 PDF is unreachable.

**gm_crit per AN2867** = 4·ESR·(2πf)²·(C0+CL)², with ESR = 400 Ω and f = 8 MHz. CL is the load the crystal actually sees. With C36 = C37 = 10 pF and 3-5 pF stray, CL_eff = 5 + (3…5) = **8-10 pF**, not just the nominal 8 pF.

| C0 \ CL_eff | 8 pF | 9 pF | 10 pF |
|---|---|---|---|
| 3 pF | 0.489 mA/V | 0.582 | 0.683 |
| 5 pF | 0.683 | 0.792 | 0.910 |
| 7 pF | 0.910 | 1.035 | **1.168** |

**MCU-side figure.**
* I could not verify D-07's "DS8626 Table 30, gm = 5 mA/V min". It rests on an unreviewable third-party mirror of unknown revision.
* The snippets I did obtain point the other way:
  * The STM32F427/F429 datasheet (same F4 RCC/HSE cell, alldatasheet mirror snippet) lists **"Gm_crit_max, Maximum critical crystal gm, Startup: 1 mA/V max"**, "based on characterization, not tested in production".
  * An ST application engineer on community.st.com (STM32L443 thread) states that the datasheet "Gm" value "means the max. allowed transconductance of the crystal which corresponds to Gm_crit_max in AN2867".
  * In those datasheets, the 5 mA/V-min style "oscillator transconductance" row appears in STM8 datasheets. The F103 datasheet shows 25 mA/V.
* So the F4 row is most likely **Gm_crit_max = 1 mA/V**. The acceptance test is then **gm_crit < 1 mA/V**, not gm/gm_crit ≥ 5.

**Result.**
* With Gm_crit_max = 1 mA/V: passes if C0 ≤ about 5 pF (0.49-0.91 mA/V, but only 9 % headroom at C0 = 5 pF and CL_eff = 10 pF). It **fails if C0 is about 7 pF** and the stray is at the high end (1.04-1.17 mA/V).
* Even on D-07's own reading (gm = 5 mA/V min, need ≥ 5×), the worst case is 5/1.168 = 4.3 < 5. D-07's "≥ 7 at C0 = 5 pF" uses the nominal CL of 8 pF rather than CL_eff (5/0.91 = 5.5).
* **Either way, the outcome depends on the unconfirmed C0.** The margin is therefore still not demonstrated, and the cited MCU figure is unverified and likely misread.

**Load caps.** CL_eff = 8-10 pF against CL = 8 pF. This pulls the frequency about 10-40 ppm low (C1 3-6 fF assumed, *not verified*). That is negligible against the USB FS ±2500 ppm limit and the ±20 ppm tolerance. 10 pF is acceptable. 8.2 pF would centre CL_eff on 8 pF and also reduce gm_crit by about 10-15 % (INFO G1M2-03).

## 4. Pin check and digital spot checks (re-run)

| # | Check | Result |
|---|---|---|
| R1 | 64 U3 pins vs pinmap §2 and §9 | Script: `U3 pins 64 s9 64 s2 64 mismatch []` |
| R2 | BF `resource` lines vs netlist | 41/41 OK: BEEPER, MOTOR1-8, LED_STRIP, SERIAL_TX 1/2/3/5/6, SERIAL_RX 1/2/3/5/6, RX4 = ESC_TLM, I2C1, LED1/2, SPI1/3, ADC ×3, PINIO1 = PC15 VTX_PWR_EN, PINIO2 = PC13 CAM_SEL, FLASH_CS, GYRO_EXTI/CS ×2. `betaflight_config.txt` and `pinmap.md` were unchanged since 356d3d8 |
| R3 | HSE | Y1.1 = HSE_IN (U3.5, C36), Y1.3 = HSE_OUT (U3.6, C37), Y1.2/4 = GND. C36/C37 are 10 pF C0G to GND |
| R4 | USB | USB_DP = J1 A6/B6, U13.3/4, U3.45. USB_DM = J1 A7/B7, U13.1/6, U3.44. VBUS = J1 A4/A9/B4/B9, U13.5, D4 → 5V_SYS. CC1/CC2 have separate 5.1k (R34/R35). SBU1/2 are unconnected (intended) |
| R5 | Straps / reset / SWD | BOOT0: R16 to GND, SW1 to 3V3, U3.60. BEEPER (PB2/BOOT1): R17 10k to GND, R40 → BUZ_G → Q1 gate. NRST: C35, TP3. SWDIO TP1, SWCLK TP2 |
| R6 | LEDs | 3V3 → R27/R28 → D11/D12 anode. Cathodes (pin 1) are on PB14/PB15, so low = on, consistent with `led_inversion` 0 |
| R7 | PINIO chains | VTX_PWR_EN → R11 → VTX_OFF_G (Q2 gate, R12 to GND), Q2 drain → EN_10V (U2.2). CAM_SEL → U11.6 with R31 pulldown, U11 VCC = 3V3 |
| R8 | UART crossings | J3: 3/4 = UART1_TX/RX, 6 = HD_R2 → R37 (DNP) → UART5_RX. J4: 3/4 = UART3_TX/RX, 5/6 = SDA/SCL. J5: 3/4 = UART2_TX/RX. J2.8 = ESC_TLM. FC-side naming is unchanged (G1M-05) |
| R9 | Gate 1 fix side effects | J3 pin 1 is now VTX_PWR through R41 0R from 10V (no digital impact). 3V3 bulk is now a single C2u2 at the LDO (C21 retired). 13 caps remain on 3V3, VCAP1/2 (C33/C34) and 3V3A (C31/C32 via FB1) are intact. The C-numbering of the MCU decoupling is unchanged. X7R/50 V cap swaps are non-digital |
| R10 | Unused / floating | PC2/PC3/PB12/PB13 have 100k pulldowns. CS pull-ups R18/R19/R20 are present. The only single-node nets are intentional NC pins (J1 SBU, U1/U2 PG, regulator NC, BMI270 aux/INT2, BMP390 INT, IIS2MDC DRDY/NC) |
| R11 | ERC | 0 errors / 0 warnings |

**Nothing digital was broken by the Gate 1 fixes.**

## 5. New findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| G1M2-01 | **MAJOR** | **HSE gain margin is still not demonstrated (G1M-01 stays open).**<br>1. Crystal C0 is unconfirmed.<br>2. D-07's "DS8626 Table 30, 5 mA/V min" cannot be verified (third-party mirror, revision unknown). It conflicts with the F4 sibling datasheet row "Gm_crit_max 1 mA/V max" and with ST's own explanation of that row.<br>3. D-07 uses nominal CL 8 pF, but the circuit gives CL_eff = 8-10 pF.<br>Under the Gm_crit_max reading the design passes only if C0 ≲ 5 pF. At C0 = 7 pF, gm_crit = 1.04-1.17 mA/V > 1 | §3 table; `circuit.py:316-320`; `decisions.md:70`; WebSearch snippets (DigiKey 15282973; STM32F427 DS mirror; community.st.com L443 thread) | **(a)** File DS8626 (current rev) and the ECX-32 datasheet under `datasheets/` (download in a normal browser; this environment's proxy blocks both). Correct D-07 to the actual Table row, its meaning (gm vs Gm_crit_max) and CL_eff = 10 pF worst case. Close only if gm_crit(C0 max, CL 10 pF) < Gm_crit_max (or gm/gm_crit ≥ 5 if the row is truly a gm min). **(b)** If C0 > 5 pF, or to remove the dependency: use an 8 MHz crystal with ESR ≤ 200 Ω (gm_crit ≤ 0.58 mA/V even at C0 7 pF / CL 10 pF), e.g. a 5032-size part, or an AN2867 §5 recommended resonator. Optionally use 8.2 pF load caps (G1M2-03) |
| G1M2-02 | INFO | D-15 references a user guide and silkscreen ("VTX 10V" / "GPS 5V", battery-before-USB) that do not exist yet | `decisions.md:111-117`; no hit in `docs/` | Track as a Gate 2 / release deliverable |
| G1M2-03 | INFO | Load caps of 10 pF with 3-5 pF stray give CL_eff = 8-10 pF against CL 8 pF. The frequency is about 10-40 ppm low (C1 assumed). Harmless for USB/UART | §3 | Optional: 8.2 pF C0G centres CL_eff and lowers gm_crit by about 10-15 % |

## 6. Verdict

**FAIL: 1 MAJOR (G1M2-01, the HSE gain margin carried over from G1M-01).** G1M-02 is resolved as an accepted, documented risk. The pin map (64/64), the Betaflight resources (41/41), USB, straps, LEDs, PINIO chains, UART connectors and ERC are all clean. The Gate 1 fixes introduced no digital regressions. G1M2-01 closes on documentation alone if the filed DS8626 and ECX-32 datasheets show gm_crit(C0 max, CL_eff 10 pF) within the MCU limit. Otherwise Y1 must change to a lower-ESR part.

Sources (search snippets only): DigiKey ECS-80-8-33-JEN-TR3 (https://www.digikey.com/en/products/detail/ecs-inc/ECS-80-8-33-JEN-TR3/15282973); STM32F427 DS mirror (https://www.alldatasheet.net/html-pdf/2184851/STMICROELECTRONICS/STM32F427NET6TR/269269/118/STM32F427NET6TR.html); ST community L443 gm thread (https://community.st.com/s/question/0D50X0000A1mqBf/); AN2867 (https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf, not opened).
