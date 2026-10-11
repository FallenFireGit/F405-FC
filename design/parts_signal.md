# F405-FC signal-part sourcing (DigiKey only)

Status: research pass on 2026-10-11 for Gate 0 and Gate 2 input. This is not yet the Gate 2 BOM.

## How this was verified, and its limits

- digikey.com, api.digikey.com, octopart, findchips and oemsecrets could not be fetched from this environment: the proxy refused the connection or DNS failed.
- All evidence comes from web-search snippets of DigiKey product pages. These include:
  - regional DigiKey storefronts, such as digikey.ca, .co.uk, .cn and .com.mx
  - DigiKey "punchouttest.digikey.*" and "azcus.digikey.com" catalogue mirrors
  - aggregator snapshots (findchips, flux.ai)
- **Stock numbers are undated snapshots.** They often disagree between regional pages. Treat each figure as "this SKU exists and has been stocked", not as live inventory.
- **Before ordering, the Gate 2 auditor must re-check every line on digikey.com.**

Confidence labels:
- **CONFIRMED-PN**: the DigiKey part number appeared verbatim on a DigiKey page, in a DigiKey URL, or on an aggregator's DigiKey row.
- **LISTED**: a DigiKey product page exists for the MPN, but the cut-tape PN was not seen. The PN given is DigiKey's usual pattern and is marked "pattern, unconfirmed".
- **NOT FOUND**: no DigiKey listing was seen.

Full evidence URLs are in `review/sourcing_research_notes.md`.

---

## 1. Signal parts

