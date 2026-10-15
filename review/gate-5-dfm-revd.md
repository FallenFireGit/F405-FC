# Gate 5 (rev D): DFM and hand-assembly review (fresh, independent reviewer)

Board: rev D (6 layers), `master` HEAD `0524b43`.
Scope:
- `kicad/F405FC.kicad_pcb` and `kicad/F405FC.kicad_dru`
- `fab/`, `bom/` and `docs/` (guide, PDF, STEP, renders)
- `design/decisions.md` (D-26, D-27) and `design/circuit.py`
- the previous reports `review/gate-5-dfm.md` (rev B) and `rev-c:review/gate-5-dfm-revc.md`

Review date: 2026-10-15. This report is the only file written in the repo. All scripts, exports and copies are under `/opt/kroot/tmp/g5d/` (chroot `/tmp/g5d/`). KiCad ran on a copy of `kicad/`, and no script calls Save.

## Verdict: **FAIL** (0 BLOCKER, 2 MAJOR, 12 MINOR, 9 INFO)

The fab data is good:
- The Gerbers, drill, job file, stencil and CPL are a 1:1 export of the current 6-layer board (re-exported and diffed).
- Layer naming and order are right for JLC.
- Track/space, annular ring, hole-to-copper and edge clearance all pass with margin.
- Mask webs are ≥ 0.15 mm.
- The J1 shell slots have real thermal reliefs on all six layers.
- The iBOM now omits the DNP R32/R37.

It fails on two counts:

1. **G5D-01 (MAJOR): the DigiKey BOM Manager upload file still orders the old inductor with no DigiKey PN.** The board, `circuit.py`, the iBOM and the costed BOM moved L1/L2 to 78438356056 / 732-11317-1-ND. `bom/F405FC_digikey_bom.csv` and `bom/bom_raw.csv` did not.
2. **G5D-02 (MAJOR): the assembly guide defers parts that the earlier stages need.**
   - The BOOT1 strap R17 is fitted in Stage C, but DFU runs in Stage B.
   - The USB-C CC pull-downs R34/R35 (and C51/R36 on VBUS) are also deferred to Stage C.
   - Step 2.1.10 plugs into the USB-C connector during Stage A, before J1 is fitted.

Both are document/BOM fixes; no re-route is needed.

## How the checks were done

| Check | Tool / evidence |
|---|---|
| DRC + parity | `kicad-cli pcb drc --severity-all --schematic-parity` on a copy → `/tmp/g5d/drc.json`. Result:<br>• 0 errors, 0 unconnected, 0 parity<br>• warnings: 16 `via_dangling`, 1 `silk_overlap` (C44/U8), and 32 `lib_footprint_issues` ("library 'F405FC' is not enabled"; there is no `fp-lib-table` in `kicad/`, an environment warning, not DFM)<br>The same DRC with `F405FC.kicad_dru` removed (`/tmp/g5d/drc_nodru.json`) adds exactly one error: `starved_thermal` on J1 SH at board (129.22, 118.82), B.Cu, "min spoke count 2; actual 1" |
| Outputs = board | I re-exported the Gerbers, drill, maps, job, stencil and pos with the exact `gen/outputs.sh` options into `/tmp/g5d/regen`:<br>• all 18 `fab/gerbers` files, the 4 stencil files and `F405FC_pos_kicad.csv` are identical apart from the date lines<br>• both zips unzip byte-identical (`cmp`) to `fab/gerbers` (18 files) and `fab/stencil` (4 files) |
| Geometry | Read-only pcbnew scripts in `/opt/kroot/tmp/g5d/s/`:<br>• `dump.py`: board JSON<br>• `geo.py`: via-to-pad distances, hole-to-hole, mask webs, by binary search on `SHAPE::Collide`<br>• `holecu.py`: hole to foreign copper per layer<br>• `npth.py`<br>• `spokes.py`: J1 shell spoke count per layer, sampled 0.12/0.20 mm outside the slot pad<br>• `j1near.py`, `near.py`: hand-tool spacing<br>• `therm.py`: GND pour around SMD GND pads<br>• `paste.py`<br>• `pol.py`: polarity marks<br>• `silk.py`: labels against holes and courtyards |
| BOM / CPL / iBOM | Python cross-check of the board fields, `fab/F405FC_cpl_jlc.csv` and the three `bom/*.csv` files. I decoded the iBOM's LZString payload with my own decoder (`/opt/kroot/tmp/g5d/h/lzd.py`) |
| Guide | Each ref, side, net and step in `docs/assembly_and_bringup.md` was checked against the board JSON (`/tmp/g5d/board.json`). The Stage A energisation was traced through the fitted R/L parts |
| Renders | I looked at `docs/renders/board_top.png` and `board_bottom.png` |

