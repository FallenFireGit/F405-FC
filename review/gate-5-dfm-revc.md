# Gate 5 (rev C): DFM and hand-assembly re-review (fresh, independent reviewer)

Board: rev C release candidate, worktree `/home/user/F405-FC-revc`, branch `rev-c`, HEAD `6080bc0`.
Scope: `kicad/F405FC.kicad_pcb`, `fab/`, `bom/`, `docs/assembly_and_bringup.md`, `design/decisions.md` (D-22, D-26, D-27), and the previous review `review/gate-5-dfm.md`.
Review date: 2026-10-15. This report is the only file written in the worktree. All scripts and exports went to `/opt/kroot/tmp/g5c/` (chroot `/tmp/g5c/`), running on a copy of `kicad/`.

## Verdict: **FAIL** (0 BLOCKER, 2 MAJOR, 12 MINOR, 7 INFO)

Fab data:
- The Gerbers, drill files and CPL are complete, and they are a 1:1 export of the current board (re-exported and diffed; see below).
- The previous MAJORs M-1 (J1 thermals), M-2 (assembly order) and M-5 (hidden labels) are fixed.
- M-3 (vias at fine-pitch pads) is only partly fixed. It is now mitigated by an optional fab setting, so it is downgraded to MINOR.

It still fails on two counts:
1. **M-4 is still open.** L1/L2 (Würth 74438356056) have no DigiKey PN. The brief says "Every part comes from DigiKey only".
2. **New: the DNP parts R32/R37 appear as normal parts in the iBOM, and the guide says to fit "the remaining top passives".** Fitting R32 ties the MCU's LED_STRIP output directly to the 5 V output of the U12 buffer.

Both are one-line fixes: a BOM/part decision and a guide/iBOM change. No re-route is needed.

## How the checks were done

| Check | Tool / evidence |
|---|---|
| DRC + parity | `kicad-cli pcb drc --severity-all --schematic-parity` on a copy, output in `/tmp/g5c/drc.json`. Result: **0 errors**, 0 unconnected, 0 parity. Warnings: 17 `via_dangling`, 3 `silk_overlap`, 1 `track_dangling` (was 17 + 26). Project severities: `solder_mask_bridge` and `courtyards_overlap` are errors with 0 hits; `silk_over_copper` is a warning with 0 hits; `missing_courtyard` is ignored, but every footprint has a courtyard (script) |
| Outputs = board | Re-exported Gerbers, drill and pos with the exact `gen/outputs.sh` options into `/tmp/g5c/regen`. Every Gerber, drill, map, job and pos file is identical to `fab/` apart from the date lines. The stencil files differ only in their date lines. Both zips are byte-identical (`cmp`) to `fab/gerbers` and `fab/stencil` |
| Geometry | Read-only pcbnew scripts `therm.py`, `viapad.py`, `cy.py`, `silk.py`, `silkhole.py`, `web.py`, `paste.py`, `near.py`, `h2h.py`, `j1r.py`, `pol.py`, `nets.py`. None calls Save |
| BOM / CPL | Python cross-check of the board footprints, `fab/F405FC_cpl_jlc.csv`, and the three `bom/*.csv` files |
| iBOM | Decoded the LZString payload of `bom/F405FC_ibom.html` with my own decoder (`/tmp/claude-0/g5c/lz.py`) |
| Renders | Inspected `docs/renders/board_top.png` and `board_bottom.png` |

Coordinates are in the Gerber/CPL frame: aux origin (100, 136), Y up, mm.

## Status of the previous findings (review/gate-5-dfm.md)

