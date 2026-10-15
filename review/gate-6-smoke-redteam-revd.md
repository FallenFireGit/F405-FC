# Gate 6 red team, rev D: "this board will smoke at first power-up"

Reviewer: fresh adversarial Gate 6 review, 2026-10-15. Review only: the only file written is this report (not committed).

**Snapshot reviewed:** git `0524b43` (design files unchanged up to HEAD `5261224`, which adds only review files).
`kicad/F405FC.kicad_pcb` md5 `df8f70f5ec8f3499b7965f65a129a286` (unchanged from the start to the end of the review).
While I was working, other agents left uncommitted edits in the working tree: `docs/assembly_and_bringup.md`, `bom/bom_raw.csv`,
`design/circuit.py` (DigiKey PN text only) and `gen/pathfinder.py`. Findings are against the committed state. Where a working-tree
edit already addresses a finding, I say so.

All scripts and outputs are in `/opt/kroot/tmp/rt6d/` (inside the chroot: `/tmp/rt6d/`). Coordinates are board-relative mm
(file coordinates minus 100,100).

## Verdict: **FAIL** (conditional PASS once G6S-11 is fixed in the bring-up guide)

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 1 |
| MINOR | 4 |
| INFO | 5 |

I found nothing in the schematic, footprints or copper that puts a rail above a part's rating at first power-up:
- every regulator pinout matches its datasheet, on the PCB as well as in the schematic;
- both divider pairs give the intended voltages;
- the copper has no short between nets and no split net (independent geometric check, below);
- DRC and parity are clean;
- the shipped Gerbers are byte-identical to the board.

The single MAJOR is a procedure gap. When U4/U5 are fitted (step 2.1.8), the bring-up guide powers the LDOs for the first time at
full 5V_SYS, but the IMUs, flash and video switch were already soldered in A1. One plausible assembly fault then puts about 4.8 V
on 4.0 V-max parts.

| ID | Severity | Title |
|---|---|---|
| G6S-11 | **MAJOR** | First LDO power-up (step 2.1.8) is at full 5V_SYS with U6/U7/U10/U11 already fitted. An unsoldered U4 GND tab or a rotated/open-GND U5 puts ~4.8 V on 4 V abs-max IMUs and the flash |
| G6S-12 | MINOR | High-voltage copper 0.13-0.21 mm from low-voltage pads (tented vias). No rail-to-rail resistance check before power. The old G6S-06 VBAT via at U3 pin 32 is still there, now 0.205 mm away |
| G6S-13 | MINOR | L1/L2 part identity is inconsistent across files, and the WE-MAIA land pattern and ratings are unverified. The DigiKey BOM also has a duplicated output-cap line |
| G6S-14 | MINOR | No ESC-harness pin-order or polarity check in the guide. A swapped VBAT/GND harness is reverse polarity with no current limit |
| G6S-15 | MINOR | Guide consistency issues: header rule vs A1, bare-board check is to GND only, and Stage B part list and step numbering (partly fixed in the working tree) |
| G6S-16 | INFO | 10 V path to P3/J3 goes through 3 single 0.3 mm vias in series. Both FB taps hang off thin branches with vias (an open via means the rail runs away; bring-up catches it) |
| G6S-17 | INFO | P1 (VBAT, bottom, bare copper) is 3.00 mm from the H3 centre: a metal M3 nut (r ≈ 3.2 mm) overlaps it. Covered only by the guide's "nylon" rule |
| G6S-18 | INFO | Bench 100 mA limit vs both soft-starts at once (estimate ~110-140 mA input at 6.5 V): may false-trigger the "in current limit" stop rule |
| G6S-19 | INFO | Stale documents and metadata: power.md (In2 vs In3, BAT54S, rev B), schematic rev "C", .kicad_pro without circuit.py's ERC rules, working-tree guide claims "FRONT" silk that is not on the PCB |
| G6S-20 | INFO | Accepted risks restated: no reverse-polarity protection, U1/U2 high-side short, R41 back-drive, J3/J4 both 6-pin SH (GPS into J3 = 10 V) |

---

## Status of the earlier (4-layer) findings, `review/gate-6-smoke-redteam.md`

