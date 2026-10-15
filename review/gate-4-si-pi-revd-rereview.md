# Gate 4 (rev D, 6-layer): SI/PI re-review after the G4D-01/G4D-02 re-route

Reviewer: fresh, independent Gate 4 SI/PI re-reviewer, 2026-10-15. This is a review only. The only repo file written is this report
(not committed). Scratch scripts and data are in `/opt/kroot/tmp/g4d2/` (`/tmp/g4d2/` in the chroot).

**Board reviewed:** `kicad/F405FC.kicad_pcb` at `176113f`, md5 `653c16f502e2028fce2b689dd5a80664`. During the review HEAD moved to
`1fae613`, which only adds `review/summary.md`. The board is byte-identical. **Baseline:** `0524b43` (md5 `df8f70f5…`, the board
the previous Gate 4 rev D report reviewed).

Coordinates are board mm (file minus 100 mm). Inner layers are `In1.GND`, `In2.SIG`, `In3.PWR` and `In4.GND`.

## Method (all run here)

| Step | Tool / script | Result |
|---|---|---|
| DRC + parity | `kicad-cli pcb drc --schematic-parity --severity-all` → `/tmp/g4d2/drc.json` | **0 errors, 0 unconnected, 0 parity**. Warnings: 16 `via_dangling` (the same 16 nets as before) and 1 `silk_overlap` (C44/U8) |
| Fill freshness | `refill.py`: stored fill vs in-memory `ZONE_FILLER` refill, not saved | All 7 zones/layers **SAME**: piece count and area |
| Geometry dump | `dump.py` (pcbnew, read-only) on HEAD and on `git show 0524b43:…` | HEAD has 1860 tracks, 267 vias, 495 pads; the baseline has 1995 / 267 / 495. Placement is identical (154 footprints, 0 pad moved) |
| Route diff | `diffnets.py`, `geodiff.py`: per-net copper uncovered between versions, sampled at 0.05 mm | 11 nets differ geometrically (below) |
| Box check | `box.py`: foreign B copper inside the U1/U2/L1/L2 courtyards (+0 / +0.5 mm) | See G4D-02 |
| Exact gaps | `exact.py`: KiCad `SHAPE::Collide` bisection, B.Cu | Via-to-pad gaps quoted below |
| Proximity | `prox.py`, `padnear.py`, `far.py`, `vianear.py`: same-layer edge gaps and parallel lengths | Quoted per finding |
| Paths | `paths.py`: Dijkstra over the track/via/pad graph | Pin-to-pin routed lengths |
| Broadside | `broad.py`: In2/In3 copper overlap in projection, plus In2 over the In3 VBAT zone | Old vs new |
| Pours | `pour.py`: GND pad and via membership per fill piece | B GND continuity |
| Planes | `plane.py`: 0.02 mm raster of the In1/In4 fills | Pieces, voids, tracks over voids |
| Return vias | `retvia.py` | Nearest GND via/TH to each re-routed via |
| placecheck | `kc 'cd /work && python3 gen/placecheck.py'` | PASS (still pad-centre based: "C52 -> U3 CURR_ADC 1.57 mm") |

**Nets whose copper changed 0524b43 → 176113f** (`geodiff.py`, mm of copper removed/added):

| Net | Change |
|---|---|
| CURR_ADC | −In2 58.4, −In3 5.9, −F 1.0; +In2 7.2, +F 0.8. Vias (10.34, 28.49) and (13.49, 17.79) replaced by (13.34, 18.06) |
| SPI1_MOSI | −B 15.6, −F 5.9; +In3 26.1, +In2 10.0, +F 3.1 (4 → 5 vias) |
| LED_DIN | −B 9.0; +In2 7.9 (vias moved to (27.01, 27.49) and (30.25, 20.94)) |
| MOTOR8 | In2 12.7 → 11.9 re-routed; via (24.21, 27.24) → (24.44, 27.31) |
| UART5_RX, BEEPER, 5V_SYS, 5V, 3V3, GYRO2_CS, GND | Local tidy only, ≤ 4.8 mm of copper, same vias except 1 UART5_RX via moved 0.075 mm and 2 GND vias moved ≤ 0.07 mm |

