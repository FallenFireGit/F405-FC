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
put("J3", C, 2.575, 180)          # HD VTX, mouth up
put("J2", C, 36 - 2.575, 0)       # ESC, mouth down
put("J1", 36 - 3.1, 14.5, 90)     # USB-C, mouth right
put("J4", 2.575, 11.0, 270)       # GPS, mouth left
put("J5", 2.575, 25.0, 270)       # ELRS, mouth left

# ---------------------------------------------------------------- TOP: MCU and its neighbours
MX, MY = 17.0, 17.5
put("U3", MX, MY, 0)
# HSE crystal next to PH0/PH1 (left side pins 5/6)
put("Y1", 9.0, 15.4, 90)
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
put("R16", 19.6, 9.9, 90)         # BOOT0 pulldown (pin 60)
put("R17", 18.6, 25.0, 90)        # BEEPER/BOOT1 pulldown (pin 28)
put("R18", 14.6, 27.2, 90)        # GYRO1_CS pullup
put("R19", 16.0, 9.9, 90)         # GYRO2_CS (pin 50)
put("R20", 18.4, 9.9, 90)         # FLASH_CS (pin 58)
put("R21", 9.5, 23.0, 0)          # PC2 pulldown
put("R22", 9.5, 24.0, 0)          # PC3
put("R23", 23.9, 23.6, 0)         # PB12
put("R24", 23.9, 22.6, 0)         # PB13
put("R25", 13.6, 9.9, 90)         # I2C SCL pullup
put("R26", 14.8, 9.9, 90)         # I2C SDA pullup
# status LEDs (PB14/PB15, right side lower)
put("D11", 26.0, 25.6, 90)
put("R27", 26.0, 28.2, 90)
put("D12", 27.4, 25.6, 90)
put("R28", 27.4, 28.2, 90)
# baro + mag top-left, away from power on the bottom-right
put("U8", 9.6, 7.6, 0)
put("C43", 11.4, 7.0, 90)
put("C44", 7.8, 7.6, 90)
put("U9", 13.4, 6.9, 0)
put("C45", 15.2, 6.9, 90)
put("C46", 11.6, 5.4, 0)
put("C47", 13.4, 5.0, 0)

# ---------------------------------------------------------------- TOP: edge pads
# top edge, either side of J3 (UART5 + S7 from the MCU top side)
put("P15", 7.6, 2.4)              # T5
put("P16", 9.8, 2.4)              # R5
put("P21", 26.2, 2.4)             # S7
put("P24", 28.4, 2.4)             # GND
put("P25", 30.6, 5.4)             # 5V
put("R37", 25.4, 6.4, 0)          # DNP HD_R2 -> UART5_RX
# right edge below USB: UART6 + M5/M6 + LED strip
put("P17", 34.4, 21.6, 90)        # T6
put("P18", 34.4, 23.8, 90)        # R6
put("P19", 34.4, 26.0, 90)        # S5
put("P20", 34.4, 28.2, 90)        # S6
put("P10", 31.6, 21.6, 90)        # LED DIN
put("P11", 31.4, 24.4, 90)        # LED 5V
put("P12", 31.4, 27.2, 90)        # LED GND
# bottom edge either side of J2
put("P22", 6.6, 34.4)             # S8
put("P23", 8.8, 34.4)             # RSSI
put("P13", 27.2, 34.4)            # buzzer +
put("P14", 29.4, 34.4)            # buzzer -
# camera / VTX video cluster, left edge between GPS and ELRS
put("P5", 1.4, 16.4, 90)          # CAM1
put("P6", 1.4, 18.6, 90)          # CAM2
put("P7", 4.0, 17.5, 90)          # VTX video
put("P8", 1.4, 20.8, 90)          # cam 5V
put("P9", 4.0, 20.0, 90)          # cam GND
# SWD test pads on top, right of the MCU
put("TP1", 26.0, 17.0)            # SWDIO
put("TP2", 26.0, 14.8)            # SWCLK
put("TP3", 7.8, 18.2)             # NRST
put("TP4", 26.0, 19.2)            # 3V3
put("TP5", 26.0, 21.4)            # GND

# ---------------------------------------------------------------- BOTTOM: IMUs at the centroid
put("U6", 16.2, 17.0, 0, "B")
put("C38", 16.2, 19.2, 0, "B")
put("C39", 16.2, 20.4, 0, "B")
put("C40", 14.2, 17.0, 90, "B")
put("U7", 20.0, 17.0, 0, "B")
put("C41", 20.0, 19.2, 0, "B")
put("C42", 22.0, 17.0, 90, "B")
put("U5", 18.2, 13.2, 0, "B")     # LP5907 for 3V3_IMU
put("C22", 21.0, 13.2, 90, "B")
put("C23", 15.6, 13.2, 90, "B")

