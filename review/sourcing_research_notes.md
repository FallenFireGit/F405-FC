# Sourcing research notes (DigiKey-only rule): evidence log

Researcher: sourcing subagent, 2026-10-11. This covers the AT7456E/MAX7456 question, signal parts, power parts and passive conventions.

The signal-part table and passive conventions are summarised in `design/parts_signal.md`. This file adds:
- the evidence trail
- the AT7456E verdict
- the power-part findings

## Method and limits (read first)

**Direct fetches failed** (tried 2026-10-11):
- www.digikey.com, api.digikey.com and www.mouser.com: the proxy rejected CONNECT with 403.
- octopart.com, www.findchips.com, www.oemsecrets.com and www.nexperia.com: DNS failed (ENOTFOUND).

**Evidence used instead.** All of it comes from web-search snippets:
- DigiKey product pages on www.digikey.com and regional stores (digikey.ca, .co.uk, .com.au, .cn, .com.mx, .lt, ...)
- DigiKey catalogue mirrors (`azcus.digikey.com`, `punchouttest.digikey.*`)
- aggregator rows that name DigiKey (origin-www.findchips.com, flux.ai)
- manufacturer pages (coilcraft.com)

**Rules for reading the stock figures:**
- They are undated snapshots, and regional mirrors often disagree.
- "0 / out of stock" on one mirror and thousands on another is common.
- These snapshots do NOT prove live stock. The Gate 2 auditor must re-check on digikey.com.

**Confidence labels:**
- CONFIRMED-PN: the PN was seen verbatim.
- LISTED: a DigiKey product page exists, but the PN is a pattern.
- NOT FOUND: no DigiKey listing was seen.

No DigiKey PN in this file was invented. Every PN marked "pattern" is DigiKey's usual scheme and was not observed.

---

## 1. AT7456E / MAX7456: verdict

### AT7456E (ZHONGKEWEI, "MAX7456 compatible"). **NOT FOUND at DigiKey**

Searches run:
- "AT7456E digikey"
- "AT7456E OSD" restricted to digikey.com, .ca, .co.uk and .de
- an extended search for "AT7456E digikey marketplace / ZHONGKEWEI distributor"