| Old ID | Status on rev D | Evidence |
|---|---|---|
| G6S-01 GND islands (BLOCKER) | **Fixed** | `geo.py` (independent geometric union of all copper, any net, per layer; via barrels joined): 4250 items, **0 shorts, 0 split nets, 0 pad-less copper clusters**, both as filled and after an in-memory refill. KiCad connectivity (`conn.py`): 0 unconnected, 0 multi-cluster nets. DRC (`--refill-zones`): 0 unconnected |
| G6S-02 first power at 8.4 V (MAJOR) | **Fixed** | Guide §2 now: A1 leaves D5/U4/U5 off; step 0 checks R4/R5/R9/R10 in circuit; step 1 is at 6.5 V with stop criteria; step 4 is the 10 V window. The residual gap on the LDO side is new finding G6S-11 |
| G6S-03 VBAT pour in H3 keepout (MAJOR) | **Fixed** | `zones.py`: every `HOLE_KEEPOUT_*` has `noPour True` on all 6 layers. `holes.py`: the closest copper of any net is 2.28 mm from each hole centre (0.68 mm from the 3.2 mm wall); VBAT In3 is also at 2.28 mm from H3 |
| G6S-04 10 V on 0.5 oz In2 (MAJOR) | **Fixed (layer); vias open** | `widths.py`: 10V is only on F.Cu/B.Cu (0.45-0.8 mm), and VTX_PWR is F.Cu 0.45 mm. The "≥ 2 vias per layer change" part was not done, see G6S-16 |
| G6S-05 5 V trunk 0.35 mm / on In1 (MINOR) | **Mostly fixed** | 5V is no longer on a GND plane. The only inner 5V copper is the FB-sense branch on In3 (7.7 mm, ~0 A). The trunk is still 0.35 mm on B.Cu (9.8 mm, (25.24,30.21)-(15.71,32.54)), about +12 °C at 1.2 A by IPC-2221 external. Acceptable |
| G6S-06 VBAT vias in/near pads (MINOR) | **Partly fixed** | Via in U2 pin 3 and via in J2 pin 1 are gone (`prox.py`). VBAT via (20.60,24.45) is now **0.205 mm** from U3 pin 32 (3V3), previously 0.28 mm. Carried into G6S-12 |
| G6S-07 stage lists (MINOR) | **Fixed** | Stage B lists R14/R15/R16. TP5 continuity check added. TP5 is now in the single GND cluster |
| G6S-08 P3/P4 LED GND (MINOR) | **Fixed** | Silk "10V" at (34.2,20.8) and "GND" at (34.2,29.2) beside P3/P4 (`txt.py`). Guide §5 warns about it |
| G6S-09 stale docs (INFO) | **Open** | See G6S-19 |
| G6S-10 accepted risks (INFO) | Unchanged | See G6S-20 |

---

## Findings

### G6S-11 MAJOR: the first LDO power-up already has the IMUs, flash and video switch on the rails

**Evidence.**
- `docs/assembly_and_bringup.md`, committed version, line 7: "the MCU (U3) and the sensors are fitted only after every power rail has
  been checked". But A1 (lines 48-55) reflows U6 (ICM-42688-P), U7 (BMI270), U10 (W25N01GV) and U11 (TS5A3159A) together with the
  bucks. That ordering is needed, because those parts cannot be hot-aired later (D-26 M-2).
- Step 2.1.8 then fits D5, U4 and U5 by hot air or iron, and repeats steps 1-3 **at 8.4 V**. That is the first time 3V3 and 3V3_IMU
  are ever powered, and their loads are already soldered. There is no pre-power check of U4/U5.
- Pinouts are correct (`pads.txt`, `lp38692.pdf` §5 NDC: 1 EN, 2 N/C, 3 OUT, 4 IN, 5 tab = GND; `lp5907.pdf` Fig. 4-3 DBV: 1 IN,
  2 GND, 3 EN, 4 N/C, 5 OUT). So the risk is assembly, not design:
  - **U4 LP38692MP:** its **only** GND connection is the SOT-223 tab (pad 5, 1.8 x 3.4 mm at (24.30,4.05), B.Cu). That tab is poured
    into a board with GND planes on In1 and In4 and pours on F/In2/In3/B. With an iron or local hot air (as the guide prescribes),
    an unwetted tab is a realistic defect. An LDO with an open ground loses regulation, and the output heads toward VIN, here 5V_SYS ≈
    4.76 V.
  - **U5 LP5907 (SOT-23-5):** it is symmetric enough to be placed rotated by hand, or pin 2 (GND) can be left open. In both cases
    3V3_IMU can reach ≈ 4.7 V.
