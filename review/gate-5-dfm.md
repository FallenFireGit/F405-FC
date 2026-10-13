# Gate 5: DFM and hand-assembly review (fresh, independent reviewer)

Scope: fab outputs in `fab/`, BOM in `bom/`, board `kicad/F405FC.kicad_pcb` (read-only), `docs/assembly_and_bringup.md`, `design/decisions.md`.
Fab target from the brief: JLCPCB, 4 layers (JLC04161H-7628), 0.127/0.127 mm, 0.3/0.6 mm vias, hand assembly with hot plate, hot air and iron.
Review date: 2026-10-13. Nothing in design/, gen/, kicad/, lib/, bom/, fab/ or docs/ was modified.

## Verdict: **FAIL** (0 BLOCKER, 5 MAJOR, 10 MINOR)

The fab data is complete and self-consistent. The Gerber set, drill files, outline, origin, annular ring, hole size, edge clearance, via tenting and mask webs all check out, and the board can be ordered as is.
It fails on hand-assembly and procurement grounds:
- the USB-C shell slots connect solidly to four copper layers;
- the documented assembly order puts hot air on the bottom IMUs directly under an already-soldered LQFP;
- tented fanout vias abut LGA, WSON and LQFP pads with 0.02-0.05 mm mask slivers;
- two BOM lines have no DigiKey PN;
- the safety label "VTX 10V" is printed under the J3 connector body.

Most fixes are doc, BOM or rule edits. Only M-1 and M-3 need a refill or re-route.

## How the checks were done (tools and evidence)

- `kc 'python3 gen/drc_summary.py'` returned violations `{'via_dangling': 17, 'silk_overlap': 26}`, unconnected 0, parity 0. Project severities: `solder_mask_bridge` = error, `silk_over_copper` = warning, `courtyards_overlap` = error, `missing_courtyard` = **ignore**.
- I unzipped `fab/F405FC_JLC_gerbers.zip` into `/tmp/claude-0/g5` and `fab/F405FC_stencil.zip` into `/tmp/claude-0/g5s`. Every file in the zip is byte-identical (`cmp`) to `fab/gerbers/*` and `fab/stencil/*`. I parsed the Gerber and Excellon text by hand.
- I wrote read-only pcbnew scripts in `/opt/kroot/tmp/g5/` (`dump.py`, `geo.py`, `vip.py`, `therm.py`, `paste.py`, `viamask.py`, `imuvia.py`, `lbl.py`). None of them calls Save. They measured:
  - mask webs between pad openings;
  - hole-to-hole spacing;
  - vias touching SMD pads;
  - perimeter coverage of zone fill around passive pads;
  - paste layers per pad;
  - tented-via-to-mask-opening distances;
  - vias inside courtyards;
  - label positions against connector bodies.
- Coordinates below are in the Gerber/CPL frame: origin at the lower-left board corner (aux origin 100,136), Y up, mm.

## Fab-output checks that PASS (evidence)