| # | Function | MPN (mfr) | Package | Key rating | DigiKey PN (CT unless noted) | Confidence | Stock / lifecycle seen | ~Price | Alternate at DigiKey |
|---|---|---|---|---|---|---|---|---|---|
| 1 | MCU | STM32F405RGT6 (ST) | LQFP-64 10x10 | 168 MHz, 1 MB flash | **497-11767-ND** (tray) | CONFIRMED-PN | Active; aggregator shows DigiKey stock about 26k; lead time 15-20 wk | about $11.67 @1 | STM32F405RGT7TR: **497-19007-1-ND** (CONFIRMED-PN; about 4,375 in stock; 105 °C grade) |
| 2 | IMU 1 | ICM-42688-P (TDK InvenSense) | LGA-14 2.5x3x0.91 | 6-axis, SPI | **1428-ICM-42688-PCT-ND** | CONFIRMED-PN | Active. **0 in stock** on NZ, MX and CA snapshots; 16-26 wk lead time. **STOCK RISK** | n/a | LSM6DSOXTR (ST): **497-18367-1-ND** (CONFIRMED-PN; 5,187 US; about $4.07 @1). Different pinout and footprint; Betaflight supports it |
| 3 | IMU 2 | BMI270 (Bosch) | LGA-14 2.5x3x0.83 | 6-axis, SPI | **828-1091-1-ND** | CONFIRMED-PN | Active. **0 in stock** on the MX snapshot; 8 wk lead time. **STOCK RISK** | $3.80 @1 | LSM6DSOXTR (as above) |
| 4 | Baro | BMP390 (Bosch) | LGA-10 2x2x0.75 | 30-125 kPa, I2C/SPI | **828-BMP390CT-ND** | CONFIRMED-PN | MX and CA snapshots 0; CN snapshot 11,591; 12 wk lead time | $3.30 @1 | No verified alternate. BMP388 (828-1079-1-ND per a Bosch forum post) is reported discontinued; BMP384 was not found |
| 5 | Mag | IIS2MDCTR (ST). "IIS2MDC" is only orderable as **IIS2MDCTR** | LGA-12 2x2x0.7 | 3-axis, I2C | **497-17728-1-ND** | CONFIRMED-PN | Active; in stock 1,067 (US) or 23,353 (azcus) | $2.67 @1 | LIS2MDLTR: **497-17588-1-ND** (CONFIRMED-PN; Active; mirrors out of stock; pin-compatible consumer twin) |
| 6 | Blackbox NAND | **W25N01GVZEIG (Winbond), WSON-8 8x6**, the DigiKey-stocked option | WSON-8 8x6 | 1 Gbit SPI NAND, 104 MHz | **W25N01GVZEIGCT-ND** (TR: 256-W25N01GVZEIGTR-ND) | CONFIRMED-PN (findchips DigiKey row, DigiKey UK URL) | TR listing (DigiKey 5803931) Active; aggregators show 106k-137k at DigiKey; 22-24 wk lead time. **Caution:** a second DigiKey listing (15181734) shows "Obsolete", and one broker marks the GV family NRND | $3.01-3.76 @1 | W25N01GVSFIG (SOIC-16): DigiKey 15181740, Active but **out of stock and backorder unavailable**. Not recommended. W25N01KVZEIR is the successor (4-bit ECC); no DigiKey listing found and Betaflight support is not verified |
| 7 | USB-C | USB4105-GF-A (GCT) | 16-pin USB 2.0 receptacle, SMT + TH posts | 5 A, 48 V | **2073-USB4105-GF-ACT-ND** | CONFIRMED-PN | Active; 7 wk lead time | n/a | USB4110-GF-A: listed as "2073-USB4110-GF-A-1-ND" in a snippet (the format is unusual, so re-check); 16,969 (CA) and 27,749 (CH) in stock; CAD 1.56 @10 |
| 8 | USB ESD | USBLC6-2SC6 (ST) | SOT-23-6 | 5.25 V, 17 V clamp | **497-5235-1-ND** | CONFIRMED-PN | Active; **mirrors out of stock**; 25 wk lead time. Do NOT pick the UMW-branded "USBLC6-2SC6" (4518- PNs, different specs) | n/a | TPD2E2U06DRLR (TI, SOT-5 DRL): **296-38361-1-ND** (CONFIRMED-PN; 535 CA, 455 KR) |
| 9 | ESC connector | SM08B-SRSS-TB(LF)(SN) (JST) | SH 1.0 mm, 8-pin, R/A SMD | 1 A/pin, 50 V | **455-1808-1-ND** | CONFIRMED-PN | Active; lead time 16-42 wk | $0.84 @1 | BM08B-SRSS-TB(LF)(SN), top entry: 455-1794-1-ND (CONFIRMED-PN) |
| 10 | HD VTX and GPS connectors | SM06B-SRSS-TB(LF)(SN) (JST) | SH 6-pin R/A | 1 A, 50 V | **455-1806-1-ND** | CONFIRMED-PN | Active; UK 19,550; US snapshot out of stock | n/a | BM06B-SRSS-TB (top entry). PN not checked |
| 11 | ELRS connector | SM04B-SRSS-TB(LF)(SN) (JST) | SH 4-pin R/A | 1 A, 50 V | **455-1804-1-ND** (CT suffix inferred; 455-1804-6-ND Digi-Reel seen) | CONFIRMED family / CT pattern | Active | n/a | BM04B-SRSS-TB (top entry). PN not checked |
| 12 | 8 MHz HSE crystal | **ECS-80-8-33-JEN-TR3** (ECS) | 3.2x2.5 4-SMD | 8 MHz, **CL 8 pF**, ESR 400 Ω, ±20 ppm (one snippet says ±50 ppm; check) | 50-ECS-80-8-33-JEN-TR3CT-ND (pattern from sibling, unconfirmed) | LISTED (DigiKey 15282973) | Active; **23,687 in stock** (azcus); 9 wk lead time | $0.58 @1 | ECS-80-8-33-JGN-TR3 (±30 ppm, 400 Ω): **50-ECS-80-8-33-JGN-TR3CT-ND** (CONFIRMED-PN; 0 stock on the MX snapshot; $0.61 @1) |
| 13 | BOOT button | **PTS810 SJM 250 SMTR LFS** (C&K) | 4.2x3.2x2.5 mm, top actuated | 160 gf, 50 mA 16 V | **CKN10502CT-ND** | CONFIRMED-PN | DigiKey FR 10,793; DE out of stock | €0.44 @1 | EVQ-P7J01P (Panasonic; side-actuated right-angle, 160 gf): DigiKey 4429451, 2,956 US, $0.28 @1; CT PN not seen. EVQ-P7A01P (220 gf): P16763CT-ND (CONFIRMED-PN; DE out of stock) |
| 14 | LED blue | LTST-C191TBKT (Lite-On) | 0603 | 470 nm, Vf 3.3 V | **160-1647-1-ND** | CONFIRMED-PN | Active; US/CA out of stock; EU about 335k; 20 wk lead time | about CAD 0.37 @1 | APT1608QBC/D (Kingbright): **754-1434-1-ND** (CONFIRMED-PN) |
| 15 | LED green | LTST-C191KGKT (Lite-On) | 0603 | 571 nm | **160-1446-1-ND** | CONFIRMED-PN | ES mirror out of stock | n/a | APT1608SGC (Kingbright, 568 nm): **754-1121-1-ND** (CONFIRMED-PN; 1,240,510 MX) |
| 16 | LED red (power) | LTST-C191KRKT (Lite-On) | 0603 | 631 nm, Vf 2 V | **160-1447-1-ND** | CONFIRMED-PN | Active; about 480k-670k | n/a | APT1608EC (Kingbright, 617 nm): **754-1117-1-ND** (CONFIRMED-PN; about 149k; $0.19 @1) |
| 17 | N-MOSFET (buzzer, general) | PMV40UN2R (Nexperia) | SOT-23 | 30 V, 3.7 A | **1727-1900-1-ND** | CONFIRMED-PN | Listed; **US page out of stock, backorder unavailable**; MX backorder 12 wk | **$0.268 @10** | PMV30UN2R: DigiKey 5395607 (LISTED; PN not seen) |
| 18 | Small-signal N-MOSFET | 2N7002-7-F (Diodes) | SOT-23 | 60 V, 115 mA | **2N7002-FDICT-ND** | CONFIRMED-PN | **Out of stock, 40 wk lead time** | n/a | **NX7002AK,215 (Nexperia): 1727-1289-1-ND** (CONFIRMED-PN; 6 wk lead time). Preferred |
| 19 | Camera-select analog switch | TS5A3159ADBVR (TI) | SOT-23-6 | SPDT 0.9 Ω, 1.65-5.5 V | **296-19265-1-ND** | CONFIRMED-PN | **Active**; mirrors out of stock; lead time 6-12 wk | n/a | TS5A3159DBVR (1.1 Ω): DigiKey 686662 (LISTED; PN not seen) |
| 20 | LED-strip 3V3→5V buffer | SN74AHCT1G125DBVR (TI) | SOT-23-5 | VCC 5 V, TTL inputs | **296-4708-1-ND** | CONFIRMED-PN | Mirrors out of stock; 12 wk lead time | n/a | **SN74LV1T125DBVR: 296-37172-1-ND** (CONFIRMED-PN; 6 wk lead time). Also 74AHCT1G125GV,125: 1727-6024-1-ND (CONFIRMED-PN). 74AHCT1G125GW,125 (DigiKey 1229653): out of stock, 20 wk lead time |
| 21 | Clamp diode | BAT54S-7-F (Diodes) | SOT-23 | 30 V, 200 mA, series pair | **BAT54S-FDICT-ND** | CONFIRMED-PN | ES mirror out of stock; 12 wk lead time | n/a | DigiKey lists Vishay and onsemi BAT54S substitutes. MPN and PN not captured (unverified) |
| 22 | Ferrite 0603 | BLM18PG221SN1D (Murata) | 0603 | 220 Ω@100 MHz, 1.4 A, 100 mΩ | **490-5221-1-ND** | CONFIRMED-PN (DigiKey URL) | Active; lead time 24-29 wk | $0.10-0.14 @1 | BLM18KG601SN1D (600 Ω, 1.3 A, 150 mΩ): **490-5258-1-ND** (CONFIRMED-PN; about 172k-749k in stock) |
| 23 | 27 MHz OSD crystal (only if the OSD survives) | ABM8-27.000MHZ-B2-T (Abracon) | 3.2x2.5 | 27 MHz, 18 pF, 50 Ω | 535-9141-1-ND (535-9141-x family seen) | CONFIRMED family | **Out of stock**; 10 wk lead time | n/a | ECS-270-18-33-AGM-TR: DigiKey 8023270, **0 in stock**. Moot if the AT7456E is dropped (see below) |