- Ratings exceeded in that case:
  - ICM-42688-P VDD/VDDIO abs max **4 V** (`ICM-42688-P_DS.pdf` line 829 of the text extract);
  - BMI270 VDD/VDDIO abs max **4 V** (`BMI270_DS.pdf` text line 799);
  - W25N01GV is a 3.6 V-max part (abs max not verified, datasheet not on file).
- The 100 mA bench limit is on VBAT, behind two conversions. It does not limit a 4.7 V LDO output into a few mA of CMOS load.

**Fix (guide only).** Insert before step 2.1.8 powers anything:
1. Unpowered DMM checks after fitting U4/U5:
   - U4 tab (pad 5) to P2: < 1 Ω;
   - U5 pin 2 to P2: < 1 Ω;
   - 5V_SYS to 3V3 and 5V_SYS to 3V3_IMU: not < 1 kΩ;
   - inspect U5's pin-1 mark against the silk.
2. **First LDO power from the bench, not from the buck.** Feed 5V_SYS directly at J5 pin 1 (or C19) with **3.6 V, 30 mA limit**,
   battery input off. D5 blocks any back-feed into 5V.
   - Check that 3V3 and 3V3_IMU are each ≤ 3.6 V, about 3.3-3.5 V.
   - Then raise to 5.0 V and check 3.25-3.35 V on both.
   - Only then fit/enable D5 and repeat at 8.4 V on VBAT.

   With 3.6 V in, no LDO fault can exceed the IMUs' 4 V limit.
3. Reword the line-7 rule: "...the MCU and the **top-side** sensors... The bottom-side IMUs/flash are protected by the 3.6 V
   first-power step".

### G6S-12 MINOR: high-voltage copper very close to low-voltage pads; no rail-to-rail check before power

**Evidence.**
- `prox.py`, outer layers, edge-to-edge distance; vias are tented on both sides (`F405FC.kicad_pcb` setup: `tenting front yes / back
  yes`). DRC is clean at 0.127 mm, so these are solder-bridge or mask-defect risks, not rule violations.

| Copper | Next to | Gap | Consequence of a bridge |
|---|---|---|---|
| VBAT via (20.60,24.45), F.Cu | U3 pin 32 (3V3) | **0.205 mm** (old G6S-06: 0.28) | VBAT on 3V3: MCU, flash, sensors |
| VBAT via (21.40,24.05), F.Cu | U3 pin 32 (3V3) | 0.226 mm | same |
| 3V3 via (21.41,23.06), B.Cu | C11 pad 1 (VBAT, 1210) | **0.154 mm** | same; C11 is hot-plate reflowed with a stencil |
| VBAT via (22.69,22.89), B.Cu | U2 pin 4 (RT_10V, 5.5 V abs max) | **0.138 mm** | U2 destroyed; a resulting high-side short puts VBAT on 10V |
| 5V via (11.41,30.16) / (9.26,30.11), F.Cu | R14 pad 1 (VBAT) / pad 2 (VBAT_ADC) | 0.148 / 0.145 mm | VBAT on 5V → 5V_SYS → LDOs/RX/U12 |
| VBAT via (16.79,30.89), B.Cu | L1 pad 2 (5V) | 0.213 mm | same |
| MOTOR4 via (21.46,22.29) / MOTOR1 via (20.56,32.01) / ESC_TLM via (19.56,32.41) | C11.1 VBAT / C16.1 10V / C6.1 5V | 0.143 / 0.152 / 0.128 mm | VBAT/10V/5V on an MCU pin |
| USB_DM via (25.10,15.67), F.Cu | U13 pin 5 (VBUS) | 0.139 mm | 5 V on D- |
| BUZ_N via (12.46,29.94), B.Cu | L1 pad 1 (SW_5V, swings to VBAT) | 0.163 mm | SW node on the PMV40UN2 drain (30 V) |

- The guide's checks before first power (§1 bare board, §2.1 step 0) measure rails **to GND only**. None of the bridges above shows up
  as a short to GND.

**Fix.**
1. Guide, before step 2.1.1 and again before Stage B power: DMM checks that read > 100 kΩ (or the expected divider value) for
   VBAT↔5V, VBAT↔3V3, VBAT↔RT_10V (U2 pin 4), 5V↔3V3, 10V↔5V, VBAT↔J2 pins 3-8. Also add a magnified inspection of the listed spots.