| Check | Result | Evidence |
|---|---|---|
| Gerber set | F/B Cu, In1 (`.g1`), In2 (`.g2`), F/B Mask, F/B Paste, F/B Silk, Edge (`.gm1`), PTH and NPTH `.drl`, job file | zip listing. Job `FilesAttributes` map L1..L4 as Top/Inr/Inr/Bot. In1=L2 (GND) and In2=L3 (PWR) match the brief's JLC04161H order |
| Naming | KiCad Protel extensions, which JLC accepts | `gen/outputs.sh` |
| Outline | Closed. Four lines and four R2 arcs, 0..36 x 0..36 | `F405FC-Edge_Cuts.gm1`: every segment end meets the next start |
| Origin consistency | Gerbers use the aux origin (`--use-drill-file-origin`), drill uses `--drill-origin plot`, CPL uses `--use-drill-file-origin`. The via at drill `X2.526Y23.974` is the F.Cu flash `X2526274Y23973726`. Mounting holes are at (2.75, 2.75) / (33.25, 33.25) in both the drill file and F.Mask. CPL U3 (17.000, 18.500) equals the board position (117.0, 117.5) after the transform. All 119 CPL rows match the board position and side (script check) | drill, gtl, gts, cpl |
| Drill sizes | PTH: vias 0.30 (T1), U1/U2 thermal vias 0.30 (T2), USB-C plated slots 0.6 x 1.7 and 0.6 x 1.4 (G85). NPTH: 0.65 (USB-C pegs) and 3.20 (M3) | `F405FC-PTH.drl`, `F405FC-NPTH.drl` |
| Annular ring | Vias 0.6/0.3, ring 0.15. USB-C slot pads 1.0 wide around a 0.6 slot, ring 0.20 | `board.json` pads/vias. DRC rule `min_via_annular_width 0.15` |
| Hole-to-hole | Smallest round-hole edge-to-edge is 0.363 mm (same-net vias, CAM_SEL at 13.35, 21.75). Smallest different-net gap is 0.366 mm (J1 NPTH peg to USB_CC1 via at 29.72, 24.39). Next is 0.436 mm (3V3/BOOT0 vias) | `geo.py` |
| Copper to edge | DRC rule 0.30 mm, 0 violations (covers zones and pads) | drc_summary |
| Min track / zone width | 0.127 / 0.127 mm, no narrower copper (zone `min_thickness 0.127`), so no slivers below 0.127 | `dump.py` (`tracks_minw 0.127`), zones |
| Via tenting | `tenting front yes / back yes`. F.Mask and B.Mask contain **no** 0.6 mm via apertures; the only C-apertures are 0.65 (USB pegs), 1.0 (TPs) and 3.2 (holes). The U1/U2 thermal-via pads have no mask layer, so they are tented on top, which closes G3R-01 | `F405FC-F_Mask.gts`, `F405FC-B_Mask.gbs` aperture lists |
| Mask webs between pads (expansion 0, `pad_to_mask_clearance 0`) | No pair of mask openings on either side is closer than 0.12 mm, except J1 A1/B12 (both GND, merged on purpose). LQFP-64, LGA-14/10/12, WSON-8 and USB-C webs are all ≥ 0.12 mm (LQFP and LGA about 0.2-0.25 mm) | `geo.py` (pairwise `Collide` binary search on pad shapes) |
| Mask bridges, different nets | `solder_mask_bridge` severity is error, with 0 errors | DRC |
| Silk on exposed copper | None. `silk_over_copper` (warning) reports 0, and the Gerbers are plotted with `--subtract-soldermask` | DRC, `outputs.sh` |
| Paste: LMR38020 HSOIC EP | Three paste-only windows (0.355 + 0.5 + 0.355) x 3.4, about 45 % of the 2.71 x 3.4 EP. No paste on the 8 thermal-via pads | `paste.py` (accepted earlier as G2R-07) |
| Paste: WSON-8 EP (U10) | Four windows of 1.37 x 1.73, 65 % of the 3.4 x 4.3 EP | `paste.py` |
| Paste: LGA parts | 1:1 with the pads (U6 0.35 x 0.625, U7 0.25 x 0.475, U8 0.25 x 0.275, U9 0.375 x 0.35) | `paste.py` (see m-6 on stencil thickness) |
| Stencil set | `F405FC_stencil.zip` holds F_Paste, B_Paste, Edge and job. It is internally consistent but uses absolute coordinates (Y negative), while the PCB zip uses the aux origin. That is fine for a separately ordered stencil (see i-3) | stencil `.gm1` vs PCB `.gm1` |
| CPL vs BOM | 119 CPL rows, no duplicates. Every placeable footprint is in the CPL. DNP R32/R37 are excluded. H*, P*, TP* are excluded (not placed). BOM refs = 119 placed + R32/R37 on a qty-0 "DNP spares" line | script cross-check of `fab/F405FC_cpl_jlc.csv`, `bom/*.csv` and the board |
| BOM values vs board | Every BOM line's refs carry matching footprint values and packages (e.g. 445-6042-1-ND for C2/C3/C10/C11 is 1210, 4.7 uF 100 V) | script |
| BOM arithmetic | Unit price x order quantity equals the extended price on all 53 lines. The extended sum is **$173.28**, matching the TOTAL row and D-24. Qty-per-board sum is 119, matching the CPL | `bom/digikey_bom_costed.csv` |
| Mounting holes | 3.2 mm NPTH at 30.5 mm pitch, 1.15 mm from the edges. Rule areas `HOLE_KEEPOUT_1..4` are R2.3 circles (4.6 mm), no tracks/vias/pours. No pad within 3.0 mm of any hole centre | `kicad_pcb` lines ~53673-53700, `lbl.py`/hole script |