| ID | Status | Evidence |
|---|---|---|
| **M-1** J1 shell slots solid to 4 layers | **FIXED** | All four SH pads have local zone connection THERMAL, gap 0.25 mm, GND zone spokes 0.3 mm. Fill coverage 0.12 mm outside each slot is 0.10-0.22, in 2-4 separate spokes, on **every** layer: F 0.20/4, 0.16/3, 0.15/3, 0.22/4; In1 0.20/4, 0.22/4, 0.20/4, 0.22/4; In2 0.15/3, 0.22/4, 0.20/4, 0.22/4; B 0.10/2, 0.22/4, 0.15/3, 0.22/4. The copper is solid again at 0.4 mm. The guide adds the ≥ 60 W chisel tip and top preheat. D-22 is corrected. See the new m-N4 (R7 next to the slot) |
| **M-2** assembly order | **FIXED** | §2 A1 now reflows every bottom part except D5/U4/U5 in one hot-plate pass. Script check: every part in the A1 table is on the bottom; every part named for the top stages is on the top; the 22 unnamed top parts fall under "remaining top passives" in Stage C. U11, U10, D10 and Q2 are fed only from 3V3/3V3_IMU/GND or switched nets (`nets.py`), so the Stage A claim holds. TP1-5 are now called bare pads. Residual: see m-N5 (top-side paste method) and i-N3 (U9 hot air above U10) |
| **M-3** vias abutting fine-pitch pads | **PARTLY FIXED → MINOR (m-N1)** | 48 unique vias are still < 0.10 mm from a same-net SMD pad (D-26 says 46). All are same-net. Of the fine-pitch cases, 6 are unchanged: U10.6 0.024, U10.8 0.026, U10.9 0.041, U10.4 0.047, U7.13 0.037 at (20.69, 17.51) and U8.3 0.040 at (13.56, 27.76). U3 still has 6 pins at 0.037-0.068 (pins 6, 16, 36, 53, 61, 62). U6's vias moved clear. Vias inside courtyards: U6 4, U7 4, U8 3, unchanged (D-22 now says so). Mitigation: §0.1 "Epoxy filled and capped (POFV) preferred; else tented" |
| **M-4** BOM PNs | **OPEN (MAJOR-1)** | Y1 is filled (`50-ECS-80-8-33-JEN-TR3CT-ND`). L1/L2 `74438356056` still has an empty DigiKey PN in `F405FC_digikey_bom.csv`; D-26 says "Still open". |
| **M-5** labels under connector bodies | **FIXED (one residual, m-N3)** | `silk.py`: no board text box intersects any part's Fab body outline on the same side. Only courtyard edges and the 0.13 mm pad-fab edges of wire pads are touched; `silk_over_copper` = 0. "GPS 5V", "ESC", "J5 RX" and "USB" are visible in the renders. Residual: "J3 VTX 10V" is on the **bottom** silk only, while J3 is a top part (m-N3) |
| m-1 small passives poured solid | OPEN (accepted) | GND zones are still `connect_pads` FULL (zone conn = 2). Not addressed in D-26. Bottom parts are now hot-plated, which reduces the risk; top passives are still fitted by hot air or iron |
| m-2 vias in paste pads | OPEN, mitigated only by POFV | Unchanged list:<br>• C8.2 and C10.1: via centred in the pad<br>• C12.1: two VBAT vias whose holes reach 0.022/0.026 mm into the pad<br>• D1: 6 vias in its pads, through to P1/P2<br>• J2 MP and P4: via in pad<br>• C15.2: hole edge exactly at the pad edge (0.000)<br>• C2.1: annulus overlap |
| m-3 silk overlaps | MOSTLY FIXED | 26 → 3 warnings. The Pad_SMD rings are gone and T5/T6 read correctly in the renders. Still present:<br>• U8 pin-1 polygon crosses C44 silk at (14.89, 28.59), so the BMP390 pin-1 mark is still ambiguous<br>• "BOOT" crosses R16's silk<br>• "3V3" (bottom) crosses TP4's circle |
| m-4 no refs / no revision | PARTLY FIXED | "F405-FC rev C" is on the bottom silk. Refs are still Fab-only (expected at this density). The job file says `"Revision": "rev?"` and the iBOM metadata `revision: ''` |
| m-5 metal hardware near VBAT | FIXED (doc) | The guide §0 requires nylon hardware or grommets |
| m-6 stencil thickness / finish | FIXED (doc) | 0.10 mm stencil and ENIG in §0 / §0.1. Recomputed U8 aperture area ratio: 0.25 x 0.275 / (2 x 0.525 x 0.10) = 0.65 |
| m-7 fab notes | FIXED (doc), job file still generic | §0.1 table added. The job file still has KiCad's generic 3 x 0.48 mm FR4 stackup and `Finish: None` (JLC does not read it; i-N1) |
| m-8 dangling vias | OPEN | 17 `via_dangling`, plus 1 new `track_dangling`: a 0.586 mm VBAT_ADC stub on F.Cu at (7.49, 11.01) |
| m-9 no spare ICs | OPEN | `digikey_bom_costed.csv` order qty is still 2 for U6, U7, U8, U9 and U10 |
| m-10 paste on DNP pads | OPEN | R32 (26.52/27.54, 14.78) and R37 (19.97/20.99, 28.70) are still on F.Paste. Now more relevant because of MAJOR-2 |
| i-1 … i-8 | Unchanged | Drill maps are still in the PCB zip (i-2). The stencil zip is still in absolute coordinates (i-3) |

## Fab-output checks that PASS (current release)