Coordinates are in the Gerber/CPL frame (aux origin 100,136, Y up, mm) unless marked "board".

## Fab-output checks that PASS

| Check | Result / evidence |
|---|---|
| Layer set and naming | F/B Cu, `In1_GND.g1`, `In2_SIG.g2`, `In3_PWR.g3`, `In4_GND.g4`, F/B Mask/Paste/Silk, `Edge_Cuts.gm1`, PTH/NPTH `.drl`, maps and job.<br>Job `LayerNumber 6`, `BoardThickness 1.6`, `FilesAttributes` L1 Top, L2-L5 Inr in G1..G4 order, L6 Bot. The `.g1`..`.g4` extensions match JLC's inner-layer order. No stale `In2_PWR` file remains in `fab/` or the zip |
| Outline | Closed: 4 lines + 4 R2 arcs, 0..36 x 0..36 (`F405FC-Edge_Cuts.gm1`). J1 body reaches x = 36.05 (flush USB-C mouth); no other part's fab body passes the edge |
| Drill | PTH:<br>• T1 0.30 (vias) and T2 0.30 (16 U1/U2 EP thermal holes)<br>• T3 0.60 G85 slots `X28.67Y17.18G85X29.77Y17.18`, `X33.0Y17.18G85X33.8Y17.18` and the mirror pair at Y25.82 (1.7/1.4 x 0.6)<br>287 PTH hits.<br>NPTH: 0.65 x 2 (J1 pegs at 29.72/18.61 and 29.72/24.39) and 3.20 x 4 at 2.75/33.25. These match the board's 267 vias and pads |
| Track/space, vias | Minimum track 0.127 mm (1280 segments). All 267 vias are 0.6/0.3, through, so the annular ring is 0.15. Aspect ratio 5.3:1 |
| Hole to foreign copper | Via holes: minimum **0.279 mm** on every one of the 6 layers. No via has unused inner pads removed (0 of 1068 inner via pads), so the inner-layer clearance is set by the 0.6 pad (`holecu.py`). For the J1 NPTH pegs see G5D-11 |
| Hole to hole | Same net minimum 0.374 mm (BEEPER vias at 19.25, 14.85).<br>Different net: minimum 0.414 mm (USB_CC1 via to the J1 NPTH peg), then 0.431 mm via-to-via (GND/CAM_SEL at 9.11, 22.73). 78 different-net pairs are < 0.5 mm, all ≥ 0.41 |
| Copper to edge | DRC rule 0.30, 0 violations |
| Mask webs (expansion 0, every pad margin 0) | Pairwise mask-opening gap: **minimum 0.150 mm** (U9 LGA-12 and U6 LGA-14 rows). LQFP gaps are 0.20. The only merged openings are the deliberate same-net J1 A1/B12, A12/B1, A4/B9 and A9/B4. `solder_mask_bridge` = 0 |
| Via tenting | All vias are tented, so the mask Gerbers carry no 0.6 via apertures. POFV is "required" in guide §0.1 |
| Paste | Every pad has paste margin 0 (1:1). Exceptions by design:<br>• U1/U2 EP: 3 paste-only windows<br>• U10 EP: 4 windows<br>• TP1-5: no paste<br>Area ratios at 0.10 mm: U6 1.12, U7 0.82, U8 0.65, U9 0.91, U3 1.26 (`paste.py`) |
| CPL | 119 rows. 0 position or side mismatches against the board (after the aux-origin transform). The set equals the placeable footprints minus DNP R32/R37 and minus H/P/TP |
| BOM arithmetic | `digikey_bom_costed.csv` now parses cleanly: all rows have 16 fields (rev C m-N2 fixed). Unit x qty = extended on all 53 lines; the sum is $173.28; qty per board is 119 |
| BOM refs | `F405FC_digikey_bom.csv` refs equal the board's BOM footprints (no duplicates, missing or extra). Every MPN and DigiKey PN equals the board fields, **except L1/L2** (G5D-01) |
| iBOM | Decoded: 119 refs, no R32/R37. `outputs.sh` blacklists `H*,P*,TP*,R32,R37`. L1/L2 show 78438356056 / 732-11317-1-ND |
| Polarity marks | `pol.py`:<br>• D1, D4, D5, D9 and D10-D12 have their closed silk end at pad 1, and pad 1 is the cathode net (D1 K = VBAT, D4/D5 K = 5V_SYS, D9 K = 5V, D10 K = GND, D11/D12 K to the MCU sink)<br>• every IC and transistor has a pin-1 polygon 0.55-0.99 mm from pad 1 |
| Hand-tool access | Nearest foreign pad (`near.py`):<br>• U3 0.555 (C32), U6 0.568 (C40), U7 0.653, U8 0.643, U9 0.593, U10 0.589 (R13), Y1 0.59<br>• J1 0.861, J2 0.806, J3 0.863, J4 0.916, J5 0.984<br>Workable with a fine tip and Kapton |
| Stage A isolation | With all bottom parts fitted except D5/U4/U5, plus D1/C1/R41, the only nets reachable from VBAT/5V/10V through fitted R/L are VTX_PWR, FB/SW/EN of both bucks. No logic-IC pin is reachable, so the guide's Stage A claim holds |

