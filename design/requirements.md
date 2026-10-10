# F405-FC requirements (source of truth for Gate 0)

## Product
Quadcopter flight controller, Betaflight (and INAV) compatible, built around the STM32F405RGT6 (LQFP-64).

## Mechanical
- 36 x 36 mm board, 30.5 x 30.5 mm M3 mounting holes (3.2 mm NPTH or PTH, rounded corners)
- Corner holes take soft-mount grommets, so a 4.6 mm keepout diameter around each hole
- 4-layer, 1.6 mm, JLCPCB JLC04161H-7628 stackup, 1 oz outer / 0.5 oz inner
- Height: top side max 3.5 mm (except USB-C), bottom side max 2.5 mm
- USB-C at a board edge

## Assembly constraints
- Hand-soldered / hot-air with stencil. Passives 0402 minimum (0603 preferred where space allows)
- No BGA, no WLCSP. LGA/QFN allowed only where unavoidable (IMUs, baro, mag)
- Every part must be stocked at **DigiKey**

## Electrical features
- Input: 2-6S LiPo (6.0 V to 25.2 V nominal, survive 35 V transients). TVS on VBAT
- Rails: 5 V / 2.5 A buck (receiver, GPS, LED strip, camera, USB OR-ing), 10 V / 2 A buck (HD/analog VTX, switchable for pit mode), 3.3 V for the MCU and peripherals, separate low-noise 3.3 V LDO for the IMUs
- USB-C (USB 2.0 FS device, CC pull-downs 5.1k, ESD protection) powers the MCU, sensors and flash when no battery is connected, back-feed protected
- Two IMUs on SPI: ICM-42688-P and BMI270, each with its own CS and its own data-ready INT on separate EXTI lines
- Barometer BMP390 on I2C
- Magnetometer IIS2MDC on the same I2C, plus external I2C pads (GPS mag)
- Blackbox W25N01GV (1 Gbit SPI NAND), own SPI bus
- Analog OSD AT7456E on its own SPI bus, 27 MHz crystal, CAM video in, VTX video out
- Camera select: two camera inputs, one PINIO GPIO selects which goes to the OSD input
- VTX power switch: PINIO GPIO high-side switch on the 10 V rail (pit mode / power cut)
- HD VTX connector: JST-SH 1.0 mm 6-pin (10V, GND, TX, RX, GND, SBUS/R2) on a full UART
- ESC connector: JST-SH 1.0 mm 8-pin (VBAT, GND, CURR, M1, M2, M3, M4, TLM) - Betaflight/BLHeli standard order
- 6 UART ports total (USART1/2/3/6 and UART4/5): ELRS RX (JST-SH 4-pin), GPS (JST-SH 6-pin incl. SDA/SCL), HD VTX, ESC telemetry RX, 2 spare
- 4 motor outputs on the ESC connector + 4 extra motor/servo pads (octo or servos) if timers allow
- WS2812 LED strip output (5V pad + DIN with series resistor)
- Buzzer output (low-side N-MOSFET, 5V buzzer)
- ADC: VBAT divider (10k/1k, max 36 V), current sense input from ESC, RSSI/analog input
- 2 status LEDs (blue + green) and a power LED
- BOOT button (BOOT0 high) and SWD test pads (SWDIO, SWCLK, NRST, 3V3, GND)
- 8 MHz HSE crystal

## Not included (decided)
- Onboard ELRS receiver: removed (RF + hand-solder risk). External ELRS on USART with JST-SH 4-pin instead
- SD card: not needed (NAND flash for blackbox)
