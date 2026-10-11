# INAV target: F405FC (pin map rev C)

Companion to `design/pinmap.md` (rev C) and `design/betaflight_config.txt`. This is a target sketch in INAV's
`src/main/target/<NAME>/` format (INAV 7.x/8.x). It has **not** been compiled; build it in an INAV tree before release.

Timer DMA encodings are from INAV `timer_def_stm32f4xx.h` (`datasheets/inav_src/`). The relevant lines:

| Timer/channel | INAV DMA options (dmavar 0, 1, ...) | Used |
|---|---|---|
| TIM3_CH3 (PB0, M1) | D(1,7,5) | dmavar 0 → DMA1 S7 |
| TIM3_CH4 (PB1, M2) | D(1,2,5) | 0 → DMA1 S2 |
| TIM2_CH3 (PB10, M3) | D(1,1,3) | 0 → DMA1 S1 |
| TIM2_CH4 (PB11, M4) | D(1,7,3), **D(1,6,3)** | **1 → DMA1 S6** (dmavar 0 = S7 clashes with M1; pin-map decision 5) |
| TIM8_CH3 (PC8, M5) | D(2,2,0), D(2,4,7) | 0 → DMA2 S2 |
| TIM8_CH4 (PC9, M6) | D(2,7,7) | 0 → DMA2 S7 |
| TIM4_CH2 (PB7, M7) | D(1,3,2) | 0 → DMA1 S3 (free: no SPI2 in rev C) |
| TIM5_CH1 (PA0, M8) | D(1,2,6) | **clashes with M2 (DMA1 S2)**: PWM/servo only. INAV assigns DMA per DEF_TIM, so M8 must be declared with `TIM_USE_ANY`/servo use and never used for DShot |
| TIM1_CH1 (PA8, LED) | D(2,6,0), ... | 0 → DMA2 S6 |

## target.h

```c
#pragma once

#define TARGET_BOARD_IDENTIFIER "F4FC"
#define USBD_PRODUCT_STRING     "F405FC"

#define LED0                    PB14   // blue, active low (sink)
#define LED1                    PB15   // green, active low
#define BEEPER                  PB2    // N-FET gate, active high
#define BEEPER_INVERTED

// ---- IMUs on SPI1 (INAV uses one IMU at a time; both are detected, first found wins)
#define USE_SPI
#define USE_SPI_DEVICE_1
#define SPI1_SCK_PIN            PA5
#define SPI1_MISO_PIN           PA6
#define SPI1_MOSI_PIN           PA7

#define USE_IMU_ICM42605        // INAV's ICM42605 driver also handles ICM-42688-P
#define IMU_ICM42605_ALIGN      CW0_DEG      // placeholder until PCB orientation is fixed
#define ICM42605_SPI_BUS        BUS_SPI1
#define ICM42605_CS_PIN         PA4
#define ICM42605_EXTI_PIN       PC4

#define USE_IMU_BMI270
#define IMU_BMI270_ALIGN        CW0_DEG      // placeholder
#define BMI270_SPI_BUS          BUS_SPI1
#define BMI270_CS_PIN           PA15
#define BMI270_EXTI_PIN         PC14

// ---- Blackbox flash on SPI3
#define USE_SPI_DEVICE_3
#define SPI3_SCK_PIN            PB3
#define SPI3_MISO_PIN           PB4
#define SPI3_MOSI_PIN           PB5
#define USE_FLASHFS
#define USE_FLASH_W25N01G
#define W25N01G_SPI_BUS         BUS_SPI3
#define W25N01G_CS_PIN          PB6
#define ENABLE_BLACKBOX_LOGGING_ON_SPIFLASH_BY_DEFAULT

// ---- I2C1: baro, mag, external GPS mag
#define USE_I2C
#define USE_I2C_DEVICE_1
#define I2C1_SCL                PB8
#define I2C1_SDA                PB9
#define DEFAULT_I2C_BUS         BUS_I2C1

#define USE_BARO
#define BARO_I2C_BUS            DEFAULT_I2C_BUS
#define USE_BARO_BMP388          // BMP390 uses the BMP388 driver (chip id 0x60)

#define USE_MAG
#define MAG_I2C_BUS             DEFAULT_I2C_BUS
#define USE_MAG_ALL              // see "Magnetometer" below for the IIS2MDC

#define TEMPERATURE_I2C_BUS     DEFAULT_I2C_BUS
#define PITOT_I2C_BUS           DEFAULT_I2C_BUS
#define RANGEFINDER_I2C_BUS     DEFAULT_I2C_BUS

// ---- OSD: no analog OSD chip (design/decisions.md D-01). MSP DisplayPort on UART1.

// ---- UARTs
#define USE_VCP
#define USE_UART1               // HD VTX (MSP DisplayPort)
#define UART1_TX_PIN            PA9
#define UART1_RX_PIN            PA10
#define USE_UART2               // ELRS
#define UART2_TX_PIN            PA2
#define UART2_RX_PIN            PA3
#define USE_UART3               // GPS
#define UART3_TX_PIN            PC10
#define UART3_RX_PIN            PC11
#define USE_UART4               // ESC telemetry, RX only (PA0 is M8)
#define UART4_TX_PIN            NONE
#define UART4_RX_PIN            PA1
#define USE_UART5               // spare
#define UART5_TX_PIN            PC12
#define UART5_RX_PIN            PD2
#define USE_UART6               // spare
#define UART6_TX_PIN            PC6
#define UART6_RX_PIN            PC7
#define SERIAL_PORT_COUNT       7   // VCP + 6

#define DEFAULT_RX_TYPE         RX_TYPE_SERIAL
#define SERIALRX_PROVIDER       SERIALRX_CRSF
#define SERIALRX_UART           SERIAL_PORT_USART2

// ---- ADC (ADC1 on DMA2 Stream 4; Stream 0 is SPI1_RX)
#define USE_ADC
#define ADC_INSTANCE            ADC1
#define ADC1_DMA_STREAM         DMA2_Stream4
#define ADC_CHANNEL_1_PIN       PC0    // VBAT, 10k/1k
#define ADC_CHANNEL_2_PIN       PC1    // CURR (10k + 10 nF + BAT54S)
#define ADC_CHANNEL_3_PIN       PC5    // RSSI
#define VBAT_ADC_CHANNEL        ADC_CHN_1
#define CURRENT_METER_ADC_CHANNEL ADC_CHN_2
#define RSSI_ADC_CHANNEL        ADC_CHN_3
#define VBAT_SCALE_DEFAULT      1100
#define CURRENT_METER_SCALE     400    // placeholder, ESC dependent

// ---- PINIO (USER1 = VTX power cut, USER2 = camera select)
#define USE_PINIO
#define USE_PINIOBOX
#define PINIO1_PIN              PC15   // HIGH = VTX off (pulls 10 V buck EN low)
#define PINIO2_PIN              PC13   // HIGH = CAM2

// ---- LED strip
#define USE_LED_STRIP
#define WS2811_PIN              PA8

#define DEFAULT_FEATURES        (FEATURE_TX_PROF_SEL | FEATURE_CURRENT_METER | FEATURE_TELEMETRY | FEATURE_VBAT | FEATURE_OSD | FEATURE_BLACKBOX)
#define USE_DSHOT
#define USE_ESC_SENSOR
#define USE_SERIAL_4WAY_BLHELI_INTERFACE

#define TARGET_IO_PORTA         0xffff
#define TARGET_IO_PORTB         0xffff
#define TARGET_IO_PORTC         0xffff
#define TARGET_IO_PORTD         (BIT(2))

#define MAX_PWM_OUTPUT_PORTS    8
```