## MAJOR findings

### M-1 MAJOR: USB-C shell slots (J1 SH, 4 plated slots) connect solidly to GND pours on all four layers, contrary to D-22
Evidence:
- All GND zones have `connect_pads yes` (full), not `thru_hole_only` (`kicad_pcb` lines 50780 and 53812, …). `gen/route.py:81` says so: `SetPadConnection(ZONE_CONNECTION_FULL) # solid on all pads: thermal spokes starved on the dense board (USB shield)`.
- `design/decisions.md` D-22 claims "thermal reliefs only on THT pads", which is wrong.
- Fill coverage measured 0.06 mm outside each J1 SH pad (`therm.py`):

| J1 shell slot | F.Cu | In1 | In2 | B.Cu |
|---|---|---|---|---|
| 1 | 1.00 | 0.95 | 0.90 | 0.93 |
| 2 | 0.88 | 1.00 | 1.00 | 1.00 |
| 3 | 0.72 | 0.88 | 0.88 | 0.72 |
| 4 | 1.00 | 1.00 | 1.00 | 1.00 |

  Each slot sits in solid copper on four layers, including the In1 GND plane.

Why it matters:
- J1 is a top-side part. The guide fits it in Stage B with hot air or iron while the bottom is already populated and the board may not go back on the hot plate.
- With no preheat, a 1.6 mm, 4-layer board with solid planes will not let a normal fine-tip iron wet the shell slots through the barrel.
- These four joints are the only mechanical retention of the most-stressed connector on a flight controller. A cold or partial shell joint means the USB-C tears off.

Fix:
- Set J1's SH pads to thermal relief locally: `SetLocalZoneConnection(THERMAL)`, 0.25 mm gap, two to four 0.3-0.4 mm spokes.
- Or change the GND zones to `connect_pads thru_hole_only` and keep SMD pads solid.
- Refill, then re-run DRC.
- Correct the D-22 text.
- In the meantime, add a note to the guide: solder J1 shell tabs with a ≥ 60 W iron, a 2-3 mm chisel tip and board preheat (hot air from the top) before the bottom-side LGA parts are fitted.

### M-2 MAJOR: the assembly sequence puts bottom-side hot air on U6/U7 directly beneath the already-soldered MCU, and contradicts its own side-order rule
Evidence:
- `docs/assembly_and_bringup.md` §2 says "the top side … is then done with hot air or the iron … never back on the hot plate … Keep hot air away from the bottom side once it is populated".
- §3 Stage B fits U3 (top LQFP) and also bottom parts: U10 (WSON-8 8 x 6 with EP), D10-D12, C24/C30/C35/C52.
- §4 Stage C then fits U6/U7 ("LGA, bottom side: local hot air with a small nozzle").
- Board positions:
  - U3 is at (17.0, 18.5); its body spans about 12-22 x 13.5-23.5.
  - **U6 (15.4, 19.0) and U7 (20.8, 19.0) lie entirely inside the U3 body footprint** on the opposite side.
  - U10 (bottom, 8.5, 28.0) lies under U9 (top, 9.55, 28.3), which is also fitted later by hot air.
- Result: reflowing U6/U7 from below re-melts U3's joints above (the board rests top-down on standoffs). Reflowing U9 from above re-melts U10 hanging below.
- With 4 solid planes, local hot air needs long dwell times, which makes this worse. Also, a WSON-8 8 x 6 EP (U10) cannot be soldered with an iron, and no preheat method is given once both sides are populated.

