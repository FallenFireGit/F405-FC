# Gate 1 review: netlist, ERC and tooling

Reviewer: independent Gate 1 schematic reviewer (netlist / ERC / tooling). Date: 2026-10-11.
Scope: `design/circuit.py`, `gen/schgen.py`, `gen/symlib.py`, `gen/netcheck.py`, `kicad/` (project, schematics, lib tables), `lib/F405FC.kicad_sym`, `lib/F405FC.pretty`, `design/pinmap.md` section 9.
Toolchain: KiCad 10.0.6 (`kc` chroot), pcbnew Python, kicad-cli.
I did not touch the `.kicad_pcb`. Only this report was written. Running `circuit.py` and `netcheck.py` rewrites `kicad/F405FC.kicad_pro` and `kicad/F405FC.net`, as the tooling is designed to. Temporary audit scripts ran from the scratchpad (piped into `kc 'python3 -'`) or from chroot `/tmp`.

**Concurrent change during review.** The lead changed `FP["HOLE"]` to `F405FC:MountingHole_3.2mm_M3_Grommet4.6mm` and regenerated the schematic while this review was running. I re-validated that state in an isolated chroot copy (`/tmp/g2`: design, gen and lib copied, schematic regenerated). netcheck passed, ERC showed 0 violations, and the regenerated `*.kicad_sch` files are byte-identical to the working tree. The new footprint loads and has one unnamed NPTH pad, which is correct for a symbol with no pins. The results below hold for that state.

## 1. Commands run and results

