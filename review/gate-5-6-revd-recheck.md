# Gate 5 / Gate 6 re-check of the rev D fixes (c1f81bb, 176113f)

Reviewer: independent re-check, 2026-10-15. Repo HEAD at review time: `1fae613` (on top of `176113f`; that commit only adds
`review/summary.md`, so the board and docs state is the `176113f` state). Board md5 `653c16f502e2028fce2b689dd5a80664`.
Coordinates are board mm (file coordinates minus 100 mm), y downwards; the J3 (VTX) edge is y = 0.

## Verdict: **PASS** (0 BLOCKER, 0 MAJOR, 7 MINOR)

All five MAJORs from the three reports are closed or reduced to a MINOR residual:
- G5D-01: the upload BOM now has the right L1/L2 part.
- G5D-02 / G6B-02: the Stage B fit list and step order are fixed.
- G6B-01: front arrows are on both silk layers and point at the J3 edge.
- G6S-11: the LDOs now get an unpowered GND check and a first power-up at 3.6 V / 30 mA.

G6S-11 is **partly** fixed. The new 3.6 V step cannot tell a working LDO from one that is not regulating (R56-01), and the guide then
goes straight to 4.8 V on 5V_SYS. What still protects the IMUs is the unpowered GND-continuity check, and only if the builder probes
the part's lead. I rate that residual MINOR. It is a two-line guide edit and should be made before anyone builds a board.

The fab outputs, iBOM, schematic and the three BOM CSVs are all consistent with the current board and `circuit.py` (section 4).

## 1. Status of the earlier findings

### Gate 5 DFM (`review/gate-5-dfm-revd.md`)

| ID | Sev | Status | Evidence |
|---|---|---|---|
| G5D-01 | MAJOR | **Fixed** (residual → R56-05) | `bom/F405FC_digikey_bom.csv:27` and `bom/bom_raw.csv:24`: 732-11317-1-ND / 78438356056. A script cross-check of all three CSVs against the PCB MPN/DigiKey fields finds 0 mismatches and 0 empty PNs (§4). `decisions.md:260-263`: D-26 amended. Still open: `design/power.md:137,139,181,496` name 74438356056, and the WE-MAIA land pattern against `L_Wuerth_MAPI-4020` is unverified |
| G5D-02 | MAJOR | **Fixed** | Guide :121-125: Stage B fits R17, R19, R34/R35, R36/C51. The USB-only test moved to Stage B step 2 (:135). Unpowered BOOT0/PB2/CC checks at :133-134. Script: every top part is named in a stage, or is a passive covered by Stage C's "remaining top passives" (C43-C47, C50, R25, R26, R33, R38-R40). The MCU-critical nets VCAP1/2 (C33/C34), 3V3A (C31/C32/FB1), HSE (C36/C37), USB (U13/J1) and the CS pull-ups (R18/R20 bottom, R19 top) are all fitted by Stage B |
| G5D-03 | MINOR | **Fixed (doc)** | Guide :29 now reads "51 vias (15 in-pad), closest 0.018 mm, U3 pin 48". POFV availability on JLC is still unverified (stated). The "do not order without POFV" sentence was not added |
| G5D-04 | MINOR | **Fixed** | Guide :127-131: six layers, R6 pad 1 VBAT warning, check R6.1 to P2 before power |
| G5D-05 | MINOR | **Fixed (doc)**; layout open | Guide :153-154: preheat from below for top-side hot air. The DRC rule for thermal spokes was not added (optional) |
| G5D-06 | MINOR | **Fixed** | Guide :151-153: print on a support carrier, with syringe or pre-tin as alternatives. The Y1 text is corrected |
| G5D-07 | MINOR | **Partly** → R56-03 | P6 and J5 labels added, but each is on the opposite side from its part. "J3 VTX 10V" and "P10 LED" are still bottom-only. The C1/C2/T5/R5 pad names are unchanged |
| G5D-08 | MINOR | **Open** → R56-03 | Glyph-to-hole-centre distances: "BZ-" 1.81 mm from H3, "GPS 5V" 2.80 mm from H1 (`holes.py`). "BOOT" is still at (20.59, 10.33), 7 mm from SW1 |
| G5D-09 | MINOR | **Open** | All 371 footprint silk shapes are 0.12 mm (`w.py`) |
| G5D-10 | MINOR | **Partly** | Schematic sheets are `(rev "D")`, and `circuit.py:23` has `rev="D"`. `requirements.md:9` gives 6 layers and records the owner's request. The PCB title block still has no revision: the job file says `"Revision": "rev?"` and the iBOM metadata has `revision: ""` |
| G5D-11 | MINOR | **Open** | `F405FC.kicad_dru` has only the J1 spoke rule, no NPTH clearance rule |
| G5D-12 | MINOR | **Open** | The upload BOM still orders 2 each of U6-U10 (lines 42-45, 52) |
| G5D-13 | MINOR | **Partly** | "pin-1 triangle" (:72) and "C53 (RSSI filter)" (:122) are fixed. D1/C1 are still "by iron **or hot air**" (:63) |
| G5D-14 | MINOR | **Open** | "(verify)" is still on the board DigiKey fields of C2/C3/C4/C10-C12/C17/C19/C22/C31/C51/U1/U2 and on 4 `bom_raw.csv` rows. "167.56" is still in the costed TOTAL row, "left blank" in rows 31/36/52, and "rev C Gate 5 M-1" in row 26 |