## Status of earlier findings

### Rev B (`review/gate-5-dfm.md`)

| ID | Rev D status | Evidence |
|---|---|---|
| M-1 J1 shell solid to the planes | **FIXED** | `spokes.py`, spokes counted 0.12 and 0.20 mm outside each slot pad, each ≈ 0.30 mm wide:<br>• slot (29.22, 17.18): F 4, In1 4, In2 3, In3 4, In4 4, **B 1**<br>• slot (33.40, 17.18): 3/4/4/4/4/4<br>• slot (29.22, 25.82): 3/4/4/4/4/3<br>• slot (33.40, 25.82): 2/4/4/4/4/3<br>The single B.Cu spoke is what the `.kicad_dru` rule accepts (INFO-2). The guide text on the layer count is wrong (G5D-04) |
| M-2 assembly order | **FIXED** (the side order). New ordering errors are inside the stages (G5D-02) | §2 A1 table: every listed part is bottom-side |
| M-3 vias at fine-pitch pads | **MITIGATED** (POFV now "required") → MINOR G5D-03 | 51 unique same-net vias < 0.10 mm from an SMD pad (15 in-pad). Closest is **0.018 mm, U3 pin 48 (3V3) at (23.44, 22.71)** |
| M-4 BOM PNs | **CHANGED → MAJOR G5D-01** | Y1 is filled. L1/L2 changed in the board and costed BOM but not in the BOM Manager CSV |
| M-5 labels under connectors | **FIXED**, with residuals (G5D-07) | `silk.py`: no board text overlaps a connector courtyard by more than 1 % (J4 1 %) |
| m-1 small pads poured solid | **OPEN, worse** (G5D-05) | 6 layers now. 55 of 59 top-side GND SMD pads are ≥ 50 % embedded |
| m-2 vias in paste pads | **MITIGATED by POFV** | In-pad vias:<br>• C10.1, C12.1 (x2), C8.2, C15.2, C2.1 (annulus)<br>• D1 (6), J2 MP, P4, TP5 |
| m-3 silk overlaps | **MOSTLY FIXED** | 1 warning left: C44 bar vs the U8 pin-1 triangle (INFO-1) |
| m-4 refs/revision | **PARTLY** (G5D-10) | "F405-FC rev D" is on B.Silk. The schematic says rev C, and the PCB title block is empty |
| m-5 metal hardware | **FIXED (doc)** | Guide §0 calls for nylon hardware |
| m-6 stencil/finish | **FIXED (doc)** | 0.10 mm stencil and ENIG |
| m-7 fab notes | **FIXED (doc)**; the job file is still generic (INFO-4) | |
| m-8 dangling vias | **OPEN, 16** (INFO-1) | |
| m-9 spare ICs | **OPEN** (G5D-12) | |
| m-10 paste on DNP pads | **OPEN, low impact** (INFO-5) | `F405FC-F_Paste.gtp` lines 72-73 (R37) and 330-331 (R32) |
| i-1..i-8 | Unchanged | i-2 (drill maps in the zip) and i-3 (stencil zip in absolute coordinates) are still true |

