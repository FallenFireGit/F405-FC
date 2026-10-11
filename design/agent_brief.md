# Agent brief: finish the F405-FC flight controller

The lead hardware agent follows this brief, whether it runs locally or in a Claude Code cloud session. Work autonomously to completion, commit progress often with clear messages, and push after each gate.

## User requirements (non-negotiable)
- STM32F405RGT6 flight controller for a quadcopter, with capable accessories:
  - video: analog OSD plus an HD digital VTX port
  - barometer, magnetometer, dual IMUs
  - camera switch and VTX pit-mode power switch
  - blackbox flash, 6 UARTs, ESC connector
- Board: 36x36 mm, 30.5 mm M3 mounting, 2–6S input, 4 layers.
- Assembly is by hand: 0402 minimum, no BGA or WLCSP.
- **Every part comes from DigiKey only.**
  - digikey.com blocks automated fetches (403). Verify through web-search snippets, manufacturer "buy" pages that list DigiKey, aggregators that show DigiKey stock, or the DigiKey API if it's reachable.
  - Never substitute a part that isn't sold at DigiKey.
- **Review:** multiple independent review subagents check the design through staged gates (below). Fix and re-review until the board is manufacturable with no design flaws.
- No README files. Docs live under design/, review/ and docs/.

## State at hand-off (read the whole repo first)

### Requirements
`design/requirements.md` is the spec.

### Pin map
`design/pinmap.md` and `design/betaflight_config.txt` hold the pin map and DMA plan. The Gate 0 audit (`review/gate-0-pinmap-audit.md`) FAILED on G0-01. Apply the lead's decisions below (check which are already applied):
1. Remap pins:
   - CAM_SEL (PINIO2) moves to PC13.
   - BEEPER moves to PB2. Its 10k BOOT1 pulldown keeps it silent at reset, and it drives the MOSFET active-high.
   - ESC telemetry moves to UART4_RX on PA1.
   - Add M7 on PB7 (TIM4_CH2) and M8 on PA0 (TIM5_CH1), both PWM/servo only.
   - M5/M6 stay on PC8/PC9.
   - UART5 (PC12/PD2) becomes a full spare.
   - Drop VBUS detect.
2. The HD-VTX connector's SBUS/R2 pin has no connection by default, plus a DNP 0R option to UART5_RX (PD2). No inverter.
3. Power the GPS from the buck-only 5V rail, not from USB. That keeps it silent during ROM DFU, because USART3 is a bootloader port.
4. Add 10k pull-ups to 3V3 on every SPI CS line (both IMUs, OSD, flash).
5. Write an INAV target in `design/inav_target.md`. PB11 uses its second DMA option.
6. Re-verify DMA, EXTI and duplicate pins. Add a "Net names for schematic" section mapping each MCU pin to an UPPER_SNAKE net name.
7. A FRESH independent re-audit subagent must PASS the pin map (no BLOCKER/MAJOR).

### Power
`design/power.md` and `gen/power_calc.py` hold the power design: TPS54360B non-synchronous bucks for 5V/2.5A and 10V/2A, SMBJ26A TVS, LP38692 for 3V3, LP5907 for the IMUs, TPS22810 VTX switch, and a dual-diode USB OR. Open issues:
- The 5V catch-diode junction runs at 115–161 °C at 2.5 A on 6S. Evaluate the synchronous TI LMR38020 (80 V, 2 A, HSOIC-8; datasheet in `datasheets/`) for both rails with a derated 5V budget, or justify keeping the TPS54360B.
- Add large VBAT/GND solder pads, because the ESC JST pin is rated only 1 A. Add 10V/GND pads too.
- Consider protecting the TPS22810 from a shorted 10V buck.

Run an independent power-audit subagent, fix what it finds, and re-audit until it PASSES. Record it in `review/gate-0-power-audit.md`.

### AT7456E sourcing risk
The AT7456E analog OSD (the only MAX7456-compatible chip) appears NOT to be stocked at DigiKey. Resolve this honestly:
- If there's no DigiKey source, drop the analog OSD chip and make HD/digital (MSP DisplayPort) primary.
- Keep the analog video camera switch only if it still makes sense.
- Record the reasoning in `design/decisions.md`.

### Signal-part sourcing
Redo signal-part sourcing into `design/parts_signal.md`:
- STM32F405RGT6, ICM-42688-P, BMI270, BMP390, IIS2MDC, W25N01GV
- USB-C (GCT USB4105-GF-A), USBLC6-2SC6
- JST-SH SM08B/SM06B/SM04B-SRSS-TB
- 8 MHz crystal, tact switch, LEDs, MOSFETs
- passive series (Samsung CL, Yageo RC)