Fix (guide change only):
- Reflow **all** bottom-side parts in the single hot-plate pass, including U6, U7, U10, U11, Q2 and all bottom passives.
- Leave off only U4 (LP38692), U5 (LP5907) and D5 (and top D4), which are the parts the staged bring-up must protect. They are SOT-223/SOT-23/SOD-123W and can go on later with hot air or iron.
- U6/U7 are fed only from U5 (3V3_IMU) and U10 only from U4 (3V3), so they stay unpowered during Stage A.
- Then do the top side (U3 first, then U8/U9, connectors) with hot air or iron.
- Rewrite §2-§4 accordingly.
- Also remove "TP1-TP5" from the Stage B fit list. These are bare pads (`TestPoint_Pad_D1.0mm`, nothing to fit).

### M-3 MAJOR: tented fanout vias abut fine-pitch pads; mask slivers of 0.02-0.05 mm will not survive at the fab
Evidence (`viamask.py`):
- 94 tented vias lie within 0.1 mm of a pad's mask opening (all same-net, so there is no short risk).
- About 30 are at ≤ 0.06 mm on fine-pitch or 0402 pads. The mask strip between the pad opening and the tented via ring would be:

| Part | Pad | Net | Sliver (mm) | Via location |
|---|---|---|---|---|
| U6 (ICM-42688-P, LGA, bottom) | 1 | SPI1_MISO | 0.038 | (14.29, 17.74) |
| U6 | 14 | SPI1_MOSI | 0.038 | (15.01, 18.74) |
| U7 (BMI270, LGA, bottom) | 13 | SPI1_SCK | 0.038 | (20.69, 17.51) |
| U8 (BMP390, LGA-10, top) | 3 | GND | 0.040 | (13.56, 27.76) |
| U8 | 4 | I2C1_SDA | 0.038 | (14.51, 27.21) |
| U10 (WSON) | 6 | SPI3_SCK | 0.024 | — |
| U10 | 8 | 3V3 | 0.026 | — |
| U10 | 9 (EP) | GND | 0.041 | — |
| U10 | 4 | GND | 0.047 | — |
| U3 (LQFP-64), 10 pins incl. HSE_OUT, I2C1_SCL, GYRO1_CS | 6, 16, 20, 26, 36, 37, 53, 61, … | various | about 0.038 | — |

  0402 passives affected: R35, C48, R33, R17, C32, R25, R26 and C25, at 0.020-0.053 mm.

- `imuvia.py` finds 4 vias inside each IMU courtyard (U6: GND, VTX_PWR_EN, SPI1_MISO, SPI1_MOSI; U7: LED_STRIP, SPI1_SCK, SPI1_MOSI, MOTOR6) and 3 inside U8.
- This contradicts D-22's "fanout vias kept 0.8 mm outside the IMU courtyards".
- `pad_to_mask_clearance` is 0 and `solder_mask_min_width` is 0, so KiCad keeps these slivers in the Gerbers. Typical LPI mask cannot hold a 0.02-0.05 mm dam: it either flakes, or the fab's CAM clears it.
- Either way the via ring next to the pad is exposed. On 0.25 mm LGA pads printed 1:1, solder then runs onto the ring or into a partially tented 0.3 mm hole. That leaves a starved, hidden joint that cannot be inspected without X-ray.

Fix:
- Move the vias that touch U6/U7/U8 pads and the U10 signal pads so the via copper is ≥ 0.10-0.15 mm from the pad edge (true dog-bone).
- Or order the board with resin-filled and capped vias (JLC "via-in-pad / POFV", paid on 4-layer).
- At minimum, set `solder_mask_min_width` to the fab's dam minimum so the CAM result is predictable, and re-check with DRC.
- Correct the D-22 statement.