Every other net, including 10V, VBAT, USB, HSE, SW/BST/FB, 3V3_IMU, EN_5V and I2C1, is geometrically unchanged.

## Verdict: **PASS** (0 BLOCKER, 0 MAJOR)

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 0 |
| MINOR | 16 (3 new G4D2 + 13 carried over unchanged) |
| INFO | 4 (G4D-09, G4-14, G4-16, G4D2-04; G4-15 fixed) |

- **G4D-02 is fixed.**
  - No foreign track remains on B inside the U1 or U2 courtyards.
  - Every FB/BST/SW pad of both bucks is now ≥ 0.97 mm from SPI1_MOSI/LED_DIN copper.
  - The B GND pour around the bucks is one piece again.
  - The residual vias and the non-persistent keep-out are covered in G4D2-03.
- **G4D-01 is much improved but not fixed to its own criterion.**
  - U3.9 → C52 is now **14.2 mm with 2 vias** (was 71.6 mm with 3). The requested limit was ≤ 3 mm.
  - The filter cap is still a 5.9 mm stub at the R38 end, not at the pin.
  - The motor/USB/VBUS neighbours are gone, so this is downgraded to MINOR (G4D2-01).
- **The re-route introduced one new MINOR:** SPI1_MOSI is now the worst detour on the board, 43 mm with 5 vias (G4D2-02).

| ID | Sev | Title |
|---|---|---|
| G4D2-01 | MINOR | CURR_ADC: pin → C52 still 14.2 mm, 2 vias; cap is a stub at the R38 end (G4D-01 residual) |
| G4D2-02 | MINOR | SPI1_MOSI re-route: 25.2 → 43.0 mm, 5 vias, 4.7× MST. New In2/In3 broadside with MOTOR8 (3.4 mm), 4.7 mm of In2 over the In3 VBAT zone, In3 beside MOTOR4/MOTOR1, via 0.23 mm from C5.1 (BST_5V) |
| G4D2-03 | MINOR | The buck B keep-out is router-only and unrecorded. Vias still overlap the U1/U2 courtyards (MOTOR8 via centre inside U2) |
| G4D2-04 | INFO | Verified OK after the re-route: planes, B GND pour, buck node clearances, return vias, IMU/crystal/USB distances |

---

## Part 1: previous G4D findings, status