2. Next spin: move the (20.60,24.45)/(21.40,24.05) VBAT vias ≥ 0.3 mm from the LQFP row, the 3V3 via (21.41,23.06) off C11, and the
   VBAT via (22.69,22.89) off U2 pin 4. Keep POFV ordered: it caps these vias.

### G6S-13 MINOR: L1/L2 part identity is inconsistent, and the land pattern is unverified

**Evidence.**
- Schematic and PCB fields (`design/circuit.py:218-219`, `kicad/power.kicad_sch` MPN property): **78438356056** (WE-MAIA, DigiKey
  732-11317-1-ND).
- Order file `bom/F405FC_digikey_bom.csv`: **74438356056** (WE-MAPI) with an empty DigiKey PN.
- `bom/bom_raw.csv` (committed): 74438356056. The uncommitted working-tree edit changes it to 78438356056.
- `bom/digikey_bom_costed.csv:27` itself says: "land pattern vs the WE-MAPI 4020 footprint NOT verified".
- The footprint is `Inductor_SMD:L_Wuerth_MAPI-4020`: pads 0.98 x 3.70 mm on 2.36 mm centres.
- No Würth datasheet is on file, so Isat, IR and DCR are distributor snippets (power.md §2.2).
- Separately, `F405FC_digikey_bom.csv` lists the `1276-3047-1-ND` (C6-C8, C14-C16, 22 uF) line **twice**.

A wrong land pattern does not overvoltage anything; an open inductor fails safe. But L1/L2 are the parts that set the guaranteed
current limits (D-19).

**Fix.**
1. Choose one MPN.
2. Get the Würth PDF and check the land pattern against `L_Wuerth_MAPI-4020`, plus Isat(10 %) ≥ 2.3 A and IR.
3. Regenerate all three BOM files from `circuit.py`, and remove the duplicated line.

### G6S-14 MINOR: no ESC harness pin-order or polarity check

**Evidence.**
- J2 pinout is VBAT, GND, CURR, M1-M4, TLM (`circuit.py:429-433`, PCB `pads.txt`). The only silk is "ESC".
- 4-in-1 ESC harnesses ship in several pin orders.
- A harness with VBAT/GND swapped is reverse polarity fed straight from the battery, with **no current limit**: D1 forward plus both
  LMR38020 body diodes (power.md §1.1, no reverse protection).
- VBAT on M1-M4 or TLM goes straight to an MCU pin, because only CURR has a series 10 k.
- Guide §5 only asks to "check the ESC harness current rating".

**Fix.**
- Add to §5 / Stage C: "Before plugging J2, check the harness pin order against VBAT-GND-CURR-M1-M4-TLM with a DMM on the ESC side.
  Make the first connection to the battery through a smoke stopper or fuse."
- Optional for the next spin: pin-1 "+" silk at J2.

### G6S-15 MINOR: bring-up guide consistency

**Evidence (committed guide).**
- **Header rule vs A1.** Line 7 says the sensors are fitted after the rails are checked, but A1 fits U6/U7/U10 (see G6S-11).
- **Bare-board check.** §1 checks VBAT, 5V, 10V, 5V_SYS, 3V3, VBUS and SW to GND. It does not check 3V3_IMU, 3V3A, VTX_PWR, or any
  rail-to-rail pair.
- **Stage B parts.** Stage B omits:
  - R17 (PB2/BOOT1 pull-down): ROM DFU needs BOOT1 = 0;
  - R34/R35 (CC 5.1 k): a C-to-C host gives no VBUS without them;
  - R36/C51.

  They fall under Stage C "remaining top passives", but DFU happens in Stage B.
- **Step numbering.** §2.1 goes from step 8 to step 10, while the A1 text points to "step 2.1.9".

The working-tree edit (uncommitted, by another agent) already adds R17/R19/R34/R35/R36/C51 to Stage B, adds the DMM checks of
BOOT0/PB2/CC, and fixes the step reference.

**Fix.** Commit that edit, and add the G6S-11 and G6S-12 checks.

### G6S-16 INFO: 10 V path through single vias; feedback taps on thin branches

