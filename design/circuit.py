"""F405-FC circuit model (single source of truth for schematic, netlist and PCB).

Run inside the KiCad chroot:  kc 'python3 design/circuit.py'
Writes the hierarchical schematic + project to kicad/ and the custom symbol library to lib/F405FC.kicad_sym.

Design documents: design/pinmap.md (rev C), design/power.md (rev B), design/decisions.md.
Every BOM part carries MPN / Manufacturer / DigiKey / Datasheet fields (catalog `CAT` below).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "gen"))

import schgen  # noqa: E402
import symlib  # noqa: E402
from sexpr import Sym, dump  # noqa: E402

OUT = os.path.join(ROOT, "kicad")
LIB = os.path.join(ROOT, "lib")

c = schgen.Circuit("F405FC", "F405-FC flight controller", rev="C")
PWR, MCU, SEN, VID, CON = (c.sheet(s) for s in ("Power", "MCU", "Sensors", "Video", "Connectors"))

# --------------------------------------------------------------------------------------------
# Part catalog: key -> (value, footprint, MPN, Manufacturer, DigiKey PN, datasheet URL)
# DigiKey PNs marked "verify" were not seen verbatim; Gate 2 confirms every line.
# --------------------------------------------------------------------------------------------
YAGEO_DS = "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"
SAMSUNG_DS = "https://product.samsungsem.com/mlcc/{}.do"  # per-MPN product page (Gate 1 G1N-03)
R0402, R0603 = "Resistor_SMD:R_0402_1005Metric", "Resistor_SMD:R_0603_1608Metric"
C0402, C0603, C0805, C1206, C1210 = ("Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric",
                                    "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric",
                                    "Capacitor_SMD:C_1210_3225Metric")


def yageo(val, code, size="0402"):
    mpn = f"RC{size}FR-07{code}L"
    dk = f"311-{val}{'L' if size == '0402' else 'H'}RCT-ND"
    return (val, R0402 if size == "0402" else R0603, mpn, "Yageo", dk, YAGEO_DS)


CAT = {
    # resistors (Yageo RC, 1 %). DigiKey pattern 311-<value><L|H>RCT-ND (confirmed pattern, see parts_signal.md)
    "R0": ("0R", R0402, "RC0402JR-070RL", "Yageo", "311-0.0JRCT-ND", YAGEO_DS),
    "R0_0805": ("0R 2A", "Resistor_SMD:R_0805_2012Metric", "RC0805JR-070RL", "Yageo", "311-0.0ARCT-ND", YAGEO_DS),
    "R100": yageo("100", "100R"),
    "R330": yageo("330", "330R"),
    "R1k": yageo("1.00K", "1K"),
    "R2k2": yageo("2.20K", "2K2"),
    "R5k1": yageo("5.10K", "5K1"),
    "R10k": yageo("10.0K", "10K"),
    "R10k_0603": yageo("10.0K", "10K", "0603"),
    "R11k": yageo("11.0K", "11K"),
    "R24k3": ("24.3K", R0402, "ERJ-2RKF2432X", "Panasonic", "P24.3KLCT-ND", "https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C304.pdf"),  # G2S-03: Yageo value not at DigiKey; PN matched by MPN
    "R34k8": ("34.8K", R0402, "ERJ-2RKF3482X", "Panasonic", "P34.8KLCT-ND", "https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C304.pdf"),  # G2S-03
    "R100k": yageo("100K", "100K"),
    "R301k_0603": yageo("301K", "301K", "0603"),
    # capacitors
    "C8p2": ("8.2pF C0G 50V", C0402, "C0402C829C5GACTU", "KEMET", "399-C0402C829C5GACTUCT-ND",
             "https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf"),  # Gate 2 G2S-01
    "C10n": ("10nF X7R 50V", C0402, "CL05B103KB5NNNC", "Samsung Electro-Mechanics", "1276-1028-1-ND", SAMSUNG_DS),
    "C100n": ("100nF X7R 16V", C0402, "CL05B104KO5NNNC", "Samsung Electro-Mechanics", "1276-1001-1-ND", SAMSUNG_DS),
    "C220n": ("220nF X5R 25V", C0402, "CL05A224KA5NNNC", "Samsung Electro-Mechanics", "1276-1455-1-ND", SAMSUNG_DS),
    "C100n_100V": ("100nF X7R 100V", C0603, "GRM188R72A104KA35D", "Murata", "490-3285-1-ND (verify)",
                   "https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM188R72A104KA35-01.pdf"),
    "C1u": ("1uF X5R 25V", C0603, "CL10A105KA8NNNC", "Samsung Electro-Mechanics", "1276-1102-1-ND (verify)", SAMSUNG_DS),
    "C2u2": ("2.2uF X5R 16V", C0603, "CL10A225KO8NNNC", "Samsung Electro-Mechanics", "1276-1040-1-ND", SAMSUNG_DS),
    "C2u2_X7R": ("2.2uF X7R 10V", C0603, "CL10B225KP8NNNC", "Samsung Electro-Mechanics", "1276-1134-1-ND", SAMSUNG_DS),  # G2S-02
    "C4u7": ("4.7uF X5R 16V", C0603, "CL10A475KO8NNNC", "Samsung Electro-Mechanics", "1276-1784-1-ND", SAMSUNG_DS),
    "C10u": ("10uF X5R 25V", C0805, "CL21A106KAYNNNE", "Samsung Electro-Mechanics", "1276-2891-1-ND (verify)", SAMSUNG_DS),
    "C22u": ("22uF X5R 25V", C1206, "CL31A226KAHNNNE", "Samsung Electro-Mechanics", "1276-3047-1-ND", SAMSUNG_DS),
    "C10u_50V": ("10uF X7R 50V", C1210, "CL32B106KBJNNNE", "Samsung Electro-Mechanics", "1276-3387-1-ND", SAMSUNG_DS),  # C1 (top side, 2.7 mm max OK)
    "C4u7_100V": ("4.7uF X7S 100V 2.0mm", C1210, "C3225X7S2A475K200AB", "TDK", "445-6042-1-ND (verify: K200AB cut tape)",
                  "https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/catalog/mlcc_commercial_midvoltage_en.pdf"),  # G2R-01: bottom-side U1/U2 input caps, 2.0 mm nominal
}


def fields(key):
    v, fp, mpn, mfr, dk, ds = CAT[key]
    ds = ds.format(mpn) if "{}" in ds else ds
    return v, fp, {"MPN": mpn, "Manufacturer": mfr, "DigiKey": dk, "Datasheet": ds}


def part(sheet, ref, lib_id, value, fp, conn, mpn, mfr, dk, ds, dnp=False, desc=""):
    f = {"MPN": mpn, "Manufacturer": mfr, "DigiKey": dk, "Datasheet": ds}
    if desc:
        f["Description"] = desc
    return c.add(sheet, ref, lib_id, value, fp, conn, fields=f, dnp=dnp)


_n = {}


def nextref(prefix):
    _n[prefix] = _n.get(prefix, 0) + 1
    return f"{prefix}{_n[prefix]}"


def R(sheet, key, a, b, dnp=False, ref=None):
    v, fp, f = fields(key)
    return c.add(sheet, ref or nextref("R"), "Device:R", v, fp, {"1": a, "2": b}, fields=f, dnp=dnp)


def C(sheet, key, a, b="GND", ref=None):
    v, fp, f = fields(key)
    return c.add(sheet, ref or nextref("C"), "Device:C", v, fp, {"1": a, "2": b}, fields=f)


pwrflags = []


def PWRFLAG(net):
    ref = f"#FLG{len(pwrflags) + 1:02d}"
    pwrflags.append(net)
    c.add(PWR, ref, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net})


# --------------------------------------------------------------------------------------------
# Custom symbols (written to lib/F405FC.kicad_sym and embedded in the schematic)
# --------------------------------------------------------------------------------------------
def custom(name, ref, left, right, top=(), bottom=(), desc=""):
    lid = "F405FC:" + name
    c.custom_symbols[lid] = symlib.make_box_symbol(lid, ref, left, right, top, bottom, desc)
    return lid


SYM_LMR = custom("LMR38020", "U",
                 [("3", "VIN", "power_in"), ("2", "EN", "input"), ("4", "RT/SYNC", "passive"), ("6", "PG", "open_collector")],
                 [("7", "BOOT", "passive"), ("8", "SW", "power_out"), ("5", "FB", "input")],
                 bottom=[("1", "GND", "power_in"), ("9", "EP", "passive")],
                 desc="80 V 2 A synchronous buck, HSOIC-8 PowerPAD")
SYM_LP38692 = custom("LP38692MP-3.3", "U",
                     [("4", "IN", "power_in"), ("1", "EN", "input"), ("2", "NC", "no_connect")],
                     [("3", "OUT", "power_out")], bottom=[("5", "GND", "power_in")],
                     desc="1 A 3.3 V LDO, SOT-223-5 (tab = GND)")
SYM_ICM = custom("ICM-42688-P", "U",
                 [("8", "VDD", "power_in"), ("5", "VDDIO", "power_in"), ("12", "AP_CS", "input"),
                  ("13", "AP_SCLK", "input"), ("14", "AP_SDI", "bidirectional"), ("1", "AP_SDO", "tri_state")],
                 [("4", "INT1", "output"), ("9", "INT2/FSYNC", "input"), ("2", "RESV2", "passive"),
                  ("3", "RESV3", "passive"), ("10", "RESV10", "passive"), ("11", "RESV11", "passive")],
                 bottom=[("6", "GND", "power_in"), ("7", "RESV7_GND", "passive")],
                 desc="6-axis IMU, LGA-14 2.5x3")
SYM_BMI = custom("BMI270", "U",
                 [("8", "VDD", "power_in"), ("5", "VDDIO", "power_in"), ("12", "CSB", "input"),
                  ("13", "SCX", "input"), ("14", "SDX", "bidirectional"), ("1", "SDO", "tri_state")],
                 [("4", "INT1", "output"), ("9", "INT2", "output"), ("2", "ASDX", "bidirectional"),
                  ("3", "ASCX", "bidirectional"), ("10", "OCSB", "input"), ("11", "OSDO", "output")],
                 bottom=[("7", "GND", "power_in"), ("6", "GNDIO", "power_in")],
                 desc="6-axis IMU, LGA-14 2.5x3")
SYM_BMP = custom("BMP390", "U",
                 [("10", "VDD", "power_in"), ("1", "VDDIO", "power_in"), ("6", "CSB", "input"),
                  ("2", "SCK", "input"), ("4", "SDI", "bidirectional"), ("5", "SDO", "input")],
                 [("7", "INT", "output")],
                 bottom=[("3", "VSS", "power_in"), ("8", "VSS", "passive"), ("9", "VSS", "passive")],
                 desc="Barometer, LGA-10 2x2")
SYM_W25N = custom("W25N01GV", "U",
                  [("8", "VCC", "power_in"), ("1", "~{CS}", "input"), ("6", "CLK", "input"), ("5", "DI", "input")],
                  [("2", "DO", "tri_state"), ("3", "~{WP}", "input"), ("7", "~{HOLD}", "input")],
                  bottom=[("4", "GND", "power_in"), ("9", "EP", "passive")],
                  desc="1 Gbit SPI NAND, WSON-8 8x6")
SYM_TS5A = custom("TS5A3159A", "U",
                  [("5", "V+", "power_in"), ("6", "IN", "input")],
                  [("4", "COM", "passive"), ("3", "NC", "passive"), ("1", "NO", "passive")],
                  bottom=[("2", "GND", "power_in")],
                  desc="SPDT analog switch; IN low = COM-NC, high = COM-NO")

# footprints
FP = {
    "STM32": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "LMR": "F405FC:TI_HSOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.71x3.4mm_DDA",
    "SOT223_5": "Package_TO_SOT_SMD:SOT-223-5",
    "SOT23_5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT23_6": "Package_TO_SOT_SMD:SOT-23-6",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "ICM": "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    "BMI": "F405FC:Bosch_LGA-14_3x2.5mm_P0.5mm_BMI270",
    "BMP": "F405FC:Bosch_LGA-10_2x2mm_P0.5mm_BMP390",
    "MAG": "Package_LGA:LGA-12_2x2mm_P0.5mm",
    "W25N": "Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm",
    "XTAL": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "USBC": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "SH8": "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal",
    "SH6": "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal",
    "SH4": "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
    "L4030": "Inductor_SMD:L_Wuerth_MAPI-4020",
    "SMB": "Diode_SMD:D_SMB",
    "SOD123W": "Diode_SMD:Nexperia_CFP3_SOD-123W",
    "LED0603": "LED_SMD:LED_0603_1608Metric",
    "FB0603": "Inductor_SMD:L_0603_1608Metric",
    "SW": "Button_Switch_SMD:SW_SPST_PTS810",
    "PAD_PWR": "F405FC:Pad_SMD_2.5x4.0mm",
    "PAD_10V": "F405FC:Pad_SMD_2.0x3.0mm",
    "PAD_MED": "F405FC:Pad_SMD_1.5x2.0mm",
    "PAD_SIG": "F405FC:Pad_SMD_1.2x1.6mm",
    "TP": "TestPoint:TestPoint_Pad_D1.0mm",
    "HOLE": "F405FC:MountingHole_3.2mm_M3_Grommet4.6mm",
}

TI = "https://www.ti.com/lit/ds/symlink/"

# ============================================================================================
# POWER sheet
# ============================================================================================
# Power entry pads (design/power.md section 5)
for ref, net, fp, desc in (("P1", "VBAT", "PAD_PWR", "Battery + solder pad"), ("P2", "GND", "PAD_PWR", "Battery - solder pad"),
                           ("P3", "10V", "PAD_10V", "10 V VTX pad"), ("P4", "GND", "PAD_10V", "GND pad (10 V VTX)")):
    part(PWR, ref, "Connector:TestPoint", net, FP[fp], {"1": net}, "n/a (PCB pad)", "n/a", "n/a (PCB pad)", "", desc=desc)
    c.parts[-1].fields["InBOM"] = "no"

part(PWR, "D1", "Device:D_Zener", "SMBJ26A", FP["SMB"], {"K": "VBAT", "A": "GND"},
     "SMBJ26A", "Littelfuse", "SMBJ26ALFCT-ND", "https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet",
     desc="TVS 26 V uni 600 W")
C(PWR, "C10u_50V", "VBAT")  # entry cap C1

for rail, vout, rfbb_key, lval, lmpn, ldk, en_net in (
        ("5V", "5V", "R24k3", "5.6uH", "74438356056", "not confirmed; alt 78438356056 = 732-11317-1-ND", "EN_5V"),
        ("10V", "10V", "R11k", "5.6uH", "74438356056", "not confirmed; alt 78438356056 = 732-11317-1-ND", "EN_10V")):
    # WE-MAPI 4020 (2.1 mm max): the bottom side is limited to 2.5 mm (Gate 3 G3-01); one part type for both rails
    u = "U1" if rail == "5V" else "U2"
    l = "L1" if rail == "5V" else "L2"
    sw, bst, fb, rt = f"SW_{rail}", f"BST_{rail}", f"FB_{rail}", f"RT_{rail}"
    part(PWR, u, SYM_LMR, "LMR38020FSDDAR", FP["LMR"],
         {"VIN": "VBAT", "EN": en_net, "RT/SYNC": rt, "PG": None, "BOOT": bst, "SW": sw, "FB": fb, "GND": "GND", "EP": "GND"},
         "LMR38020FSDDAR", "Texas Instruments", "296-LMR38020FSDDARCT-ND (verify)", TI + "lmr38020.pdf",
         desc=f"{rail} buck, 750 kHz FPWM+SS")
    C(PWR, "C4u7_100V", "VBAT")
    C(PWR, "C4u7_100V", "VBAT")  # two per IC: >= 4.7 uF effective at 25 V (power audit P0-06; G2R-01 100 V part, ~3.5 uF each at 25 V)
    C(PWR, "C100n_100V", "VBAT")
    R(PWR, "R301k_0603", "VBAT", en_net)
    R(PWR, "R100k", en_net, "GND")
    R(PWR, "R34k8", rt, "GND")
    C(PWR, "C100n", bst, sw)
    part(PWR, l, "Device:L", lval, FP["L4030"], {"1": sw, "2": vout}, lmpn, "Würth Elektronik", ldk,
         "https://www.we-online.com/components/products/datasheet/" + lmpn + ".pdf", desc="WE-MAPI 4020 power inductor")
    R(PWR, "R100k", vout, fb)
    R(PWR, rfbb_key, fb, "GND")
    for _ in range(3):
        C(PWR, "C22u", vout)
    C(PWR, "C100n_100V" if rail == "10V" else "C100n", vout)  # 10 V HF cap rated >= 50 V (Gate 1 G1P-06)

# VTX power cut: Q2 pulls U2 EN low when VTX_PWR_EN is high (decisions D-04)
part(PWR, "Q2", "Transistor_FET:2N7002", "NX7002AK", FP["SOT23"], {"G": "VTX_OFF_G", "S": "GND", "D": "EN_10V"},
     "NX7002AK,215", "Nexperia", "1727-1289-1-ND", "https://assets.nexperia.com/documents/data-sheet/NX7002AK.pdf",
     desc="VTX off: pulls 10 V buck EN low")
R(PWR, "R1k", "VTX_PWR_EN", "VTX_OFF_G")
R(PWR, "R100k", "VTX_OFF_G", "GND")

# 5V_SYS OR-ing (USB VBUS diode D4 lives on the Connectors sheet)
part(PWR, "D5", "Device:D_Schottky", "PMEG4030ER", FP["SOD123W"], {"A": "5V", "K": "5V_SYS"},
     "PMEG4030ER,115", "Nexperia", "1727-5313-1-ND", "https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf",
     desc="5V -> 5V_SYS OR diode")
C(PWR, "C4u7", "5V_SYS")  # limited so USB plug-in inrush stays bounded (power audit P0-05)

# 3V3 main LDO
part(PWR, "U4", SYM_LP38692, "LP38692MP-3.3", FP["SOT223_5"], {"IN": "5V_SYS", "EN": "5V_SYS", "NC": None, "OUT": "3V3", "GND": "GND"},
     "LP38692MP-3.3/NOPB", "Texas Instruments", "LP38692MP-3.3/NOPBCT-ND", TI + "lp38692.pdf", desc="3.3 V 1 A LDO")
C(PWR, "C1u", "5V_SYS")
C(PWR, "C2u2", "3V3")  # single local output cap: ESR within LP38692 5-500 mOhm window (Gate 1 G1P-02)
nextref("C")  # C21 retired (was the LDO-local 100 nF); refdes kept stable for placement

# 3V3_IMU low-noise LDO
part(PWR, "U5", "Regulator_Linear:LP5907MFX-3.3", "LP5907MFX-3.3", FP["SOT23_5"],
     {"IN": "5V_SYS", "EN": "5V_SYS", "NC": None, "OUT": "3V3_IMU", "GND": "GND"},
     "LP5907MFX-3.3/NOPB", "Texas Instruments", "296-38557-1-ND", TI + "lp5907.pdf", desc="3.3 V low-noise LDO for IMUs")
C(PWR, "C1u", "5V_SYS")
C(PWR, "C2u2_X7R", "3V3_IMU")

# Power LED (red)
R(PWR, "R1k", "3V3", "LED_PWR_A")
part(PWR, "D10", "Device:LED", "Red", FP["LED0603"], {"A": "LED_PWR_A", "K": "GND"},
     "LTST-C191KRKT", "Lite-On", "160-1447-1-ND", "https://optoelectronics.liteon.com/upload/download/DS22-2000-223/LTST-C191KRKT.pdf",
     desc="power LED")

# VBAT divider 10k/1k + 100 nF
R(PWR, "R10k_0603", "VBAT", "VBAT_ADC")
R(PWR, "R1k", "VBAT_ADC", "GND")
C(PWR, "C100n", "VBAT_ADC")

for n in ("VBAT", "GND", "5V", "10V", "5V_SYS", "VBUS", "3V3A"):
    PWRFLAG(n)

# ============================================================================================
# MCU sheet
# ============================================================================================
mcu_conn = {
    "VBAT": "3V3", "PC13": "CAM_SEL", "PC14": "GYRO2_INT", "PC15": "VTX_PWR_EN", "PH0": "HSE_IN", "PH1": "HSE_OUT",
    "NRST": "NRST", "PC0": "VBAT_ADC", "PC1": "CURR_ADC", "PC2": "UNUSED_PC2", "PC3": "UNUSED_PC3", "VSSA": "GND", "VDDA": "3V3A",
    "PA0": "MOTOR8", "PA1": "ESC_TLM", "PA2": "UART2_TX", "PA3": "UART2_RX", "VSS": "GND", "VDD": "3V3",
    "PA4": "GYRO1_CS", "PA5": "SPI1_SCK", "PA6": "SPI1_MISO", "PA7": "SPI1_MOSI", "PC4": "GYRO1_INT", "PC5": "RSSI_ADC",
    "PB0": "MOTOR1", "PB1": "MOTOR2", "PB2": "BEEPER", "PB10": "MOTOR3", "PB11": "MOTOR4", "VCAP_1": "VCAP1",
    "PB12": "UNUSED_PB12", "PB13": "UNUSED_PB13", "PB14": "STATUS_LED_BLUE", "PB15": "STATUS_LED_GREEN", "PC6": "UART6_TX",
    "PC7": "UART6_RX", "PC8": "MOTOR5", "PC9": "MOTOR6", "PA8": "LED_STRIP", "PA9": "UART1_TX", "PA10": "UART1_RX",
    "PA11": "USB_DM", "PA12": "USB_DP", "PA13": "SWDIO", "VCAP_2": "VCAP2", "PA14": "SWCLK", "PA15": "GYRO2_CS",
    "PC10": "UART3_TX", "PC11": "UART3_RX", "PC12": "UART5_TX", "PD2": "UART5_RX", "PB3": "SPI3_SCK",
    "PB4": "SPI3_MISO", "PB5": "SPI3_MOSI", "PB6": "FLASH_CS", "PB7": "MOTOR7", "BOOT0": "BOOT0", "PB8": "I2C1_SCL",
    "PB9": "I2C1_SDA",
}
part(MCU, "U3", "MCU_ST_STM32F4:STM32F405RGTx", "STM32F405RGT6", FP["STM32"], mcu_conn,
     "STM32F405RGT6", "STMicroelectronics", "497-11767-ND", "https://www.st.com/resource/en/datasheet/stm32f405rg.pdf",
     desc="MCU 168 MHz Cortex-M4F, LQFP-64")
for _ in range(4):
    C(MCU, "C100n", "3V3")  # VDD pins 19, 32, 48, 64
C(MCU, "C4u7", "3V3")       # bulk
C(MCU, "C100n", "3V3")      # VBAT pin 1
part(MCU, "FB1", "Device:FerriteBead_Small", "600R@100MHz", FP["FB0603"], {"1": "3V3", "2": "3V3A"},
     "BLM18KG601SN1D", "Murata", "490-5258-1-ND",
     "https://www.murata.com/en-us/products/productdata/8796740616222/ENFA0003.pdf", desc="VDDA filter bead")
C(MCU, "C1u", "3V3A")
C(MCU, "C100n", "3V3A")
C(MCU, "C2u2", "VCAP1")
C(MCU, "C2u2", "VCAP2")
C(MCU, "C100n", "NRST")
R(MCU, "R10k", "BOOT0", "GND")
part(MCU, "SW1", "Switch:SW_Push", "BOOT", FP["SW"], {"1": "3V3", "2": "BOOT0"},
     "PTS810 SJM 250 SMTR LFS", "C&K", "CKN10502CT-ND",
     "https://www.ckswitches.com/media/1476/pts810.pdf", desc="BOOT button (BOOT0 high)")
R(MCU, "R10k", "BEEPER", "GND")  # PB2 = BOOT1 strap + beeper FET gate pulldown
part(MCU, "Y1", "Device:Crystal_GND24", "8MHz", FP["XTAL"], {"1": "HSE_IN", "3": "HSE_OUT", "2": "GND", "4": "GND"},
     "ECS-80-8-33-JEN-TR3", "ECS Inc.", "50-ECS-80-8-33-JEN-TR3CT-ND (verify)",
     "https://ecsxtal.com/store/pdf/ECX-32.pdf", desc="8 MHz HSE crystal, CL 8 pF")
C(MCU, "C8p2", "HSE_IN")   # 8.2 pF: CL 8 pF crystal with 3-5 pF stray (Gate 1 G1M2-01/03)
C(MCU, "C8p2", "HSE_OUT")
for cs in ("GYRO1_CS", "GYRO2_CS", "FLASH_CS"):
    R(MCU, "R10k", "3V3", cs)
for n in ("UNUSED_PC2", "UNUSED_PC3", "UNUSED_PB12", "UNUSED_PB13"):
    R(MCU, "R100k", n, "GND")  # define unused pins (re-audit R-03)
R(MCU, "R2k2", "3V3", "I2C1_SCL")
R(MCU, "R2k2", "3V3", "I2C1_SDA")
R(MCU, "R330", "3V3", "LED_BLUE_A")
part(MCU, "D11", "Device:LED", "Blue", FP["LED0603"], {"A": "LED_BLUE_A", "K": "STATUS_LED_BLUE"},
     "LTST-C191TBKT", "Lite-On", "160-1647-1-ND", "https://optoelectronics.liteon.com/upload/download/DS22-2000-213/LTST-C191TBKT.pdf",
     desc="status LED0")
R(MCU, "R1k", "3V3", "LED_GREEN_A")
part(MCU, "D12", "Device:LED", "Green", FP["LED0603"], {"A": "LED_GREEN_A", "K": "STATUS_LED_GREEN"},
     "LTST-C191KGKT", "Lite-On", "160-1446-1-ND", "https://optoelectronics.liteon.com/upload/download/DS22-2000-222/LTST-C191KGKT.pdf",
     desc="status LED1")

# ============================================================================================
# SENSORS sheet
# ============================================================================================
part(SEN, "U6", SYM_ICM, "ICM-42688-P", FP["ICM"],
     {"VDD": "3V3_IMU", "VDDIO": "3V3_IMU", "AP_CS": "GYRO1_CS", "AP_SCLK": "SPI1_SCK", "AP_SDI": "SPI1_MOSI",
      "AP_SDO": "SPI1_MISO", "INT1": "GYRO1_INT", "INT2/FSYNC": "GND", "RESV2": "GND", "RESV3": "GND", "RESV10": "GND",
      "RESV11": "GND", "GND": "GND", "RESV7_GND": "GND"},
     "ICM-42688-P", "TDK InvenSense", "1428-ICM-42688-PCT-ND",
     "https://invensense.tdk.com/wp-content/uploads/2020/04/ds-000347_icm-42688-p-datasheet.pdf", desc="IMU 1 (gyro_1)")
C(SEN, "C100n", "3V3_IMU")
C(SEN, "C2u2_X7R", "3V3_IMU")  # ICM-42688-P BOM: X7R 2.2 uF
C(SEN, "C10n", "3V3_IMU")
part(SEN, "U7", SYM_BMI, "BMI270", FP["BMI"],
     {"VDD": "3V3_IMU", "VDDIO": "3V3_IMU", "CSB": "GYRO2_CS", "SCX": "SPI1_SCK", "SDX": "SPI1_MOSI", "SDO": "SPI1_MISO",
      "INT1": "GYRO2_INT", "INT2": None, "ASDX": None, "ASCX": None, "OCSB": None, "OSDO": None, "GND": "GND", "GNDIO": "GND"},
     "BMI270", "Bosch Sensortec", "828-1091-1-ND",
     "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf", desc="IMU 2 (gyro_2)")
C(SEN, "C100n", "3V3_IMU")
C(SEN, "C100n", "3V3_IMU")
part(SEN, "U8", SYM_BMP, "BMP390", FP["BMP"],
     {"VDD": "3V3", "VDDIO": "3V3", "CSB": "3V3", "SCK": "I2C1_SCL", "SDI": "I2C1_SDA", "SDO": "GND", "INT": None, "VSS": "GND"},
     "BMP390", "Bosch Sensortec", "828-BMP390CT-ND",
     "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp390-ds002.pdf", desc="baro, I2C 0x76")
C(SEN, "C100n", "3V3")
C(SEN, "C100n", "3V3")
part(SEN, "U9", "Sensor_Magnetic:LIS2MDL", "IIS2MDC", FP["MAG"],
     {"1": "I2C1_SCL", "2": None, "3": "3V3", "4": "I2C1_SDA", "5": "MAG_C1", "6": "GND", "7": None, "8": "GND",
      "9": "3V3", "10": "3V3", "11": None, "12": None},
     "IIS2MDCTR", "STMicroelectronics", "497-17728-1-ND", "https://www.st.com/resource/en/datasheet/iis2mdc.pdf",
     desc="magnetometer, I2C 0x1E (LIS2MDL-compatible pinout)")
C(SEN, "C220n", "MAG_C1")
C(SEN, "C100n", "3V3")
C(SEN, "C4u7", "3V3")  # IIS2MDC bulk (Gate 1 G1S-04)
part(SEN, "U10", SYM_W25N, "W25N01GV", FP["W25N"],
     {"VCC": "3V3", "~{CS}": "FLASH_CS", "CLK": "SPI3_SCK", "DI": "SPI3_MOSI", "DO": "SPI3_MISO", "~{WP}": "FLASH_WP",
      "~{HOLD}": "FLASH_HOLD", "GND": "GND", "EP": "GND"},
     "W25N01GVZEIG TR", "Winbond", "256-W25N01GVZEIGTRCT-ND",
     "https://www.winbond.com/resource-files/w25n01gv%20revl%20050918%20unsecured.pdf", desc="blackbox flash 1 Gbit")
C(SEN, "C100n", "3V3")
R(SEN, "R10k", "3V3", "FLASH_WP")
R(SEN, "R10k", "3V3", "FLASH_HOLD")

# ============================================================================================
# VIDEO sheet: camera switch (no OSD, decisions D-01) and LED strip buffer
# ============================================================================================
part(VID, "U11", SYM_TS5A, "TS5A3159A", FP["SOT23_6"],
     {"V+": "3V3", "IN": "CAM_SEL", "COM": "VTX_VID", "NC": "CAM1_VID", "NO": "CAM2_VID", "GND": "GND"},
     "TS5A3159ADBVR", "Texas Instruments", "296-19265-1-ND", TI + "ts5a3159a.pdf", desc="camera select (low = CAM1)")
C(VID, "C100n", "3V3")
R(VID, "R100k", "CAM_SEL", "GND")
for ref, net in (("P5", "CAM1_VID"), ("P6", "CAM2_VID"), ("P7", "VTX_VID")):
    part(VID, ref, "Connector:TestPoint", net, FP["PAD_SIG"], {"1": net}, "n/a (PCB pad)", "n/a", "n/a (PCB pad)", "",
         desc="video pad")
    c.parts[-1].fields["InBOM"] = "no"
for ref, net in (("P8", "5V"), ("P9", "GND")):
    part(VID, ref, "Connector:TestPoint", net, FP["PAD_SIG"], {"1": net}, "n/a (PCB pad)", "n/a", "n/a (PCB pad)", "",
         desc="camera power pad")
    c.parts[-1].fields["InBOM"] = "no"

part(VID, "U12", "74xGxx:74AHCT1G125", "SN74LV1T125", FP["SOT23_5"],
     {"1": "GND", "2": "LED_STRIP", "3": "GND", "4": "LED_DIN_BUF", "5": "5V"},
     "SN74LV1T125DBVR", "Texas Instruments", "296-37172-1-ND", TI + "sn74lv1t125.pdf", desc="WS2812 3.3->5 V buffer")
C(VID, "C100n", "5V")
R(VID, "R0", "LED_STRIP", "LED_DIN_BUF", dnp=True)  # bypass option (G0-10): fit ONLY with U12 removed
R(VID, "R330", "LED_DIN_BUF", "LED_DIN")
for ref, net, fp in (("P10", "LED_DIN", "PAD_SIG"), ("P11", "5V", "PAD_MED")):  # LED GND shares P4 (Gate 3 G3-11, D-21)
    part(VID, ref, "Connector:TestPoint", net, FP[fp], {"1": net}, "n/a (PCB pad)", "n/a", "n/a (PCB pad)", "",
         desc="LED strip pad")
    c.parts[-1].fields["InBOM"] = "no"

# ============================================================================================
# CONNECTORS sheet
# ============================================================================================
part(CON, "J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB4105-GF-A", FP["USBC"],
     {"VBUS": "VBUS", "GND": "GND", "CC1": "USB_CC1", "CC2": "USB_CC2", "D+": "USB_DP", "D-": "USB_DM",
      "SBU1": None, "SBU2": None, "SHIELD": "GND"},
     "USB4105-GF-A", "GCT", "2073-USB4105-GF-ACT-ND", "https://gct.co/files/drawings/usb4105.pdf", desc="USB-C (USB 2.0 FS)")
R(CON, "R5k1", "USB_CC1", "GND")
R(CON, "R5k1", "USB_CC2", "GND")
part(CON, "U13", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", FP["SOT23_6"],
     {"I/O1": "USB_DM", "I/O2": "USB_DP", "GND": "GND", "VBUS": "VBUS"},
     "USBLC6-2SC6", "STMicroelectronics", "497-5235-1-ND", "https://www.st.com/resource/en/datasheet/usblc6-2.pdf",
     desc="USB ESD")
C(CON, "C1u", "VBUS")
R(CON, "R100k", "VBUS", "GND")
part(CON, "D4", "Device:D_Schottky", "PMEG4030ER", FP["SOD123W"], {"A": "VBUS", "K": "5V_SYS"},
     "PMEG4030ER,115", "Nexperia", "1727-5313-1-ND", "https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf",
     desc="VBUS -> 5V_SYS OR diode")

part(CON, "J2", "Connector_Generic_MountingPin:Conn_01x08_MountingPin", "ESC", FP["SH8"],
     {"1": "VBAT", "2": "GND", "3": "ESC_CURR", "4": "MOTOR1", "5": "MOTOR2", "6": "MOTOR3", "7": "MOTOR4", "8": "ESC_TLM",
      "MP": "GND"},
     "SM08B-SRSS-TB(LF)(SN)", "JST", "455-1808-1-ND", "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
     desc="ESC: VBAT GND CURR M1 M2 M3 M4 TLM")
part(CON, "J3", "Connector_Generic_MountingPin:Conn_01x06_MountingPin", "HD VTX", FP["SH6"],
     {"1": "VTX_PWR", "2": "GND", "3": "UART1_TX", "4": "UART1_RX", "5": "GND", "6": "HD_R2", "MP": "GND"},
     "SM06B-SRSS-TB(LF)(SN)", "JST", "455-1806-1-ND", "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
     desc="HD VTX: 10V GND TX RX GND SBUS/R2")
R(CON, "R0", "HD_R2", "UART5_RX", dnp=True)  # G0-05: DNP link, no inverter
v, fp, f = fields("R0_0805")
c.add(CON, "R41", "Device:R", v, fp, {"1": "10V", "2": "VTX_PWR"}, fields=f)  # remove on 2S HD builds (power re-audit P1-03)
part(CON, "J4", "Connector_Generic_MountingPin:Conn_01x06_MountingPin", "GPS", FP["SH6"],
     {"1": "5V", "2": "GND", "3": "UART3_TX", "4": "UART3_RX", "5": "I2C1_SDA", "6": "I2C1_SCL", "MP": "GND"},
     "SM06B-SRSS-TB(LF)(SN)", "JST", "455-1806-1-ND", "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
     desc="GPS: 5V GND TX RX SDA SCL")
part(CON, "J5", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "ELRS", FP["SH4"],
     {"1": "5V_SYS", "2": "GND", "3": "UART2_TX", "4": "UART2_RX", "MP": "GND"},
     "SM04B-SRSS-TB(LF)(SN)", "JST", "455-1804-1-ND", "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
     desc="ELRS RX: 5V GND TX RX")

# CURR / RSSI protection: 10k series + 10 nF + BAT54S (pinmap G0-09, power.md 10.2)
for src, adc, dref in (("ESC_CURR", "CURR_ADC", "D7"), ("RSSI_IN", "RSSI_ADC", "D8")):
    R(CON, "R10k", src, adc)
    C(CON, "C10n", adc)
    part(CON, dref, "Diode:BAT54S", "BAT54S", FP["SOT23"], {"A": "GND", "K": "3V3", "COM": adc},
         "BAT54S-7-F", "Diodes Incorporated", "BAT54S-FDICT-ND", "https://www.diodes.com/assets/Datasheets/ds11005.pdf",
         desc="ADC clamp")

# Buzzer driver: PMV40UN2, gate 100R from PB2 node (10k BOOT1 pulldown on MCU sheet)
R(CON, "R100", "BEEPER", "BUZ_G")
part(CON, "Q1", "Transistor_FET:2N7002", "PMV40UN2", FP["SOT23"], {"G": "BUZ_G", "S": "GND", "D": "BUZ_N"},
     "PMV40UN2R", "Nexperia", "1727-1900-1-ND", "https://assets.nexperia.com/documents/data-sheet/PMV40UN2.pdf",
     desc="buzzer low-side switch")
part(CON, "D9", "Device:D_Schottky", "PMEG4030ER", FP["SOD123W"], {"A": "BUZ_N", "K": "5V"},
     "PMEG4030ER,115", "Nexperia", "1727-5313-1-ND", "https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf",
     desc="buzzer flyback")

pads = [("P13", "5V", "PAD_SIG", "buzzer +"), ("P14", "BUZ_N", "PAD_SIG", "buzzer -"),
        ("P15", "UART5_TX", "PAD_SIG", "T5"), ("P16", "UART5_RX", "PAD_SIG", "R5"),
        ("P17", "UART6_TX", "PAD_SIG", "T6"), ("P18", "UART6_RX", "PAD_SIG", "R6"),
        ("P19", "MOTOR5", "PAD_SIG", "S5"), ("P20", "MOTOR6", "PAD_SIG", "S6"),
        ("P21", "MOTOR7", "PAD_SIG", "S7"), ("P22", "MOTOR8", "PAD_SIG", "S8"),
        ("P23", "RSSI_IN", "PAD_SIG", "RSSI"), ("P24", "GND", "PAD_SIG", "GND (spare UART/servo)"),
        ("P25", "5V", "PAD_SIG", "5V (servo/spare)")]
for ref, net, fp, desc in pads:
    part(CON, ref, "Connector:TestPoint", net, FP[fp], {"1": net}, "n/a (PCB pad)", "n/a", "n/a (PCB pad)", "", desc=desc)
    c.parts[-1].fields["InBOM"] = "no"
for ref, net in (("TP1", "SWDIO"), ("TP2", "SWCLK"), ("TP3", "NRST"), ("TP4", "3V3"), ("TP5", "GND")):
    part(CON, ref, "Connector:TestPoint", net, FP["TP"], {"1": net}, "n/a (test pad)", "n/a", "n/a (test pad)", "",
         desc="SWD test pad")
    c.parts[-1].fields["InBOM"] = "no"
for i in range(1, 5):
    part(CON, f"H{i}", "Mechanical:MountingHole", "M3", FP["HOLE"], {}, "n/a (hole)", "n/a", "n/a (hole)", "",
         desc="30.5 mm M3 mounting hole")
    c.parts[-1].fields["InBOM"] = "no"

c.note(PWR, "Power: see design/power.md rev B. U1/U2 LMR38020FSDDAR 750 kHz. U2 EN pulled low by Q2 when VTX_PWR_EN is high (VTX off).")
c.note(MCU, "MCU: pin map design/pinmap.md rev C. PC2/PC3/PB12/PB13 unused (OSD removed, D-01).")
c.note(SEN, "Sensors: IMUs on 3V3_IMU (LP5907), SPI1. Baro 0x76 + mag 0x1E on I2C1. Flash on SPI3.")
c.note(VID, "Video: analog camera switch only (no OSD chip, D-01); DC-coupled cameras only (signal must stay 0..3.3 V). LED buffer U12 from 5V; DNP bypass R32 only with U12 removed.")
c.note(CON, "Connectors: JST-SH. ESC pin order VBAT GND CURR M1 M2 M3 M4 TLM. HD VTX pin 6 (R2) NC unless R DNP fitted.")


# --------------------------------------------------------------------------------------------
def write_symbol_lib(path):
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "f405fc_gen"],
           [Sym("generator_version"), "10.0"]]
    for lid, tree in sorted(c.custom_symbols.items()):
        t = list(tree)
        t[1] = lid.split(":", 1)[1]
        lib.append(t)
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(dump(lib) + "\n")


def net_settings():
    """Net classes + patterns (single definition, also re-applied by gen/build_pcb.py after pcbnew saves)."""
    def nc(name, w, clr=0.127, **k):
        d = {"name": name, "clearance": clr, "track_width": w, "via_diameter": 0.6, "via_drill": 0.3,
             "diff_pair_width": 0.2, "diff_pair_gap": 0.15, "microvia_diameter": 0.3, "microvia_drill": 0.1,
             "priority": 0}
        d.update(k)
        return d
    classes = [nc("Default", 0.15), nc("PWR_HI", 0.45, 0.2, priority=1), nc("PWR_MID", 0.35, 0.15, priority=2),
               nc("PWR", 0.2, priority=3),  # buck hot loops + main VBAT/5V copper: gen/critical.py
               nc("USB", 0.2, diff_pair_width=0.2, diff_pair_gap=0.15, priority=4)]
    patterns = ([("PWR_HI", n) for n in ("10V", "SW_5V", "SW_10V", "VTX_PWR")] + [("PWR_MID", n) for n in ("VBAT", "5V")] +
                [("PWR", n) for n in ("5V_SYS", "3V3", "3V3_IMU", "3V3A", "VBUS", "BUZ_N", "BST_5V", "BST_10V",
                                       "VCAP1", "VCAP2")] +
                [("USB", n) for n in ("USB_DP", "USB_DM")])
    return classes, patterns


def enable_erc_rules(pro_path):
    """Turn on the ERC checks the brief requires (single global label = error)."""
    import json
    with open(pro_path) as f:
        pro = json.load(f)
    pro.setdefault("erc", {})["rule_severities"] = {"single_global_label": "error", "global_label_dangling": "error",
                                      "similar_labels": "warning", "unconnected_wire_endpoint": "warning",
                                      "lib_symbol_issues": "warning", "lib_symbol_mismatch": "warning",
                                      "footprint_link_issues": "warning"}
    with open(pro_path, "w") as f:
        json.dump(pro, f, indent=2)


def write_lib_tables(outdir):
    with open(os.path.join(outdir, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n  (version 7)\n  (lib (name "F405FC")(type "KiCad")(uri "${KIPRJMOD}/../lib/F405FC.kicad_sym")(options "")(descr "F405-FC custom symbols"))\n)\n')
    with open(os.path.join(outdir, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "F405FC")(type "KiCad")(uri "${KIPRJMOD}/../lib/F405FC.pretty")(options "")(descr "F405-FC custom footprints"))\n)\n')


def main():
    res, problems = c.resolve()
    unassigned = [p for p in problems if "unassigned" in p]
    hard = [p for p in problems if "unassigned" not in p]
    if hard or unassigned:
        print("PROBLEMS:\n  " + "\n  ".join(hard + unassigned))
        raise SystemExit(1)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(LIB, exist_ok=True)
    schgen.write(c, OUT)
    schgen.write_project(c, OUT, *net_settings())
    enable_erc_rules(os.path.join(OUT, c.name + ".kicad_pro"))
    write_symbol_lib(os.path.join(LIB, "F405FC.kicad_sym"))
    write_lib_tables(OUT)
    nets = c.nets()
    print(f"parts={len(c.parts)} nets={len(nets)} sheets={len(c.sheets)}")


if __name__ == "__main__":
    main()