### Gate 6 Betaflight red team (`review/gate-6-betaflight-redteam-revd.md`)

| ID | Sev | Status | Evidence |
|---|---|---|---|
| G6B-01 | MAJOR | **Fixed** (clarity nits in R56-07; stale release copy R56-04) | B.Silk: "FRONT" (26.28, 1.05), with the arrow stem (24.05, 1.50)→(24.05, 0.60) and barbs to (23.75/24.35, 0.95). F.Silk: "FWD" (29.09, 31.05), with the arrow (27.55, 31.50)→(27.55, 30.60) and barbs to (27.25/27.85, 30.95). Both tips point to −y, which is the J3 edge (J3 at (18.0, 3.1), pads at y = 5.1). A physical arrow points at the same edge whichever way the board is flipped, and the mirrored B.Silk text reads correctly from below (`board_bottom.png`: "FRONT↑"). Guide :169, `design/betaflight_config.txt:156` and INAV :41 name the J3 edge |
| G6B-02 | MAJOR | **Fixed** | Same as G5D-02 |
| G6B-03 | MINOR | **Partly** → R56-03 | P6/J5 labels are on the far side. "BOOT" (20.59, 10.33) and "USB" (24.44, 22.3) are unchanged, far from SW1 (26.5, 6.4) and J1 (bbox x 27.5-36.5) |
| G6B-04 | MINOR | **Fixed** in `design/betaflight_config.txt:13-14,162,167` and guide :168. **Not** in the release copy `docs/F405FC_betaflight_config.txt` (R56-04) |
| G6B-05 | MINOR | **Open** (bench mitigation at :165-166) | No `align_mag`. No IIS2MDC datasheet in `datasheets/` |
| G6B-06 | MINOR | **Partly** | The pre-flight checklist was added (:170-172). §3 step 4 still says only "Flash Betaflight (STM32F405 target)", with no build/driver list and no `defaults nosave` → paste → `save` sequence |
| G6B-07 | MINOR | **Partly** → R56-02 | The BOOT0 ≈ 10 kΩ check is correct (U3.60 BOOT0, R16 10k). The SW1 wording is wrong |
| G6B-08 | MINOR | **Fixed** | Steps 0-8 run in sequence. The "A2 (step 2.1.8)" reference (:68) and step 8 (:99) agree. C53 and Y1 texts are fixed |
| G6B-09..14 | INFO | Unchanged | Config/INAV headers still say "rev C" (`betaflight_config.txt:3-4`, `inav_target.md:1`). LEDs on the bottom, baro foam and `vcd_video_system` are not added |

### Gate 6 smoke red team (`review/gate-6-smoke-redteam-revd.md`)