| Check | Result / evidence |
|---|---|
| Gerber set | F/B Cu, In1 `.g1`, In2 `.g2`, F/B Mask, F/B Paste, F/B Silk, Edge `.gm1`, PTH/NPTH `.drl`, maps, job. The job maps L1..L4 as Top/Inr/Inr/Bot |
| Drill completeness | PTH: T1 0.30 x 263 (= 263 vias on the board), T2 0.30 x 16 (= U1/U2 EP thermal holes), T3 0.60 x 4 G85 slots (J1 SH: 1.1 and 0.8 mm strokes = 1.7/1.4 x 0.6 slots). NPTH: 0.65 x 2 (J1 pegs), 3.20 x 4 at (2.75 / 33.25). Matches the board (`holes.py`) |
| Origin | Gerbers and CPL on the aux origin; drill origin "plot" agrees (holes at 2.75/33.25). CPL: 119 rows, 0 position or side mismatches against the board |
| Via tenting | Every via is 0.6/0.3 with no per-via tenting override. Neither mask Gerber has a 0.6 mm aperture; the only round apertures are 0.65, 1.0 (TPs) and 3.2 |
| Mask webs | Pairwise mask-opening distance (expansion 0): no pair < 0.15 mm on either side, except the deliberate J1 A1/B12, A12/B1, A4/B9, A9/B4 merges (same net). `solder_mask_bridge` = 0 |
| Silk | `silk_over_copper` = 0, `silk_edge_clearance` = 0. All board text is 0.8 mm high with 0.15 mm stroke. Footprint silk lines are 0.12 mm (see i-N4) |
| Copper | Min track/space 0.127, via annular ring 0.15, edge clearance 0.30 (0 DRC errors) |
| Hole-to-hole | Same net: minimum 0.252 mm (GND pair at 25.14, 18.06). Different net: minimum 0.34 mm (J1 peg to its own SH slot, vendor footprint), then 0.366 mm (USB_CC1 via at (30.31, 24.99) to the J1 peg), then 0.432 mm via-to-via. 80 different-net pairs are < 0.5 mm (see Not verified) |
| Paste | U1/U2 EP: 3 paste-only windows, no paste on the thermal holes. U10 EP: 4 x 1.37 x 1.73 (65 %). LGA pads 1:1. Board paste margin 0 |
| Polarity marks vs nets | The closed silk end sits at pad 1 (cathode) on:<br>• D1 (K = VBAT)<br>• D4 (K = 5V_SYS, A = VBUS)<br>• D5 (K = 5V_SYS, A = 5V)<br>• D9 (K = 5V, A = BUZ_N)<br>• D10-D12 (K to GND or the MCU sink)<br>All ICs and transistors have a pin-1 polygon; Y1 has an L corner mark |
| Courtyards | 0 courtyard overlaps; every footprint has a courtyard |
| BOM ↔ board ↔ CPL | 121 placeable refs (excluding H/P/TP) = 121 refs in the DigiKey BOM. CPL = those 121 minus DNP R32/R37. MPNs in the board fields equal the BOM MPNs. `bom_raw.csv` values and footprints match the board, apart from J3/J4 sharing one group. The costed BOM sums to $173.28 (unit x qty checked on all 53 lines) with 119 placements |
| Hand-tool access | Nearest foreign pad copper: U3 0.56 (C32) / 0.70 (Y1); U6 0.57; U7 0.64; U8 0.64; U9 0.59; U10 0.59; Y1 0.59; U1/U2 0.61. Workable with a fine tip and Kapton |

## MAJOR findings

### MAJOR-1: L1/L2 still have no DigiKey part number (carried over from M-4)
Evidence:
- `bom/F405FC_digikey_bom.csv`: `"","74438356056","5","L1 L2"`.
- The board DigiKey field reads `not confirmed; alt 78438356056 = 732-11317-1-ND`, and the iBOM shows the same text.
- D-26: "no DigiKey PN found (DigiKey lists the MPN only as a related part) … Still open".
- My own web search found no DigiKey listing for 74438356056 either; it returned only the 78438356056 WE-MAIA alternate.
- The brief is non-negotiable: "Every part comes from DigiKey only … Never substitute a part that isn't sold at DigiKey."
- "Order by MPN in BOM Manager" fails if DigiKey does not stock the MPN, and these are the buck inductors on both rails.

Fix:
- Switch L1/L2 to the documented alternate, Würth 78438356056 (DigiKey 732-11317-1-ND, D-20; same 4020 size and ratings per D-20).
- Or confirm a real DigiKey PN for 74438356056 and record the evidence.
- Then update `circuit.py` fields, the board fields and both BOM CSVs, and re-check the Isat/height values used in `design/power.md`.

