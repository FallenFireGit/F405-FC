# Gate 2: DigiKey sourcing audit (F405-FC)

Auditor: independent Gate 2 sourcing re-audit, 2026-10-12. This replaces the unreviewed draft that an earlier auditor left after hitting a usage limit.
Input: `bom/bom_raw.csv`, regenerated with `kc 'python3 gen/bom.py'` (53 lines, 125 placements, DNP R32 R37) from the current `design/circuit.py`.
Outputs: `bom/F405FC_digikey_bom.csv` (BOM Manager upload) and `bom/digikey_bom_costed.csv` (prices, evidence, alternates).

## Verdict

**FAIL as the design BOM stands. It becomes PASS once the replacements below are adopted in `design/circuit.py`.**

- **BLOCKERs: 3.** Four design MPNs have no DigiKey listing: C36/C37, C23/C39, and R3/R8 + R5, which share one finding. Each has a drop-in DigiKey replacement, and the upload CSV already uses the replacements.
- **MAJORs: 0.** Every stock-out has an alternate with stock evidence at DigiKey, or is covered by an accepted decision (D-05, D-10).
- **MINORs: 10.**

The upload CSV can be ordered today. The design files are unchanged and still name the parts that DigiKey does not sell, so Gate 2 can only close as PASS after `circuit.py` takes in G2S-01, G2S-02, G2S-03 and G2S-09, and the BOM is regenerated.

**Estimated cost for 2 boards plus spares: $167.56** (499 pieces, 54 order lines). This uses qty-1 cut-tape prices from search snippets dated 2026-10-11/12; see the cost section.

## Method

- digikey.com and vendor sites are blocked here: the proxy returns 403 and WebFetch has no DNS. Evidence therefore comes from WebSearch snippets of:
  - DigiKey regional storefronts (digikey.gr/.be/.at/.es/.my/.cn and others) and their azcus/punchouttest mirrors
  - aggregator rows that name DigiKey (Findchips, TrustedParts, Octopart, electronicsdatasheets, Flux)
  - manufacturer pages
- **Rule for part numbers:** a DigiKey PN goes into the upload CSV only if it was seen verbatim in a snippet tied to DigiKey. Otherwise the PN column is left empty, and DigiKey's BOM Manager matches the line by MPN. Three lines are left blank this way: R3/R8, R5 and Y1.
- **Reuse of the draft:** I reused the draft's cited evidence and spot-checked about 30 lines. I re-ran searches for every line the draft marked FAIL or REPLACED, every line that changed in the new `bom_raw.csv`, every stock-out, and the lifecycle items. Where the spot-checks disagreed with the draft, I changed the result (see "Changes vs. draft").
- **MPN decoding:**
  - Samsung CLxx: size / dielectric (A = X5R, B = X7R, C = C0G) / value / tolerance / voltage (O = 16 V, A = 25 V, B = 50 V, P = 10 V, Q = 6.3 V)
  - Murata GRM: R7/Z7 = X7R, 1H = 50 V, 2A = 100 V
  - Yageo RC: size, F = 1%, -07 = 7" reel
  - Every line's MPN matched its value, rating and package, except the four BLOCKER MPNs, which do not exist at DigiKey.
- **Quantities:**
  - ICs, connectors and inductors: per-board quantity × 2
  - Small passives (0402/0603 R/C/FB): × 2 + 10
  - Larger passives (0805/1206/1210): × 2 + 3
  - Discrete semiconductors, crystal and switch: × 2 + 1. The brief did not specify these; I used the draft's rule.
  - DNP R32/R37: 10 spares
- **Stock caveat:** all stock figures are undated search snapshots. Regional storefronts often disagree, and punchouttest mirrors show 0 for many parts. Re-check stock in BOM Manager before ordering.

## Per-line status

