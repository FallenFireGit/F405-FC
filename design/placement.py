"""Scripted placement for the F405-FC PCB (gen/build_pcb.py applies it).

Board 36 x 36 mm, origin top-left, y down, mm. Entry: ref -> (x, y, rotation_deg, side) with side "T"/"B".
Coordinates are the footprint anchor as seen from the TOP. Connector mouths: rotation 0 = +y (down), 90 = +x,
180 = -y, 270 = -x (KiCad orientation is counter-clockwise as viewed from the top).

Layout intent (Gate 3):
  TOP    : MCU centred, crystal/decoupling/pull-ups around it, baro + mag top-left (away from power),
           connectors on the edges: HD VTX top, USB right (PA11/PA12 are on the MCU's right side),
           GPS + ELRS left, ESC bottom. Signal pads along the free edge segments.
  BOTTOM : IMUs at the board centroid, LP5907 next to them. Power stage in the lower half,
           5 V buck bottom-left, 10 V buck bottom-right, battery pads + TVS on the bottom edge,
           3V3 LDO / flash / video switch in the upper half.
"""

C = 18.0  # board centre

PLACE = {}


def put(ref, x, y, rot=0, side="T"):
    PLACE[ref] = (round(x, 3), round(y, 3), rot % 360, side)


# ---------------------------------------------------------------- mounting holes (30.5 mm square)
for ref, x, y in (("H1", 2.75, 2.75), ("H2", 33.25, 2.75), ("H3", 2.75, 33.25), ("H4", 33.25, 33.25)):
    put(ref, x, y)

# ---------------------------------------------------------------- TOP: connectors on edges
put("J3", C, 3.1, 180)          # HD VTX, mouth up
put("J2", 21.0, 36 - 3.1, 0)  # shifted right of centre to make room for the TVS (Gate 3 rework)       # ESC, mouth down
put("J1", 36 - 3.675, 14.5, 90)   # GCT drawing: PCB edge 2.60 mm from the rear shell slots (Gate 2 G2F-02)     # USB-C, mouth right
put("J4", 3.1, 11.0, 270)       # GPS, mouth left
put("J5", 3.1, 21.0, 270)       # ELRS, mouth left

# ---------------------------------------------------------------- TOP: MCU and its neighbours
MX, MY = 17.0, 17.5
put("U3", MX, MY, 0)
# HSE crystal next to PH0/PH1 (left side pins 5/6)
put("Y1", 8.4, 15.45, 270)
put("C36", 10.8, 13.0, 0)
put("C37", 10.8, 17.9, 0)
put("C35", 10.6, 19.4, 0)         # NRST
put("FB1", 8.6, 20.6, 90)         # VDDA bead (pin 13)
put("C31", 10.6, 21.4, 0)         # VDDA 1u
put("C32", 10.6, 20.4, 0)         # VDDA 100n (closest)
put("C30", 10.6, 12.0, 0)         # VBAT pin 1
# VDD decoupling: pin 64 (top-left), pin 48 (right-top), pins 19/32 (bottom)
put("C25", 12.4, 10.0, 90)        # pin 64
put("C26", 23.9, 10.6, 0)         # pin 48
put("C27", 13.6, 25.0, 90)        # pin 19
put("C28", 21.6, 25.0, 90)        # pin 32
put("C29", 15.2, 25.3, 90)        # bulk 4.7u
put("C33", 20.4, 25.0, 90)        # VCAP1 (pin 31)
put("C34", 23.9, 11.6, 0)         # VCAP2 (pin 47)
# pull-ups / pull-downs
put("R16", 19.5, 7.7, 0)          # BOOT0 pulldown (pin 60); rev D: up under J3, frees the via strip above U3 pins 51-54
put("R17", 18.6, 25.0, 90)        # BEEPER/BOOT1 pulldown (pin 28)
put("R18", 13.25, 19.55, 0, "B")   # GYRO1_CS pull-up; rev D: bottom beside U6 (its top-side branch forced GYRO1_CS across 3V3 at pin 19)
put("R19", 24.55, 13.55, 90)      # GYRO2_CS pull-up (moved off the MCU top-row corridor, routing)
put("R20", 13.55, 12.0, 90, "B")   # FLASH_CS pull-up; rev D: bottom, between the pin-58 escape via and U10 (no top-side branch across SPI3_MISO)
put("R25", 7.6, 4.8, 0)           # I2C SCL pullup, west of the MCU next to the I2C sensors (routing)
put("R26", 9.4, 4.8, 0)           # I2C SDA pullup, west of the MCU next to the I2C sensors (routing)
# status LEDs (PB14/PB15, right side lower)
put("D11", 13.0, 3.0, 0, "B")
put("R27", 10.6, 3.0, 0, "B")
put("D12", 13.0, 4.4, 0, "B")
put("R28", 10.6, 4.4, 0, "B")
# baro + mag top-left, away from power on the bottom-right
put("U8", 16.0, 8.9, 0)   # rev D: 1.2 mm right, frees the strip above U3 pins 61-63 for the I2C vias
put("C43", 11.4, 7.0, 90)
put("C44", 7.8, 7.6, 90)
put("U9", 9.55, 7.7, 0)
put("C45", 15.2, 6.9, 90)
put("C46", 11.6, 5.4, 0)
put("C47", 13.4, 5.0, 0)