### M-4 MAJOR: two BOM lines have no DigiKey part number (brief: "Every part comes from DigiKey only")
Evidence:
- `bom/F405FC_digikey_bom.csv` line for **74438356056 (L1, L2)**: Digi-Key Part Number is `''`.
- Line for **ECS-80-8-33-JEN-TR3 (Y1)**: `''`.
- `digikey_bom_costed.csv` lines 26 and 52 are marked "DigiKey PN NOT CONFIRMED" and "PN unconfirmed".
- Line 4 (445-6042-1-ND, C2/C3/C10/C11) is still "DigiKey PN to verify (one snippet ties 445-6042-1-ND to the NRND …M200AB)". The same line in `bom_raw.csv` reads "445-6042-1-ND (verify: K200AB cut tape)".
- BOM Manager can match by MPN, but an empty PN column fails the brief's sourcing rule, and three power-path parts are unconfirmed.

Fix:
- Confirm and fill the DigiKey PNs for L1/L2 (or switch to the alternate WE-MAIA 78438356056 = 732-11317-1-ND, D-20) and for Y1.
- Confirm 445-6042-1-ND resolves to the K200AB part.
- Regenerate both BOM CSVs.
- This review does not re-verify any DigiKey listing.

### M-5 MAJOR: the safety label "VTX 10V" (and "ESC", "USB", "RX") is printed under the connector bodies and is hidden after assembly
Evidence (`lbl.py`):
- `gr_text "VTX 10V"` covers x 115.42-120.58, y 102.37-103.83 (board coordinates). That is entirely inside J3's F.Fab body outline (x 113.95-122.05, y 100.47-104.83).
- In the same way, "ESC" sits inside J2's body, "USB" inside J1's and "RX" inside J5's.
- `docs/renders/board_top.png` shows none of the four once the 3D bodies are on.
- The bring-up guide §5 and D-15 rely on this marking: "**J3 (front, silk "VTX 10V") carries 10 V** … never plug a GPS … into it". Plugging a 5 V GPS into J3 destroys it.

Fix: move these labels to free board area beside each connector, outside the courtyard (e.g. "VTX 10V!" beside J3, with an arrow). Use ≥ 1.0 mm text height.

## MINOR findings