### Analog OSD: AT7456E. **Not sold at DigiKey.**
- No DigiKey listing for the AT7456E chip was found in any search, including restricted to digikey.com, .ca, .co.uk and .de.
- The chip is sold by LCSC/JLCPCB (C82351, ZHONGKEWEI, HTSSOP-28) and by marketplace sellers.
- The only DigiKey item that contains it is the **DFRobot DFR0515** FireBeetle OSD expansion *board* (DigiKey 8598401, Active). That is not a component that can go on a 36x36 FC.
- The original **MAX7456EUI+ / +T** is listed at DigiKey but **Obsolete**: EOL notice 15-Jan-2016, quantity 0.
- **Verdict:** the analog OSD chip fails the DigiKey-only rule. Drop it and make MSP DisplayPort the primary OSD. See `review/sourcing_research_notes.md` §1.

### 8 MHz crystal engineering note (for the HW reviewer)
- 8 MHz crystals in 3.2x2.5 are only offered with ESR of about 300-500 Ω. Searches found no 8 MHz 3225 part with ESR ≤ 200 Ω at DigiKey.
- A low CL keeps the critical gm small: gm_crit = 4·ESR·(2πf)²·(C0+CL)².
  - ECS-80-8-33-JEN-TR3 (400 Ω, CL 8 pF, assumed C0 ≈ 1.5 pF): gm_crit ≈ 0.37 mA/V.
  - The 5x3.2 ABM3B-8.000MHZ-B2-T (200 Ω, 18 pF): gm_crit ≈ 0.9 mA/V. This is worse, so it is rejected.