# ---------------------------------------------------------------- TOP: edge pads
# top edge, either side of J3 (UART5 + S7 from the MCU top side)
put("P15", 7.6, 2.4)              # T5
put("P16", 9.8, 2.4)              # R5
put("P21", 26.6, 2.4, 0)             # S7
put("P24", 24.4, 2.4, 0)             # GND
put("P25", 28.8, 2.4, 0)             # 5V
put("R37", 25.4, 6.4, 0)          # DNP HD_R2 -> UART5_RX
put("R41", 22.6, 6.6, 90)         # 0R in series with HD VTX 10 V pin (remove for 2S HD builds)
# right edge below USB: UART6 + M5/M6 + LED strip
put("P17", 34.1, 12.9, 0, "B")        # T6
put("P18", 34.1, 15.5, 0, "B")        # R6
put("P19", 31.9, 15.5, 0, "B")        # S5
put("P20", 31.9, 12.9, 0, "B")        # S6
put("P10", 26.0, 28.3, 0)        # LED DIN
put("P11", 28.4, 28.3, 0)        # LED 5V
# bottom edge either side of J2
put("P22", 23.6, 28.3, 0)             # S8
put("P23", 30.8, 28.3, 0)             # RSSI
put("P13", 4.5, 27.2, 0)     # buzzer + (5V), paired with P14 and D9 in the top-left corner
put("P14", 4.5, 29.65, 0)    # buzzer - (BUZ_N)
# camera / VTX video cluster, left edge between GPS and ELRS
put("P5", 1.6, 13.2, 90, "B")          # CAM1
put("P6", 1.6, 15.3, 90, "B")          # CAM2
put("P7", 1.6, 17.4, 90, "B")          # VTX video
put("P8", 1.6, 9.0, 90, "B")          # cam 5V
put("P9", 1.6, 11.1, 90, "B")          # cam GND
# SWD test pads on top, right of the MCU
put("TP1", 28.9, 6.4, 0, "B")            # SWDIO (rev D: top-right corner, next to the SWD pins)
put("TP2", 31.0, 6.4, 0, "B")            # SWCLK
put("TP3", 33.1, 6.4, 0, "B")             # NRST
put("TP4", 8.1, 16.0, 0, "B")           # 3V3 (rev D: under the MCU left edge, next to TP5)
put("TP5", 12.4, 18.0, 0, "B")           # GND (rev D: under the MCU left edge)

# ---------------------------------------------------------------- BOTTOM: IMUs at the centroid
put("U6", 15.4, 17.0, 0, "B")
put("C38", 16.2, 19.2, 0, "B")
put("C39", 16.2, 20.4, 0, "B")
put("C40", 14.2, 17.0, 90, "B")
put("U7", 19.2, 17.0, 0, "B")   # rev D: 1.6 mm in from under the MCU right pin row (escape vias, Gate 4 G4-05)
put("C41", 20.0, 19.2, 0, "B")
put("C42", 22.0, 17.0, 90, "B")
put("U5", 15.5, 5.2, 0, "B")       # LP5907 for 3V3_IMU; rev D: where TP1-TP3 were, clear of the via strip above the U3 top pins
put("C22", 14.9, 8.0, 0, "B")      # U5 input cap
put("C23", 19.1, 4.0, 0, "B")      # U5 output cap

