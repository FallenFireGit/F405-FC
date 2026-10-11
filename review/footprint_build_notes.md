# Footprint build notes (F405-FC)

Generator: `gen/footprints.py` (plain Python, no UUIDs or timestamps, so output is deterministic. Two runs produced identical md5sums.)
Output: `lib/F405FC.pretty/` (KiCad 10 format, `version 20260206`). Every footprint loads with
`pcbnew.FootprintLoad('/work/lib/F405FC.pretty', name)` under KiCad 10.0.6. Pad dumps are at the end of this file.

Conventions: pads use F.Cu/F.Mask/F.Paste. Each footprint has Reference on F.SilkS, Value on F.Fab, `${REFERENCE}` on F.Fab, and a body outline on F.Fab
with a pin-1 chamfer, plus a filled silk triangle as the pin-1 marker. The courtyard (F.CrtYd, 0.05 line) sits 0.25 mm outside the body or pads, rounded outward to a 0.01 mm grid.

## Final footprint IDs

| Part | Footprint ID | Source |
|---|---|---|
| BMP390 | `F405FC:Bosch_LGA-10_2x2mm_P0.5mm_BMP390` | **new** |
| ICM-42688-P | `Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y` | **use stock** |
| BMI270 | `F405FC:Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270` | **new** (stock pads are too long, see below) |
| LMR38020 (DDA) | `F405FC:TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA` | **new** (stock does not match the TI land pattern) |
| W25N01GVZEIG | `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm` | stock, **UNVERIFIED** (no datasheet on disk) |
| USB4105-GF-A | `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | stock, matches the drawing |
| WE-MAPI 4030 | `Inductor_SMD:L_Wuerth_MAPI-4030` | stock, sanity check OK (WE datasheet not on disk) |
| Solder pads | `F405FC:Pad_SMD_2.5x4.0mm`, `F405FC:Pad_SMD_2.0x3.0mm`, `F405FC:Pad_SMD_1.5x2.0mm`, `F405FC:Pad_SMD_1.2x1.6mm` | **new** |

**`design/circuit.py` FP map needs two edits (not done here):** change `"BMI"` to `F405FC:Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270` and
`"LMR"` to `F405FC:TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA`. All other entries in that map are already correct.

**Name change:** the brief proposed `..._EP2.95x2.95mm_DDA`. The DDA0008B exposed pad is 2.71 x 3.4 mm max (p.37). The TI land has 2.95 x 4.9 mm metal
with a 2.71 x 3.4 mm mask opening (p.38). Nothing in the package is 2.95 x 2.95, so the footprint uses the package EP size in its name, as KiCad naming does.

## 1. BMP390: new `Bosch_LGA-10_2x2mm_P0.5mm_BMP390`

Evidence: BMP390_DS.pdf rev 1.7.
- p.49, Fig.26, bottom view:
  - 6 side pads are 0.275 x 0.250, with the left and right column centres 1.525 apart.
  - Side pads are on a 0.5 pitch (1.000 over 3 rows).
  - 4 top/bottom pads are 0.250 x 0.275, with the two pad centres 0.500 apart.
  - All pads are 0.100 ±0.05 from the package edge. The body is 2.00 ±0.05.
  - Top view: vent hole Ø0.25, 0.6/0.6 from the pin-1 corner.
- p.49, sec 7.2: "Bosch Sensortec suggests the BMP390 outline dimensions (see 7.1 bottom view) as landing pattern". The land pattern is therefore 1:1 rectangular pads.
- p.46, Fig.23 / Table 52, top view: pin 1 (VDDIO) is on the top edge, right of centre. Pin 2 (SCK) is top-left. Pins 3/4/5 (VSS/SDI/SDO) run down the left side.
  Pins 6/7 (CSB/INT) run left to right along the bottom. Pins 8/9/10 (VSS/VSS/VDD) run up the right side. Numbering is counter-clockwise seen from the top.

Pad centres in the footprint (top view, y down):
- 1 (+0.25, −0.7625); 2 (−0.25, −0.7625)
- 3/4/5 (−0.7625, −0.5/0/+0.5)
- 6 (−0.25, +0.7625); 7 (+0.25, +0.7625)
- 8/9/10 (+0.7625, +0.5/0/−0.5)

The footprint uses the datasheet's top-view orientation, so the pin-1 corner is **top-right**, not top-left. The fab outline has a chamfer at that corner. The silk triangle sits above pad 1.
The vent hole is drawn on F.Fab at (+0.4, −0.4).

Stock comparison: KiCad has no Bosch LGA-10 2x2 footprint. The closest one is `Package_LGA:ST_HLGA-10_2x2mm_P0.5mm_LayoutBorder3x2y` (LPS22HH).
- Same 0.7625 / 0.5 pad grid.
- Its numbering matches the BMP390 if the part is rotated 90° (its pin 1 is at the upper left on the 2-pad side, counter-clockwise).
- Its pads are 0.425 x 0.35 against Bosch's recommended 0.275 x 0.25. That leaves only 0.15 mm gaps and does not follow Bosch's 1:1 recommendation.
- It would be electrically usable, but **the custom footprint is preferred**.

## 2. ICM-42688-P: **use stock** `Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y`

Evidence: ICM-42688-P_DS.pdf DS-000347 rev 1.2.
- p.54, sec 10.2, top/bottom view:
  - E = 3.0 (x) and D = 2.5 (y).
  - Pin 1 is top-left. Pins 1–4 are on the left side, 5–7 on the bottom, 8–11 on the right side going up, and 12–14 on the top going right to left (counter-clockwise from the top).
  - Side-pad centres are 2x 1.1625 from the centre; top/bottom pad centres are 2x 0.9125. The bottom-view pin numbers 1/4/5/7/8/11/12/14 agree with this.
- p.55 table: W 0.25 (0.20–0.30), L 0.475 (0.425–0.525), e 0.5, D1 1.5, E1 1.0, pads 0.10 from the body edge.
- p.19, Fig./Table 9: pin-out diagram with the same placement.
- The datasheet gives **no recommended land pattern**, only package pads.

The stock footprint has:
- Pad centres at ±1.1625 / ±0.9125, pitch 0.5, with **identical numbering and orientation**.
- Pads of 0.35 x 0.625. That is the package pad (0.25 x 0.475) grown by +0.05 per side in width and +0.075 per end in length.
  The pad-to-pad gap is 0.15 mm, the side-to-corner gap is 0.175 mm, and the copper stays inside the body (outer edge at 1.475 / 1.225).

That is a reasonable IPC-style enlargement, and the numbering and positions match exactly, so this footprint is **use stock**.

## 3. BMI270: new `Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270`

Evidence: BMI270_DS.pdf BST-BMI270-DS000-08.
- p.143, sec 8.1: package pads 0.475 x 0.250 (both orientations). L1 = 0.100 from the edge. D 3.00 / E 2.50. e 0.5, D1 1.00, ZE 0.50.
- p.145, sec 8.3, landing pattern recommendation:
  - Pads 0.475 x 0.25.
  - Side pads have their inner edge 0.925 from the centre, so the centre is at x = ±1.1625 and the outer edge 0.1 inside the body.
  - Top/bottom pads have their inner edge 0.675 from the centre, so the centre is at y = ±0.9125.
  - Pin 1 is top-left, numbered counter-clockwise from the top (14/13/12 along the top, 5/6/7 along the bottom).
- p.134, sec 7.1, pin-out top view: the same numbering.

Stock `Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm` (made from the BMI160 datasheet):
- Numbering and orientation **match**, and the pad width of 0.25 matches.
- Its pads are **0.675 long** (centre 1.2625 / 1.0125). The inner edge is the same, but they extend 0.2 mm further out, ending 0.1 mm *outside* the body.
- It differs from the BMI270 recommendation of 0.475, so under the stated rule I created a custom footprint that is 1:1 with sec 8.3.
- The stock part would still solder fine and is easier to inspect or rework. It is an acceptable fallback, since the pin map is identical.

## 4. Solder pads: new `Pad_SMD_2.5x4.0mm`, `Pad_SMD_2.0x3.0mm`, `Pad_SMD_1.5x2.0mm`, `Pad_SMD_1.2x1.6mm`

- Single SMD pad "1", roundrect with a 0.25 mm corner radius, on F.Cu/F.Mask/F.Paste (paste included for pre-tinning).
- `solder_mask_margin 0`, so the mask opening equals the copper.
- Silk rectangle 0.26 mm outside the copper. F.Fab outline equals the pad.
- The courtyard encloses the silk ring (0.37 mm from the copper).
- Attributes: `smd exclude_from_pos_files exclude_from_bom` (no placed part).
- There is no pin-1 marker, because a single pad has no meaningful pin 1.

## 5. LMR38020 DDA: new `TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA`

Evidence: lmr38020.pdf, DDA0008B (4214849/B 09/2025).
- p.37, package: body 3.8–4.0 x 4.8–5.0, pitch 1.27. Exposed pad 2.11–2.71 (x) by 2.8–3.4 (y).
- p.38, example board layout:
  - 8x pads 1.55 x 0.6, R0.05, with row centres 5.4 apart.
  - Thermal **metal 2.95 x 4.9**, solder-mask-defined, with a **mask opening of 2.71 x 3.4**.
  - Optional vias Ø0.2 on a 1.3 mm grid: 8 drawn, at x = ±0.65 and y = ±0.65, ±1.95. The outer row sits under the mask.
  - Note 10 says to fill or plug vias that sit under paste.
- p.39, stencil: 2.71 x 3.40 at 0.125 mm thickness (100 % coverage). Other options are 3.03 x 3.80 at 0.1 mm and 2.47 x 3.10 at 0.15 mm.

The new footprint has:
- Pads 1–8 exactly as on p.38.
- Pad 9 made of several parts:
  - a 2.71 x 3.4 F.Cu+Mask+Paste opening;
  - 2.95 x 4.9 F.Cu metal with no mask opening;
  - 2.95 x 4.9 B.Cu metal;
  - 8 thru-hole vias of 0.2 drill / 0.4 copper.
- **Fab note:** the 4 vias inside the paste opening should be filled or plugged (TI note 10), or reduce the paste in the board's DFM step.

Stock `Package_SO:TI_SO-PowerPAD-8_ThermalVias` (based on the TPS5430 datasheet) compared with TI DDA0008B for the LMR38020:

| Item | TI p.38/39 | Stock ThermalVias |
|---|---|---|
| Signal pads | 1.55 x 0.6 @ ±2.7, 1.27 | 1.55 x 0.6 @ ±2.7, 1.27 (match) |
| EP mask opening / paste | 2.71 x 3.4 | 2.6 x 3.1 (smaller) |
| EP metal | 2.95 x 4.9 | 2.95 x 4.5 |
| Vias | 8x Ø0.2, x ±0.65, y ±0.65/±1.95 | 8x Ø0.3/0.6, x ±0.6, y −1.8/−0.6/**+0.7**/+1.8 (asymmetric) |

The stock footprint therefore **does not match**, so I created the custom one. (Stock `TI_SO-PowerPAD-8` is a third variant, with 1.91 x 0.61 pads at ±2.78 and the EP split into 4 pads; it does not match either.)

## 6. W25N01GVZEIG WSON-8 8x6: stock `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm`, **UNVERIFIED**

**There is no Winbond datasheet in `datasheets/`.** The stock footprint's own source is a GigaDevice GD5F1GQ4 WSON 8x6 drawing.

The stock footprint has:
- Pads 0.65 x 0.5 at x = ±3.75, pitch 1.27, numbered 1–4 down the left and 5–8 up the right.
- EP 3.4 x 4.3 (mask = copper) with 4 paste windows of 1.37 x 1.73.

From memory, the Winbond "WSON 8x6-mm" (ZE) package is:
- 8.0 mm across the pad rows and 6.0 mm along them, SOIC-8-208mil compatible.
- e 1.27, b ≈ 0.40, L ≈ 0.50.
- EP ≈ 3.4 x 4.3. Winbond notes say the EP is not internally connected (GND or float).

That is consistent with the stock footprint, but **it has not been checked against a drawing**. Fetch the W25N01GV datasheet (package section "8-pad WSON 8x6-mm") and confirm EP size, L/b and the EP connection before release.

## 7. USB4105-GF-A: stock `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`, **matches**

Evidence: USB4105_drawing.pdf p.1, "Recommended PCB Layout, as viewed from component side". I checked it from a 600 dpi render. Distances are measured from the centre line of the rear shell slots.

| Item | Drawing | Stock |
|---|---|---|
| Pad length | 12x 1.15 | 1.15 |
| Pad width | 4x 0.60 (A1/B12, A4/B9, B4/A9, B1/A12 shared), 8x 0.30 | 0.60 / 0.30 |
| Pad x positions | 6.40 / 4.80 / 3.50 / 0.50 spans | A1+B12 ±3.20, A4+B9 / B4+A9 ±2.40, B8/B5 ±1.75, A5/A8 ±1.25, B7/B6 ±0.75, A6/A7 ±0.25 |
| Pad inner edge from rear-slot centre | 4.18 | 4.755 − 0.575 = 4.18 |
| Locating holes | 2x Ø0.65, 5.78 apart, 3.68 from rear slots | NPTH Ø0.65 at ±2.89, Δy 3.68 |
| Front shell slots | 2x pad 2.10 / slot 1.70, width 1.00 / 0.60, 8.64 apart; centre on the pad inner-edge line | 1.0 x 2.1, drill 0.6 x 1.7, ±4.32, Δy 4.18 |
| Rear shell slots | 2x pad 1.80 / slot 1.40, 2.60 from the PCB edge | 1.0 x 1.8, drill 0.6 x 1.4, ±4.32 |
| Pin names | A1 B12 A4 B9 B8 A5 B7 A6 A7 B6 A8 B5 B4 A9 B1 A12, left to right | identical, with stacked A1/B12, A4/B9, B4/A9, B1/A12 |

All checked dimensions match. The shell tabs are named "SH" (4 plated slots), so connect SH to GND or the shield net in the symbol. The PCB edge belongs 2.60 mm behind the rear-slot centre line, which is y = +3.675 in footprint coordinates.

## 8. WE-MAPI 4030: stock `Inductor_SMD:L_Wuerth_MAPI-4030`, sanity check OK

- Pads 0.98 x 3.7 at x = ±1.185, so the gap is 1.39 and the span 3.35.
- Fab body is 4.1 x 4.1 (descr "4.1x4.1x3.1mm", the max of 4.0 nominal). Courtyard ±2.3.
- That is plausible for a 4.0 x 4.0 body. No Würth datasheet is on disk, so the pad dimensions have **not been verified** against the WE land pattern.

## Unverified / open items
- W25N01GV WSON-8 8x6: no datasheet on disk (section 6).
- WE-MAPI 4030: no datasheet on disk. Only the body size was sanity-checked.
- BMP390: the land is 1:1 small pads (0.25 x 0.275). Use a stencil of ≤0.1 mm, and keep the vent hole at top (+0.4, −0.4) clear of conformal coat.
- LMR38020: vias inside the paste opening need plugging, or a paste reduction, per TI note 10.
- No 3D models are attached to the custom footprints.

## pcbnew load check (KiCad 10.0.6)
```
Bosch_LGA-10_2x2mm_P0.5mm_BMP390: 10 pads
  1 (+0.2500,-0.7625) 0.250x0.275   2 (-0.2500,-0.7625) 0.250x0.275
  3 (-0.7625,-0.5000) 0.275x0.250   4 (-0.7625, 0.0000) 0.275x0.250   5 (-0.7625,+0.5000) 0.275x0.250
  6 (-0.2500,+0.7625) 0.250x0.275   7 (+0.2500,+0.7625) 0.250x0.275
  8 (+0.7625,+0.5000) 0.275x0.250   9 (+0.7625, 0.0000) 0.275x0.250  10 (+0.7625,-0.5000) 0.275x0.250
Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270: 14 pads
  1-4  (-1.1625, -0.75/-0.25/+0.25/+0.75) 0.475x0.250
  5-7  (-0.5/0/+0.5, +0.9125) 0.250x0.475
  8-11 (+1.1625, +0.75/+0.25/-0.25/-0.75) 0.475x0.250
  12-14 (+0.5/0/-0.5, -0.9125) 0.250x0.475
TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA: 19 pad objects
  1-4 (-2.7, -1.905/-0.635/+0.635/+1.905) 1.55x0.60 roundrect; 8-5 (+2.7, same y) 1.55x0.60
  9: 2.71x3.40 F.Cu/Mask/Paste; 2.95x4.90 F.Cu; 2.95x4.90 B.Cu; 8 vias 0.40/0.20 at (±0.65, ±0.65/±1.95)
Pad_SMD_2.5x4.0mm / 2.0x3.0mm / 1.5x2.0mm / 1.2x1.6mm: pad 1 at (0,0), roundrect r=0.25, mask margin 0, F.Cu/Mask/Paste
```