| ID | Prev | Status now | Evidence |
|---|---|---|---|
| **G4D-01** CURR_ADC 70 mm loop | MAJOR | **Changed → MINOR (G4D2-01)** | `paths.py`: U3.9 → C52.1 **14.23 mm, 2 vias** (B 5.87, In2 7.07, F 1.29), was 71.63 mm with 3 vias. The In2 loop round the board is deleted. Net total 16.7 mm (matches the commit). The 0.29 mm In1-void crossing is gone. The cap is still not at the pin; see G4D2-01 |
| **G4D-02** SPI1_MOSI / LED_DIN through U1/U2 on B | MAJOR | **Fixed** (residual MINOR → G4D2-03) | Below |
| G4D-03 crystal residuals | MINOR | Open, unchanged | HSE_IN/HSE_OUT, I2C1_SDA and CAM_SEL copper are not in the route diff |
| G4D-04 MCU PDN residuals | MINOR | Open, unchanged | 3V3 differs only by 0.2 mm on In3. F/B 3V3 is unchanged and no via moved |
| G4-06 5 V east trunk | MINOR | Open, unchanged | 5V differs by ≤ 0.34 mm (tidy), with the same vias |
| G4-07 10 V single vias | MINOR | Open, unchanged | 10V is not in the geometric diff |
| G4-08 VBAT neck | MINOR | Open, unchanged | The In3 VBAT fill is 136.41 mm² before and after. The GND via at (17.30, 24.60) is still present |
| G4-09 USB | MINOR | Open, unchanged | USB_DP/USB_DM/VBUS are not in the diff |
| G4-11 5 V sense beside L1 SW | MINOR | Open, unchanged | The 5V B leg differs by only 0.08 mm |
| G4-12 dangling vias | MINOR | Open | DRC: the same 16 `via_dangling` nets as the baseline list |
| G4-13 stitching | MINOR | Open | 64 GND vias (2 moved ≤ 0.07 mm). B GND pieces with ≤ 1 tie: 2; F: 8 |
| G4D-05 stackup / In2-In3 broadside | MINOR | Open, **slightly worse** | Still no `(stackup)`. Job file `"Finish": "None"`, `"Revision": "rev?"`. New overlaps from the re-route: MOTOR8/SPI1_MOSI 3.42 mm and SPI1_MOSI over VBAT 4.73 mm (G4D2-02). The CURR_ADC/STATUS_LED_GREEN 1.98 mm overlap is gone |
| G4D-06 3V3_IMU | MINOR | Open, unchanged | Not in the diff |
| G4D-07 EN_5V in C4 loop | MINOR | Open, unchanged | Not in the diff. Also R1.2 (EN_5V) is close to the UART2_TX via (6.39, 20.71): ≤ 0.07 mm by pad bounding box, while DRC passes |
| G4D-08 flash decap | MINOR | Open, unchanged | Not in the diff |
| G4D-09 3V3 tree | INFO | Unchanged | — |
| G4-14 stackup | INFO | Open | As G4D-05 |
| G4-15 `review/summary.md` | INFO | **Fixed** | The file now exists (`1fae613`) and has the inner-5V inventory (lines 62-66) |
| G4-16 video | INFO | Unchanged | Not in the diff |
| G4D-10 verified OK | INFO | Re-verified → G4D2-04 | — |

### G4D-02 verification detail