**Evidence** (`segs.py 10V`, `segs.py 5V`):
- L2/C14/C16 reach C15 only through F.Cu, via (26.11,31.89) → (31.36,29.54), and then via (32.74,27.59) to P3.
- J3 is fed P3 → F.Cu 9.9 mm → via (31.56,11.64) → B.Cu → via (23.66,8.49) → R41.
- So up to 1.3 A crosses **three single 0.3 mm vias in series**. That is about a 0.5 mm 1 oz trace equivalent each, which is
  thermally OK by estimate but has no redundancy.
- FB_10V (R9.1) taps 10V at via (32.73,21.85), downstream of those vias.
- FB_5V (R4.1) taps 5V through via (11.41,30.16) → In3 → via (14.84,24.39).
- An open via in either chain is equivalent to "top FB resistor open": the output runs toward VIN. Bring-up steps 1 and 4 catch a
  fab-open via; a field crack would not be caught.

**Fix (next spin).** Use two vias at each 10V layer change, and tap R4/R9 directly at C8/C15 on the same layer.

### G6S-17 INFO: P1 near H3

**Evidence.** `holes.py`: P1.1 (VBAT, B.Cu bare pad) is 3.00 mm from the H3 centre, and D4.2 (VBUS) is 3.12 mm from H2. A steel M3
nut (6.35 mm across corners, r ≈ 3.18 mm) overlaps P1. The guide §0 requires nylon hardware, so this is accepted. Keep that warning
in the user notes (§5) as well, not only in the tools list.

### G6S-18 INFO: bench limit vs simultaneous soft-start (estimate)

At 6.5 V the two bucks start together, because their EN dividers are identical.

Output charging over the 4 ms soft start (§8.3.9):
- 5V: ≈ 42 uF x 5.1 V / 4 ms ≈ 54 mA out;
- 10V, in dropout: ≈ 36 uF x 6.3 V / 4 ms ≈ 57 mA out.

That is ≈ 110 mA at the input, plus FPWM switching current. It can touch the 100 mA limit for a few ms, so the step-2 rule "if it hits
the limit, switch off" may false-trigger.

**Fix.** Say "steady state" in the stop rule, or use a 150 mA limit with the 6.5 V start (a runaway is still bounded by the 6.5 V input).

### G6S-19 INFO: stale documents and metadata

- `design/power.md`:
  - §5 (line 243) still says the VBAT zone is "on In2". On the board it is on **In3.PWR**; the zone is still named `VBAT_In2`
    (`zones.py`).
  - §10.2 and the §13 D7/D8 row still describe the removed BAT54S clamps.
  - Line 1 says "rev B". §12 thermal vias go "into L2 GND".
- `circuit.py:23` has `rev="C"`, so the schematic and netlist header say rev C on a rev D board.
- Committed `kicad/F405FC.kicad_pro` has no `erc.rule_severities` block, although `circuit.py:521-531` writes one (pcbnew re-saved
  the project). I re-ran ERC on a regenerated copy with the strict rules: **0 violations**, so nothing is hidden today.
- The working-tree guide edit says the board front is "marked 'FRONT' with an arrow on both silk layers". **No such text exists on the
  PCB** (md5 above; `txt.py` lists every board text). Do not commit that sentence without the PCB change.

### G6S-20 INFO: accepted risks, restated

- No reverse-polarity protection (power.md §1.1).
- U1 high-side short puts VBAT on 5V/5V_SYS, with no OVP (power.md R12).
- U2 high-side short puts VBAT on 10V and its 25 V caps (R7).
- R41 fitted with a VBAT-powered VTX back-drives U2 (D-11/D-16).
- J3 (10 V) and J4 (GPS, 5 V) are both 6-pin JST-SH. A GPS plugged into J3 gets 10 V. J3's warning silk is on the back only (D-15).

---

## Checked and OK (with evidence)

**DRC, parity, ERC, fab outputs**
- `kicad-cli pcb drc --schematic-parity --severity-all` on the repo board: **0 errors, 0 unconnected, 0 parity**. The 17 warnings are
  16 `via_dangling` on signal nets and 1 silk overlap (C44/U8) (`d.json`). The only DRC exclusions are the documented
  `ignored_checks` (courtyard, track-not-centred, filters, type, tuning); `.kicad_dru` only relaxes J1 shell spokes.
- Same DRC with `--refill-zones` on a copy: 0 errors, 0 unconnected, 0 parity (`d2.json`). Its extra lib warnings come from the copy
  location only.