| # | Refs | MPN ordered | DigiKey PN | Status |
|---|---|---|---|---|
| 1 | C5…C50 (20) | CL05B104KO5NNNC | 1276-1001-1-ND | CONFIRMED |
| 2 | C6-8 C14-16 | CL31A226KAHNNNE | 1276-3047-1-ND | CONFIRMED (stock risk) |
| 3 | C1-3 C10 C11 | CL32B106KBJNNNE | 1276-3387-1-ND | CONFIRMED (stock risk) |
| 4 | C19 C22 C31 C51 | CL10A105KA8NNNC | 1276-1102-1-ND | CONFIRMED (stock risk) |
| 5 | C40 C52 C53 | CL05B103KB5NNNC | 1276-1028-1-ND | CONFIRMED (PN in circuit.py wrong) |
| 6 | C20 C33 C34 | CL10A225KO8NNNC | 1276-1040-1-ND | CONFIRMED (PN in circuit.py wrong) |
| 7 | C18 C29 C47 | CL10A475KO8NNNC | 1276-1784-1-ND | CONFIRMED (PN in circuit.py wrong) |
| 8 | C4 C12 C17 | GRM188R72A104KA35D | 490-3285-1-ND | CONFIRMED |
| 9 | C36 C37 | **C0402C829C5GACTU** (KEMET) | 399-C0402C829C5GACTUCT-ND | **FAIL → replaced (G2S-01)** |
| 10 | C23 C39 | **CL10B225KP8NNNC** | 1276-1134-1-ND | **FAIL → replaced (G2S-02)** |
| 11 | C45 | CL05A224KA5NNNC | 1276-1455-1-ND | CONFIRMED (PN in circuit.py wrong) |
| 12 | D4 D5 D9 | PMEG4030ER,115 | 1727-5313-1-ND | CONFIRMED, **stock-out** (G2S-04) |
| 13 | D7 D8 | BAT54S-7-F | BAT54S-FDICT-ND | CONFIRMED |
| 14-16 | D10-D12 | LTST-C191KRKT/KGKT/TBKT | 160-1447/1446/1647-1-ND | CONFIRMED |
| 17 | D1 | SMBJ26A (Littelfuse) | SMBJ26ALFCT-ND | CONFIRMED |
| 18 | FB1 | BLM18KG601SN1D | 490-5258-1-ND | CONFIRMED |
| 19-21 | J3 J4, J5, J2 | SM06B/SM04B/SM08B-SRSS-TB(LF)(SN) | 455-1806/1804/1808-1-ND | CONFIRMED (J2 stock varies) |
| 22 | J1 | USB4105-GF-A | 2073-USB4105-GF-ACT-ND | CONFIRMED |
| 23 | L1 | 74438357068 | 732-11204-1-ND | CONFIRMED, stock unverified (G2S-10) |
| 24 | L2 | 74438357082 | 732-11205-1-ND | CONFIRMED (PN in circuit.py wrong), stock unverified (G2S-10) |
| 25 | Q2 | **NX7002AK,215** | 1727-1289-1-ND | CONFIRMED; design MPN wrong (G2S-09) |
| 26 | Q1 | PMV40UN2R | 1727-1900-1-ND | CONFIRMED, **stock-out** (G2S-05) |
| 27-31, 33-35, 38 | 0402/0603 Yageo RC (100k, 10k, 1k, 2.2k, 330, 5.1k, 301k, 100R, 10k 0603) | RC0402FR-07… / RC0603FR-07… | 311-…RCT-ND | CONFIRMED |
| 32 | R3 R8 | **ERJ-2RKF3482X** | (blank) | **FAIL → replaced (G2S-03)**, PN unconfirmed |
| 36 | R10 | RC0402FR-0711KL | 311-11.0KLRCT-ND | CONFIRMED, stock-out snapshot (G2S-12) |
| 37 | R5 | **ERJ-2RKF2432X** | (blank) | **FAIL → replaced (G2S-03)**, PN unconfirmed |
| 39 | R41 | RC0805JR-070RL | 311-0.0ARCT-ND | CONFIRMED (0805 jumper, 2 A) |
| 40 | SW1 | PTS810 SJM 250 SMTR LFS | CKN10502CT-ND | CONFIRMED |
| 41 | U1 U2 | LMR38020FSDDAR | 296-LMR38020FSDDARCT-ND | CONFIRMED |
| 42 | U7 | BMI270 | 828-1091-1-ND | CONFIRMED |
| 43 | U8 | BMP390 | 828-BMP390CT-ND | CONFIRMED (stock varies by region; D-10) |
| 44 | U6 | ICM-42688-P | 1428-ICM-42688-PCT-ND | CONFIRMED, **stock-out** (G2S-06; D-10) |
| 45 | U9 | IIS2MDCTR | 497-17728-1-ND | CONFIRMED (stock risk) |
| 46 | U4 | LP38692MP-3.3/NOPB | LP38692MP-3.3/NOPBCT-ND | CONFIRMED |
| 47 | U5 | LP5907MFX-3.3/NOPB | 296-38557-1-ND | CONFIRMED |
| 48 | U12 | SN74LV1T125DBVR | 296-37172-1-ND | CONFIRMED |
| 49 | U3 | STM32F405RGT6 | 497-11767-ND | CONFIRMED (stock risk, G2S-07) |
| 50 | U11 | TS5A3159ADBVR | 296-19265-1-ND | CONFIRMED |
| 51 | U13 | USBLC6-2SC6 (genuine ST) | 497-5235-1-ND | CONFIRMED |
| 52 | U10 | **W25N01GVZEIG TR** | W25N01GVZEIGCT-ND | CONFIRMED (lifecycle risk, G2S-08) |
| 53 | Y1 | ECS-80-8-33-JEN-TR3 | (blank) | UNCONFIRMED (PN only; listing confirmed) |
| 54 | R32 R37 (DNP) | RC0402JR-070RL | 311-0.0JRCT-ND | CONFIRMED (spares) |