### Rev C (`rev-c:review/gate-5-dfm-revc.md`)

| ID | Rev D status | Evidence |
|---|---|---|
| MAJOR-1 L1/L2 no DigiKey PN | **PARTLY FIXED → G5D-01** | Board/iBOM/costed/circuit.py: 78438356056, 732-11317-1-ND. `F405FC_digikey_bom.csv` line 27 still reads `"","74438356056"` |
| MAJOR-2 DNP in iBOM / guide | **FIXED** | The iBOM omits R32/R37. Guide §4: "Do not fit R32 or R37" |
| m-N1 POFV only preferred | **FIXED** (now "required"). The counts are stale (G5D-03) | |
| m-N2 costed CSV malformed | **FIXED** (16 fields per row). Residual nits in G5D-14 | |
| m-N3 J3 10 V mark only on the bottom | **OPEN** (documented in guide §5) → G5D-07 | |
| m-N4 R7 near the J1 slot | **PARTLY** (the guide names R7). R6 pad 1 (VBAT) is not named → G5D-04 | |
| m-N5 top-side paste method | **CHANGED** (syringe or pre-tin is now written) → G5D-06 | |
| m-N6 labels under hardware | **OPEN, worse** → G5D-08 | |
| m-N7 ambiguous labels | **OPEN** → G5D-08 | |
| m-N8 guide nits | **OPEN** (the numbering is still broken; "silk dot") → G5D-13 | |
| i-N1..i-N7 | i-N1/N2/N4/N5/N6/N7 unchanged. i-N3: U6/U7 under U3, U10 under U9 (INFO-6) | |

## MAJOR findings

### G5D-01 MAJOR: the DigiKey upload BOM still lists the old inductor 74438356056 with an empty DigiKey PN, while the board uses 78438356056

Evidence:
- `bom/F405FC_digikey_bom.csv:27` reads `"","74438356056","Wurth Elektronik","5","L1 L2",…`.
- `bom/bom_raw.csv:24` reads `74438356056 … "not confirmed; alt 78438356056 = 732-11317-1-ND"`.
- The board fields for L1 and L2 are MPN `78438356056` and DigiKey `732-11317-1-ND` (`board.json`). `design/circuit.py:218-219` agree, and so does the decoded iBOM.
- `bom/digikey_bom_costed.csv` row 26 has 732-11317-1-ND / 78438356056. My script's cross-check reports `MPN mismatch L1 78438356056 74438356056` and `DK mismatch L1 732-11317-1-ND | ''` (the same for L2).
- Commit `2834883` ("port the rev C Gate 5 fixes (L1/L2 WE-MAIA PN …)") touched only `digikey_bom_costed.csv` and `circuit.py`; the BOM Manager file was not regenerated.
- `design/decisions.md:260` (D-26) still says "L1/L2 (Würth 74438356056): no DigiKey PN found … Still open".
- Costed row 26 itself says: "land pattern vs the WE-MAPI 4020 footprint NOT verified … check before ordering". The board still uses `L_Wuerth_MAPI-4020`.
- `review/gate-2-recheck.md:109` asked for that land-pattern check and for a record in decisions.md before the switch. Neither exists.

Why it matters:
- The brief's sourcing rule is "Every part comes from DigiKey only".
- The file meant for DigiKey BOM Manager orders the part that has no DigiKey PN (or nothing), not the part the board and the costing assume.
- These are the buck inductors on both rails, on the hot-plate side.

Fix:
1. Regenerate `F405FC_digikey_bom.csv` and `bom_raw.csv` from the current `circuit.py`. L1/L2 become `732-11317-1-ND`, `78438356056`, "WE-MAIA".
2. Confirm from the Würth WE-MAIA 4020 drawing that its recommended land pattern and 2.1 mm max height match `L_Wuerth_MAPI-4020`, or change the footprint.
3. Add a D-28 entry (or amend D-26) recording the switch, and update `design/power.md` §2.2/§3.1 and table line 496, which still name 74438356056.

### G5D-02 MAJOR: the guide's stage lists defer parts that the Stage A and Stage B tests depend on