| # | Command | Result |
|---|---|---|
| 1 | `kc 'python3 design/circuit.py'` | `parts=168 nets=93 sheets=5`, exit 0 (168 = 161 real parts + 7 `#FLG`) |
| 2 | `kc 'python3 gen/netcheck.py'` | `model pins=467 exported pins=467 nets=109 parts=161`, `netcheck: OK`, no single-pin nets printed (109 = 93 named + 16 `unconnected-*`) |
| 3 | `kc 'cd kicad && kicad-cli sch erc --severity-all --format report -o /tmp/erc.rpt F405FC.kicad_sch && cat /tmp/erc.rpt'` | `ERC messages: 0  Errors 0  Warnings 0`. Sheets checked: `/`, `/Power/`, `/MCU/`, `/Sensors/`, `/Video/`, `/Connectors/` |
| 4 | Ran `circuit.py` twice more, then `sha1sum -c` of all 6 `.kicad_sch`, `lib/F405FC.kicad_sym` and both lib tables; `git diff --stat` | All files OK (byte-identical to HEAD). The only diffs were `kicad/F405FC.kicad_pro` (see G1N-01) and the `kicad/F405FC.net` date line (G1N-05) |
| 5 | ERC rule test: copied the project to chroot `/tmp/g1`, injected one orphan `global_label "TEST_SINGLE"` into `video.kicad_sch`, ran ERC | `[single_global_label]` and `[label_dangling]` reported, 2 errors. The rule is active, not just present in the JSON |
| 6 | Independent netlist audit (my own s-expression parser on `kicad/F405FC.net`; pin names resolved against the netlist's own `libparts`, not `symlib.py`) | 0 errors. All 467 libpart pins of all 161 parts are present in exported nets and match the model. No extra nodes |
| 7 | MCU pins vs `design/pinmap.md` section 9 (64 rows) vs exported U3 nets | 64/64 match |
| 8 | `pcbnew.FootprintLoad` for every footprint (35 unique: stock `/usr/share/kicad/footprints` and `lib/F405FC.pretty`); symbol pin set vs numbered copper pad set, both ways | All 35 load. 161/161 parts match both ways. Unnamed pads are legitimate only: H* NPTH, J1 two NPTH pegs, U10 four paste-only apertures |
| 9 | `kicad-cli sch export bom --exclude-dnp` (isolated copy) | 159 rows (161 minus DNP R32 and R37). It includes 34 PCB pads, test points and holes (G1N-02) |

### Project ERC settings (`kicad/F405FC.kicad_pro` → `erc.rule_severities`)
`single_global_label: error`, `global_label_dangling: error`, `similar_labels: warning`, `unconnected_wire_endpoint: warning`, `lib_symbol_issues: warning`, `lib_symbol_mismatch: warning`, `footprint_link_issues: warning`. Everything else uses KiCad defaults.
The report's "Ignored checks" are the KiCad defaults:
- four connection points joined: irrelevant, since there are no wires
- SPICE model issue: irrelevant
- footprint does not match footprint filters: acceptable, because some parts deliberately use substitute symbols (Q1 PMV40UN2 on the 2N7002 symbol, U12 SN74LV1T125 on 74AHCT1G125, U9 IIS2MDC on LIS2MDL), and step 8 checked pin/pad numbering directly.

## 2. Checks passed

- **Netlist = model.** Every (ref, pin) → net matches `circuit.py`, confirmed by both the repo's netcheck and my independent comparison.
- **netcheck blind spots, audited:**
  - Stacked pins: `schgen.write` skips a second label at a shared position. KiCad still connects the pins by position, and a conflicting assignment would appear as a mismatch.
  - Hidden pins: `symlib.pins` includes them.
  - Multi-unit symbols: none are used. Every libpart pin (all units) is present in the export.
  - No pin is silently missing today. Latent gaps are listed in G1N-04.
- **Single-connection nets:** none (0 named nets with 1 node). 55 two-node nets, all point-to-point by design (MCU↔connector/pad, LED anode, RT/BST/VCAP, etc.).
- **Near-duplicate net names:** none after normalising case and punctuation. Similar-ratio pairs are intentional families: UARTn_TX/RX, SPI1/SPI3, GYRO1/2, CAM1/2, USB_CC1/2, UNUSED_*, 3V3/3V3A.
- **Power nets:** ERC `power_pin_not_driven` = 0.
  - 3V3 is driven by U4 OUT (power_out) and 3V3_IMU by U5 OUT (power_out).
  - PWR_FLAG sits on VBAT (battery pad), GND, 5V (via L1), 10V (via L2), 5V_SYS (D4/D5), VBUS (J1) and 3V3A (FB1). In every case the real source is a passive or connector pin, so no flag hides an undriven rail.
- **MCU pin map:** 64/64 match pinmap.md section 9.
- **Refdes:** 161 unique (`Circuit.add` also raises on duplicates). Gaps: D2, D3, D6 (cosmetic).
- **Sheet structure:**
  - Root contains 5 sheets: Power (`power.kicad_sch`, 60 symbols), MCU (32), Sensors (18), Video (15), Connectors (43). 168 symbols in total.
  - 16 no-connect markers, equal to the 16 `unconnected-*` nets.
- **BOM fields:** all 127 BOM parts (excluding the 34 InBOM=no pads, test points and holes, and #FLG) have non-empty MPN, Manufacturer, DigiKey and Datasheet. DNP is set on R32 and R37 (the 0R options).
- **Determinism:** schematic, symbol library and lib tables regenerate byte-identically.
- **Footprints:** all exist, and pin/pad numbering matches both ways (spot-checked LP38692 SOT-223-5: 1 EN, 2 NC, 3 OUT, 4 IN, 5 GND/tab, which agrees with the TI datasheet NDC table).

### NC pins (16): all legitimately unused

| Part | Pin | Justification |
|---|---|---|
| J1 USB4105 | A8 SBU1, B8 SBU2 | USB 2.0 only |
| U1, U2 LMR38020 | 6 PG | Open drain. Datasheet: "Can be left open when not used" |
| U4 LP38692MP | 2 NC | Datasheet N/C |
| U5 LP5907 | 4 NC | Datasheet N/C |
| U7 BMI270 | 2 ASDx, 3 ASCx | Datasheet footnote **: "can be connected to VDDIO or left unconnected. Do not connect to GND" |
| U7 BMI270 | 9 INT2 | Footnote *: "If INT1 and/or INT2 are not used, please do not connect them (DNC)" |
| U7 BMI270 | 10 OCSB, 11 OSDO | Table: "DNC or OIS CSB/SDO" |
| U8 BMP390 | 7 INT | Datasheet: "host INT input or DNC" |
| U9 IIS2MDC (LIS2MDL symbol) | 7 DRDY | Output, unused (polled) |
| U9 IIS2MDC | 2, 11, 12 NC | Symbol NC pins. ~CS (pin 3) is tied to 3V3 for I2C mode, which is correct |

### DigiKey PNs marked "(verify)" (11 distinct, for Gate 2)

| PN | Parts |
|---|---|
| 1276-1621-1-ND | CL05C100JB5NNNC: C36, C37 |
| 1276-1015-1-ND | CL05B103KB5NNNC: C40, C52, C53 |
| 1276-1255-1-ND | CL05A224KA5NNNC: C45 |
| 490-3285-1-ND | GRM188R72A104KA35D: C4, C12 |
| 1276-1102-1-ND | CL10A105KA8NNNC: C19, C22, C31, C47, C51 |
| 1276-1183-1-ND | CL10A225KO8NNNC: C23, C33, C34, C39 |
| 1276-1044-1-ND | CL10A475KO8NNNC: C18, C29 |
| 1276-2891-1-ND | CL21A106KAYNNNE: C20 |
| 296-LMR38020FSDDARCT-ND | U1, U2 |
| 732-74438357082CT-ND | L2 |
| 50-ECS-80-8-33-JEN-TR3CT-ND | Y1 |

## 3. Findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| G1N-01 | MINOR | Two generators write `kicad/F405FC.kicad_pro`, and whichever runs last wins. `schgen.write_project` / `circuit.enable_erc_rules` rewrite the whole file from scratch: `"board": {"design_settings": {}}` and Default netclass `track_width 0.127`. `gen/build_pcb.py` sets the board rules (min_track 0.127, min_clearance 0.127, edge 0.3, annular 0.15, via 0.6) and netclass track 0.15, and these also live in `.kicad_pro`. Running `circuit.py` after `build_pcb.py` silently discards the PCB rules (KiCad falls back to defaults, e.g. min_track 0.2 and edge 0.5) and resets the netclass track to 0.127. The netclass track width is also defined twice with different values (0.127 vs 0.15). | After my `circuit.py` run, `git diff --stat` showed `kicad/F405FC.kicad_pro` 342 lines (325 deletions). The file then contained only meta/net_settings/sheets/erc. HEAD and the lead's later build carry `board.design_settings.rules`. `build_pcb.py:69` sets `SetTrackWidth(mm(0.15))`; `circuit.py:527` sets `track_width: 0.127`. | `write_project` should load the existing `.kicad_pro` if present and update only `sheets`, `erc.rule_severities` and `meta`. Define the netclass values in one place (e.g. a dict in `circuit.py` imported by `build_pcb.py`). Alternatively, document a strict order: always `circuit.py` → `build_pcb.py` → DRC. |
| G1N-02 | MINOR | The `InBOM = "no"` marking on the 34 PCB pads, SWD test points and mounting holes is only a custom text field. Every symbol is written with `(in_bom yes)`, so KiCad's own BOM export (and any fab-house BOM generated from it) lists P1–P25, TP1–TP5 and H1–H4 as purchasable lines with no MPN. | `schgen._symbol_instance` hard-codes `[S("in_bom"), S("yes")]`. `kicad-cli sch export bom --exclude-dnp` gives 159 rows, of which 34 match `"(P\|H\|TP)[0-9]+"`, e.g. `"H1","M3","F405FC:MountingHole_3.2mm_M3_Grommet4.6mm","1",""`. | In `_symbol_instance`, emit `(in_bom no)` when `p.fields.get("InBOM") == "no"` (optionally also `(on_board yes)`). Re-check that the netlist `exclude_from_bom` property appears. |
| G1N-03 | MINOR | The Datasheet field for all Samsung MLCCs (51 placements, 10 MPNs) is a generic landing page (`https://product.samsungsem.com/mlcc/`), not a part-specific datasheet. The field is non-empty but does not identify the part's ratings (DC-bias derating matters for C10u_50V, C22u and C4u7). | `circuit.py:31` `SAMSUNG_DS`, used for every `CL*` entry in `CAT`. | Use per-MPN URLs (e.g. `https://product.samsungsem.com/mlcc/CL32B106KBJNNNE.do`), or the DigiKey product page, in Gate 2. |
| G1N-04 | INFO | Latent netcheck gaps. None is triggered in this design (my independent check found no instance). (a) `symlib.pins` keeps only the selected unit plus unit 0. If a multi-unit symbol had unplaced units, their pins would be missing from both the model and the KiCad export, and netcheck would not see it. (b) Single-pin nets are printed but do not fail. ERC `single_global_label=error` covers this, and I verified it by injection. (c) netcheck does not compare symbol pins to footprint pads, Value or BOM fields. | `gen/netcheck.py` lines 59–68: `singles` printed, no `raise`. `symlib.pins`: `if u not in (0, unit)`. | Optional: make single-pin nets fatal. Add a pin↔pad check (as in step 8) and an assert that every libpart pin of each placed part appears in the export. |
| G1N-05 | INFO | `kicad/F405FC.net` is tracked and is rewritten by every `netcheck.py` run with a new `(date ...)` line, so each check run dirties the tree. | `git diff kicad/F405FC.net` shows only `(date "2026-10-11T15:03:14")` → `(date "2026-10-11T19:14:38")`. | Export to a temp path or untrack/ignore the `.net` file, or strip the date line. |
| G1N-06 | INFO | The schematic is "labels on every pin" with no wires, so ERC here mostly proves label consistency and power-driver presence; it cannot catch wiring mistakes. Connectivity correctness rests on netcheck (model == export) and on the review of `circuit.py` itself. | 449 global labels, 0 wires across 5 sheets. | None needed for Gate 1. Reviewers must audit `circuit.py` connections (Gate 0 did this for the pin map). |
| G1N-07 | INFO | Substitute symbols: Q1 (PMV40UN2) and Q2 (NX7002AK) on `Transistor_FET:2N7002`, U12 (SN74LV1T125) on `74xGxx:74AHCT1G125`, U9 (IIS2MDC) on `Sensor_Magnetic:LIS2MDL`. Pin/pad numbering is verified and the pinouts agree with SOT-23 G/S/D = 1/2/3, SN74LV1T125 DBV and IIS2MDC LGA-12. The footprint-filter ERC check is ignored, so this is not flagged by tooling. | Netlist libsource vs MPN fields. | Acceptable. Optionally add a Description noting the substitution (U9 already has one). |
| G1N-08 | INFO | Refdes gaps D2, D3, D6. | Netlist component list. | Cosmetic. Renumber before release if desired. |

## 4. Verdict

**PASS** (no BLOCKER or MAJOR findings). The netlist is exactly the circuit model: 467/467 pins, 0 single-pin nets, 16 NC pins all justified. ERC is clean with `single_global_label` proven active. All footprints exist and their pin/pad numbering matches. BOM fields are complete, with 11 DigiKey PNs still marked "(verify)" for Gate 2.

Before layout freeze, fix G1N-01 (project-file clobbering) and G1N-02 (pads, test points and holes in the KiCad BOM).