### MAJOR-2 (new): DNP R32/R37 appear as normal parts in the iBOM, and the guide's "remaining top passives" includes them
Evidence:
- The board marks R32 and R37 DNP (`IsDNP()`), and the CPL and the DigiKey BOM ("R32 R37 (DNP spares)", qty 0 per board) exclude them.
- The decoded iBOM, however, lists group `['R32','R37'] 0R RC0402JR-070RL 311-0.0JRCT-ND` like any fitted part, with no DNP flag. Its skip list covers only H*, P* and TP*.
- `docs/assembly_and_bringup.md` §4 says to fit "the remaining top passives". Both parts are on the top, and neither "R32", "R37" nor "DNP" appears anywhere in the guide (grep).
- Their pads also carry paste (m-10).
- R32 connects LED_STRIP (MCU timer output) to LED_DIN_BUF, the output of U12 (SN74LV1T125, VCC = 5 V, `nets.py`). If R32 is fitted:
  - the 5 V buffer output is tied straight to a 3.3 V MCU push-pull output, which gives contention and injection through the MCU pin;
  - the LED level shifter is bypassed.
- R37 ties HD_R2 (VTX side) to UART5_RX, which is only an option.

Fix:
- Regenerate the iBOM with DNP handling (iBOM `--dnp-field` / a DNP field on R32/R37, or add them to `--blacklist`).
- Add "R32 and R37 are not fitted (DNP); leave their pads empty" to §4 of the guide.
- Optionally drop R32/R37 from F.Paste (m-10).

## MINOR findings

- **m-N1: residual vias at fine-pitch pads; POFV is only "preferred" (remainder of M-3).**
  - Evidence: 48 vias are < 0.10 mm from same-net SMD pads; 20 of them overlap pad copper (in-pad).
  - Fine-pitch cases are U10 pins 6/8/9/4 at 0.024-0.047 mm, U7.13 0.037, U8.3 0.040 and U3 pins 6/16/36/53/61/62 at 0.037-0.068.
  - The guide's figure "About 26 … 0.03-0.09 mm" understates both the count and the minimum (0.024 at U10.6, (8.44, 31.99)).
  - With "tented" ordered, the C8/C10/C12/D1 vias are open holes inside paste pads, and the LGA/WSON slivers are 0.024-0.04 mm.
  - Fix: make POFV **mandatory** in §0.1 (delete "else tented"), or move the 6 U7/U8/U10 vias to ≥ 0.10 mm. Correct the count in §0.1.
- **m-N2: the costed BOM CSV is malformed.**
  - `bom/digikey_bom_costed.csv` rows 4, 26 and 52 have unquoted commas in the "Gate 2 status" column. They parse to 18/17/18 fields against a 16-field header, so any spreadsheet import shifts the price and extended columns. The TOTAL row has 17 fields.
  - Rows 31, 36 and 52 also say "left blank" in the evidence column while the PN column is filled.
  - The board DigiKey fields still carry "(verify)" suffixes. These show in the iBOM for C2/C3/C10/C11, C19/C22/C31/C51, C4/C12/C17, U1/U2 and Y1.
  - Fix: quote the fields and regenerate; clean up the field text.
- **m-N3: the J3 "VTX 10V" warning is only on the bottom silk.**
  - "J3 VTX 10V" is on B.Silkscreen at (18.0, 33.9). J3 is a top part at (18.0, 32.9), and the top silk has no 10 V mark near J3; see the `board_top.png` top edge.
  - J4's "GPS 5V" label is on the top, so the two identical SM06B connectors are labelled on opposite sides.
  - The guide §5 still says 'J3 (front, silk "VTX 10V")'.
  - "P10 LED" is likewise on the bottom, while P10 (LED_DIN) is a top pad at (26.0, 7.7) with no top label.
  - Fix: add a short top mark ("10V" or "!") beside J3 and "LED" beside P10, even at 0.8 mm, and correct the guide wording.
- **m-N4 (new): R7 (EN_10V) is 0.354 mm from a J1 shell slot ring on B.Cu.**
  - R7 is a bottom 0402 at (27.5, 17.53), fitted in Stage A. Its pad 1 is EN_10V; R6 pad 2 (EN_10V) is 0.54 mm away.
  - The guide says to fill each shell slot "until solder shows at the bottom" with a ≥ 60 W iron. A bottom fillet can bridge to R7 pad 1, shorting the 10 V buck enable to GND (the shell is GND), and the iron heat can reflow R6/R7.
  - Fix: add to §3 "inspect the J1 slot exits on the bottom next to R6/R7; re-check 10V after J1". Or move R7 by ≥ 0.3 mm on a respin.