| ID | Sev | Status | Evidence |
|---|---|---|---|
| G6S-11 | MAJOR | **Partly** (residual MINOR → R56-01) | Guide :99-103 adds U4 tab / U5 pin 2 to GND < 1 Ω, rail-pair checks, and a first LDO power-up at 3.6 V / 30 mA on 5V_SYS. Back-feed analysis is in §2.3: safe. Not adopted from the proposed fix: the 5.0 V intermediate check, the tight window, and the U5 pin-1 inspection |
| G6S-12 | MINOR | **Partly** → R56-06 | Rail-to-rail checks added (:42-44). VBAT↔RT_10V (U2.4), VBAT↔J2 pins 3-8 and the magnified inspection of the listed spots are missing. Layout items are left for the next spin |
| G6S-13 | MINOR | **Partly** → R56-05 | The three BOMs agree and the duplicate 1276-3047-1-ND line is gone (script: no duplicate DK lines). `power.md` still names the old MPN. The land pattern is unverified |
| G6S-14 | MINOR | **Fixed** | Guide :178-180, and J2 pin 1 VBAT / pin 2 GND matches the PCB (J2.1 VBAT (17.5, 30.9), J2.2 GND). The smoke-stopper suggestion is not included |
| G6S-15 | MINOR | **Partly** → R56-06 | The header rule (:7-11), Stage B list and numbering are fixed. The §1 bare-board list still omits 3V3_IMU, 3V3A and VTX_PWR |
| G6S-16 | INFO | Open (next spin) | Not re-measured |
| G6S-17 | INFO | Open | The nylon rule is only in §0, not in §5 |
| G6S-18 | INFO | Open | The stop rule (:85-86) still has no "steady state" |
| G6S-19 | INFO | **Mostly fixed** | `power.md:243,247,360,514`: In3, BAT54S removed. Schematic rev D. Still stale: `power.md:1` (header lists rev B/C/D), `power.md:429` ("L2 GND"), and committed `F405FC.kicad_pro` has an empty `erc.rule_severities`, while `circuit.py` writes 7 rules. ERC on a regenerated copy with those rules: **0 violations** |
| G6S-20 | INFO | Unchanged (accepted risks) | |

## 2. Assembly guide walk-through (builder's view)

### 2.1 Parts on the board at each step

| Step | Fitted | Notes |
|---|---|---|
| §1 bare | none | Probe points exist: P1, P2, P3, P8/P11, J5.1 pad (top (5.1, 19.5), 5V_SYS), TP4 (bottom (8.1, 16.0), 3V3), J1 VBUS pads (bare) |
| A1 (hot plate) | all 69 bottom parts except D5/U4/U5 (script list) | Includes U6/U7/U10/U11 and the LDO caps C18/C19/C22/C23/C38-C42 |
| A1 top | D1, C1, R41 | |
| 2.1.0-7 | + nothing | 3V3, 3V3_IMU and 5V_SYS are unfed because D5/U4/U5 are absent. Checked: the 5V_SYS pads are only C18/C19/C22, D4.1, D5.1, J5.1, U4.1/4 and U5.1/3 (`net.py`) |
| 2.1.8 | + D4 (top), D5, U4, U5 | 3.6 V / 30 mA on J5.1, then 8.4 V on P1 |
| Stage B | + U3, Y1, C25-C29, C31-C37, C53, R14-R17, R19, R34-R36, C51, FB1, U13, J1, SW1 | |
| Stage C | + U8, U9, U12, D9, Q1, J2-J5, C43-C47, C50, R25, R26, R33, R38-R40 | R32/R37 DNP |

The order is possible: no step needs a part that is fitted later. One awkward point: in step 2.1.8 the 3.6 V source goes onto the
bare JST-SH pad J5.1 (top, 1.0 mm pitch next to J5.2 GND). That works with a fine probe or a soldered wire. C19.1 (bottom, 0603 at
(26.72, 12.65)) is an easier 5V_SYS point; the guide could name it.

### 2.2 Values and pin numbers quoted in the guide