What they found:
- **No DigiKey catalogue or marketplace listing for the chip.** The only DigiKey hits for "AT7456E" were unrelated Yageo "AT" resistors and the DFRobot module below.
- **Where the chip is sold:**
  - LCSC C82351: ZHONGKEWEI, about 35k in stock, about $3.59 @1 and $1.98 @1k ([lcsc](https://www.lcsc.com/product-image/C82351.html))
  - JLCPCB C82351: HTSSOP-28-EP, 3.15-5.25 V
  - Alibaba, AliExpress and eBay
- **The only DigiKey item containing an AT7456E:** DFRobot **DFR0515** "AT7456E On-Screen Display (OSD) FireBeetle Platform Evaluation Expansion Board".
  - DigiKey product 8598401, Active. The AU snapshot shows 41 in stock at about AUD 14.62.
  - Sources: [digikey.com](https://www.digikey.com/en/products/detail/dfrobot/DFR0515/8598401), [digikey.com.au](https://www.digikey.com.au/en/products/detail/dfrobot/DFR0515/8598401).
  - This is a hobby module board. It is not a placeable component, and harvesting chips from modules is not a sourcing strategy.

### MAX7456 (Maxim/ADI). **At DigiKey but OBSOLETE, quantity 0**

| Listing | DigiKey | Status seen |
|---|---|---|
| MAX7456EUI+ (tube) | product 1701658. The URL path shows "MAX7456EUI-ND"; the true PN is presumably MAX7456EUI+-ND ('+' is stripped in URLs) | Obsolete; "end-of-life notice dated 15 January 2016" ([digikey.co.uk](https://digikey.co.uk/product-detail/en/maxim-integrated/MAX7456EUI/MAX7456EUI-ND/1701658), [digikey.com](https://www.digikey.com/en/products/detail/analog-devices-inc-maxim-integrated/MAX7456EUI/1701658)) |
| MAX7456EUI+T (T&R) | products 1703848 and 5405874 | "Part Status Obsolete … no longer manufactured", quantity available 0 ([digikey.com](https://www.digikey.com/en/products/detail/analog-devices-inc-maxim-integrated/MAX7456EUI-T/1703848)) |

- ADI lists MAX7456 as Obsolete and says there is no Maxim replacement ([analog.com](https://www.analog.com/en/products/MAX7456.html), [ADI EZ](https://ez.analog.com/power/battery-management-system/a/documents/do7300/what-is-maxim-s-closest-equivalent-part-to-obsolete-part-number-max7456eui)).
- Brokers (Lisleapex, Digipart) show stock, but that is not DigiKey.

### Verdict
**Neither MAX7456-family OSD chip can be bought new from DigiKey.** Under the "every part from DigiKey, never substitute a non-DigiKey part" rule:
- **Drop the analog OSD chip.**
- Make HD/digital **MSP DisplayPort** primary. Betaflight can also run MSP DisplayPort to an analog VTX that has its own OSD, or to a goggle-side OSD.
- Removing the chip also removes these lines: the 27 MHz crystal (ABM8-27.000MHZ-B2-T and ECS-270-18-33-AGM-TR were both out of stock anyway), the video input/output passives, and the OSD SPI bus.
- The camera switch (TS5A3159A) only makes sense if analog video still passes through the board to a VTX without OSD. That is the lead's decision; record it in `design/decisions.md`.

---

## 2. Signal parts: evidence

The full table is in `design/parts_signal.md`. Per-line evidence follows.

### STM32F405RGT6
- **497-11767-ND** (tray), DigiKey 2754208, Active.
- Lead time 15-20 wk. An aggregator shows a DigiKey row with $11.67 and "Stock 26K (Active)".
- [digikey.com](https://www.digikey.com/en/products/detail/stmicroelectronics/STM32F405RGT6/2754208)
- Alternate: STM32F405RGT7TR, **497-19007-1-ND**, about 4,375 in stock ([digikey.com](https://www.digikey.com/en/products/detail/stmicroelectronics/STM32F405RGT7TR/9974339)). The tray part STM32F405RGT7 is 497-17433-ND.

### ICM-42688-P
- **1428-ICM-42688-PCT-ND** (TR -PTR-ND, DKR -PDKR-ND), DigiKey 10824934, Active.
- **0 in stock** on the NZ, MX and CA snapshots; lead time 16-26 wk.
- [punchouttest.digikey.ca](https://punchouttest.digikey.ca/en/products/detail/tdk-invensense/ICM-42688-P/10824934), [digikey.co.nz](https://digikey.co.nz/en/products/detail/tdk-invensense/ICM-42688-P/10824934)
- **Stock risk:** buy early or plan the alternate.

### BMI270
- **828-1091-1-ND** (TR -2, DKR -6), DigiKey 9974486.
- 0 in stock on the MX snapshot; 8 wk lead time; $3.80 @1 and $2.58 @1k.
- [punchouttest.digikey.com.mx](https://punchouttest.digikey.com.mx/en/products/detail/bosch-sensortec/BMI270/9974486)

### IMU alternate
- LSM6DSOXTR, **497-18367-1-ND**: 5,187 in stock (US), $4.07 @1 ([digikey.com](https://www.digikey.com/en/products/detail/stmicroelectronics/LSM6DSOXTR/9841887)).
- LSM6DSV16XTR is 497-LSM6DSV16XTRCT-ND with 0 in stock.
- Neither is a footprint-compatible drop-in for ICM/BMI.

### BMP390
- **828-BMP390CT-ND** (TR 828-BMP390TR-ND, DKR 828-BMP390DKR-ND), DigiKey 16164575 and 16164577.
- MX snapshot: out of stock with backorder, 12 wk, $3.30 @1. CA snapshot: 0. CN snapshot: 11,591.
- [digikey.com.mx](https://www.digikey.com.mx/en/products/detail/bosch-sensortec/BMP390/16164575)
- No verified alternate. BMP388 is reported discontinued (cytechsystems); a Bosch community post cites 828-1079-1-ND. BMP384 was not found.

### IIS2MDCTR
- **497-17728-1-ND** (TR -2, DKR -6), DigiKey 7927710 and 7927708.
- US snapshot in stock 1,067 at $2.67 @1; azcus snapshot 23,353 at $2.55. Lead time 20-28 wk.
- [digikey.com](https://www.digikey.com/en/products/detail/stmicroelectronics/IIS2MDCTR/7927710)
- Alternate: LIS2MDLTR, **497-17588-1-ND**, Active. Mirrors are out of stock.

### W25N01GV: which variant DigiKey stocks
- **WSON-8 8x6 (ZEIG), recommended.**
  - Listing "W25N01GVZEIG TR", DigiKey 5803931: PNs **W25N01GVZEIGCT-ND** (CT) and **256-W25N01GVZEIGTR-ND** (TR).
  - Part Status **Active** on azcus; 24 wk lead time.
  - Findchips DigiKey row: W25N01GVZEIGCT-ND, 106,446 in stock, $3.01 @1. Flux: DigiKey $3.76, 137K.
  - URLs: [digikey.co.uk ...W25N01GVZEIGCT-ND/7393545](https://www.digikey.co.uk/en/products/detail/winbond-electronics/W25N01GVZEIG-TR/W25N01GVZEIGCT-ND/7393545), [azcus](https://azcus.digikey.com/en/products/detail/winbond-electronics/W25N01GVZEIG-TR/5803931)
  - **Caveat:** a separate listing "W25N01GVZEIG" (DigiKey 15181734) shows **Obsolete** on the US page and Active on the AU page. One broker (pcxco) labels W25N01GVZEIGS "NRND / Last Time Buy".
  - The GV family may be heading to EOL; the successor is W25N01KV (4-bit ECC). Recommend: buy the GV now, and log a lifecycle risk.
- **SOIC-16 (SFIG):** DigiKey 15181740, Active but **"out of stock, backorders currently unavailable"** ([digikey.com](https://www.digikey.com/en/products/detail/winbond-electronics/W25N01GVSFIG/15181740)). Not recommended.
- **W25N01KVZEIR:** no DigiKey page found (LCSC 3,782; Avnet 0 with a 210-day lead time). Betaflight driver support was not verified.

### GCT USB4105-GF-A
- **2073-USB4105-GF-ACT-ND** (TR 2073-USB4105-GF-ATR-ND, DKR 2073-USB4105-GF-ADKR-ND), DigiKey 11198441 and 11198510.
- Active; 7 wk lead time; 5 A, 48 V.
- [digikey.com](https://www.digikey.com/en/products/detail/gct/USB4105-GF-A/11198441)
- Alternate: USB4110-GF-A, DigiKey 10384547. The snippet gave the PN as "2073-USB4110-GF-A-1-ND", an unusual format, so re-check. 16,969 (CA) and 27,749 (CH) in stock; CAD 1.563 @10.

### USBLC6-2SC6 (ST)
- **497-5235-1-ND**, DigiKey 1040559. Mirrors show "out of stock, backorder"; 25 wk lead time.
- [digikey.com](https://www.digikey.com/en/products/detail/stmicroelectronics/USBLC6-2SC6/1040559)
- **Trap:** DigiKey also lists a **UMW** "USBLC6-2SC6" (4518- PNs, DigiKey 16705896) with 5 V standoff and 15 V clamp. Different specs; do not use.
- Alternate: TPD2E2U06DRLR, **296-38361-1-ND**, 535 (CA) ([digikey.com](https://www.digikey.com/en/products/detail/texas-instruments/TPD2E2U06DRLR/4878710)).

### JST SH
- DigiKey shows two listings per size: plain "SMxxB-SRSS-TB" and the "(LF)(SN)" alias.

| Part | DigiKey CT PN | DigiKey product | Notes |
|---|---|---|---|
| SM08B-SRSS-TB(LF)(SN) | **455-1808-1-ND** (TR -2) | 926879, plus listing 926714 | 1 A, 50 V; $0.84 @1 and $0.42 @3k reel; lead time 16 or 42 wk |
| SM06B-SRSS-TB(LF)(SN) | **455-1806-1-ND** | 926877 / 926712 | UK 19,550 in stock; one US page out of stock |
| SM04B-SRSS-TB(LF)(SN) | 455-1804-6-ND (Digi-Reel) seen, so CT is **455-1804-1-ND** by family pattern | 1963508 / 926875 / 926710 | |

- Note: "455-1792-1-ND" (a guess for SM08B) was **not** confirmed. Use 455-1808-1-ND.
- Sources: [digikey.com SM08B](https://digikey.com/product-detail/en/jst-sales-america-inc/SM08B-SRSS-TB-LF-SN/455-1808-1-ND/926879), [SM06B](https://www.digikey.com/product-detail/en/SM06B-SRSS-TB(LF)(SN)/455-1806-1-ND/926877), [SM04B](https://digikey.com/product-detail/en/SM04B-SRSS-TB(LF)(SN)/455-1804-6-ND/1963508)

### 8 MHz crystal
- **Pick: ECS-80-8-33-JEN-TR3**: 8 MHz, CL 8 pF, ESR 400 Ω, 4-SMD 3.2x2.5.
  - DigiKey 15282973, Active, **23,687 in stock** (azcus), $0.58 @1, 9 wk lead time.
  - Stability: one snippet says ±20 ppm and another ±50 ppm; confirm.
  - CT PN not seen. Pattern from sibling: 50-ECS-80-8-33-JEN-TR3CT-ND (unconfirmed).
  - [azcus](https://azcus.digikey.com/en/products/detail/ecs-inc/ECS-80-8-33-JEN-TR3/15282973)
- **Alternate: ECS-80-8-33-JGN-TR3** (±30 ppm, 400 Ω): **50-ECS-80-8-33-JGN-TR3CT-ND** (CONFIRMED-PN); 0 on the MX snapshot; $0.61 @1 ([mx](https://punchouttest.digikey.com.mx/en/products/detail/ecs-inc/ECS-80-8-33-JGN-TR3/15282974)).
- Rejected candidates:
  - "ABM8-8.000MHZ-B2-T" does not appear to exist; the Abracon ABM8 range starts above 8 MHz.
  - NDK NX3225GA is only specified from 9.84 MHz.
  - Epson FA-238 and TSX-3225 start at 16 MHz.
  - ABM3B-8.000MHZ-B2-T is 5x3.2, 18 pF and 200 Ω (535-9720-x-ND); its higher gm_crit was computed in parts_signal.md.
- See the gm_crit note in parts_signal.md. Searches found no 8 MHz 3.2x2.5 crystal with ESR ≤ 200 Ω at DigiKey.

### Tact switch
- **C&K PTS810 SJM 250 SMTR LFS**: **CKN10502CT-ND**, top actuated, 4.2x3.2x2.5 mm, 160 gf.
  - FR snapshot 10,793 in stock at €0.44 @1; DE snapshot out of stock.
  - [digikey.fr](https://www.digikey.fr/en/products/detail/c-k/Y97LT25B2DBFP/4176610)
- **Panasonic EVQ-P7A01P** (side-actuated right-angle, 220 gf): **P16763CT-ND**; DE out of stock; 18 wk lead time ([digikey.com](https://www.digikey.com/en/products/detail/panasonic-electronic-components/EVQ-P7A01P/4429447)).
- **EVQ-P7J01P** (160 gf): DigiKey 4429451, 2,956 US, $0.28 @1. CT PN not seen.

### LEDs (0603)
| MPN | DigiKey CT PN | Snapshot |
|---|---|---|
| LTST-C191TBKT (blue) | **160-1647-1-ND** | US/CA out of stock; EU about 335,553 |
| LTST-C191KGKT (green) | **160-1446-1-ND** | ES out of stock |
| LTST-C191KRKT (red) | **160-1447-1-ND** | about 480k-670k |
| APT1608QBC/D (Kingbright blue) | **754-1434-1-ND** | |
| APT1608SGC (Kingbright green) | **754-1121-1-ND** | MX 1,240,510 |
| APT1608EC (Kingbright red) | **754-1117-1-ND** | about 149k, $0.19 @1 |

The 160-1838-1-ND number from the brief was **not** found. Use 160-1647-1-ND for LTST-C191TBKT.

### MOSFETs
- **PMV40UN2R:** **1727-1900-1-ND**. "Out of stock, backorders currently unavailable" on the US-facing page; MX $0.39 @1, $0.268 @10; 12 wk lead time.
  - [azcus](https://azcus.digikey.com/en/products/detail/nexperia-usa-inc/PMV40UN2R/5056344)
  - Alternate: PMV30UN2R, DigiKey 5395607 (PN not seen).
- **2N7002-7-F:** **2N7002-FDICT-ND**, out of stock, **40 wk** lead time ([digikey.com](https://www.digikey.com/en/products/detail/diodes-incorporated/2N7002-7-F/717681)).
  - **Recommended instead: NX7002AK,215, 1727-1289-1-ND**, 6 wk lead time ([digikey.cn](https://digikey.cn/en/products/detail/nexperia-usa-inc/NX7002AK-215/4020917)). The datasheet is already in `datasheets/NX7002AK.pdf`.

### TS5A3159ADBVR
- **296-19265-1-ND**, DigiKey 936395, **Active** on the CN listing.
- Regional mirrors out of stock; lead time 6-12 wk.
- [digikey.cn](https://digikey.cn/en/products/detail/texas-instruments/TS5A3159ADBVR/936395)
- Alternate: TS5A3159DBVR, DigiKey 686662.

### LED-strip buffer
- **SN74AHCT1G125DBVR:** **296-4708-1-ND**, 12 wk lead time, mirrors out of stock ([azcus](https://azcus.digikey.com/en/products/detail/texas-instruments/SN74AHCT1G125DBVR/376028)).
- **74AHCT1G125GW,125:** DigiKey 1229653, out of stock, 20 wk lead time; DigiKey substitute 74AHCT1G125SE-7 (Diodes) also 0.
- **74AHCT1G125GV,125:** **1727-6024-1-ND**, seen in a substitute table.
- **SN74LV1T125DBVR:** **296-37172-1-ND**, 6 wk lead time ([digikey.com](https://www.digikey.com/en/products/detail/texas-instruments/SN74LV1T125DBVR/4555571)). Its low-threshold inputs translate 3.3 V to 5 V at VCC = 5 V. Recommended alternate.
- A UMW-branded "SN74AHCT1G125DBVR" also exists at DigiKey (4518- PNs). Avoid it.

### BAT54S-7-F
- **BAT54S-FDICT-ND** (not "BAT54SFDICT-ND"), DigiKey 717925. ES mirror out of stock; 12 wk lead time.
- [azcus](https://azcus.digikey.com/en/products/detail/diodes-incorporated/BAT54S-7-F/717925)
- Vishay and onsemi substitutes are listed but were not captured (unverified).

### Ferrite beads
- BLM18PG221SN1D: **490-5221-1-ND** (seen in DigiKey URL /490-5221-1-ND/1948397); 1.4 A, 100 mΩ.
- BLM18KG601SN1D: **490-5258-1-ND** (seen in DigiKey URL /490-5258-1-ND/1982781); 1.3 A, 150 mΩ; about 172k-749k.
- Note: "490-1052-1-ND" from the brief was not confirmed.

---

## 3. Power parts: evidence

| Line | MPN | DigiKey PN | Confidence | Stock / lifecycle seen | ~Price | Alternate at DigiKey |
|---|---|---|---|---|---|---|
| Sync buck (candidate) | **LMR38020SDDAR** (TI), HSOIC-8 (DDA) | **296-LMR38020SDDARCT-ND** | CONFIRMED-PN (DigiKey 15853832) | Active; **out of stock, backorder**; 12 wk lead time | regional snapshots inconsistent | LMR38020FDDAR |
| Sync buck (candidate) | **LMR38020FDDAR** (TI), FPWM, no spread spectrum | **296-LMR38020FDDARCT-ND** | CONFIRMED-PN (DigiKey 18159245 / 21822668) | Active; **out of stock, backorder**; 12 wk lead time | about €2.85-2.90 | DigiKey substitute LMR38020FSDDAR (FPWM + SS): 296-LMR38020FSDDARCT-ND (pattern, unconfirmed) |
| Non-sync buck (current) | **TPS54360BDDAR** (TI) | **296-TPS54360BDDARCT-ND** | CONFIRMED-PN (aggregator DigiKey row) | 1,510-2,293 in stock (two snapshots); 12 wk lead time | n/a | **Do not** use TPS54360DDAR (non-B): 296-37676-1-ND is **NRND** and out of stock |
| VBAT TVS | **SMBJ26A** (Littelfuse), SMB | **SMBJ26ALFCT-ND** | CONFIRMED-PN (DigiKey 285998) | azcus **1,688 in stock**; 12 wk lead time; "Volume Production" | $0.18 @1, **$0.151 @10** | Vishay SMBJ26A-E3/5B: SMBJ26A-E3/5BGICT-ND (findchips DigiKey row). Bourns SMBJ26A: SMBJ26ABCT-ND (Ciiva marks Bourns NRND) |
| 5 V inductor (spec) | Coilcraft **XGL5030-472MEC** | DigiKey 15794435 | **"No longer available at DigiKey"** | Coilcraft direct only | Coilcraft €2.26 @1 | see below |
| 10 V inductor (spec) | Coilcraft **XGL5030-822MEC** | none | **NOT FOUND at DigiKey** (Coilcraft page shows stock) | — | — | see below |
| XGL4030 series | XGL4030-472MEC (12714598), XGL4030-102MEC (12714858) | — | **"No longer available at DigiKey"** (US); UK listing 4652-XGL4030-472MEC-ND is also discontinued | — | — | — |
| 4.7 µH alt (recommended) | **Würth 74437336047** (WE-LHMI 5030) | 732-xxxx-1-ND (pattern, unconfirmed) | LISTED (DigiKey 5051073) | **Active, 1,354 in stock**; 19 wk lead time | $2.72 @1 | Bourns SRP5030TA-4R7M |
| 4.7 µH alt | **Bourns SRP5030TA-4R7M** | **SRP5030TA-4R7MCT-ND** | CONFIRMED-PN (DigiKey 5429673) | LT snapshot 3,140; AEC-Q200; 12-14 wk lead time | n/a | — |
| 10 µH alt | **Bourns SRP5030TA-100M** | SRP5030TA-100MCT-ND (pattern, unconfirmed; family pattern confirmed by SRP5030TA-1R0MCT-ND) | LISTED (DigiKey 5429667) | Active; **2,155 in stock**; 20 wk lead time | $1.04 @1 | SRP5030TA-6R8M (DigiKey 5429675) |
| Load switch | **TPS22810DBVR** (TI) | **296-45297-1-ND** | CONFIRMED-PN (DigiKey 6595640) | Mirrors out of stock; findchips DigiKey row 12,214; 12 wk lead time | n/a | TPS22810TDBVRQ1 (DigiKey 8604617; PN not seen) |
| 3V3 LDO | **LP38692MP-3.3/NOPB** | **LP38692MP-3.3/NOPBCT-ND** | CONFIRMED-PN (DigiKey 723328) | findchips DigiKey 2,289; a mirror is out of stock; 12 wk lead time | $1.86 @1 | LP38693MP-3.3/NOPB (500 mA): LP38693MP-3.3/NOPBCT-ND (CONFIRMED-PN) |
| IMU LDO | **LP5907MFX-3.3/NOPB** | **296-38557-1-ND** | CONFIRMED-PN (DigiKey 3906441) | about 2,031 (aggregator); lead time 6-12 wk; DE mirror out of stock | $0.45 @1 | not verified this pass |
| Schottky 40 V 3 A | **PMEG4030ER,115** (orderable suffix is ",115"; **"PMEG4030ERX" was not found**) | **1727-5313-1-ND** | CONFIRMED-PN (DigiKey 2228704) | Active; MY/CA out of stock; lead time 6-26 wk | n/a | PMEG4030ER-QX (AEC-Q101): 1727-PMEG4030ER-QXCT-ND (CONFIRMED-PN) |
| Schottky 60 V 3 A | **PMEG6030EP,115** | **1727-5218-1-ND** | CONFIRMED-PN (DigiKey 2296186) | DigiKey: Active, out of stock, lead time 8-16 wk. **Lifecycle doubt:** the Nexperia page snippet says the type numbers in one ordering table are "Discontinued / End-of-life". The **/8X** variant is Obsolete at DigiKey and Future. | $0.54 @1 | Nexperia lists PMEG6030ETP / PMEG6030EVP (SOD128) as Active (DigiKey PNs not seen). PMEG060V030EPE-QZ (CFP15B, different footprint): 1727-PMEG060V030EPE-QZCT-ND, 3,298 in stock. This part is moot if the LMR38020 synchronous buck replaces the TPS54360B |
| EN clamp zener | **BZT52C6V2-7-F** | **BZT52C6V2-FDICT-ND** | CONFIRMED-PN (DigiKey 814853) | ES mirror out of stock; 12 wk lead time | n/a | BZT52C6V2S-7-F (SOD-323, DigiKey 814852; PN not seen) |
| 22 µF 25 V | **CL31A226KAHNNNE** (1206 X5R) | **1276-3047-1-ND** | CONFIRMED-PN (DigiKey 3891133 / 3888705) | **Out of stock; lead time 31-61 wk** | n/a | **CL32A226KAJNNNE** (1210, 25 V X5R): DigiKey 3886759, Active, one snapshot 17,755, another 0; PN not seen. Avoid GRM32ER61E226KE15L (**NRND**) and GRM31CR61E226KE15L (**Obsolete**) |
| 10 µF 50 V | **GRM32ER71H106KA12L** (1210 X7R) | **490-6544-1-ND** | CONFIRMED-PN (DigiKey URL) | **Conflicting:** one listing says "Discontinued at DigiKey / backorders unavailable"; another says Active, not normally stocked | n/a | **CL32B106KBJNNNE** (Samsung, 10 µF 50 V X7R 1210): **1276-3387-1-ND** (CONFIRMED-PN, DigiKey URL); DigiKey also names CL32B106KBJNFNE as a direct substitute |
| 10 V rail clamp (VTX switch protection) | **SMAJ12A** (Littelfuse), SMA | **SMAJ12ALFCT-ND** | CONFIRMED-PN (DigiKey 762270) | 12 wk lead time; aggregator DigiKey row 212 in stock | $0.38 | Bourns SMAJ12A: SMAJ12ABCT-ND (out of stock on mirrors) |
| 13 V zener alternative | onsemi **SZMMSZ13ET1G** (SOD-123, 500 mW) | LISTED (DigiKey 18687601); PN not seen | — | 5,695 in stock | $0.19 @1 | MCC MMSZ5243B-TP (DigiKey 1793205). **BZT52C13-7** is "discontinued, no longer carried" at DigiKey; **BZT52C13-7-F** was not found at DigiKey |

### Inductor finding (important)
- **Coilcraft parts are largely being delisted at DigiKey.** These listings all read "This product is no longer available at DigiKey":
  - XGL5030-472MEC, XGL5030-103MEC, XGL5030-821MEC
  - XGL4030-472MEC, XGL4030-102MEC
  - XGL6060-472MEC, XAL5050-562MEC, XAL6060-333MEC, XAL1010-221MED
- Some other values (for example XGL5030-183MEC) still show stock, so this is not a blanket exit, but it is a strong trend.
- **Coilcraft parts fail the DigiKey-only rule for this board.**
- Replacements:
  - **5 V, 4.7 µH:** Würth **74437336047** (5030 size, Isat 7.6 A, Irms 3.9 A, DCR 53 mΩ max, Active, 1,354 in stock). Bourns SRP5030TA-4R7M (Isat 6 A, Irms 4.6 A, 53 mΩ) is the alternate, **but its footprint is 5.7 x 5.2 x 3.0 mm, which exceeds the 5.5 mm limit**.
  - **10 V rail:** the old design used 8.2 µH. The best confirmed ≥3 A part in this size is **Bourns SRP5030TA-100M**: 10 µH, Isat 3.5 A, Irms 2.75 A, DCR 128 mΩ max (lossy), 5.7 x 5.2 x 3.0 mm.
    - At 2 A that is about 0.5 W of copper loss, so the power designer must re-check.
    - SRP5030TA-6R8M is also listed; a lower L means lower DCR.
    - No Würth 5030 10 µH with Isat ≥ 3 A was confirmed. 74437336100 was not found, and 74437346100 is 7030.
  - The power designer must re-run the inductor current and loss calculations with the chosen part.

### SMAJ12A as the 10 V rail clamp (engineering note)
- VWM 12 V, VBR min 13.3 V, clamp 19.9 V at 20.1 A (10/1000 µs).
- This leaves the TPS22810 (20 V abs max) with almost no margin at high surge current.
- It works as a slow-fault clamp only if something upstream limits the current, such as a fuse/PTC or the buck's current limit.
- A 13 V zener does not clamp energy; it only sets a threshold.
- Flag for the power auditor (R8 in power.md).

---

## 4. Summary of problems for the lead

1. **AT7456E: not sold at DigiKey.** MAX7456: obsolete at DigiKey, quantity 0. Drop the analog OSD; make MSP DisplayPort primary.
2. **Not available at DigiKey:**
   - AT7456E
   - Coilcraft XGL5030-472MEC (delisted), XGL5030-822MEC (no listing), XGL4030-472MEC and -102MEC (delisted)
   - BZT52C13-7 / -7-F
   - W25N01KVZEIR (no listing)
   - "ABM8-8.000MHZ" (does not exist)
3. **NRND / obsolete / lifecycle doubt:**
   - MAX7456 (Obsolete)
   - TPS54360DDAR non-B (NRND; the BOM correctly uses the B)
   - GRM32ER61E226KE15L (NRND) and GRM31CR61E226KE15L (Obsolete)
   - GRM32ER71H106KA12L ("Discontinued at DigiKey" on one listing)
   - PMEG6030EP (Nexperia shows discontinued status for an ordering table; the /8X variant is Obsolete)
   - W25N01GVZEIG (one DigiKey listing says Obsolete, the TR listing says Active; a broker says NRND)
4. **Stock and lead-time risks (snapshots):**
   - ICM-42688-P (0), BMI270 (0), BMP390 (0 US, stock CN)
   - LMR38020S/F (out of stock)
   - USBLC6-2SC6 (out of stock), PMV40UN2R (out of stock), 2N7002-7-F (40 wk)
   - CL31A226KAHNNNE (31-61 wk), 74AHCT1G125 (out of stock)
   - W25N01GVSFIG (backorder unavailable)
5. **Suggested substitutes:**

| Replace | With | DigiKey PN |
|---|---|---|
| 2N7002-7-F | NX7002AK,215 | 1727-1289-1-ND |
| USBLC6-2SC6 (alternate) | TPD2E2U06DRLR | 296-38361-1-ND |
| SN74AHCT1G125DBVR | SN74LV1T125DBVR | 296-37172-1-ND |
| W25N01GV SOIC | W25N01GVZEIG (WSON) | W25N01GVZEIGCT-ND |
| Coilcraft XGL 4.7 µH | Würth 74437336047 | PN pattern unconfirmed (DigiKey listing 5051073) |
| 8.2 µH (10 V rail) | Bourns SRP5030TA-100M or -6R8M, after a loss re-check | — |
| CL31A226KAHNNNE | CL32A226KAJNNNE (1210) | PN not seen |
| GRM32ER71H106KA12L | CL32B106KBJNNNE | 1276-3387-1-ND |
| 8 MHz crystal | ECS-80-8-33-JEN-TR3 (CL 8 pF) | — |
| Tact switch | PTS810 SJM 250 SMTR LFS | CKN10502CT-ND |
| Blue LED (alternate) | Kingbright APT1608QBC/D | 754-1434-1-ND |

6. **DigiKey PN conventions:**
   - Yageo RC is predictable: `311-<3-digit value>{H=0603, L=0402}RCT-ND`.
   - Samsung CL and Murata GRM use sequential numbers, so each part needs an individual lookup.