- **m-N5 (new): no paste method for the top-side LGA and no-lead parts.**
  - U8 (LGA-10, 0.25 mm pads), U9 (LGA-12) and Y1 (3225 4-pad) are fitted by hot air after the bottom is populated.
  - The guide names no paste method for them. Printing the top stencil is not possible on a board with populated bottom parts unless it is supported.
  - Fix: specify it, e.g. print the top paste with the 0.10 mm stencil on a carrier that supports the board around the bottom parts, or pre-tin and flux the pads (with a stated method for U8).
- **m-N6: labels under the mounting hardware.**
  - "BZ-" is 1.81 mm from the H3 centre and "GPS 5V" 2.16 mm from H1 (`silkhole.py`). Both sit under any M3 nut, standoff or grommet (≥ 2.75 mm radius).
  - "GPS 5V" is the label D-15 relies on.
  - Fix: move both ≥ 3.0 mm from the hole centres.
- **m-N7: ambiguous labels.**
  - "BOOT" sits at (20.59, 25.67), right under R41 (0R, VTX feed) and about 6 mm from SW1 (26.5, 29.6).
  - "USB" sits at (24.44, 13.7), about 3.5 mm off J1.
  - Fix: place "BOOT" next to SW1 (or use an arrow).
- **m-N8: guide nits.**
  - §2.1 numbering jumps from step 7 to step 9.
  - §2 says "check pin 1 orientation against the silk dot" for U1/U2; the marker is a triangle.
- **m-1, m-8, m-9, m-10** are still open, as in the table above.
- **m-3 residual:** the U8 pin-1 polygon still crosses C44's silk.

## INFO

- **i-N1:** The job file still has a generic stackup, `"Revision": "rev?"` and `"Finish": "None"`. Harmless for JLC, which ignores the job file. Set the title block revision to "C".
- **i-N2:** Drill map files are still inside `F405FC_JLC_gerbers.zip` (old i-2).
- **i-N3:** U9 (top) sits directly above U10 (bottom WSON), and U8 above several bottom 0402s. Stage C hot air re-melts those hanging joints. They are light parts held by surface tension, so the risk is low, but use the smallest nozzle and a short dwell.
- **i-N4:** Footprint silk lines are 0.12 mm and board text is 0.8 mm / 0.15 mm stroke. That is at or below the commonly quoted JLC legibility minimum (about 0.15 mm line, 1.0 mm text; not verified). The renders look legible.
- **i-N5:** The U1/U2 EP thermal holes are open on the bottom EP and tented on top. Without POFV, outgassing during the hot-plate pass can blister the top tents. POFV removes this.
- **i-N6:** 15 tented vias lie under the J1 metal shell's courtyard and 17 under U10. That is normal practice with intact mask.
- **i-N7:** The JLC order-number mark is not addressed in §0.1. On a 36 mm board JLC may print it over the labels. Choose "remove mark" or add a placement marker.
- **3D models:** U4 and U7 render without bodies in `board_bottom.png`, and U8 in `board_top.png`.

## Not verified

- **JLCPCB capability values and options**, not checked against the live site:
  - whether "Epoxy filled & capped" via covering is available on 4-layer, and at what price;
  - the mask dam minimum;
  - the different-net hole-to-hole minimum (80 pairs < 0.5 mm, minimum 0.366 mm via to NPTH);
  - silk minimums;
  - the order-number mark options.
- **DigiKey listings, stock and prices.** One web search for 74438356056 found no DigiKey listing (inconclusive). The PNs in the BOM were checked only for consistency, and the $173.28 total only arithmetically.
- **Footprints against vendor land patterns, pin-1 conventions, part heights and 3D models** (Gate 2 territory). Polarity was checked only as silk mark vs pad 1 vs net.
- **CPL rotations against JLC's convention.** The CPL is informational for hand assembly.
- **No Gerber viewer render.** Correctness rests on the byte-level comparison with a fresh KiCad export of the current board plus pcbnew geometry. The silk checks use text bounding boxes, not glyph outlines.
- **Physical solderability**, including the thermal claims for J1 and the small passives. There was no assembly trial.
- **SI/PI effects** of the dangling vias and the VBAT_ADC stub (Gate 4).
- **The 'J3 VTX 10V' layout reasoning.** I did not check whether there is room for a top-side label near J3.