| Guide | PCB / `circuit.py` | OK |
|---|---|---|
| R16 10k BOOT0 to GND, U3 pin 60 | R16 10.0K, pads BOOT0/GND; U3.60 = BOOT0; `circuit.py:315` | yes |
| R17 10k BOOT1/PB2, U3 pin 28 | R17 10.0K, pads BEEPER/GND; U3.28 = BEEPER; `circuit.py:292` PB2 = BEEPER | yes |
| R34/R35 5.1k on CC1/CC2 | R34 USB_CC1 (J1.A5), R35 USB_CC2 (J1.B5), 5.10K | yes |
| J2 pin 1 VBAT, pin 2 GND | J2.1 VBAT, J2.2 GND, 3 ESC_CURR, 4-7 MOTOR1-4, 8 ESC_TLM | yes |
| U4 tab, U5 pin 2 = GND | U4.5 GND (24.30, 4.05); U5.2 GND (14.36, 5.20) | yes |
| 5V FB 100k/24.3k, 10V 100k/11.0k | `circuit.py:218-219` R24k3 / R11k | yes (not re-derived) |
| SW1 check "two pads on the BOOT0 side" | SW1 pad 1 = 3V3 at y 5.33 (both), pad 2 = BOOT0 at y 7.47 (both) | **no** (R56-02) |

### 2.3 The 3.6 V / 30 mA step on 5V_SYS (guide :101-102)

- **Back-feed is blocked.** Both OR diodes point into 5V_SYS: D5 has its anode on 5V and cathode on 5V_SYS, and D4 has its anode on
  VBUS and cathode on 5V_SYS (`circuit.py:251,425`; PCB pads D5.1/D4.1 = 5V_SYS).
- **The leakage through them is harmless.** PMEG4030ER IR is 5 µA typ at 10 V reverse (`PMEG4030ER.pdf` Table 7). At this step
  VBUS has nothing fitted, because J1/U13/R36/C51 are Stage B parts, and 5V sees only U1 (off), the R4/R5 divider and caps. The
  result is µA into high-impedance nodes. Nothing else is on 5V_SYS.
- **LP38692 at 3.6 V in.**
  - VIN range is 2.7-10 V (`lp38692.pdf` §6.3).
  - Dropout at 3.3 V is 65 mV typ at 0.1 A.
  - EN is tied to IN (U4.1 = 5V_SYS), and Output ON needs ≥ 1.8 V at VIN = 4 V.
  - It "remains stable and in regulation with no external load" (§8.2.2.2.3).
  - It therefore regulates at about 3.3 V on a few mA of load.
- **LP5907 at 3.6 V in.** VIN range is 2.2-5.5 V, it has no UVLO, and it regulates once VIN ≥ VOUT + VDO (`lp5907.pdf` §6.4.2).
  It regulates as well.
- **Behaviour at 3.6 V is as intended.** No LDO fault can exceed 3.6 V, below the 4.0 V IMU abs max. The 30 mA limit covers the
  inrush into about 7 µF on 5V_SYS.
- **The pass window is too wide to be a test (R56-01).**

## 3. New silk

| Check | Result | Evidence |
|---|---|---|
| Arrows point at the J3 edge | **Yes, both sides** | Segment end points in §1 (G6B-01). The tips are at y = 0.60 and y = 30.60 with the barbs below them, so both point to −y. J3 is the y ≈ 0-6.4 part. The bottom arrow sits at the J3 edge, 0.2 mm right of the J3 bbox. The top arrow is in the bottom-right corner, 30 mm from J3 |
| Bottom mirroring | OK | "FRONT" `mirrored=True` and reads correctly in `board_bottom.png`. The arrow is geometry, so mirroring does not change where it points |
| Text height ≥ 0.8 mm | **Yes** | All 42 board texts are 0.80 mm high with a 0.15 mm stroke. Footprint reference/value texts are not visible (count 0). Arrow strokes are 0.15 mm |
| Silk on pads | **None** | Glyph-polygon distance from every board silk item to every pad mask opening on its side: minimum 0.087 mm ("S8" to C29.1); FRONT/FWD/arrows > 0.15 mm. DRC: 0 `silk_over_copper` |
| Silk-to-silk | Cosmetic | The FRONT arrow touches the "FRONT" glyph (0.000 mm). FWD is 0.086 mm from its arrow. "P10 LED" is 0.067 mm from U2 footprint silk. DRC reports only C44/U8 |
| P6 / J5 labels unambiguous | **No** → R56-03 | "P6 C2" is on **F.Silk** at (8.35, 11.55), but P6 is a **bottom** pad at (1.6, 15.3), 7.7 mm away. On the top it sits between J4 (GPS) and Y1. The bottom pad column still reads "5V, G, C1, —, VID". "J5 RX" is on **B.Silk** at (10.85, 21.5), but J5 is a **top** connector (3.1, 21.0). On the top, J5 is unlabeled next to the identical J4 "GPS 5V". Cause: `gen/build_pcb.py:216-217` deliberately falls back to the far side |
| FRONT/FWD near holes | OK | FWD glyphs are > 3.2 mm from the H4 centre and FRONT is > 3.2 mm from H2 (`holes.py`) |