# ---------------------------------------------------------------- BOTTOM: upper half (flash, 3V3 LDO, video, USB support)
put("U10", 8.5, 8.0, 90, "B")     # W25N01GV WSON-8 8x6
put("C48", 12.2, 6.8, 90, "B")
put("R29", 12.2, 12.4, 90, "B")
put("R30", 11.0, 12.4, 90, "B")
put("U4", 24.3, 7.3, 90, "B")      # LP38692 SOT-223-5
put("C19", 20.2, 5.6, 90, "B")
put("C20", 30.4, 9.4, 90, "B")
put("C21", 29.0, 9.6, 90, "B")
put("C18", 21.6, 6.0, 90, "B")    # 5V_SYS bulk
put("D5", 21.2, 9.2, 0, "B")      # 5V -> 5V_SYS
put("D4", 30.0, 5.6, 0)    # VBUS -> 5V_SYS
put("U13", 25.6, 17.8, 90)   # USB ESD between J1 and the MCU (fixed: the MCU routing ring leaves no other spot)
put("C51", 30.0, 8.0, 0)
put("R36", 28.2, 8.0, 90)
put("R34", 29.4, 6.2, 0)
put("R35", 29.4, 7.0, 0)
put("SW1", 26.5, 6.4, 0)     # BOOT button, bottom side, top edge
put("U11", 4.8, 16.9, 90, "B")    # camera switch next to the video pads P5-P7; rev D: out from under Y1 (routing pocket)
put("C49", 8.8, 17.6, 90, "B")
put("R31", 8.8, 20.0, 90, "B")
put("U12", 29.5, 24.5, 90)   # LED strip buffer near the LED pads
put("C50", 29.2, 27.6, 0)
put("R32", 27.4, 24.4, 90)
put("R33", 29.4, 21.8, 0)
put("Q2", 25.8, 25.2, 0, "B")     # VTX off FET near U2 EN
put("R11", 24.5, 17.9, 90, "B")
put("R12", 26.0, 17.9, 90, "B")
put("D10", 3.6, 9.2, 90, "B")     # power LED
put("R13", 3.6, 12.0, 90, "B")

# ---------------------------------------------------------------- BOTTOM: power stage (lower half)
# battery entry on the bottom edge
put("P1", 7.0, 33.2, 0, "B")     # VBAT pad
put("P2", 10.4, 33.2, 0, "B")     # GND pad
put("D1", 9.5, 33.3, 0)     # TVS
put("C1", 7.3, 28.6, 90)     # entry cap
put("R14", 8.8, 23.6, 90)   # VBAT divider
put("R15", 10.0, 23.6, 90)
put("C24", 11.0, 16.7, 90, "B")
# 5 V buck, bottom-left
put("U1", 10.2, 25.6, 0, "B")
put("C2", 12.4, 22.8, 90, "B")
put("C3", 12.4, 26.8, 90, "B")
put("C4", 10.6, 22.0, 0, "B")
put("R1", 5.8, 21.6, 0, "B")
put("R2", 5.8, 22.8, 0, "B")
put("R3", 5.4, 27.4, 90, "B")
put("C5", 4.2, 25.6, 90, "B")
put("L1", 14.6, 30.85, 0, "B")
put("R4", 3.6, 28.6, 90, "B")
put("R5", 4.8, 30.0, 90, "B")
put("C6", 10.6, 35.0 - 1.4, 0, "B")
put("C7", 1.9, 23.2, 90, "B")
put("C8", 1.9, 28.2, 90, "B")
put("C9", 4.0, 23.0, 90, "B")
# 10 V buck, bottom-right
put("U2", 26.6, 24.6, 0, "B")
put("C10", 23.6, 26.6, 90, "B")
put("C11", 23.6, 30.4, 90, "B")
put("C12", 25.4, 30.6, 0, "B")
put("R6", 30.6, 24.0, 0, "B")
put("R7", 30.6, 25.2, 0, "B")
put("R8", 31.4, 29.4, 90, "B")
put("C13", 31.6, 27.0, 90, "B")
put("L2", 28.2, 30.8, 180, "B")
put("R9", 32.8, 30.4, 90, "B")
put("R10", 33.8, 27.6, 90, "B")
put("C14", 34.1, 23.0, 90, "B")
put("C15", 34.1, 17.9, 90, "B")
put("C16", 31.8, 34.4, 0, "B")
put("C17", 32.6, 21.2, 90, "B")
put("P3", 34.2, 23.0, 0)      # 10V pad
put("P4", 34.2, 27.0, 0)
# CURR / RSSI protection and buzzer driver, bottom side near the ESC
put("R38", 9.4, 26.4, 90)
put("C52", 11.0, 18.0, 90, "B")
put("R39", 14.0, 29.0, 90)
put("C53", 11.0, 19.3, 90, "B")
put("R40", 14.0, 27.4, 90)
put("Q1", 16.0, 27.0, 0)
put("D9", 1.8, 27.85, 90)    # buzzer flyback (5V to BUZ_N); no room near Q1 once the MCU routing ring is kept clear


