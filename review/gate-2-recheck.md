# Gate 2 re-check: sourcing and footprints after D-17 / D-18 / D-19

Reviewer: independent Gate 2 re-check agent, 2026-10-12. Scope: the parts and footprints changed since `review/gate-2-sourcing.md` and
`review/gate-2-footprints.md` (L1/L2, the five 1210 input caps, the D-17 substitutions, the LMR38020 footprint changes from D-18), plus the
two DigiKey BOM CSVs. This was a read-only review. Nothing in design/, gen/, kicad/, lib/ or bom/ was modified.

## Verdict: **FAIL** (1 BLOCKER, 2 MAJOR)

- The 1210 input-cap MPN `GRM32DR71H106KA01L` could not be found at DigiKey or at any distributor (G2R-01).
- The DigiKey PN and stock for L1/L2 `74438356056` are still unconfirmed (G2R-02).
- Both DigiKey BOM CSVs still order the old 3.1 mm inductors and 2.7 mm caps (G2R-03).

## Evidence limits (read first)

- **Vendor sites.** Every vendor site was unreachable from this sandbox. digikey.com, mouser.com, rs-online.com, octopart.com,
  findchips.com, trustedparts.com, we-online.com, murata.com, search.murata.co.jp, ti.com and api.digikey.com all returned
  `CONNECT tunnel failed, response 403` (curl). WebFetch returned `ENOTFOUND`.
- **Search snippets.** All sourcing evidence below therefore comes from **WebSearch result snippets** (undated page caches). Stock
  figures are indicative only.
- **Würth datasheet.** The 74438356056 PDF was **not downloaded**. Its values come from search snippets that quote the PDF.
- **Local measurements.** Board pad coordinates were measured with pcbnew (KiCad 10 chroot) on `kicad/F405FC.kicad_pcb`. Library
  footprints were read from `/opt/kroot/usr/share/kicad/footprints`. TI land data was read from `datasheets/lmr38020.pdf` with
  `pdftotext` (text extraction only; nothing was executed).

## Findings

| ID | Sev | Item | Finding |
|---|---|---|---|
| G2R-01 | **BLOCKER** | C1, C2, C3, C10, C11 `GRM32DR71H106KA01L` | The MPN was not found anywhere |
| G2R-02 | **MAJOR** | L1, L2 `74438356056` | The DigiKey PN and stock are not confirmed |
| G2R-03 | **MAJOR** | BOM CSVs | Both BOMs are stale against circuit.py |
| G2R-04 | MINOR | L1/L2 datasheet values vs power.md | Values confirmed, with three corrections |
| G2R-05 | MINOR | U10 DigiKey PN | The PN points at a listing that is being phased out |
| G2R-06 | MINOR | circuit.py DigiKey fields | Stale "unconfirmed" and "verify" markers |
| G2R-07 | MINOR | LMR38020 DDA footprint (D-18) | Thin paste and few vias |
| G2R-08 | INFO | `Inductor_SMD:L_Wuerth_MAPI-4020` | Matches the Würth land pattern |
| G2R-09 | INFO | `Capacitor_SMD:C_1210_3225Metric` | Within IPC tolerance |
| G2R-10 | INFO | D-17 parts | Confirmed |

### G2R-01 BLOCKER: GRM32DR71H106KA01L cannot be found at DigiKey or any distributor

**Evidence**

- **circuit.py.** `design/circuit.py:74` carries the DigiKey PN `490-GRM32DR71H106KA01LCT-ND (verify)`. The PN was never seen, and
  `design/power.md:113` says the DC-bias derating was never confirmed.
- **Origin of the MPN.** It came from a suggestion in the Gate 3 review (`review/gate-3-placement.md:99`), not from a distributor listing.
- **Searches.** Four searches turned up no listing and no datasheet for this MPN:
  - `"GRM32DR71H106KA01L"`
  - `"GRM32DR71H106"`
  - `GRM32DR71H106KA01L digikey 490- stock price`
  - a thickness/DC-bias query