## 4. Fab outputs and BOM

- **DRC on a copy of `kicad/`** (`kicad-cli pcb drc --severity-all --schematic-parity`): 0 errors, 0 unconnected, **0 parity**.
  Warnings: 16 `via_dangling`, 1 `silk_overlap` (C44/U8) and 32 `lib_footprint_issues`. The last group comes from the copy location
  and was also seen by Gate 6.
- **Re-export.** I ran the exact `gen/outputs.sh` commands into `/opt/kroot/tmp/g56r/re/`. All 18 Gerber, drill and job files and
  all 4 stencil files are **identical** to `fab/` once the creation-date lines are excluded. The pos CSV is byte-identical.
  `F405FC_JLC_gerbers.zip` and `F405FC_stencil.zip` unpack to exactly `fab/gerbers` and `fab/stencil` (`diff -r`).
  `F405FC_cpl_jlc.csv`: 119 rows, matching the pos file in ref, X, Y, rotation and side.
- **iBOM.** I regenerated it with the same InteractiveHtmlBom 2.12.0 command. The decoded pcbdata JSON differs from
  `bom/F405FC_ibom.html` only in `metadata.date`.
- **Schematic vs `circuit.py`.** I ran `design/circuit.py` in a scratch copy, inside the chroot with the KiCad symbol dir. All 6
  `.kicad_sch` files and `lib/F405FC.kicad_sym` are byte-identical to the repo. ERC with `circuit.py`'s strict rules: 0 violations.
- **BOM consistency** (script, PCB fields vs each CSV, "(verify)" suffixes stripped):

  | File | Rows | Refs | Missing / extra | MPN mismatches | DigiKey PN mismatches | Duplicates |
  |---|---|---|---|---|---|---|
  | `F405FC_digikey_bom.csv` | 53 | 121 fitted + R32/R37 on the "DNP spares" line | 0 / 0 | 0 | 0 | 0 |
  | `bom_raw.csv` | 52 | 119 | 0 / 0 | 0 | 0 | 0 |
  | `digikey_bom_costed.csv` | 53 | 121 fitted + R32/R37 on the "DNP spares" line | 0 / 0 | 0 | 0 | 0 |

  `bom_raw.csv` per-row quantities match the ref counts. No upload line has an empty DigiKey PN.

## 5. Findings

### R56-01 MINOR: the 3.6 V LDO step's pass window cannot detect a non-regulating LDO, and the next step goes straight to 4.8 V

Evidence:
- Guide :102: "3V3 and 3V3_IMU must read 3.2-3.6 V and never more".
- With 3.6 V in, an LDO whose GND is open, or that is otherwise not regulating, pulls its output toward VIN, about 3.5-3.6 V. That
  is inside the window, so it passes.
- A good part reads 3.22-3.38 V (LP38692 ±2.5 % at 25 °C, `lp38692.pdf` §6.5; LP5907 ±2 %, `lp5907.pdf` §6.5).
- The guide then goes directly to "repeat steps 1-3 at 8.4 V" (:102-103), which puts 5V_SYS at about 4.8-5.0 V. The intermediate
  5.0 V check proposed in G6S-11 was not adopted.