# Footprints the legalizer must not move (gen/legalize.py); everything else is nudged to the nearest legal spot.
# Silk label areas kept free of movable parts (Gate 3 G3-11): (side, (x0, y0, x1, y1))
RESERVED = [("B", (2.6, 8.0, 4.6, 18.4)),      # video/camera pad column labels
            ("B", (12.8, 2.3, 20.2, 3.5)),     # SWD test-point row labels (above)
            ("B", (13.2, 8.1, 17.6, 9.3))]     # 3V3 / GND test-point labels (below)

FIXED = ["C22", "C23", "U13", "D9", "P13", "P14", "P22", "P23", "P10", "P11", "P24", "P21", "P25", "P5", "P6", "P7", "P8", "P9", "P20", "P17", "P19", "P18", "TP1", "TP2", "TP3", "TP4", "TP5", "H1", "H2", "H3", "H4", "J1", "J2", "J3", "J4", "J5", "U3", "U1", "U2", "L1", "L2", "U4", "U10",
         "P1", "P2", "P3", "P4", "D1", "C1", "U6", "U7", "U5", "Y1", "U8", "U9", "U11", "U12"]

# Pin-anchored parts (Gate 3 G3-02/03/05/08/09): ref -> (anchor ref, anchor pad, dx, dy, rotation, side).
# Offsets are from the anchor pad centre (board mm, as seen from the top). These parts are fixed after anchoring and
# gen/placecheck.py verifies the resulting pin distances.
ANCHOR = {
    # U1 (5 V buck, bottom): VIN pin 3 / GND pin 1 on the left, BST 7 / SW 8 / FB 5 on the right
    "C4": ("U1", 3, -1.9, 1.27, 270, "B"),
    "C2": ("U1", 3, -4.45, 1.27, 270, "B"),
    "C3": ("U1", 3, -4.45, -3.55, 90, "B"),
    "R3": ("U1", 4, -0.3, -1.5, 0, "B"),       # RT
    "R2": ("U1", 4, -1.6, -2.6, 0, "B"),       # EN pulldown (EN is DC; kept clear of the battery pads)
    "R1": ("U1", 4, -1.6, -3.6, 0, "B"),       # EN top
    "C5": ("U1", 7, 1.7, 0.63, 270, "B"),   # pad 1 (BST) level with U1 pin 7, pad 2 (SW) with pin 8: no crossing
    "R5": ("U1", 5, 1.6, -1.0, 90, "B"),
    "R4": ("U1", 5, 2.6, -1.0, 90, "B"),
    "C6": ("L1", 2, 2.45, 0.0, 90, "B"),        # 5 V output caps beside L1 (bottom)
    "C7": ("L1", 2, 0.7, 3.6, 0, "B"),
    "C8": ("U1", 8, 3.55, -1.4, 90, "B"),
    "C9": ("L1", 2, 4.32, 0.0, 90, "B"),
    # U2 (10 V buck, bottom), same orientation
    "C12": ("U2", 3, -1.95, 1.27, 270, "B"),
    "C10": ("U2", 3, -4.5, 1.75, 270, "B"),
    "C11": ("U2", 3, -4.45, -3.55, 90, "B"),
    "R8": ("U2", 4, -0.3, -1.5, 0, "B"),
    "R7": ("U2", 4, 3.0, -2.0, 0, "B"),
    "R6": ("U2", 4, 3.0, -3.0, 0, "B"),
    "Q2": ("U2", 4, 1.0, -3.2, 0, "B"),
    "C13": ("U2", 7, 1.7, 0.63, 270, "B"),
    "R10": ("U2", 5, 1.6, -0.9, 90, "B"),
    "R9": ("U2", 5, 2.6, -0.9, 90, "B"),
    "C14": ("L2", 2, -2.6, 0.0, 90, "B"),
    "C15": ("U2", 8, 3.55, 0.6, 90, "B"),
    "C16": ("L2", 2, -5.1, 0.0, 90, "B"),
    "C17": ("L2", 2, -2.6, 2.6, 0, "B"),
    # IMUs: VDD (pin 8) and VDDIO (pin 5) decoupling hugging the pins
    "C38": ("U6", 8, 0.25, -1.7, 0, "B"),      # rev D: below U6, frees the gap to U7
    "C39": ("U6", 8, -0.16, 3.15, 0, "B"),
    "C40": ("U6", 5, 0.0, -1.1, 0, "B"),
    "C41": ("U7", 8, 1.2, 0.25, 90, "B"),
    "C42": ("U7", 5, 0.0, -1.1, 0, "B"),
    # LDOs
    "C20": ("U4", 3, 0.0, 2.2, 0, "B"),
    "C19": ("U4", 1, 0.0, 2.2, 0, "B"),
    # MCU decoupling (top) — outside the LQFP courtyard (13.5 mm), closest to their pins
    "C25": ("U3", 64, 0.0, -2.75, 90, "T"),
    "C26": ("U3", 48, 1.7, -2.4, 90, "T"),    # at the MCU top-right corner: keeps the right pin row free for routing (G3R-10)
    "C34": ("U3", 47, 3.05, -3.6, 90, "T"),
    "C27": ("U3", 19, 0.0, 2.75, 90, "T"),
    "C29": ("U3", 32, 1.9, 3.3, 90, "T"),
    "C33": ("U3", 31, -0.5, 2.75, 270, "T"),
    "C28": ("U3", 32, 0.5, 2.75, 90, "T"),
    "C32": ("U3", 13, -2.75, 0.0, 0, "T"),
    "C31": ("U3", 13, -2.75, 2.0, 90, "T"),
    "FB1": ("U3", 13, -4.6, 0.9, 90, "T"),
    # under the MCU's left edge (bottom): VBAT pin, NRST and ADC filter caps right below their pins
    "C30": ("U3", 1, -0.9, 0.0, 0, "B"),
    "C35": ("U3", 7, -0.9, -0.25, 0, "B"),
    "C24": ("U3", 8, -0.9, 0.25, 0, "B"),
    "C52": ("U3", 9, -0.9, 0.75, 0, "B"),
    "C53": ("R39", 2, -1.0, 0.0, 90, "T"),   # RSSI RC filter cap next to its series resistor (frees MCU under-body via sites)
    # crystal load caps
    "C36": ("Y1", 1, 0.0, -1.4, 0, "T"),
    "C37": ("Y1", 2, -1.95, -0.05, 180, "T"),   # left of Y1 between J4/J5 (FB1 holds the spot under pin 3; Gate 4 G4-01)
    # sensors / flash / video switch / LED buffer
    "C43": ("U8", 10, 1.0, 0.0, 90, "T"),
    "C44": ("U8", 1, 0.0, -1.0, 0, "T"),
    "C45": ("U9", 5, 0.0, 1.0, 0, "T"),
    "C46": ("U9", 9, 1.0, -0.25, 90, "T"),
    "C48": ("U10", 8, 1.3, 0.0, 90, "B"),
    "C49": ("U11", 5, 0.0, -1.1, 0, "B"),
    "C50": ("U12", 5, 0.0, -1.1, 0, "T"),
}

# Lower value = placed earlier by the legalizer (gets the spot closest to its seed).
PRIORITY = {r: -10 for r in ("Y1", "C36", "C37", "C25", "C26", "C27", "C28", "C30", "C32", "C33", "C34", "C35", "FB1",
                             "C31", "C29")}
PRIORITY.update({r: -9 for r in ("U13", "C24", "C52", "C53", "R38", "R39", "C48", "C46", "C45", "C43",
                                 "C49", "C50", "C18")})

# rev D placement freeze (gen/build_pcb.py): every other part keeps its position from kicad/placement_frozen.json
UNFREEZE = ("U5", "C22", "C23", "TP1", "TP2", "TP3", "TP4", "TP5")