Every line has an alternate MPN in `digikey_bom_costed.csv`. Alternate DigiKey PNs are filled in only where they were seen verbatim.

## Findings

### BLOCKER

**G2S-01: C36/C37 CL05C8R2CB5NNNC (8.2 pF crystal load caps) is not at DigiKey.**
- **Evidence:** 3 searches found only IBS/aggregator pages. The PN in `circuit.py`, 1276-1650-1-ND, was never seen. Samsung's automotive CL05C8R2CB51PNC has a DigiKey entry on an aggregator, but no PN was seen for it.
- **Replacement:** KEMET **C0402C829C5GACTU**, DigiKey **399-C0402C829C5GACTUCT-ND**.
  - Same value and rating: 8.2 pF, ±0.25 pF (same tolerance letter C), C0G, 50 V, 0402.
  - Active; 37,106-49,279 in stock; 13-17 wk; about €0.09 @1.
  - The crystal C_L math in D-07 does not change.
- **Alternate:** KEMET C0402C829B5GACTU (±0.1 pF), DigiKey listing 12701379.
- **Action:** update `C8p2` in `circuit.py`.

**G2S-02: C23/C39 CL10B225KO8NNNC (2.2 µF X7R 16 V 0603) is not at DigiKey, and no other distributor lists it either.**
- **Evidence:** 3 searches. Samsung's 0603 2.2 µF X7R exists only as KP8 (10 V) and KQ8 (6.3 V).
- **Replacement:** **CL10B225KP8NNNC** (2.2 µF 10 V X7R 0603), DigiKey **1276-1134-1-ND**, about 322,867 in stock, about $0.16 @1 (aggregator DigiKey row).
  - Both caps are on 3V3_IMU (3.3 V), so 10 V gives 3× margin.
  - X7R is kept, as the ICM-42688-P bypass table asks (G1P-05).
  - The LP5907 output effective-C minimum is met.
- **Alternate:** Murata GRM188Z71E225ME43D (25 V X7R ±20%). DigiKey staff on the DigiKey forum name it; its TR PN is 490-GRM188Z71E225ME43DTR-ND.
- **Draft replacement rejected:** the draft used GRM188Z71E225KE43D. The DigiKey forum states that KE43D is *not listed*, which contradicts the draft's claim.
- **Action:** update `C2u2_X7R` in `circuit.py`. The "16V" label becomes "10V".

**G2S-03: R3/R8 RC0402FR-0734K8L (RT, 34.8 k) and R5 RC0402FR-0724K3L (FB, 24.3 k) are not at DigiKey.**
- **Evidence:** the draft's 3 searches plus my re-check on 2026-10-12 found only Future/Avnet/IBS listings.
- **Replacements** (same value, 1%, 0402, 0.1 W):
  - **Panasonic ERJ-2RKF3482X** for R3/R8
  - **ERJ-2RKF2432X** for R5
- **Evidence gaps:** the draft cited DigiKey listings 192243 and 1178181, but I could not reproduce them. P34.8KLCT-ND and P24.3KLCT-ND were seen only on third-party pages or inferred from the family pattern. The PN column is therefore blank, and BOM Manager will match by MPN.
- **Fallbacks:** Vishay CRCW040234K8FKED and Yageo AC0402FR-0724K3L.
- **Action:** update `circuit.py`. If BOM Manager does not match these MPNs, use the Vishay part or another stocked 1% 0402 E96 resistor.

### MAJOR

None.

### MINOR