- That leaves the unpowered "U4 tab and U5 pin 2 to P2 GND < 1 Ω" check (:99-100) as the only guard. It catches an unwetted joint
  only if the probe touches the component's tab or lead. On the pad copper it always reads < 1 Ω, because U4.5 and U5.2 are poured
  into GND.
- The header's claim (:9-11) that the 3.6 V source means "no LDO fault can exceed the IMUs' 4.0 V absolute maximum" is true only
  during that step.

Fix:
1. Tighten the 3.6 V window to 3.22-3.38 V. A reading above 3.40 V means stop.
2. Add "then raise 5V_SYS to 5.0 V (still 30 mA): both rails 3.22-3.38 V" before going to 8.4 V on P1.
3. Write "probe on the U4 tab / U5 pin 2 lead itself, not on the pad", and add "check U5's pin-1 mark against the silk".

### R56-02 MINOR: the SW1 pre-power check measures two pads of the same terminal

Evidence:
- Guide :133: "across the two SW1 pads on the BOOT0 side: open with the button released, ≈ 0 Ω pressed".
- On the PCB both pads at y = 7.47 ((24.42, 7.47) and (28.57, 7.47)) are pad 2 = BOOT0, and both pads at y = 5.33 are pad 1 = 3V3.
- Two pads "on the BOOT0 side" therefore read ≈ 0 Ω whether or not the button is pressed. A builder following the text would
  conclude that SW1 is stuck closed.
- With U3 and the rails fitted, pad 1 to pad 2 also does not read "open": the DMM sees 3V3 → loads → GND → R16 10k → BOOT0, which
  is a finite, drifting value. This is the same flaw as G6B-07.

Fix: "SW1 pad 1 (3V3, the row nearer the board edge) to pad 2 (BOOT0): released, well above 10 kΩ and drifting; pressed, < 1 Ω."
Keep the BOOT0-to-GND ≈ 10 kΩ check.

### R56-03 MINOR: the new P6 and J5 labels are on the opposite side from their parts; older label issues remain

Evidence:
- "P6 C2" is on F.Silk (8.35, 11.55), while P6 is on B.Cu (1.6, 15.3).
- "J5 RX" is on B.Silk (10.85, 21.5), while J5 is on F.Cu (3.1, 21.0) (pcbnew dump; `board_top.png`, `board_bottom.png`).
- On the top, "P6 C2" sits between J4 and the crystal, where it reads as a label for those parts.
- The bottom video-pad column still has a blank where CAM2 is.
- The receiver connector, as seen when plugging it, has no label next to the identical J4 "GPS 5V".
- Not fixed from G5D-07/G5D-08/G6B-03:
  - "BOOT" is 7 mm from SW1, and "USB" is about 3 mm from J1.
  - "BZ-" is 1.81 mm from the H3 centre, and "GPS 5V" 2.80 mm from H1 (under an M3 nut/standoff).
  - No top "10V" mark at J3, and no top label for P10.

Fix:
1. Place pad labels on the side of the pad. For P6, shorten the label to "C2" or "V2" so it fits in the column, or use a leader
   line.
2. Label J5 on F.Silk (for example "RX" at (5.5-7, 23.5)). Use `--fresh` labels.
3. Move the labels near the holes ≥ 3.2 mm from the hole centres.

### R56-04 MINOR: the release copy `docs/F405FC_betaflight_config.txt` is stale

Evidence:
- `diff design/betaflight_config.txt docs/F405FC_betaflight_config.txt` shows that the docs copy still has
  `set baro_hardware = AUTO` / `set mag_hardware = AUTO` (:161, :166).
- It also still has the old "enum names not verified" comment (:13).
- At :155 it says "marked "FRONT" on silk". That was the G6B-01 evidence line, and it is not updated to the two arrows.
- `docs/F405FC_inav_target.md` is identical to `design/inav_target.md`, so only the BF copy lags.