**Tracks.**
- Foreign B tracks inside the courtyard (`box.py`; U1 courtyard (6.425, 22.855)-(13.975, 28.345), U2 (22.825, 21.855)-(30.375, 27.345),
  both read from the footprints' own courtyards):
  - Baseline: U1 has SPI1_MOSI **5.35 mm**; U2 has LED_DIN **6.16 mm**.
  - HEAD: **0 mm in both**.
  - With +0.5 mm: U1 has only CURR_ADC 1.73 mm. That is C52's B leg at y = 22.76, which is unchanged from the baseline and 1.9 mm
    from FB_5V.
- Foreign B copper within 0.5 mm of buck FB/BST/SW/EN pads (`padnear.py`):
  - **Baseline:**
    - U1.5 FB_5V: SPI1_MOSI 0.117.
    - U1.7 BST_5V: 0.334.
    - R4.2 FB_5V: 0.144.
    - U2.5 FB_10V: LED_DIN 0.127.
    - U2.7 BST_10V: 0.164.
    - U2.8 SW_10V: 0.177.
  - **HEAD:** none of these remain. What is left (all vias, all pre-existing apart from the moved SPI1_MOSI via):
    - BEEPER via → C5.1 (BST_5V): **0.143 mm** (exact).
    - BEEPER via → C5.2 (SW_5V): 0.276 mm.
    - SPI1_MOSI via (14.99, 25.61) → C5.1 (BST_5V): **0.229 mm** (exact; it was 0.273 at (14.99, 25.54)).
    - BUZ_N via → L1.1 (SW_5V): 0.163 mm.
    - LED_DIN via → R6.2 (EN_10V): 0.263 mm.
    - UART2_RX via → R5.1 (FB_5V): 0.438 mm.

**Where the re-routed nets go now.**
- **SPI1_MOSI:** U3.23 → F → via (14.99, 25.61) → **In3** SW to (11.94, 29.74) → via (10.84, 30.74) → **In2** (13.94, 33.84) → (19.51, 33.84)
  → via → **In3** N along x = 23.29 (y 30.06 → 22.51) → (21.19, 20.86) → via (18.81, 18.49) → U7.14 (B) / F → via (14.99, 18.56) → U6.14.
  - Same-layer minimum gaps (`far.py`):
    - SW_5V 1.17, FB_5V 1.91, BST_5V 0.27 (the via);
    - HSE 3.37, USB 3.79, VBUS 6.34 mm.
  - The In3/In2 legs are below In1 and above In4, so the B-side bucks are shielded by In4.
- **LED_DIN:** R33.2 → F → via (30.25, 20.94) → **In2** x = 27.76, y 23.39 → 26.66 (over U2, shielded by In3 GND fill + In4) → via
  (27.01, 27.49) → F → P10.1.
  - Path 8.96 mm, 2 vias.
  - Gaps: FB_10V 0.97, SW_10V 1.46, BST_10V 2.29, USB_DP 2.73 mm.
- **MOTOR8:** U3.14 → F → via (14.71, 19.74) → In2 → via (24.44, 27.31) → P22. Path 18.85 mm, 2 vias (was 19.70).
  - Gaps: FB_5V 1.69, SW_10V 3.86, HSE 3.13 mm.
  - The B pad of the end via is 0.205 mm from U2.1 (GND) and 3.82 mm from U2.8 (SW_10V).

**B GND pour (`pour.py`, fills verified current).**
- **HEAD:** B GND has 11 pieces. The main piece is **650.1 mm² with 51 GND vias** and holds U1.1/U1.9, U2.1/U2.9, C2, C3, C4, C10, C11,
  C12, **C6, C8, C9**, C14, C16, P2.1 and all IMU/LDO grounds.
- **Baseline:** the same parts were split between piece #11 (558.5 mm², U1 side) and piece #0 (81.9 mm², U2 + C6/C8/C9 + C10/C12/C14/C16).
- The split reported in G4D-02 is gone.

---

## Part 2: new findings

### G4D2-01 MINOR: CURR_ADC filter cap still not at the ADC pin (G4D-01 residual)

**Evidence.**
- Pads: R38.2 (8.08, 24.66) F; C52.1 (9.995, 18.59) B; U3.9 (11.325, 17.75) F.
- Topology: the junction is via (10.04, 22.71).
  - R38.2 → junction is F 2.27 mm.
  - Junction → C52.1 is a **B stub of 5.87 mm**: (10.04, 22.71) → (11.81, 22.04) → (11.81, 20.56) → (10.14, 18.89).
  - Junction → U3.9 is **In2 7.07 + F 1.29 mm** through via (13.34, 18.06).
- U3.9 → C52.1 = **14.23 mm, 2 vias**. The fix asked for ≤ 3 mm with one via.
- The sister net shows it can be done: VBAT_ADC U3.8 → C24.1 = **1.68 mm, 1 via** (`paths.py`).
- Unfiltered pin-leg neighbours (`prox.py`):
  - In2: UART2_RX 2.32 mm at 0.149 mm; 3V3 1.26 mm at 0.149; CAM_SEL 0.81 at 0.162.
  - In2/In3 broadside: 3V3 0.80 mm.
  - None of these is a DShot, USB or VBUS net any more.
- The C52 stub on B runs at y = 22.76, 0.1 mm outside U1's courtyard and 1.9 mm from FB_5V (exact via-to-U1.5 gap 1.910 mm).
- Estimate, not simulated:
  - Mutual capacitance to UART2_RX is about 0.05-0.09 pF.
  - With a 3.3 V/5 ns edge, that is about 50 µA into a pin node of about 12 nH / 6 pF (Z ≈ 45 Ω).
  - The result is ringing of about 2 mV that settles in a few ns, well inside the ADC sample window. Before the re-route this was
    tens of mV.

**Fix.**
1. Put the junction at C52: a via beside U3.9 down to C52.1 (≤ 3 mm, as VBAT_ADC does), and bring R38's feed to C52.1 rather than
   to the pin leg.
2. `gen/placecheck.py` still judges C52 by pad-centre distance (1.57 mm, PASS). Add a routed pin-to-cap check (G4D-01 fix 3 is still open).

### G4D2-02 MINOR: SPI1_MOSI re-route is long and picks up new neighbours

**Evidence.**
- Lengths:
  - U3.23 → U6.14 = **42.91 mm, 5 vias** (F 6.57, In3 26.04, In2 9.96, B 0.35).
  - U3.23 → U7.14 = 38.23 mm, 4 vias.
  - The baseline was 24.40 / 20.74 mm.
- Net total **43.0 mm against a 9.2 mm pad MST = 4.7×**, now the worst detour on the board (`detour.py`). Next are EN_5V and SPI3_SCK
  at 2.5×.
- New couplings:
  - **In2 MOTOR8 directly over In3 SPI1_MOSI for 3.42 mm.** The coordinates coincide at (21.89, 21.11) → (23.29, 22.51) and
    (21.19 → 21.89, 20.86 → 21.11).
  - ESC_TLM (In2) over SPI1_MOSI for 0.74 mm.
  - SPI1_MOSI's In2 leg lies **over the In3 VBAT zone for 4.73 mm**, now the largest In2-over-VBAT run (`broad.py`).
- In3 same-layer neighbours:
  - 5V 2.63 mm at 0.149;
  - BUZ_N 1.21 at 0.149;
  - MOTOR4 0.80 at 0.162;
  - MOTOR1 0.74 at 0.185;
  - VBAT zone edge 0.56 at 0.237 mm.
- Via (14.99, 25.61) has its B pad **0.229 mm from C5.1 (BST_5V)**. It is outside the U1 courtyard, so the AVOID box did not catch it.
- Return vias are fine: every SPI1_MOSI layer change has a GND via/TH within 0.74-2.23 mm. The In3↔In2 changes at (10.84, 30.74)
  and (19.51, 33.84) have one at 1.88 and 0.74 mm.
- Magnitude (estimate):
  - The MOTOR8 broadside length is about 23 ps of delay against a GPIO edge of ≥ 2 ns.
  - Backward crosstalk is therefore ≤ 1 % even with tight In2–In3 coupling, i.e. tens of mV on a 3.3 V CMOS line.
  - 43 mm adds about 0.3 ns at IMU SPI rates.
- Not a functional risk on its own. It is the exposure G4D-05 warns about, now on the IMU bus.

**Fix.**
- Route SPI1_MOSI north of U1, U3.23 → IMUs directly (pad MST 9.2 mm), for example on F or In2 over In1. Aim for ≤ 15 mm. I did not
  check free space for this.
- Keep it off the In3 VBAT zone and away from the MOTOR8 In2 run.
- Move the (14.99, 25.61) via ≥ 0.5 mm from C5.

### G4D2-03 MINOR: buck B keep-out is not persistent; vias still overlap the courtyards

**Evidence.**
- The fix is the router env var `AVOID` (`gen/pathfinder.py:56-59, 304-309`). The values used are recorded nowhere in the repo:
  `grep -rI AVOID` finds only the pathfinder and an unrelated Betaflight source file. No `.sh` sets it.
- The board has only 6 keepout areas (the L1/L2 bodies) and no buck rule in `F405FC.kicad_dru`.
- A re-run of `route_pipeline.sh` or a later tidy can therefore silently undo G4D-02, and DRC will not flag it.
- Vias whose B pads still overlap the courtyards (`box.py`, exact gaps from `exact.py`):

  | Via | Courtyard | Position | Nearest buck pads (B) |
  |---|---|---|---|
  | **MOTOR8** (24.44, 27.31) | U2 | **Centre inside the box** (y 27.31 < 27.345; it was moved from (24.21, 27.24), also inside) | U2.1 GND 0.205 mm, U2.8 SW_10V 3.82 mm |
  | LED_DIN (27.01, 27.49) | U2 | Pad overlaps the box edge by 0.15 mm | U2.9 GND 0.138, SW_10V 1.376, BST_10V 2.190 mm |
  | CURR_ADC (10.04, 22.71) | U1 | Pad overlap (pre-existing) | U1.9 GND 0.138, FB_5V 1.910 mm |
  | UART2_RX (11.99, 22.59) | U1 | Pad overlap (pre-existing) | — |

  - None of them is near SW/BST/FB, so the electrical effect is negligible.
  - The commit text ("foreign nets removed from B.Cu inside the courtyards") holds for tracks, not for via pads.
  - Vias keep all layer pads (`GetRemoveUnconnected() == False`), so each one is B copper.
- Pre-existing foreign vias at buck nodes are unchanged:
  - BEEPER via 0.143 mm from C5.1 (BST_5V) and 0.276 mm from C5.2 (SW_5V);
  - BUZ_N via 0.163 mm from L1.1 (SW_5V).

**Fix.**
- Make the keep-out a design rule, for example in `F405FC.kicad_dru`:
  `(rule "buck B" (layer B.Cu) (constraint disallow track via) (condition "A.intersectsCourtyard('U1') && A.NetName != 'GND' && …"))`,
  or rule areas with net exceptions done by custom rules. Then DRC enforces it.
- Record the `AVOID` string in `route_pipeline.sh`.
- Move the MOTOR8 via out of the U2 box.
- Move the BEEPER via away from C5.

### G4D2-04 INFO: verified OK after the re-route

- **In1/In4 planes.**
  - **One piece each** (raster 1060.3 mm², 81.8 %; KiCad area 1056.1 mm²; identical before and after).
  - **0 tracks** on In1/In4 (track count by layer: F 910, B 496, In2 257, In3 197).
  - Each Gerber `F405FC-In1_GND.g1` / `-In4_GND.g4` has 1 `G36` region and 287 flashes.
  - The largest non-hole voids are 4.76 mm² (J1 area, x 27.6-30.9 / y 8.8-12.1), 3.84 mm² (under the MCU, x 18.3-21.8 / y 12.6-15.7)
    and 2.79 mm².
  - Signal track over a foreign void: only VBUS 0.11 mm and USB_CC1 0.04 mm on F at J1's TH clearances (same as the baseline).
    The CURR_ADC 0.29 mm crossing is gone.
- **Other pours.**
  - F 32, B 11, In2 8, In3 12 GND pieces (baseline 34/12/14/11).
  - The only pieces with no via or pad inside are the J1 shell-spoke pieces: F 1.79 mm², B 2.44 mm² (baseline also had In2 2.08 mm²).
- **SW/BST/FB nets.** These are B-only and unchanged. No foreign track within 0.3 mm of any SW/BST/FB copper (`prox.py`); only vias,
  listed in G4D2-03.
- **Return vias.** Every via of the 4 re-routed nets has a GND via/TH within 0.74-2.23 mm (`retvia.py`).
- **Sensitive areas.**
  - None of the re-routed nets comes within 1.07 mm of HSE (CURR_ADC 1.07 to HSE_OUT, F) or 2.73 mm of the USB pair.
  - Inside the U6/U7 area, SPI1_MOSI is the IMU's own net.

---

## Not verified

- **Stackup.** Still undefined in the board; every In2/In3 reference and broadside statement depends on it (G4D-05).
- **No field solver, SPICE, EMI or thermal simulation.** Coupling and crosstalk numbers are closed-form estimates.
- **No hardware measurement** (ADC noise, gyro noise, buck FB disturbance).
- **Gap measurements.**
  - `prox.py`/`padnear.py` treat pads as their bounding rectangles, which is pessimistic for rotated or rounded pads.
  - Gaps quoted as "exact" come from KiCad shape collision on B.Cu only.
  - Same-layer scans and In2/In3 broadside only; F↔In2 and In3↔B broadside are not checked, since a GND plane lies between them.
- **Unchanged findings.** The 13 carried-over MINORs were confirmed unchanged **by the route diff** (their copper is identical); I did
  not re-measure their individual numbers.
- **Release outputs.** Only the In1/In4 Gerber region/flash counts were checked against the board; the other Gerbers, STEP, renders
  and iBOM were not compared.
- **pathfinder.** The `AVOID` implementation was read, not run; I did not re-run the router or tidy.
