# F405-FC: review summary

Date 2026-10-15. This summary covers two boards built from the same circuit:

| Board | Where | Layers | Status |
|---|---|---|---|
| **Rev D** (recommended build) | branch `master` | 6 (F / In1 GND / In2 SIG / In3 SIG + VBAT / In4 GND / B) | DRC clean; Gate 4/5/6 reviewed; MAJOR fixes made; re-review results below |
| Rev C (fallback) | branch `rev-c` | 4 (JLC04161H-7628) | DRC clean; **Gate 4 re-review FAIL (6 MAJOR)**: not recommended |

The owner chose 6 layers on 2026-10-15 ("6 layer would be best"), kept 0.3/0.6 mm vias, and asked for the top side to be
re-planned (D-27). `design/requirements.md` and the brief still mention the 4-layer stackup in places; requirements.md now records
the change.

Every reviewer was a separate, fresh agent told to assume mistakes exist and to cite evidence. Nothing in this file claims a check
that was not run; the "Not verified" section lists what was not.

## 1. Rev D board state (master)

- `kicad-cli pcb drc --schematic-parity`: **0 errors, 0 unconnected, 0 parity**. Warnings: 16 dangling signal vias (unused MCU
  fanout vias; automatic trimming cut used stubs and was reverted, D-27) and 1 silk overlap (C44 bar touching U8's pin-1 mark).
- ERC 0 violations; `gen/netcheck.py` OK (circuit model == exported netlist); `gen/placecheck.py` PASS.
- In1 and In4 carry no tracks; each is one solid GND piece over ~82 % of the board (Gate 4 rev D).
- Outputs regenerated from the current board: `fab/` (6-layer Gerbers, drill, job, JLC zip, stencil, CPL), `bom/` (CSV, iBOM),
  `docs/` (schematic PDF, STEP, renders, assembly and bring-up guide), Betaflight config and INAV target.

## 2. Gate outcomes

| Gate | Report(s) | Outcome |
|---|---|---|
| 0 Pin map | gate-0-pinmap-audit, -reaudit | FAIL (1 MAJOR) -> re-audit **PASS** |
| 0 Power | gate-0-power-audit, -reaudit, -reaudit-2 | FAIL -> FAIL -> **PASS** |
| 1 Netlist/ERC | gate-1-netlist-erc | **PASS** |
| 1 Power integrity | gate-1-power-integrity | **PASS** (4 MINOR) |
| 1 Sensors/video | gate-1-sensors-video | **PASS** |
| 1 MCU/digital | gate-1-mcu-digital, -rereview, -rereview-2 | FAIL -> FAIL -> **PASS** |
| 2 Footprints | gate-2-footprints | NOT PASSED: G2F-01 open as a verification gap (IIS2MDC LGA land pattern from the LIS2MDL drawing; ST PDF not obtainable). Accepted as residual risk (D-18) |
| 2 Sourcing | gate-2-sourcing, gate-2-recheck | FAIL -> substitutions adopted (D-17, D-20); re-check FAIL items fixed in D-20 |
| 3 Placement | gate-3-placement, -rereview | FAIL -> FAIL (4 MAJOR) -> fixes in D-21. **No fresh Gate 3 re-review after D-21**; the rev D Gate 4/5/6 reviews covered the resulting board |
| 4 SI/PI | gate-4-si-pi (rev B) | FAIL -> led to rev C fixes and to the 6-layer rev D |
| 4 SI/PI rev C | rev-c: gate-4-si-pi-revc | **FAIL** (6 MAJOR) - rev C not fixed further (needs 6 layers) |
| 4 SI/PI rev D | gate-4-si-pi-revd, gate-4-si-pi-revd-rereview | FAIL (2 MAJOR: CURR_ADC detour, signals inside the buck footprints) -> fixed in 176113f -> re-review: see §3 |
| 5 DFM | gate-5-dfm (rev B), rev-c: gate-5-dfm-revc | FAIL -> fixes (D-26) -> rev C FAIL (2 MAJOR) -> fixed |
| 5 DFM rev D | gate-5-dfm-revd, gate-5-6-revd-recheck | FAIL (2 MAJOR: stale DigiKey upload BOM, guide part order) -> fixed in c1f81bb -> re-check: see §3 |
| 6 Smoke red team | gate-6-smoke-redteam, -revd | FAIL -> rev D FAIL (1 MAJOR, guide only: LDO first power) -> fixed in 176113f -> re-check: see §3 |
| 6 Betaflight red team | gate-6-betaflight-redteam, -revd | FAIL -> rev D FAIL (2 MAJOR: no front mark, DFU parts fitted late) -> fixed -> re-check: see §3 |

## 3. Rev D MAJOR fixes and their re-review

Re-reviews of the fixes are in progress (fresh agents); this section is filled in when they report.

## 4. DigiKey BOM cost

`bom/digikey_bom_costed.csv`: **$173.28 estimated for 2 boards plus spares** (53 lines; Gate 5 rev D checked unit x qty = extended
on every line). Prices are qty-1 cut-tape figures from dated web snippets (2026-10-11/12), some marked "est." where no price was
seen; quantity breaks will lower it. It excludes the PCB, stencil, shipping and tax. A 6-layer JLC board with epoxy-filled vias
costs considerably more than the 4-layer board; that price was **not** checked.

## 5. Residual risks (rev D)

Design / layout (from the rev D Gate 4/5/6 reports; MINOR unless noted):
- **Stackup undefined** in the board file; the job file carries KiCad's default. If JLC's 6-layer build has a thin core between
  In2 and In3, In2 signals reference In3 (VBAT zone, broadside coupling) rather than In1 (G4D-05). Pick the stackup at order time.
- VBAT neck to U2 0.64 mm on In3 (≈ 16 mΩ); 5 V east trunk 0.35 mm with a single via at ≈ 1.2 A (≈ +12 °C, IPC-2221 estimate);
  10 V feed to P3/J3 through single vias in series (G4-06/07/08, G6S-16).
- Inner-layer 5V copper (D-27 promise): one branch, **In3, 0.35 mm wide, 7.7 mm long**, from (11.41, 30.16) to the via at
  (14.84, 24.39) feeding R4 (the 5 V feedback divider, Gate 4: "5 V sense branch"). On 0.5 oz inner copper IPC-2221 gives about
  0.34 A for +10 °C; as a feedback-sense branch it carries microamps.
- USB D+/D- change layers separately; no VBUS cap at U13 (G4-09). Sparse edge GND stitching (G4-13).
- Decoupling paths: C26 (pin 48, 100 nF) 14 mm away (C20, 2.2 µF, is 2.4 mm away), flash cap C48 9.7 mm (G4D-04/08);
  3V3_IMU 26 mm on four layers (G4D-06); EN_5V between C4's pads (G4D-07); I2C1_SDA 0.14 mm from C36 (G4D-03).
- Vias of a higher-voltage rail 0.13-0.21 mm from lower-voltage pads (e.g. VBAT via 0.205 mm from U3 pin 32): pass DRC and are
  tented/filled, but a solder bridge there is destructive; the guide now adds rail-to-rail resistance checks (G6S-12).
- About 51 vias < 0.10 mm from same-net pads (15 in-pad): **POFV (epoxy filled, capped) vias are required**; availability on JLC
  6-layer boards not checked.
- No reverse-polarity protection; a U1/U2 high-side short puts VBAT on the 5 V/10 V rail; R41 back-drive; J3 (10 V) and J4 (5 V
  GPS) are both 6-pin (accepted risks, D-11/D-15, G6S-20). The guide adds an ESC harness pin-order check.
- Gyro alignment (U6 CW270FLIP, U7 CW0FLIP) derived on paper only; `align_mag` not derived (no IIS2MDC datasheet). Bench-verify.
- Silk: the top "FWD" arrow sits near the bottom-right corner (no room at the front edge on the top side); the P6 and J5 labels
  are ref-prefixed ("P6 C2", "J5 RX") because there is no legal spot beside them; C44/U8 silk overlap.
- L1/L2 are Würth WE-MAIA 78438356056 on the WE-MAPI 4020 footprint: **land pattern not verified** against the WE-MAIA drawing.
- 445-6042-1-ND (C2/C3/C10/C11) seen only on a distributor aggregator ("verify" in the BOM).

Rev C (fallback) additionally carries the six Gate 4 MAJORs of `gate-4-si-pi-revc.md` on branch `rev-c`: HSE_OUT load-cap path
11.8 mm with 2 vias (G4C-01), In1 used as a routing layer (G4-02), shared analog/digital ground fragment (G4-03), long MCU
decoupling paths (G4-04), routes under the BMI270 (G4-05), and a 3V3 track over U2's hot loop (G4C-02).

## 6. Not verified

- No hardware exists: nothing was built, powered, flashed or measured. All results are DRC/ERC, scripts and paper review.
- No field solving or circuit simulation; currents/temperatures are IPC-2221 estimates; coupling figures are order-of-magnitude.
- JLCPCB: 6-layer stackup name and thicknesses, POFV availability and price, PCB price, silk/mask minimums on the live site.
- DigiKey: live stock and prices (dated snippets only); 445-6042-1-ND not seen on DigiKey itself.
- Datasheets not on file or not obtainable: IIS2MDC (land pattern and mag alignment), WE-MAIA/WE-MAPI inductors, SMBJ26A,
  SN74LV1T125, USBLC6, W25N01GV absolute maximum, PTS810 button, TDK cap DC-bias curve; ST AN2606/RM0090 boot references.
- Part heights against vendor drawings; CPL rotations against JLC's convention; vendor pin-1 marks on symmetric packages.
- Betaflight/INAV: no firmware was compiled; some BF tables (alignment matrices, SPI pin tables, USER box IDs) were checked from
  memory by the red team, others against `datasheets/bf_src/` on disk.
- Real harness pin orders of VTX/GPS/ESC/receiver cables.