- ERC (repo): 0. ERC with circuit.py's strict rules on a regenerated copy: 0.
- **Schematic = circuit.py:** I regenerated the schematic from `design/circuit.py` in a copy (`/tmp/rt6d/repo`) and exported the
  netlist. All 154 components have identical value, footprint and pin→net maps to the committed schematic (`comps.json` vs
  `comps_regen.json`).
- **Gerbers = board:** re-exported F/In1-In4/B copper, both masks and both pastes with `--use-drill-file-origin`. All are **identical**
  to `fab/F405FC_JLC_gerbers.zip`, apart from timestamps.

**Copper connectivity (independent of KiCad's ratsnest)**
- `geo.py` unions every pad, track, via (barrel across layers) and filled-zone island by physical contact per layer, ignoring nets.
  - 0 clusters contain more than one net, so there is no short between any two nets, power or signal.
  - Every net's pads form one cluster.
  - There is no floating copper.
  - The same result holds after an in-memory zone refill.
  - Sanity test: injecting one B.Cu track from U2 pin 3 to its EP produced a `SHORT [EN_10V, GND, VBAT]` report.
- Zones: GND on all 6 layers, plus VBAT on In3.PWR at priority 2 with 0.2 mm clearance. Hole keepouts forbid tracks, vias and pours.
  The L1/L2 under-body keepouts are on B.Cu.

**Regulators: pinout vs footprint vs datasheet** (`pads.txt`, netlist `comps.json`)

| Part | PCB pads → net | Datasheet |
|---|---|---|
| U1/U2 LMR38020 (custom DDA, bottom) | 1 GND, 2 EN, 3 VIN=VBAT, 4 RT, 5 FB, 6 PG open, 7 BOOT, 8 SW, 9 EP + 8 thermal vias = GND. Pin 1 at (7.50,27.50)/(23.90,26.50); pin 5 is opposite pin 4, CCW seen from the part side | `lmr38020.pdf` Table 6-1 |
| U4 LP38692MP-3.3 (SOT-223-5) | 1 EN=5V_SYS, 2 NC, 3 OUT=3V3, 4 IN=5V_SYS, 5 tab=GND. Leads at 1.5 mm pitch, tab 6.3 mm from the lead row | `lp38692.pdf` §5 and NDC0005A land pattern (p. 31: 1.5 pitch, 6.3) |
| U5 LP5907MFX-3.3 (SOT-23-5) | 1 IN, 2 GND, 3 EN (=IN), 4 NC, 5 OUT=3V3_IMU | `lp5907.pdf` Fig. 4-3 |
| U3 STM32F405RGT6 | 1 VBAT, 12 VSSA, 13 VDDA, 18/63 VSS, 19/32/48/64 VDD, 31/47 VCAP, 60 BOOT0, 7 NRST | `st_open_pin_data/F405RGTx.xml` |
| U6 ICM-42688-P | 1-4 left, 5-7 bottom, 8-11 right, 12-14 top. Columns ±1.16, rows ±0.91 (datasheet 2X 1.1625 / 2X 0.9125); 4-pin sides along the 2.5 mm edge (E = 3 horizontal); VDD 8 / VDDIO 5 = 3V3_IMU; GND 6/7 | `ICM-42688-P_DS.pdf` Fig. 4 and p. 54 |
| U7 BMI270 | same layout; 8 VDD, 5 VDDIO, 6/7 GND | `BMI270_DS.pdf` §7.1, §8.3 (p. 145) |
| U8 BMP390 (top) | 1 VDDIO (right of 2), 3/4/5 left, 6/7 bottom, 10/9/8 right; VDD/VDDIO/CSB = 3V3, SDO/VSS = GND | `BMP390_DS.pdf` Fig. 23/26 |
| U11 TS5A3159A | 1 NO, 2 GND, 3 NC, 4 COM, 5 V+, 6 IN | `TS5A3159A_DS.pdf` Pin Functions |
| Q1 PMV40UN2, Q2 NX7002AK | 1 G, 2 S, 3 D | Nexperia pinning tables |
| D1/D4/D5/D9 | pad 1 = K: D1.1 VBAT, D4.1/D5.1 5V_SYS, D9.1 5V. **Silk cathode bar is on the pad-1 side** for D1/D4/D5/D9/D10/D11/D12 (`silk2.py`) | `PMEG4030ER.pdf` (pin 1 = K, bar = cathode) |

**Set points and ratings**
- **Bucks:**
  - VREF 1.000 V (0.985-1.015) (`lmr38020.pdf` §7.5). 100 k/24.3 k gives **5.115 V**; 100 k/11.0 k gives **10.09 V**. Netlist: R4
    5V→FB_5V 100K, R5 FB_5V→GND 24.3K, R9 10V→FB_10V 100K, R10 FB_10V→GND 11.0K.
  - RT 34.8 k (R3/R8).
  - EN 301 k/100 k: VON 4.41-5.61 V. At 6.5 V, EN = 1.62 V > 1.4 V max. EN abs max is VIN + 0.3 V; 10.5 V on EN at the 42.1 V clamp is
    fine.
  - BOOT-SW 5.5 V on a 16 V cap. PG left open, allowed by Table 6-1.
- **VBAT, at the 42.1 V SMBJ26A clamp:**
  - C1 50 V; C2/C3/C10/C11 100 V; C4/C12 100 V;
  - R1/R6/R14 are 0603;
  - LMR38020 VIN/SW 85 V; Q2 60 V (EN_10V ≤ 10.5 V).
  - TVS VWM 26 V ≥ 25.2 V (6S).
- **Lower rails:**
  - 10V caps 25 V (C17 100 V); 5V caps 16-25 V; 5V_SYS 16-25 V; VBUS 25 V; 3V3/3V3_IMU 10-16 V;
  - LP38692 IN ≤ 5.3 V (12 V abs max); LP5907 IN ≤ 5.3 V (6 V abs max);
  - U12 VCC ≤ 5.28 V (7 V);
  - D4/D5/D9 reverse ≤ 5.3 V (40 V); Q1 drain ≤ 5.5 V (30 V).
- **VBAT_ADC:** 25.2/11 = 2.29 V. At 42.1 V the injection is ≈ 0.25 mA (power.md §1.1), under 5 mA.

**Back-feed and hot-plug paths** (netlist)
- USB only: VBUS → D4 → 5V_SYS → U4/U5/J5. D5 blocks 5V (so no path into U1 → VBAT); 5V and 10V stay unpowered.
- Battery: D4 blocks 5V_SYS → VBUS.
- 10V has no node shared with 5V or VBAT (pads: R41, P3, C14-C17, L2, R9).
- VBUS carries the USBLC6 clamp plus the 100 k bleeder.
- Battery hot-plug: the TVS clamps the ceramic-only LC ring below the 50 V/85 V ratings. The external electrolytic is documented.

**Guide vs PCB sides** (`sides.py`): every A1 part is really on the bottom; D1/C1/R41/D4 are top; D5/U4/U5 are bottom. The Stage B part
list matches the PCB sides. R7.1 (EN_10V) is 0.350 mm from the J1 shell, as the guide states.

**Mechanical:** the guide's "P1/D1/D4 3.0-3.4 mm from hole centres" matches `holes.py`. The holes are NPTH, with no annular ring.

## Not verified

- **Datasheets not on file, so not read:**
  - SMBJ26A (VBR/VC from power.md);
  - Würth 74438356056 / 78438356056 (Isat, IR, DCR, land pattern; G6S-13);
  - TDK C3225X7S2A475K200AB DC bias;
  - SN74LV1T125; USBLC6-2SC6; IIS2MDC/LIS2MDL (pinout taken from the KiCad `Sensor_Magnetic:LIS2MDL` symbol only; C1 on pin 5 is
    consistent);
  - W25N01GV abs max; LTST-C191 LED polarity marks; Yageo resistor voltage ratings.
- **Silkscreen pin-1 marks** for the symmetric packages (U5, U7, U9, U11, U12, U13): my proximity heuristic was inconclusive. Diode
  bars and U1/U2/U3/U4/U8 marks were checked.
- **Thermal:** trace and via temperature rises are IPC-2221 estimates only, with no IPC-2152 or simulation. Buck/LDO thermals were not
  re-derived.
- **The soft-start input-current estimate** (G6S-18): order-of-magnitude only.
- **Physical stackup** (JLC 6-layer dielectric) and **POFV availability**: not checked.
- **Hardware:** none exists. No measurement was made.
- **Working-tree edits by other agents** (guide, bom_raw, circuit.py field text, pathfinder): read but not reviewed beyond what is
  noted in G6S-13, G6S-15 and G6S-19.