# ---------------------------------------------------------------- BOTTOM: upper half (flash, 3V3 LDO, video, USB support)
put("U10", 9.0, 9.5, 90, "B")     # W25N01GV WSON-8 8x6
put("C48", 12.2, 6.8, 90, "B")
put("R29", 12.2, 12.4, 90, "B")
put("R30", 11.0, 12.4, 90, "B")
put("U4", 25.4, 6.6, 0, "B")      # LP38692 SOT-223-5
put("C19", 20.2, 5.6, 90, "B")
put("C20", 30.4, 9.4, 90, "B")
put("C21", 29.0, 9.6, 90, "B")
put("C18", 21.6, 6.0, 90, "B")    # 5V_SYS bulk
put("D5", 21.2, 9.2, 0, "B")      # 5V -> 5V_SYS
put("D4", 30.4, 13.2, 90, "B")    # VBUS -> 5V_SYS
put("U13", 26.6, 13.8, 90, "B")   # USB ESD, under the USB connector
put("C51", 28.6, 17.2, 90, "B")
put("R36", 27.4, 17.2, 90, "B")
put("R34", 31.4, 17.4, 90, "B")
put("R35", 32.6, 17.4, 90, "B")
put("SW1", 15.0, 3.6, 0, "B")     # BOOT button, bottom side, top edge
put("U11", 6.6, 17.6, 90, "B")    # camera switch near the video pads
put("C49", 8.8, 17.6, 90, "B")
put("R31", 8.8, 20.0, 90, "B")
put("U12", 28.0, 21.6, 90, "B")   # LED strip buffer near the LED pads
put("C50", 30.2, 21.4, 90, "B")
put("R32", 26.0, 21.8, 90, "B")
put("R33", 30.2, 24.0, 90, "B")
put("Q2", 25.8, 25.2, 0, "B")     # VTX off FET near U2 EN
put("R11", 23.6, 23.0, 90, "B")
put("R12", 22.4, 23.0, 90, "B")
put("D10", 3.6, 9.2, 90, "B")     # power LED
put("R13", 3.6, 12.0, 90, "B")

# ---------------------------------------------------------------- BOTTOM: power stage (lower half)
# battery entry on the bottom edge
put("P1", 11.6, 33.2, 0, "B")     # VBAT pad
put("P2", 24.4, 33.2, 0, "B")     # GND pad
put("D1", 18.0, 33.4, 0, "B")     # TVS
put("C1", 18.0, 30.0, 0, "B")     # entry cap
put("R14", 14.4, 30.2, 90, "B")   # VBAT divider
put("R15", 13.2, 30.2, 90, "B")
put("C24", 12.0, 30.2, 90, "B")
# 5 V buck, bottom-left
put("U1", 8.4, 25.6, 90, "B")
put("C2", 12.4, 22.8, 90, "B")
put("C3", 12.4, 26.8, 90, "B")
put("C4", 10.6, 22.0, 0, "B")
put("R1", 5.8, 21.6, 0, "B")
put("R2", 5.8, 22.8, 0, "B")
put("R3", 5.4, 27.4, 90, "B")
put("C5", 4.2, 25.6, 90, "B")
put("L1", 7.6, 31.0, 0, "B")
put("R4", 3.6, 28.6, 90, "B")
put("R5", 4.8, 30.0, 90, "B")
put("C6", 10.6, 35.0 - 1.4, 0, "B")
put("C7", 1.9, 23.2, 90, "B")
put("C8", 1.9, 28.2, 90, "B")
put("C9", 4.0, 23.0, 90, "B")
# 10 V buck, bottom-right
put("U2", 27.6, 27.8, 90, "B")
put("C10", 23.6, 26.6, 90, "B")
put("C11", 23.6, 30.4, 90, "B")
put("C12", 25.4, 30.6, 0, "B")
put("R6", 30.6, 24.0, 0, "B")
put("R7", 30.6, 25.2, 0, "B")
put("R8", 31.4, 29.4, 90, "B")
put("C13", 31.6, 27.0, 90, "B")
put("L2", 28.6, 32.8, 0, "B")
put("R9", 32.8, 30.4, 90, "B")
put("R10", 33.8, 27.6, 90, "B")
put("C14", 34.1, 23.0, 90, "B")
put("C15", 34.1, 17.9, 90, "B")
put("C16", 31.8, 34.4, 0, "B")
put("C17", 32.6, 21.2, 90, "B")
put("P3", 34.4, 9.6, 0, "B")      # 10V pad
put("P4", 34.4, 5.6 + 0.4, 0, "B")
# CURR / RSSI protection and buzzer driver, bottom side near the ESC
put("R38", 15.2, 27.0, 90, "B")
put("C52", 16.4, 27.0, 90, "B")
put("D7", 18.6, 26.4, 0, "B")
put("R39", 15.2, 23.6, 90, "B")
put("C53", 16.4, 23.6, 90, "B")
put("D8", 18.6, 23.0, 0, "B")
put("R40", 21.4, 28.6, 90, "B")
put("Q1", 21.6, 31.6, 0, "B")
put("D9", 15.2, 31.8, 90, "B")