- **What does exist in the same family:**
  - GRM32DR71**C**106KA01L, 16 V ([TME](https://www.tme.com/us/en-us/details/grm32dr71c106ka01l/mlcc-smd-capacitors/murata/)).
  - GRM32DR71**E**106KA12L, 25 V, NRND at DigiKey ([DigiKey 586590](https://www.digikey.com/en/products/detail/murata-electronics/GRM32DR71E106KA12L/586590)).
  - The 50 V 10 µF X7R 1210 from Murata is GRM32**E**R71H106KA12L. It is 2.5 mm thick (2.7 mm max), out of stock with backorders
    unavailable ([DigiKey 2548481](https://www.digikey.com/en/products/detail/murata-electronics/GRM32ER71H106KA12L/2548481)).
- **Other vendors.** No 10 µF / 50 V / 1210 part at ≤ 2.2 mm was found from TDK, KEMET or Samsung either:
  - TDK C3225X7R1H106K250AC is 2.8 mm max ([DigiKey 10413509](https://www.digikey.com/en/products/detail/tdk-corporation/C3225X7R1H106K250AC/10413509)).
  - KEMET C1210C106K5RACTU is 2.8 mm.

**Impact**

- As drawn, the part cannot be ordered, which breaks the DigiKey-only rule. These five parts are the LMR38020 VIN hot-loop capacitors.

**Fix**

Replace C1/C2/C3/C10/C11 with **TDK C3225X7S2A475K200AB**: 4.7 µF ±10 %, 100 V, X7S, 1210, T = 2.0 ± 0.2 mm, so 2.2 mm max. This keeps
the same `C_1210_3225Metric` footprint, the same quantity and the same placement.

- **DigiKey listing.** The part is listed at DigiKey: [2443520](https://www.digikey.com/en/products/detail/tdk-corporation/C3225X7S2A475K200AB/2443520)
  and [2444083](https://www.digikey.com/en/products/detail/tdk-corporation/C3225X7S2A475K200AB/2444083).
- **Price and stock (snippets).** $1.24 @1. Stock reads 21,171 in one DigiKey snapshot, 0 in another (restock dated 03-Sep-2026), and
  7,786 in TDK's distributor table dated 2026-09-29.
- **Cut-tape PN.** The snippet gives 445-6042-1-ND. Another snippet ties 445-6042-1-ND to the NRND `...M200AB` sibling, so **verify
  the CT PN in BOM Manager** before ordering.
- **Thickness.** The family is 2.00 ± 0.20 mm (sibling C3225X7S2A335M200AB spec,
  [Arrow PDF](https://static6.arrow.com/aropdfconversion/4a7753a4bfe3d309b5eeb7bb749caf7ea6ab2de3/pgurl_infopart_noc3225x7s2a335m200ab.pdf)).
  IBS lists 2.21 mm, which is under the 2.5 mm bottom limit (`design/requirements.md:10`).
- **DC bias.** No numeric DC-bias value was findable. Only a curve exists, in the TDK PDF
  ([Farnell](https://www.farnell.com/datasheets/3920907.pdf)). At 25 V a 100 V-rated part sits at 25 % of rating, so ≥ 2.4 µF per cap
  (≥ 4.7 µF per IC with two caps) is expected, but **read the TDK curve and record it in power.md §1.2** before releasing.
- **Rejected alternatives:**
  - Samsung CL31B106KBHNNNE (10 µF 50 V X7R 1206, 1.6 mm, [DigiKey 5961251](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL31B106KBHNNNE/5961251)
    1276-6767-1-ND): rejected because DigiKey showed 0 stock with a 61-week lead time.
- **C1 option.** C1 is on the **top** side (measured at (7.30, 28.60), side T), where the limit is 3.5 mm. C1 alone may keep the
  orderable CL32B106KBJNNNE (1276-3387-1-ND) if a 10 µF entry cap is preferred. The corrected BOM below uses the TDK part for all five,
  so there is a single line.

### G2R-02 MAJOR: L1/L2 74438356056: DigiKey PN and stock not confirmed

**Evidence**

- **circuit.py.** `design/circuit.py:217-218` sets the DigiKey field to "unconfirmed (BOM Manager matches by MPN)".
- **Searches.** Seven searches found no DigiKey product page and no 732- PN for this MPN.
- **Indirect DigiKey evidence.** The only sign of a DigiKey listing is a related-products entry on DigiKey's BD9G101G-TR page, which
  shows the row "74438356056 FIXED IND 5.6UH 2.8A 81 MOHM SMD Würth Elektronik"
  ([DigiKey 3947476](https://www.digikey.com/en/products/detail/rohm-semiconductor/BD9G101G-TR/BD9G101G-CT-ND/3947476)).
- **Other distributors:**
  - RS 923-6208 showed 180 pcs in one cache and "temporarily out of stock" in another.
  - IC Components showed 2,862 pcs.
- **Same-electrical alternate.** Würth's automotive twin **78438356056** (WE-MAIA 4020, 5.6 µH, 2.8 A, 81 mΩ max, Isat 4.6 A
  catalog figure, 4.1 x 4.1 x 2.1 mm) **is** at DigiKey as **732-11317-1-ND** (CT), Active, 19-week lead time
  ([DigiKey 6833655](https://www.digikey.in/en/products/detail/w%C3%BCrth-elektronik/78438356056/6833655)). DigiKey stock for it was
  not visible in the snippets.

**Fix**

1. Before ordering, put 74438356056 into DigiKey BOM Manager and confirm a 732-…-1-ND line with stock ≥ 5.
2. If it cannot be ordered, switch L1/L2 to 78438356056 (732-11317-1-ND). Before that switch, confirm from the WE-MAIA PDF that it
   uses the same 4020 land pattern, Isat(10 %) and height.
3. Record the outcome in decisions.md.

### G2R-03 MAJOR: Both DigiKey BOM CSVs are stale against circuit.py

I compared the circuit.py BOM against the CSV programmatically: I imported `circuit` in the chroot and diffed the result against
`bom/F405FC_digikey_bom.csv`. All other refs match.

| CSV line | Lists (stale) | circuit.py now |
|---|---|---|
| `F405FC_digikey_bom.csv:4`, `digikey_bom_costed.csv` line 3 | 1276-3387-1-ND CL32B106KBJNNNE x13, C1 C2 C3 C10 C11 (2.7 mm max) | GRM32DR71H106KA01L (see G2R-01: replace with TDK C3225X7S2A475K200AB) |
| `F405FC_digikey_bom.csv:24`, costed line 23 | 732-11204-1-ND 74438357068 (6.8 µH 4030, 3.1 mm) x2, L1 | 74438356056 (5.6 µH 4020, 2.1 mm), L1 |
| `F405FC_digikey_bom.csv:25`, costed line 24 | 732-11205-1-ND 74438357082 (8.2 µH 4030, 3.1 mm) x2, L2 | 74438356056, L2 |
| (missing) | no row | 74438356056 x2 per board, L1 L2 |
| `F405FC_digikey_bom.csv:31,37`, costed 32, 37 | DigiKey PN blank for ERJ-2RKF3482X / ERJ-2RKF2432X | P34.8KLCT-ND / P24.3KLCT-ND now confirmed (G2R-10) |
| `F405FC_digikey_bom.csv:53`, costed 52 | W25N01GVZEIGCT-ND | 256-W25N01GVZEIGTRCT-ND (G2R-05) |
| `F405FC_digikey_bom.csv:10`, costed 9 | KEMET priced $0.10 | DigiKey snippet: $0.14 @1 |

- **bom_raw.csv is also stale.** `bom/bom_raw.csv` lines 5 and the two L rows still list CL32B106KBJNNNE, 74438357068 and
  74438357082 with `L_Wuerth_MAPI-4030`. Regenerate it with `kc 'python3 gen/bom.py'` after circuit.py is fixed.
- **Impact.** Ordering from these CSVs buys 3.1 mm inductors and 2.7 mm caps for the bottom side, which is the G3-01/G3-04 violation
  again.
- **Fix.** Apply the corrected rows below.

#### Corrected rows: `bom/F405FC_digikey_bom.csv` format

```
"<verify: 445-xxxx-1-ND for C3225X7S2A475K200AB>","C3225X7S2A475K200AB","TDK Corporation","13","C1 C2 C3 C10 C11","CAP CER 4.7UF 100V X7S 1210 2.0MM (replaces CL32B106KBJNNNE / GRM32DR71H106KA01L)"
"<verify in BOM Manager; fallback 732-11317-1-ND = 78438356056>","74438356056","Wurth Elektronik","5","L1 L2","FIXED IND 5.6UH 2.8A 81 MOHM SMD 4020 2.1MM (replaces 74438357068 + 74438357082)"
"P34.8KLCT-ND","ERJ-2RKF3482X","Panasonic","14","R3 R8","RES 34.8K OHM 1% 1/10W 0402"
"P24.3KLCT-ND","ERJ-2RKF2432X","Panasonic","12","R5","RES 24.3K OHM 1% 1/10W 0402"
"256-W25N01GVZEIGTRCT-ND","W25N01GVZEIG TR","Winbond","2","U10","IC FLASH 1GBIT SPI NAND 8WSON 8x6"
```

Delete the 732-11204-1-ND and 732-11205-1-ND rows and the 1276-3387-1-ND row.

#### Corrected rows: `bom/digikey_bom_costed.csv` (changed lines only; qty = 2 boards + spares)

| MPN | DigiKey PN | Qty/board | Order qty | Unit USD | Extended USD | Basis |
|---|---|---|---|---|---|---|
| C3225X7S2A475K200AB (TDK) | 445-6042-1-ND **(verify)** | 5 | 13 | 1.24 | 16.12 | @1, DigiKey snippet |
| 74438356056 (Würth) | **not confirmed** (alt. 732-11317-1-ND / 78438356056) | 2 | 5 | 1.70 | 8.50 | est. (old 4030 row price; no 4020 price seen) |
| C0402C829C5GACTU (KEMET) | 399-C0402C829C5GACTUCT-ND | 2 | 14 | 0.14 | 1.96 | @1, DigiKey snippet |
| ERJ-2RKF3482X (Panasonic) | P34.8KLCT-ND | 2 | 14 | 0.10 | 1.40 | @1, DigiKey snippet |
| ERJ-2RKF2432X (Panasonic) | P24.3KLCT-ND | 1 | 12 | 0.11 | 1.32 | est. (unchanged) |
| W25N01GVZEIG TR (Winbond) | 256-W25N01GVZEIGTRCT-ND | 1 | 2 | 3.62 | 7.24 | @1, DigiKey MX snippet |
| ~~CL32B106KBJNNNE~~ | ~~1276-3387-1-ND~~ | – | 0 | – | −8.97 | removed |
| ~~74438357068~~ / ~~74438357082~~ | ~~732-11204-1-ND / 732-11205-1-ND~~ | – | 0 | – | −6.80 | removed |

**Corrected estimated total.** $167.56 − 8.97 − 6.80 − 1.40 − 7.52 + 16.12 + 8.50 + 1.96 + 7.24 = **$176.69** for 2 boards + spares.
The order quantity changes from 499 to 500. These are qty-1 snippet prices with an undated basis. The L1/L2 price is an estimate.

### G2R-04 MINOR: L1/L2 datasheet values confirmed, but power.md has three errors

The Würth datasheet for 74438356056 is quoted in search snippets of
`https://www.we-online.com/components/products/datasheet/74438356056.pdf`. I did not download the PDF.

| Parameter | Würth datasheet (snippet) | Catalog / distributor | power.md |
|---|---|---|---|
| L | 5.6 µH ±20 % @100 kHz/10 mA | same | 5.6 µH ±20 % ✓ |
| Isat 10 % | **2.65 A typ** | – | 2.65 A ✓ (it is a *typical* value, not a minimum) |
| Isat 30 % | **5.5 A typ** | 4.6 A "Isat" (Farnell 2543215, DigiKey catalog row; criterion unstated) | not stated |
| IR | I_RP,40K = **3.85 A** (IEC 62024-2, 40 mm/105 µm Cu) | 2.8 A Idc (RS 923-6208, DigiKey description) | 2.8 A ✓ (conservative) |
| RDC | **68 mΩ typ / 81 mΩ max** @20 °C | 81 mΩ max (RS) | 81 mΩ ✓ |
| Size | 4.1 ± 0.2 x 4.1 ± 0.2 x **2.1 max** | 4.1 x 4.1 x 2.1 | see below |
| Other | SRF 20 MHz typ, 80 V DC, −40…+125 °C, MSL 1, AEC-Q200 | | |

Corrections for power.md:

- **Line 526 (R9).** It still says "WE-MAPI Isat(10 %) 3.5 A / 3.35 A (snippets)". The correct figures are 2.65 A typ (10 %) and 5.5 A
  typ (30 %).
- **Lines 135 and 137.** They say "4.0 x 4.0" and "2.0 mm WE-MAPI 4020". The correct size is 4.1 x 4.1 x 2.1 mm max. That is still
  ≤ 2.5 mm.
- **Line 143.** At 2.0 A the peak is 2.48 A, which is only 7 % below the *typical* Isat(10 %). Note this, and note that the LMR38020 HS
  limit (2.6-3.8 A) drives the core into the 10-30 % roll-off region under overload. That is acceptable given the soft saturation and
  the 5.5 A 30 % point.

The D-19 current-limit floor uses −20 % L. It does not add the ≈10 % saturation droop at the 2.48 A peak, so the 1.78 A floor at 2.0 A
load is slightly optimistic. At the 1.71 A planned load the peak is about 2.2 A, below the knee, so the plan holds.

### G2R-05 MINOR: U10 DigiKey PN points at the listing being phased out

- **Old listing.** `W25N01GVZEIGCT-ND` belongs to DigiKey listing 7393545. DigiKey AU/UK pages for that listing say "no longer
  manufactured… will no longer be stocked once stock is depleted"
  ([DigiKey AU 7393545](https://www.digikey.com.au/en/products/detail/winbond-electronics/W25N01GVZEIG-TR/W25N01GVZEIGCT-ND/7393545)).
- **Current listing.** Listing 5803931 uses **256-W25N01GVZEIGTRCT-ND**, at $3.62 @1
  ([DigiKey MX 5803931](https://www.digikey.com.mx/en/products/detail/winbond-electronics/W25N01GVZEIG-TR/5803931)).
  Findchips cut-tape stock reads 19,840-80,667.
- **Lifecycle.** Findchips marks the part lifecycle "Obsolete".

Fix: use 256-W25N01GVZEIGTRCT-ND, buy now, and keep the documented W25Q128JVEIQ alternate.

### G2R-06 MINOR: circuit.py DigiKey fields not updated

- **Stale markers.** `design/circuit.py:56-57` (R24k3, R34k8) and `:217-218` (L) say "unconfirmed". `:74` says "(verify)".
- **Wrong PN.** `:375` U10 carries `W25N01GVZEIGCT-ND`.
- **Effect.** These fields flow into the schematic and the BOM.

Fix: set P24.3KLCT-ND and P34.8KLCT-ND, set U10 to 256-W25N01GVZEIGTRCT-ND, and apply the G2R-01 and G2R-02 outcomes. Then regenerate
the BOM.

### G2R-07 MINOR: LMR38020 DDA footprint has thin paste and fewer thermal vias than TI recommends

The geometry was measured from `lib/F405FC.pretty/TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA.kicad_mod` and on the board
(U1 B-side at (10.20, 25.60), U2 at (26.60, 24.60)). It was checked against `datasheets/lmr38020.pdf` DDA0008B "Example board layout"
and "Example stencil design" (rev 4214849/B 09/2025), and §9.5.1.1.

**Matches TI:**

- Signal pads are 8x 1.55 x 0.6 at ±2.7 (5.4 row pitch), P1.27, R0.05. On the board, U1 pads 1-4 are at x = 7.50 and pads 5-8 at
  x = 12.90.
- EP metal is 2.95 x 4.9 with a solder-mask opening of 2.71 x 3.4 (pad "9" B.Cu+B.Mask), and the 2.95 x 4.9 copper is B.Cu only.
- Vias are on TI's 1.3 mm grid: (±0.65, ±0.65/±1.95).

**D-18 changes are present on the board:**

- The EP and all 8 via pads carry `zone_connect 2` (solid). This closes G2F-04.
- The paste is three windows (0.355 / 0.5 / 0.355 x 3.4 at x = −1.1775 / 0 / +1.1775) that do not overlap the via rings. This closes
  G2F-03.

**Residual issues:**

1. **Paste coverage is about 45 %.** The windows total 1.21 x 3.4 = 4.11 mm² against 9.21 mm² of mask opening (44.6 %). TI's stencil is
   100 % (2.71 x 3.40 at 0.125 mm, and 83 % at 0.15 mm). Under 50 % risks a thin EP joint and a higher θJA than power.md assumes.
2. **Paste windows almost touch the exposed via rings.** The side windows span |x| 1.0-1.355 and the via copper reaches |x| 0.95, a gap
   of **0.05 mm**. The centre window edge is 0.10 mm from the via copper. The four inner vias at y = ±0.65 sit inside the B.Mask
   opening, so they are open on the paste side and tented on F (no F.Mask), and molten paste will still wick into them. TI note 10:
   "vias under paste be filled, plugged or tented".
3. **Via count is below TI's recommendation.** TI §9.5.1.1 (lmr38020.pdf, text line ~1525) says "Use a minimum 4 × 3 array of 10-mil
   thermal vias". The footprint has 8 (2 x 4) 0.3 mm vias.

**Fix (preferred)**

1. Specify IPC-4761 Type VII (filled and capped) vias for the U1/U2 EP in the fab notes.
2. Return to a single paste window of about 2.47 x 3.10 mm (TI's 0.15 mm table entry, about 83 %), or 4 windows of about 1.1 x 1.4.
3. Add a third via column (x = 0) to reach 12 vias.

**Fix (alternative).** Keep the current windows, but increase the window-to-ring gap to ≥ 0.15 mm and accept about 40 % coverage. Then
verify the EP temperature at the bring-up thermal gate.

### G2R-08 INFO: MAPI-4020 footprint matches the Würth land pattern

- **Footprint.** `Inductor_SMD:L_Wuerth_MAPI-4020` (KiCad 10 lib) has pads 0.98 x 3.7 roundrect at ±1.185. That gives an inner gap of
  1.39 and an outer extent of 3.35. Fab body 4.1 x 4.1, courtyard 4.6 x 4.6. Measured on the board: L1 pads at (13.415, 30.85) and
  (15.785, 30.85), L2 at (29.385, 30.80) and (27.015, 30.80), 0.98 x 3.70, B.Cu/B.Mask/B.Paste. This matches the library.
- **Würth land pattern.** Würth's WE-MAPI 4020 land pattern (sibling datasheet snippets for 744383560033 and 74438356033) is 3.7 / 1.39
  / 0.98 / 3.35, an **exact match**. The 74438356056 datasheet snippet confirms the same 4020 body and terminal dimensions
  (4.1 ± 0.2, 2.1 max, 1.25 ± 0.2, 2.4 ± 0.2, 0.45 ± 0.2). Its own land figure values were not seen verbatim.
- **Routing caution.** Würth marks a "restricted area: no vias and traces" under the body between the pads. The board has 0
  tracks and 0 vias today (checked), so add a rule-area keepout under L1/L2 before routing.

### G2R-09 INFO: 1210 footprint against the vendor land pattern

- **Footprint.** `Capacitor_SMD:C_1210_3225Metric` has pads 1.15 x 2.7 at ±1.475, a gap of 1.80 and an outer extent of 4.10. The board
  matches: C1 pads at (7.30, 30.075) and (7.30, 27.125), 1.15 x 2.70.
- **Murata.** Murata's GRM32 land table could not be retrieved, because murata.com is blocked and the snippets gave no 3.2 x 2.5 row.
- **TDK.** The TDK C3225 reflow land (Arrow-hosted TDK sheets) is PA 2.00-2.40 (gap), PB 1.00-1.20 (pad length) and PC 1.90-2.50 (pad
  width). The KiCad IPC-nominal land is 0.2 mm tighter in gap and 0.2 mm wider than TDK's range. That is acceptable for hand assembly,
  so no change is needed. Do not enlarge it further (Murata warns that oversized lands crack MLCCs).

### G2R-10 INFO: D-17 parts confirmed at DigiKey (snippets)

| Ref | MPN | DigiKey PN | Status / stock / price | Source |
|---|---|---|---|---|
| C36, C37 | C0402C829C5GACTU | 399-C0402C829C5GACTUCT-ND ✓ | Active, about 62,800, $0.14 @1, 17-week lead time | [DigiKey 2196986](https://www.digikey.com/en/products/detail/C0402C829C5GACTU/399-7813-2-ND/2196986) |
| R3, R8 | ERJ-2RKF3482X | **P34.8KLCT-ND** ✓ | Active, $0.10 @1, AEC-Q200, 15-week lead time | [DigiKey 192312](https://www.digikey.com/en/products/detail/panasonic-electronic-components/ERJ-2RKF3482X/192312) |
| R5 | ERJ-2RKF2432X | **P24.3KLCT-ND** ✓ | 12-week lead time; OEMsTrade ties D# P24.3KLCT-ND | [DigiKey 192243](https://www.digikey.com/en/products/detail/panasonic-electronic-components/ERJ-2RKF2432X/192243) |
| Q2 | NX7002AK,215 | 1727-1289-1-ND ✓ | UK 2,980 / US 8,478 / SI 27,950 | [DigiKey UK 4386095](https://www.digikey.co.uk/en/products/detail/nexperia-usa-inc/NX7002AK215/1727-1289-1-ND/4386095) |
| U10 | W25N01GVZEIG TR | see G2R-05 | | |
| C23, C39 | CL10B225KP8NNNC | 1276-1134-1-ND ✓ | 1,155,712 in stock, 31-week lead time | [DigiKey 3886792](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL10B225KP8NNNC/3886792) |

## Sources

- [RS 923-6208 (74438356056)](https://th.rs-online.com/web/p/surface-mount-inductors/9236208)
- [RS 163-8224](https://th.rs-online.com/web/p/surface-mount-inductors/1638224)
- [Farnell 2543215](https://be.farnell.com/wurth-elektronik/74438356056/inductor-5-6uh-2-8a-20-shielded/dp/2543215)
- [Würth datasheet 74438356056](https://www.we-online.com/components/products/datasheet/74438356056.pdf) (snippet only)
- [Würth 744383560033](https://www.we-online.com/components/products/datasheet/744383560033.pdf) (snippet only)
- [DigiKey BD9G101G-TR page](https://www.digikey.com/en/products/detail/rohm-semiconductor/BD9G101G-TR/BD9G101G-CT-ND/3947476)
- [DigiKey 78438356056](https://www.digikey.in/en/products/detail/w%C3%BCrth-elektronik/78438356056/6833655)
- [DigiKey GRM32ER71H106KA12L](https://www.digikey.com/en/products/detail/murata-electronics/GRM32ER71H106KA12L/2548481)
- [DigiKey GRM32DR71E106KA12L](https://www.digikey.com/en/products/detail/murata-electronics/GRM32DR71E106KA12L/586590)
- [TME GRM32DR71C106KA01L](https://www.tme.com/us/en-us/details/grm32dr71c106ka01l/mlcc-smd-capacitors/murata/)
- [DigiKey C3225X7S2A475K200AB](https://www.digikey.com/en/products/detail/tdk-corporation/C3225X7S2A475K200AB/2443520)
- [DigiKey C3225X7R1H106K250AC](https://www.digikey.com/en/products/detail/tdk-corporation/C3225X7R1H106K250AC/10413509)
- [DigiKey CL31B106KBHNNNE](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL31B106KBHNNNE/5961251)
- [TDK C3225 land (Arrow copy)](https://static6.arrow.com/aropdfconversion/a97c7865c23eed2108459b711842405cf3ada873/c3225x7r1a226k230ac.pdf)
- DigiKey pages linked in G2R-05 and G2R-10.
- Local: `datasheets/lmr38020.pdf` pages "Example board layout" and "Example stencil design" plus §9.5.1.1; `kicad/F405FC.kicad_pcb`;
  `/opt/kroot/usr/share/kicad/footprints/{Inductor_SMD.pretty/L_Wuerth_MAPI-4020,Capacitor_SMD.pretty/C_1210_3225Metric}.kicad_mod`.