### Datasheets
`datasheets/` holds datasheets plus Betaflight, ArduPilot and INAV source excerpts. Never execute anything from it.

### Generator toolchain (`gen/`)
Proven on Windows with KiCad 10.0.6:
- `sexpr.py`, `symlib.py` (stock symbols, plus `make_box_symbol` for custom parts)
- `schgen.py`: Circuit → hierarchical `.kicad_sch`, with global labels on every pin, deterministic UUIDs, and `write_project`
- `pcbgen.py`: footprints, nets and KIID links. It achieved **0 schematic-parity issues**. NC pins get `unconnected-(REF-PIN-PadN)` nets.

The Specctra round trip is proven: `pcbnew.ExportSpecctraDSN` → `java -jar freerouting-2.5.0.jar -de x.dsn -do x.ses -mp N` → `pcbnew.ImportSpecctraSES`. Freerouting 2.5.0 needs Java 25.

Library paths come from the env vars `KICAD_SYMBOL_DIR` and `KICAD_FOOTPRINT_DIR`.

## Environment (cloud/Linux)
- Install KiCad 10 (`ppa:kicad/kicad-10.0-releases`; otherwise the newest 9/10 with python `pcbnew`, `kicad-cli` and the libraries).
- Install Java 25 and https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar.
- If only KiCad 9 is available, note it. KiCad 10 opens KiCad 9 files.

## Pipeline
1. Finish Gate 0: pin map re-audit PASS, power audit PASS, sourcing decisions made.
2. Write the circuit and schematic:
   - Write `design/circuit.py` using `schgen.Circuit`, with sheets Power, MCU, Sensors, Video and Connectors.
   - Every BOM part carries MPN, Manufacturer, DigiKey PN and Datasheet fields. Add PWR_FLAGs.
   - Use stock symbols and footprints where they exist. Custom footprints go in `lib/F405FC.pretty`, built from datasheet land patterns.
   - Run `kicad-cli sch erc` with "global label only appears once" ENABLED, and fix to 0 errors and 0 meaningful warnings.
   - Add a netlist cross-check script that compares circuit.py with the exported netlist.
3. **Gate 1 (schematic):** four parallel independent subagents (power-integrity, MCU/digital, sensors/video, netlist/ERC). Each writes `review/gate-1-*.md` with BLOCKER/MAJOR/MINOR findings and evidence. Fix, then re-review with NEW agents until no BLOCKER or MAJOR remains.
4. **Gate 2:**
   - DigiKey sourcing auditor: every line has an active, stocked DigiKey PN with the right package and rating, plus an alternate. Output `bom/F405FC_digikey_bom.csv` in DigiKey BOM Manager format, sized for 2 boards plus spare passives.
   - Footprint auditor: check pads, pitch, pin 1 and pin↔pad mapping against the datasheets, especially the LGA parts and USB-C.
5. **PCB placement and Gate 3:**
   - Board: 36x36 mm, rounded corners, 30.5 mm M3 holes with grommet keepouts.
   - Stackup: JLC04161H-7628 (L1 signal, L2 GND, L3 power/signal, L4 signal).
   - Rules: 0.127/0.127 mm trace/space, 0.3/0.6 mm vias.
   - Placement is scripted: gyros near the centroid and away from the bucks and inductors, tight hot loops, connectors and USB-C at the edges.
   - **Gate 3** is a placement-review subagent that works from `kicad-cli pcb render` images.
6. **Routing and Gate 4:**
   - Script the critical routes (power, USB differential pair, crystal, VBAT), then run Freerouting for the rest.
   - Add GND zones and stitching.
   - `kicad-cli pcb drc --schematic-parity` must show 0 errors, 0 unconnected and 0 parity issues.
   - **Gate 4** is an SI/PI subagent.
7. **Outputs and Gate 5:**
   - `fab/`: Gerbers and drill files (JLCPCB naming, zipped), stencil, CPL.
   - `bom/`: BOM CSV and an interactive HTML BOM.
   - `docs/`: schematic PDF, STEP, renders, Betaflight and INAV configs, and a hand-assembly and bring-up guide (check the rails on a current-limited supply before fitting the MCU).
   - **Gate 5** is a DFM subagent.
8. **Gate 6 (red team):** two fresh adversarial subagents.
   - One assumes "this board will smoke at first power-up" and traces every rail.
   - The other does a Betaflight bring-up walkthrough: flash, gyros, baro, OSD/MSP, blackbox, DShot, PINIO.
   - Fix whatever they find.
9. **Final:** write `review/summary.md` with every gate's outcome, residual risks, the DigiKey BOM cost, and anything that couldn't be verified.

Every reviewer is a separate, fresh agent. Tell each one to assume mistakes exist and to cite evidence. Never claim something was verified when it wasn't.