Fix: copy `design/betaflight_config.txt` to `docs/F405FC_betaflight_config.txt` (and add it to `gen/outputs.sh`). Update the
"Rev C" header lines in both files to "valid for rev D".

### R56-05 MINOR: the L1/L2 part change is not finished outside the BOMs

Evidence:
- `design/power.md:137,139` (§2.2), `:181` (§3.1) and `:496` (BOM table) still name 74438356056 "WE-MAPI".
- The circuit, schematic, all BOMs and the iBOM use 78438356056 WE-MAIA.
- The WE-MAIA land pattern and height against `L_Wuerth_MAPI-4020` are still unverified. This is stated in
  `decisions.md:262-263` and on the upload BOM line 27.

Fix: update power.md. Get the WE-MAIA 4020 drawing into `datasheets/` and compare the pads (0.98 x 3.70 mm on 2.36 mm centres in
the current footprint) before ordering.

### R56-06 MINOR: the rail checks are incomplete and may false-alarm

Evidence:
- §1 (:40-44) still omits 3V3_IMU, 3V3A and VTX_PWR on the bare board (G6S-15).
- The rail-pair list omits the pairs G6S-12 called out: VBAT↔RT_10V (U2 pin 4, 0.138 mm from a VBAT via) and VBAT↔J2 pins 3-8.
- The magnified inspection of the listed via/pad spots is also missing.
- After A1, "never < 1 kΩ" for VBAT-5V can read low in one DMM polarity: 5V → L1 → SW → U1 high-side body diode → VIN. The
  reading depends on the meter's range.

Fix:
1. Add the three rails to §1 and the two pairs to the rail-pair list.
2. Say "measure both polarities and accept a diode-like reading in one direction; a reading < 1 kΩ in both is a short".
3. Add the inspection list from G6S-12.

### R56-07 MINOR: expected-value windows and front-mark clarity

Evidence:
- The step-8 table window for 3V3 and 3V3_IMU, 3.25-3.35 V (:108-109), is tighter than the datasheet tolerance (§2.3: 3.22-3.38 /
  3.23-3.37 V). A good part can fail it.
- The 5V_SYS window is "≈ 4.7-4.9 V". 5V (4.96-5.28 V) minus D5's VF at light load (< 295 mV typ at 0.1 A) gives about 4.75-5.1 V,
  so a board at nominal 5.115 V reads about 4.9 V or more and sits at or past the upper bound.
- On the top silk, the "↑FWD" arrow tip sits right under the P11 "5V" label in the 5V/RSSI/ESC cluster (`board_top.png`). It can
  be read as pointing at the 5V pad.
- On the bottom, the arrow touches "FRONT" and abuts "F405-FC rev D" ("FRONT↑F405-FC rev D").

Fix:
1. Widen the windows to the datasheet limits: 3V3 3.22-3.38 V, 5V_SYS 4.7-5.1 V, USB 5V_SYS 4.4-5.0 V.
2. Add 0.3 mm spaces around the arrows.
3. If space allows, put the top arrow at the J3 edge, as G6B-01 suggested.

## 6. Not verified

- JLC capabilities (POFV on 6-layer, stackup, silk minimums, NPTH clearance). DigiKey listings and stock. The WE-MAIA drawing.
- Real LP38692 behaviour with an open GND tab at 3.6 V in. R56-01 assumes the output pulls toward VIN, which the datasheet does not
  specify.
- DMM readings through unpowered silicon (R56-02, R56-06). Reasoned from the circuit, not measured.
- Renders were checked visually only (the current PNGs show the new arrows and labels). I did not re-render them, and I did not
  re-export or compare the STEP or the schematic PDF.
- The Gate 4 re-route in `176113f` (SI/PI) is outside this gate. Only DRC and parity were re-run.
- Footprint and pin-1 conventions (Gate 2) and the BF/INAV CLI behaviour beyond the text checks above.
- Physical assembly: no board was built.

Scripts and outputs: `/opt/kroot/tmp/g56r/` (`dump.py`, `net.py`, `silk.py`, `holes.py`, `fields.py`, `w.py`, `drc.json`, `re/`,
`ibom/`, `repo/`).