**G2S-04: D4/D5/D9 PMEG4030ER,115 is out of stock at DigiKey.**
- **Evidence:** MY/CA show 0 with backorder at 16-26 wk. The same-footprint Nexperia alternates are also at 0 on DigiKey mirrors: PMEG4030ER-QX and PMEG40T30ERX (1727-7481-1-ND).
- **Stocked alternate:** Taiwan Semi **SS34LWH** (40 V 3 A SOD-123W, AEC-Q101), DigiKey **1801-SS34LWHCT-ND**, 4,442-19,332 in stock per Findchips DigiKey rows, about $0.45 @1.
- **Before swapping:** check the land pattern against the Nexperia CFP3 footprint, and check Vf. Vf is a little higher, which matters little at the 0.41 A OR-diode current.

**G2S-05: Q1 PMV40UN2R (buzzer FET) is out of stock at DigiKey.**
- **Evidence:** 0 stock; CA shows "backorders unavailable".
- **Stocked alternate:** UMW AO3400A (30 V 5.7 A, SOT-23, same G-S-D pinout, logic-level), DigiKey listing 16705910, 1,476-14,935 in stock. The CT PN was not seen verbatim, so BOM Manager should match it by MPN.
- **Second option:** Diodes DMG3420U-7. Its DigiKey PN was not confirmed.

**G2S-06: U6 ICM-42688-P shows 0 stock on every DigiKey snapshot (NZ/CA/MX), with 16-26 wk lead time.**
- This is accepted under D-10.
- Mitigation: U7 BMI270 is a stocked second IMU, so a board can be built and flown with U6 unpopulated.
- The ICM-42605 alternate (same pinout) has an unconfirmed DigiKey PN and lifecycle. Order U6 early.

**G2S-07: U3 STM32F405RGT6 stock is uncertain.**
- **Evidence:** Findchips shows DigiKey at 0; Flux showed 26k in Jan-2025.
- **Stocked alternate:** **STM32F405RGT7** (105 °C grade, same die and package), DigiKey **497-17433-ND**, 1,022 in stock. This replaces the draft's T7TR suggestion.

**G2S-08: U10 W25N01GV lifecycle evidence conflicts.**
- The orderable cut-tape PN W25N01GVZEIGCT-ND belongs to the listing **"W25N01GVZEIG TR"**, which the draft saw at 16,965-36,000 in stock.
- The base listing "W25N01GVZEIG" (15181734) shows Obsolete on some DigiKey storefronts, but Active / out of stock / 24 wk on the ES mirror.
- I could not find any Winbond EOL notice. The draft's "EOL 03-Jan-2026" claim was not reproduced, so I downgraded the draft's FAIL to MINOR.
- **Actions:**
  - order "W25N01GVZEIG TR" now
  - correct the MPN in `circuit.py`
  - functional alternate: W25Q128JVEIQ (same WSON-8 8×6 pinout, 128 Mbit NOR, DigiKey W25Q128JVEIQ-ND, Active)

**G2S-09: Q2 MPN "NX7002AKR" is not an orderable Nexperia type.**
- Nexperia lists NX7002AKZ, NX7002AK,215 and NX7002AKVL.
- The PN 1727-1289-1-ND belongs to **NX7002AK,215**. Correct the MPN in `circuit.py` and in D-07.
- **Alternate:** 2N7002NXAKR (60 V, 190 mA), DigiKey **1727-8643-1-ND**. Q2 needs ≥ 42 V, because the EN node clamps at 42.1 V.

**G2S-10: L1/L2 (Würth WE-MAPI 4030) DigiKey stock is unverified.**
- L1: Octopart showed DigiKey with 3 pieces.
- L2: no stock figure was seen.
- This is accepted under D-05. Confirm stock in BOM Manager.
- The Bourns SRP4020TA alternates are electrically marginal (Isat 2.5-2.8 A, about 175 mΩ).

**G2S-11: wrong DigiKey PNs in `circuit.py`.** Neither the BOM CSVs nor the design files fix these; they need to be corrected in `circuit.py`.

| Part | Wrong PN in `circuit.py` | Correct PN |
|---|---|---|
| 10 nF | 1276-1015-1-ND | 1276-1028-1-ND |
| 2.2 µF X5R | 1276-1183-1-ND | 1276-1040-1-ND |
| 4.7 µF | 1276-1044-1-ND | 1276-1784-1-ND |
| 220 nF | 1276-1255-1-ND | 1276-1455-1-ND |
| L2 | 732-74438357082CT-ND | 732-11205-1-ND |