## target.c

```c
#include <stdint.h>
#include "platform.h"
#include "drivers/bus.h"
#include "drivers/io.h"
#include "drivers/pwm_mapping.h"
#include "drivers/timer.h"
#include "drivers/pinio.h"
#include "drivers/sensor.h"

timerHardware_t timerHardware[] = {
    DEF_TIM(TIM3, CH3, PB0,  TIM_USE_OUTPUT_AUTO, 0, 0),  // M1  DMA1 S7
    DEF_TIM(TIM3, CH4, PB1,  TIM_USE_OUTPUT_AUTO, 0, 0),  // M2  DMA1 S2
    DEF_TIM(TIM2, CH3, PB10, TIM_USE_OUTPUT_AUTO, 0, 0),  // M3  DMA1 S1
    DEF_TIM(TIM2, CH4, PB11, TIM_USE_OUTPUT_AUTO, 0, 1),  // M4  DMA1 S6 (dmavar 1!)
    DEF_TIM(TIM8, CH3, PC8,  TIM_USE_OUTPUT_AUTO, 0, 0),  // M5  DMA2 S2
    DEF_TIM(TIM8, CH4, PC9,  TIM_USE_OUTPUT_AUTO, 0, 0),  // M6  DMA2 S7
    DEF_TIM(TIM4, CH2, PB7,  TIM_USE_OUTPUT_AUTO, 0, 0),  // M7  DMA1 S3
    DEF_TIM(TIM5, CH1, PA0,  TIM_USE_SERVO,       0, 0),  // S8  servo only: DMA1 S2 belongs to M2 (no DShot)
    DEF_TIM(TIM1, CH1, PA8,  TIM_USE_LED,         0, 0),  // LED strip DMA2 S6
};

const int timerHardwareCount = sizeof(timerHardware) / sizeof(timerHardware[0]);
```

Note on S8: INAV's `DEF_TIM` macro always records the dmavar-0 stream. Because the pin is declared `TIM_USE_SERVO`, INAV drives it
as plain PWM and never starts DMA on it, so it does not conflict with M2 at run time. If INAV's mixer ever assigns it as a motor
with DShot, the M2/M8 DMA clash would break M2; the target therefore keeps it servo-only. **Confirm with an INAV build + bench test.**

## Driver checklist (INAV)

| Device | INAV support | Status |
|---|---|---|
| ICM-42688-P | `USE_IMU_ICM42605` driver detects ICM-42688-P (WHO_AM_I 0x47) | believed supported (INAV 5+); confirm in tree |
| BMI270 | `USE_IMU_BMI270` | supported |
| Dual IMU | INAV uses **one** IMU; it picks the first detected | gyro 2 unused under INAV |
| BMP390 | `USE_BARO_BMP388` (BMP390 chip id accepted) | believed supported; confirm chip-id list in the INAV tree |
| IIS2MDC / LIS2MDL | **No INAV driver as of the sources on file** (pinmap open question 1) | onboard mag unusable in INAV; use a GPS module's mag on the external I2C (address clash: onboard IIS2MDC is fixed 0x1E — an HMC5883-class external mag at 0x1E would clash; QMC5883L (0x0D) or IST8310 (0x0E) are fine) |
| W25N01GV | `USE_FLASH_W25N01G` | supported |
| MSP DisplayPort OSD | supported (`osd_video_system = HDZERO/DJIWTF/AVATAR`) | supported |

Unverified items (no INAV tree on file beyond `timer_def_stm32f4xx.h`): driver names and the INAV ADC/PINIO macro names above follow
current INAV conventions from memory and must be checked by compiling.