Evidence (the board nets come from `board.json`; the parts not named in §2-§3 fall to §4's "the remaining top passives"):

1. **R17 (10k, BEEPER = U3 pin 28 = PB2/BOOT1, to GND)** is a top part (F, 19.25, 7.46). It is not in the Stage B list (guide l.114-116), so it goes on in Stage C.
   - Stage B step 3 runs ROM DFU by holding BOOT (BOOT0 = 1).
   - The STM32F405 boots system memory only with BOOT1 = 0. With BOOT0 = 1 and BOOT1 = 1 it boots SRAM.
   - The pin map makes R17 the BOOT1 strap: `design/pinmap.md:57` says "BOOT1 needs a 10k pulldown for ROM DFU", and `:280` "PB2/BOOT1 (28): 10k pulldown to GND (ROM DFU strap)".
   - Without R17, PB2 floats at reset, and DFU enumeration is not guaranteed. A failing first DFU on a freshly drag-soldered LQFP invites needless rework.
2. **R34/R35 (5.1k, USB_CC1/USB_CC2 to GND)**, **C51 (1 uF, VBUS)** and **R36 (100k, VBUS)** are all top parts, also fitted only in Stage C.
   - In Stage B, step 3 (DFU over USB) uses USB power only.
   - A USB-C (C-to-C) host supplies no VBUS without the Rd pull-downs. With a C-to-C cable the board stays unpowered and DFU "fails".
3. **Step 2.1.10** ("USB only … plug USB-C … 5V_SYS ≈ 4.6-4.7 V (via D4), 3V3 present") sits in §2, Stage A. J1 (USB-C) and U13 are fitted only in Stage B (guide l.114-115), so the test cannot be done where it is written.
4. Minor in the same area: step 8 is the A2 fit, but §2 l.62 calls it "A2 (step 2.1.9)", and there is no step 9 (the numbers run 8 → 10).

Fix:
- Add R17, R34, R35, R36 and C51 to the Stage B fit list. Also add R19 (GYRO2_CS pull-up), so both IMU CS lines are defined from the first MCU power-up.
- Move step 2.1.10 into Stage B, after J1/U13 are fitted.
- Renumber §2.1 and correct the "step 2.1.9" reference.
- Optionally add to Stage B: "if DFU does not enumerate, check R17 (BOOT1) and use a USB-A-to-C cable".

## MINOR findings

### G5D-03: vias at fine-pitch pads; POFV is now required, but the guide's figures are stale and its availability is unverified
- `geo.py`: 51 unique same-net vias lie < 0.10 mm from an SMD pad (61 via/pad pairs), and 15 of them are in-pad.
- Fine-pitch cases:
  - U3 pins 48 **0.018**, 59/39/49 0.038, 37 0.040 (LQFP 0.3 mm pads)
  - U7.6 0.020 (BMI270, 0.25 mm pads)
  - U6.14 0.038
  - U10 pins 6/3/4 at 0.028/0.031/0.056
  - U13.4, U11.6 and J2.4/J3.4/J4.6 at about 0.038
- 0402/0603 pads at 0.020-0.043: C27, C20 (both pads), C39, C47, C50, R5, R7, R17, R20, R29, U5.2.
- Guide §0.1 l.26 still says "rev C: 48, closest 0.024 mm".
- With POFV these are harmless, and different-net via-to-pad is ≥ 0.1278 mm. Without POFV the rev B/C M-3 risk returns: the via ring is exposed by mask registration and solder wicks into open holes in the C8/C10/C12/D1 pads.
- Fix: update the figures to "rev D: 51, closest 0.018 mm (U3.48)". Add to §0.1: "if POFV is not offered for this stackup, do not order; move the vias listed in review/gate-5-dfm-revd.md G5D-03 first".

### G5D-04: J1 shell guide text is wrong on the layer count and misses a VBAT pad next to a slot
- §3 l.118 says the slots "sit in five GND copper layers (F, In1, In3 pour, In4, B)". They connect on **six**: In2.SIG also has a GND pour with 3-4 spokes per slot (`spokes.py`).
- `j1near.py`, bottom-side pads near slot (29.22, 17.18):
  - R7.1 EN_10V 0.352 mm (B.Cu)
  - R6.2 EN_10V 0.491
  - R7.2 GND 0.586
  - **R6.1 VBAT 0.737**
- The guide warns only about R7. A shell-slot fillet bridged to R6.1 shorts the battery to GND, because the shell is GND.
- Fix: correct the text to "six layers". Add "check R6 pad 1 (VBAT) and R6/R7 (EN_10V) next to the lower-left slot exit; measure VBAT-GND before the next power-up". On a respin, move R6/R7 ≥ 1 mm from the slot.

### G5D-05: top-side GND pads poured solid (rev B m-1), now on a 6-layer board with two solid planes
- `therm.py`: **55 of 59** top-side GND SMD pads have ≥ 50 % of their perimeter (sampled 0.08 mm outside the pad) in solid F.Cu GND pour.
  - 100 %: C45.2, C51.2, R17.2, **U8.3, U8.8** (BMP390 LGA), C29.2, C53.2, R35.2, U13.2, C37.2, R15.2
  - 90 %: J2.2, C25.2
- All zones have `connect_pads` FULL (`pc=2`). In1/In4 are solid planes (1056 mm² each), and GND vias tie these pads into four GND layers.
- The top side is fitted by iron or local hot air with no preheat stated, except for J1. On U8 the two fully poured GND pads lag the signal pads, which invites tilt or opens on a 2 x 2 mm LGA. 0402s tombstone.
- Bottom: 58 of 60 GND SMD pads, but they go through the hot-plate pass, which is less affected.
- Fix (doc): add bottom-side preheat (hot air ≈ 150 °C from below, or a preheater) for every top-side hot-air step in Stages B/C.
- Fix (layout, optional): a DRC rule giving thermal connections (0.2 mm gap, 2 spokes) to SMD pads of footprints ≤ 0603 and to U8/U9.

### G5D-06: top-side paste method for U8/U9/Y1 is weak, and its rationale is wrong
- §4 l.138: "the stencil cannot lie flat any more. Dispense paste from a syringe … on U8, U9 and Y1, or tin their pads".
- The stencil lies on the bare top surface. What the bottom parts prevent is resting the board on a flat bed, and a support fixture (foam, or a 3D-printed carrier around the bottom parts) solves that.
- Syringe-dispensing 10 dots on 0.25 x 0.275 mm pads at 0.5 mm pitch (U8) is the least repeatable method on the board. `F405FC-F_Paste.gtp` already holds the apertures (area ratio 0.65 at 0.10 mm).
- §0 also justifies the 0.10 mm stencil with "the BMP390's 0.25 x 0.275 mm apertures", which the guide then does not print.
- Fix: print the top paste for U8/U9/Y1 with the 0.10 mm stencil, or a cut-down section of it, on a support carrier. Keep syringe or pre-tin only as the fallback.

### G5D-07: silk labels lost or misplaced in rev D
- Rev C board text included "C2" and "J5 RX" (`git show rev-c:kicad/F405FC.kicad_pcb`). Rev D has neither (34 texts against 36).
  - **P6 (CAM2_VID, bottom, 1.6/20.7) is unlabeled.** The video pad column reads "5V, G, C1, —, VID" (`board_bottom.png` right edge).
  - J5 (ELRS receiver) has no label.
- "J3 VTX 10V" is still on **B.Silk** (18.0, 33.15) while J3 is a top part, and the top has "GPS 5V" next to the identical J4 (rev C m-N3).
- "P10 LED" is likewise bottom-only, while P10 is a top pad (26.0, 7.7) and is unlabeled in `board_top.png`.
- The pad labels "R5", "R6" and "C1" are also refdes names of real parts (R5 24.3k, R6 301k, C1 10 µF). That is confusing during iBOM-driven assembly.
- Fix:
  - restore "C2" beside P6 and an "RX" mark beside J5;
  - add at least a "10V" or "!" mark on the top beside J3, and "LED" beside P10;
  - use "CAM1/CAM2" or "V1/V2" instead of "C1/C2", and "TX5/RX5" instead of "T5/R5".

### G5D-08: labels under the mounting hardware, and ambiguous labels (rev C m-N6/m-N7, worse)
- `silk.py`, distance from the text bounding box to the hole centre:
  - "BZ-" **1.46 mm** from H3
  - "CLK" (B.Silk, the SWCLK test pad) **1.81 mm** from H2
  - "GPS 5V" **1.94 mm** from H1 (rev C: 2.16)
  - "RSSI" 2.93 mm from H4
- An M3 nut, standoff or grommet covers ≥ 2.75 mm radius, and "GPS 5V" is the label D-15 relies on.
- "BOOT" at (20.59, 25.67) overlaps the U3 courtyard by 11 % and sits about 6 mm from SW1 (26.5, 29.6).
- Fix: move these labels ≥ 3.0 mm from the hole centres, and put "BOOT" against SW1.

### G5D-09: all footprint silk lines are 0.12 mm, including every polarity and pin-1 mark
- 371 footprint silk shapes, all 0.12 mm wide (script count). Board text is 0.8 mm high with a 0.15 mm stroke.
- The commonly quoted JLC silk minimums are about 0.15 mm line and about 1.0 mm text height (not verified).
- The diode cathode bars and IC pin-1 triangles are what the guide asks the assembler to check (§2 l.66).
- Fix: set the footprint silk to ≥ 0.15 mm, at least for the polarity and pin-1 shapes, or confirm the minimums on the JLC page.

### G5D-10: revision and spec traceability
- All six schematic sheets carry `(rev "C")` (`kicad/F405FC.kicad_sch:9` and the sub-sheets), and so does the PDF title block.
- The PCB has no title block revision, so the job file shows `"Revision": "rev?"` and the iBOM `revision: ''`. Only the silk says "rev D".
- `design/requirements.md:9` still specifies "4-layer, 1.6 mm, JLCPCB JLC04161H-7628". The brief's non-negotiable list says "4 layers". The board is 6 layers (D-27), and decisions.md records no user sign-off.
- Fix:
  - set rev D in the schematic and PCB title blocks and regenerate the PDF/job/iBOM;
  - update `requirements.md` to the D-27 stackup;
  - record that the user accepted the 4 → 6 layer change (cost and lead time at JLC).

### G5D-11: J1 NPTH peg holes have GND pour 0.191 mm from the hole edge on all six layers
- `npth.py`: both 0.65 mm pegs (29.72, 18.61 / 24.39) see the GND zone at 0.191 mm on F, In1-In4 and B.
- That is the board `hole_clearance` 0.19.
- Fabs usually want ≥ 0.2-0.25 mm from an NPTH to copper, especially on inner layers (JLC figure not verified).
- Impact is low: the copper is GND and the pegs are plastic. The fab may still flag it or pull back the copper.
- Fix: a rule `(constraint hole_clearance (min 0.25))` for NPTH, then refill.

### G5D-12: no spare ICs (rev B m-9, still open)
- `F405FC_digikey_bom.csv` orders exactly 2 each of U6, U7, U8, U9 and U10.
- These are the LGA/WSON parts that are hardest to hand-solder, and U6/U7/U10 cannot be reworked once U3/U9 are on.
- Fix: add 1 spare each (about +$32 at the costed prices).

### G5D-13: guide nits
- §2 l.66 says "Check pin 1 orientation against the silk dot" for U1/U2; the marker is a triangle (`pol.py`).
- §3 l.115 lists C53 as "top MCU decoupling". It is the RSSI filter cap (D-22). Harmless.
- §2 l.57: D1 (SMB) and C1 (1210) are fitted "by iron or hot air" with the bottom populated. Courtyard overlap through the board: D1 over L1 (1.76 mm²) and C1 over U1 (4.82 mm²).
  - Hot air there re-melts the hanging L1 and U1 EP joints.
  - Specify the iron for D1/C1.

### G5D-14: BOM housekeeping
- The board DigiKey fields, `bom_raw.csv` and the iBOM still carry "(verify)" suffixes:
  - C2/C3/C10/C11 "445-6042-1-ND (verify: K200AB cut tape)"
  - C19/C22/C31/C51, C4/C12/C17, U1/U2 and Y1
- `digikey_bom_costed.csv`:
  - the TOTAL row puts a stray "167.56" in the evidence column next to 173.28;
  - row 26 cites "rev C Gate 5 M-1" (it was MAJOR-1 / M-4);
  - rows 31, 36 and 52 say "left blank" while the PN is filled.
- Fix: clean the fields and regenerate. The tracked status belongs in the costed CSV only.

## INFO

1. **DRC warnings.**
   - The 16 `via_dangling` vias (listed in `/tmp/g5d/drc.json`, e.g. UART5_RX (18.0, 22.15), SPI1_SCK (15.25, 14.85)) are tented, or filled under POFV, and pass the hole and annulus rules. They have no fab or assembly impact; the stub SI is Gate 4's call.
   - The one `silk_overlap` is C44's bar touching the U8 pin-1 triangle at (16.09, 28.59). The triangle sits over pad 1 (16.25, 27.86) and stays readable in `board_top.png`. Cosmetic.
2. **`kicad/F405FC.kicad_dru`.**
   - The rule `min_resolved_spokes 1` for J1 plated pads suppresses exactly one DRC error: the slot at (29.22, 17.18), B.Cu, 1 spoke.
   - The same barrel has 3-4 spokes on each of the other five layers, so the electrical and mechanical joint is unaffected. Fewer spokes also make the joint easier to solder.
   - Acceptable. The condition is broad (any plated J1 pad), but only the four SH slots are plated.
3. **STEP and renders lack bodies for U1, U2, U4, U7, U8 and U10.**
   - U1/U2/U7/U8 have no model entry.
   - The U4 `SOT-223-5.step` and U10 `WSON-8-1EP_8x6mm…step` files do not exist in the library.
   - The STEP is therefore not complete for a stack-height check (L1/L2 at 2.1 mm are present).
4. **Job file.** It uses KiCad's generic 5 x 0.274 mm FR4 / 35 µm stackup and `Finish: None`, and JLC ignores it. Guide §0.1 leaves the JLC 6-layer stackup name unverified.
5. **Packaging.**
   - Drill maps are still in the JLC zip.
   - The stencil zip is in absolute coordinates (Edge `X100000000Y-102000000`) while the PCB zip uses the aux origin, yet both declare `TF.SameCoordinates,Original`.
   - The J1 SH slots carry F.Paste apertures (`O,2.1x1.0`/`O,1.8x1.0`, `F_Paste.gtp` D20/D21).
   - DNP R32/R37 carry paste.
   - None of this matters for hand assembly. Strip it if the stencil is ever used on the top.
6. **Through-board overlaps** (courtyard intersection):
   - U6/U7 under U3, U10 under U9 (by design; A1 covers this)
   - J1 over R6, R7, U4, C19 and P17-P20
   - J2 over L1, L2, C6, C7, C14 and C16
   - J3 over U5/C18/C23/D11
   - Y1 over C24/C30/C35

   The guide's order covers these, apart from G5D-13 (D1/C1).
7. **CPL.** Rotations are KiCad's raw values; JLC per-package and bottom-side corrections were not checked. The CPL is informational for hand assembly.
8. **The JLC order-number placement** is not addressed in §0.1 (rev C i-N7).
9. **Mask webs.** The minimum is 0.150 mm (U6/U9). That passes a 0.1 mm dam. If the fab applies its own mask expansion of more than 0.025 mm per side, the LGA dams go away.

## Not verified

- **JLCPCB capability and options.** None of these were checked against the live site:
  - 6-layer POFV availability and price;
  - the 6-layer stackup names and thicknesses;
  - the minimum mask dam;
  - NPTH-to-copper and different-net hole-to-hole minimums;
  - silk line and text minimums;
  - the order-number options.
  All figures quoted are from memory and labelled as such.
- **DigiKey listings, stock and prices**, including 732-11317-1-ND, 445-6042-1-ND and every "(verify)" PN. The PNs were checked only for consistency with the board. The $173.28 total was checked only arithmetically.
- **The WE-MAIA 78438356056 land pattern and height** against `L_Wuerth_MAPI-4020`. No Würth drawing is in `datasheets/`.
- **Footprints against vendor land patterns and vendor pin-1 conventions** (Gate 2). Polarity was checked only as silk mark vs pad 1 vs net.
- **CPL rotations against JLC's convention.**
- **No Gerber viewer render.** Correctness rests on the re-export diff plus pcbnew geometry. Silk checks use text bounding boxes, not glyph outlines.
- **Physical solderability** (J1 shell, solid-poured pads, top-side LGA). There was no assembly trial.
- **SI/PI effects** of the dangling vias and the 6-layer stackup (Gate 4).
- **Whether the STM32F405 actually mis-boots** with PB2 floating. The finding rests on the BOOT0/BOOT1 strap logic and the project's own pin map, not on a bench test.