The `circuit.py` PNs for 8.2 pF (1276-1650-1-ND) and 2.2 µF X7R (1276-1184-1-ND) belong to MPNs that DigiKey does not sell (G2S-01/02).

**G2S-12: R10 RC0402FR-0711KL is out of stock / backordered (18 wk) in one snapshot.**
- **Alternate:** Panasonic ERJ-2RKF1102X, DigiKey P11.0KLCT-ND, $0.11 @1.

**G2S-13: these PNs were not seen verbatim, so the upload leaves them blank.**
- Y1: ECS-80-8-33-JEN-TR3. The listing (15282973, Active, 23-49k in stock) is confirmed; 50-ECS-80-8-33-JEN-TR3CT-ND appeared only in a search summary.
- R3/R8 and R5 (see G2S-03).
- Many alternate PNs are also blank. All of those alternates are mainstream DigiKey-catalogue families, but their PNs were not seen.

### INFO

These are stock-risk lines whose regional snapshots disagree, though at least one DigiKey snapshot shows stock:
- C6-8/C14-16 22 µF 1206
- C1-3/C10/C11 10 µF 1210
- 1 µF 0603
- J2 8-pin JST-SH
- U8 BMP390 (BG 17,678 / CN 11,591 in stock)
- U9 IIS2MDC (US restock date 26-Oct-2026)

USBLC6-2SC6 (genuine ST, with VBUS clamp) meets D-07. Its alternate USBLC6-4SC6 (497-4492-1-ND) also has a VBUS pin. The KiCad symbol ties I/O pins 1/6 to USB_DM and pins 3/4 to USB_DP, so the 4-channel part is electrically equivalent. The TPD2E2U06 is not used.

## Changes vs. draft

1. **C36/C37:** the draft priced 10 pF CL05C100JB5NNNC. The design now uses 8.2 pF CL05C8R2CB5NNNC, which is not at DigiKey, so I replaced it with KEMET C0402C829C5GACTU.
2. **C23/C39:** the draft's Murata GRM188Z71E225KE43D is not listed at DigiKey (DigiKey forum), so I replaced it with CL10B225KP8NNNC (1276-1134-1-ND).
3. **R3/R8 and R5:** the PNs P34.8KLCT-ND and P24.3KLCT-ND were not verbatim, so I blanked them per the no-invented-PN rule.
4. **Y1:** still blank.
5. **W25N01GV:** downgraded from FAIL to MINOR. The orderable TR/CT listing is Active and stocked, and the EOL notice could not be reproduced.
6. **Alternates:**
   - D4/D5/D9 alternate changed to the stocked SS34LWH (the draft's -QX variant is also out of stock)
   - Q1 alternate: AO3400A (UMW), which has DigiKey stock evidence
   - Q2 alternate: 2N7002NXAKR, with a verbatim PN
   - U3 alternate: STM32F405RGT7 tray, 497-17433-ND (in stock)
   - U5 alternate: TLV75533PDBVR, 296-50411-1-ND (pinout matches)
   - W25Q128JVEIQ: PN added
7. **Quantities:** ICs and connectors set to exactly × 2, per the brief. The draft had added +1 spares on cheap ICs and connectors.

## Cost (2 boards + spares)

| Item | Value |
|---|---|
| Order lines | 54 (53 BOM lines + DNP spares) |
| Pieces | 499 |
| **Estimated total** | **$167.56 USD** |

- **What the prices are:** qty-1 cut-tape unit prices from dated search snippets of DigiKey storefronts and aggregators, captured 2026-10-11/12. EUR is converted at about 1.18. Lines marked "est." had no price visible.
- **What the total leaves out:** shipping, tax and the PCB.
- **Where the money goes:** the main costs are U3 STM32 ($22.62), U1/U2 LMR38020 ($18.20), the IMUs and sensors (about $30) and the inductors ($6.80).
- **Accuracy:** real quantity breaks on passives will lower the total. Re-price in BOM Manager before ordering.

## Required design actions to reach PASS

These are not done here, because design files are out of scope for this audit.

1. In `circuit.py`, set these MPNs:
   - `C8p2` → C0402C829C5GACTU / KEMET
   - `C2u2_X7R` → CL10B225KP8NNNC, 10 V
   - R3/R8 → ERJ-2RKF3482X
   - R5 → ERJ-2RKF2432X
   - Q2 → NX7002AK,215
   - U10 → W25N01GVZEIG TR
2. Correct the DigiKey PNs listed in G2S-11.
3. Regenerate `bom_raw.csv` and re-run this check on the changed lines.