- **m-1: 0402/0603 GND pads poured solid, which affects tombstoning and iron rework.**
  - `therm.py`: of 82 two-pad 0402/0603/0805 parts, **51 have one pad ≥ 50 % embedded** in a same-net pour and the other pad on a trace only.
  - 19 are 100 % embedded, e.g. C26/C28/C44 (3V3 decaps, top), C40/C41 (3V3_IMU, bottom), R10 (FB_10V divider), C12/C4 (VBAT HF caps), C53, R36.
  - With local hot air (the guide's top-side method), the asymmetric heat sinking invites tombstoning and makes iron rework slow.
  - The board-wide hot-plate pass is less affected.
  - Fix: a custom DRC rule giving thermal connection (0.2 mm gap, 2 spokes ≥ 0.2 mm) to SMD pads of footprints ≤ 0603, keeping solid connection on U1/U2, L1/L2, C2/C3/C10/C11, the input/output caps of the buck hot loops, and P1/P2/P3/P4. Or accept it and add "preheat; tack the trace-side pad last" to the guide.
- **m-2: vias in paste-bearing SMD pads.** `vip.py` finds:
  - C12 pad 1 (0603, VBAT HF cap at U2): **two** VBAT vias whose 0.3 mm holes touch the pad, at (21.40, 11.95) and (22.40, 12.05);
  - C10.1 and C8.2: via centred inside the pad;
  - D1 (SMB, top): 6 vias inside both pads, straight through to P1/P2;
  - J2 MP at (26.20, 2.00), P4 at (33.90, 10.40), C2.1 and C15.2: annulus only.

  Paste wicks into the open holes, so the 0603 C12 joint is the one at risk. Fix: pull the C12/C8/C10 vias off the pads, or plug them.
- **m-3: silk overlaps (26 DRC warnings).**
  - 25 are label text crossing the 0.12 mm silk rectangle that `Pad_SMD_*` draws 0.26 mm outside each pad (`lib/F405FC.pretty/Pad_SMD_1.2x1.6mm.kicad_mod` `fp_rect ±0.86 x ±1.06`).
  - None touches exposed copper (silk_over_copper = 0).
  - Legibility suffers in the renders. "T5" and "T6" read as "I5"/"I6" because the rectangle edge erases the crossbar (`board_top.png` top-left, `board_bottom.png` left). "S8", "VID", "5V" (bottom) and "G" are partly struck through.
  - One is U8's pin-1 polygon crossing C44's silk segment at (14.9, 28.6). That makes the BMP390 pin-1 mark ambiguous.
  - Fix: drop the silk rectangles from the Pad_SMD footprints (the mask opening is the marking), or move the labels ≥ 0.2 mm clear. Clip C44's silk at U8's pin-1 marker.
- **m-4: no reference designators on silk.** Every `Reference` field is on F.Fab or B.Fab (154 refs, 0 on silk). The board also has no name, revision or date marking (job `"Revision": "rev?"`). Hand assembly then relies entirely on `bom/F405FC_ibom.html`. Acceptable at this density, but add at least "F405-FC rev C" plus polarity and pin-1 notes for D4/D5/D9, and set the project revision.
- **m-5: exposed VBAT copper near mounting holes.**
  - P1 (VBAT, bottom) is 3.00 mm from the H3 centre, D1.1 (VBAT, top) 3.35 mm, P14 (BUZ_N, top) 3.03 mm and D4.2 (VBUS) 3.12 mm from H2.
  - These are outside the 4.6 mm grommet keepout. But an M3 nut or aluminium standoff (5.5 mm A/F, corner radius 3.18 mm) or a solder fillet on the battery lead can reach the P1 corner.
  - Fix: specify nylon hardware or grommets on H3 in the guide, or move P1 0.5 mm inward.
- **m-6: stencil thickness and surface finish are not specified anywhere** (grep over design/, docs/, review/).
  - U8's 0.25 x 0.275 mm apertures have an area ratio of 0.65 at a 0.10 mm stencil but only 0.55 at 0.12 mm, below the usual 0.66 release guideline (IPC-7525).
  - U7's 0.25 x 0.475 apertures are 0.68 at 0.12 mm.
  - Fix: order a 0.10 mm stencil (or shrink U8 to a single larger aperture per pad if the land allows), and ENIG finish. HASL on 0.25 mm LGA pads and 0.5 mm LQFP is uneven.
  - The guide's "0.4 mm stencil-printed or syringe paste" is unclear; state the thickness.
- **m-7: no fab notes.**
  - The job file's stackup is KiCad's generic one: 3 x 0.48 mm FR4 and 35 µm inner copper. JLC04161H-7628 is about 0.21 / 1.065 / 0.21 mm with 0.5 oz inner copper.
  - `"Finish": "None"`.
  - JLC ignores the job file, so the stackup, 1.6 mm thickness, ENIG, tented vias and "use the JLC04161H-7628 impedance stackup" must be selected by hand at order time. Add a short fab-notes section in `docs/assembly_and_bringup.md` §0, or set the stackup in the board.
- **m-8: 17 dangling MCU fanout vias** (`via_dangling`: UART5_RX, BEEPER, MOTOR1/4/7/8, UART2_RX, ESC_TLM, CAM_SEL, SPI1_SCK, SPI1_MISO, GYRO1_INT, STATUS_LED_BLUE, SWDIO, SWCLK, SPI3_SCK, SPI3_MOSI).
  - Not a fab or assembly problem: they are tented both sides (no 0.6 mask apertures) and pass hole and annulus rules.
  - Some contribute to M-3. They are stubs on SPI clocks (SI reviewer's call).
  - `gen/prune.py` was meant to remove them (D-22). Remove them and refill, for a clean DRC.
- **m-9: no spare ICs for hand assembly.** Every IC line is ordered at qty 2 for 2 boards (`digikey_bom_costed.csv` lines 40-51), including the LGA sensors (U6/U7/U8/U9), which are the most likely hand-assembly casualties. Add 1 spare each of U6, U7, U8, U9 and U10 (about +$32).
- **m-10: paste on DNP pads.** R32 and R37 pads are in F_Paste (`F405FC-F_Paste.gtp` lines 547-548: X27.54/26.52 Y14.78; lines 116-117: X19.97/20.99 Y28.70). Harmless for hand assembly (tinned pads), but R37 then needs its pads wicked clean if the 0R option is fitted later. The CPL and BOM handle DNP correctly.

## INFO

- **i-1: fiducials.** There are none. They are not needed for hand assembly, and JLC PCBA adds its own on panel rails if machine assembly is ever wanted.
- **i-2: drill maps in the zip.** `F405FC-PTH-drl_map.gbr` and `F405FC-NPTH-drl_map.gbr` are inside `F405FC_JLC_gerbers.zip`. JLC's parser normally ignores them, but they can be flagged as unknown layers. Consider excluding them.
- **i-3: stencil origin.** The stencil zip is plotted in absolute coordinates while the PCB zip uses the aux origin. Each set is self-consistent. If a stencil is ordered together with the PCB, JLC uses the paste layers in the PCB zip.
- **i-4: CPL format.** `F405FC_cpl_jlc.csv` uses JLC column names. Rotations are KiCad's (bottom side as exported by `kicad-cli pos`). JLC usually needs per-package rotation corrections (SOT-23, SOT-223, SMB and bottom side), which only their DFM preview shows. For hand assembly the CPL is informational.
- **i-5: spacing for hand tools.** The nearest foreign pads to fine-pitch parts are:
  - U3 LQFP: C32 0.55 mm and Y1 0.70 mm (left pin row; drag soldering needs care next to Y1);
  - U6: C40/C38 0.57 mm;
  - U8: C25/C44/C43 0.64 mm;
  - U9: C45 0.59 mm;
  - U10: R13 0.58 mm;
  - J1: R36 0.86 mm.

  Workable with a fine tip, hot air with a 3-5 mm nozzle, and Kapton.
- **i-6: test points.** TP1-TP5 are 1.0 mm round pads on 2.4 mm pitch on the bottom (14.0-18.8, 28.8-31.6), probe-accessible before stacking. USB DFU is the primary flashing path.
- **i-7: acid traps and copper slivers.** Zone `min_thickness` is 0.127 with island removal on every pour, and DRC shows no copper narrower than 0.127 mm. Acid traps were not geometrically analysed; they are a non-issue at modern fab etch control.
- **i-8: heavy parts and second side.** The bottom side carries L1/L2, the 1210/1206 caps and U1/U2. The guide's rule (bottom first on the hot plate, top never back on the hot plate) correctly avoids dropping them. M-2 is about which parts are fitted when, not about this rule.

## Not verified (explicitly)

- **JLCPCB capability limits.** `jlcpcb.com` did not resolve from this sandbox (WebFetch: `getaddrinfo ENOTFOUND jlcpcb.com`), and web search did not return the rigid-PCB capability page. All JLC figures here come from memory and were not checked against the current page: minimum mask dam about 0.08-0.1 mm, plated slot ≥ 0.5 mm, silk ≥ 0.15 mm line and ≥ 0.8-1.0 mm text, hole-to-hole for different nets, annular ring. The measured values are given so they can be compared with the live page.
- No Gerber viewer render (gerbonara or gerbv not installed). Checks are text parses plus pcbnew geometry on the board file. I did not confirm that the Gerbers are a 1:1 plot of the current `kicad_pcb` beyond spot coordinates (one via, the holes, the edge). The zip and `fab/gerbers` are identical.
- Footprint land patterns against vendor drawings (Gate 2 territory), part heights, 3D models (U4, U6, U8 render without bodies) and courtyard sizes. `missing_courtyard` is set to ignore.
- CPL rotations against JLC's convention and polarity against vendor pin-1 definitions (only silk pin-1/cathode markers were seen in the renders).
- iBOM content (the HTML data is compressed; not decoded).
- DigiKey PNs, stock and prices. The $173.28 total is checked only arithmetically.
- Actual solderability: no physical assembly trial. The thermal claims in M-1 and m-1 are judgement based on the measured pour coverage.
- SI effects of the dangling vias and stubs (Gate 4 reviewer).