- Check this against the STM32F405 datasheet HSE gm/Gm_crit_max figure, which has not been re-read in this pass.
- Load caps: CL1 = CL2 ≈ 2·(8 pF − ~3 pF stray) ≈ 10 pF C0G 0402/0603.

---

## 2. Passive families: DigiKey PN conventions (verified examples)

### Yageo RC series (thick film): **pattern is predictable**
The DigiKey CT PN is `311-<value><size letter>RCT-ND`.
- `<value>` uses 3 significant digits with a decimal (10.0K, 1.00K, 100K, 88.7K).
- The size letter is **H = 0603** and **L = 0402**.

Variants follow the same scheme: TR = `...RTR-ND`, Digi-Reel = `...RDKR-ND`.

| MPN | DigiKey CT PN | Evidence |
|---|---|---|
| RC0603FR-0710KL (10 k 1 % 0603) | **311-10.0KHRCT-ND** | DigiKey listing snippet, 12.27 M in stock, $0.006 @10 |
| RC0603FR-071KL (1 k 1 % 0603) | **311-1.00KHRCT-ND** (TR 311-1.00KHRTR-ND, DKR 311-1.00KHRDKR-ND) | DigiKey regional listings |
| RC0402FR-0710KL (10 k 1 % 0402) | **311-10.0KLRCT-ND** | azcus.digikey.com listing, about 8.28 M in stock |
| RC0402FR-07100KL (100 k 1 % 0402) | **311-100KLRCT-ND** | azcus.digikey.com listing |

The same pattern gives values in the power BOM that were **not individually seen**. Mark them "pattern, unconfirmed" in the BOM:
- RC0603FR-07357KL → 311-357KHRCT-ND
- RC0603FR-0788K7L → 311-88.7KHRCT-ND

### Samsung CL series MLCC: **pattern is NOT derivable from the MPN**
- Older parts carry sequential PNs: `1276-<serial>-1-ND` for CT, `-2-ND` for TR, `-6-ND` for Digi-Reel.
- The serial has no relation to the value. **Every Samsung cap needs its own lookup.**
- Newer listings sometimes use `1276-<MPN>CT-ND`.

| MPN | DigiKey CT PN | Evidence |
|---|---|---|
| CL10B104KB8NNNC (100 nF 50 V X7R 0603) | **1276-1000-1-ND** | azcus.digikey.com; Active; 31 wk lead time |
| CL05B104KO5NNNC (100 nF 16 V X7R 0402) | **1276-1001-1-ND** | azcus.digikey.com; Active |
| CL31A226KAHNNNE (22 µF 25 V X5R 1206) | **1276-3047-1-ND** | DigiKey URL; **out of stock, 31-61 wk lead time** |
| CL32B106KBJNNNE (10 µF 50 V X7R 1210) | **1276-3387-1-ND** | DigiKey URL |
| CL10A106KP8NNNC (10 µF 10 V X5R 0603) | 1276-1192-1-ND | aggregator listing only (about 349,796) |

### Murata GRM
- Murata uses sequential `490-<serial>-1-ND` (for example GRM32ER71H106KA12L = **490-6544-1-ND**, from a DigiKey URL). Each part needs its own lookup.
- Newer Murata listings use `490-<MPN>CT-ND`.
