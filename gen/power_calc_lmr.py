"""Rev B power calcs: LMR38020FSDDAR (FPWM + spread spectrum) for 5V and 10V rails (python -I gen/power_calc_lmr.py)."""
import math

FSW = 750e3            # RT = 34.8k (datasheet Table 8-1)
RHS25, RLS25 = 0.303, 0.133   # datasheet typ 25 C
HOT = 1.45             # Rds(on) multiplier at Tj ~ 110-125 C (typical CMOS power FET tempco)
TONMIN, TOFFMIN = 131e-9, 300e-9   # max limits
ILS_MIN, IHS_MIN, IHS_MAX = 1.8, 2.6, 3.8
TEDGE = 10e-9          # tr+tf estimate (not specified in datasheet)
QSW = 0.03             # gate drive + IQ allowance, W


def rt_k(f_khz):
    return 30970 * f_khz ** -1.027  # Eq. 2


def rail(name, vo, L, dcr, iout, vins):
    print(f"\n== {name}: Vo={vo} L={L*1e6:.1f}uH DCRmax={dcr*1e3:.0f}mOhm Iout={iout}A fsw={FSW/1e3:.0f}kHz")
    print(f"  Lmin (Eq.11, M=0.25) = {0.25*vo/FSW*1e6:.2f} uH")
    print(f"  Vin_max w/o foldback (Eq.5, tonmin max) = {vo/(TONMIN*FSW):.1f} V; Vin_min w/o foldback (Eq.6) = {vo/(1-TOFFMIN*FSW):.2f} V")
    for vin in vins:
        if vin <= vo / (1 - TOFFMIN * FSW):
            vdrop = vin - iout * (RHS25 * HOT + dcr)
            print(f"  Vin={vin:5.1f}: dropout/foldback, Vout ~ {min(vo, vdrop):.2f} V at {iout} A")
            continue
        D = vo / vin
        dil = (vin - vo) / (L * FSW) * D
        ipk = iout + dil / 2
        imax = ILS_MIN + dil / 2                      # Eq.7 with ILS min
        imax_hs = IHS_MIN - dil / 2
        pc = iout ** 2 * (RHS25 * HOT * D + RLS25 * HOT * (1 - D))
        psw = 0.5 * vin * iout * TEDGE * FSW
        pl = (iout ** 2 + dil ** 2 / 12) * dcr + 0.05
        pic = pc + psw + QSW
        eff = vo * iout / (vo * iout + pic + pl)
        print(f"  Vin={vin:5.1f}: D={D:.3f} ton={D/FSW*1e9:4.0f}ns dIL={dil:.3f}A Ipk={ipk:.2f}A "
              f"Iout_max(guar.)={min(imax, imax_hs):.2f}A Pic={pic:.2f}W (cond {pc:.2f} sw {psw:.2f}) PL={pl:.2f}W eff={eff*100:.1f}% "
              f"Tj@Ta50 (29/43 C/W)={50+pic*29:.0f}/{50+pic*43:.0f}C")


print(f"RT(750k) Eq.2 = {rt_k(750):.1f} k -> 34.8k (Table 8-1)")
# Gate 3 rev (D-19): both rails Wurth WE-MAPI 4020 74438356056 (5.6uH, 81 mOhm max, Isat(10%) 2.65 A, 2.1 mm max)
rail("5V1", 5.1, 5.6e-6, 0.081, 1.8, [6.0, 7.4, 8.4, 12.6, 16.8, 25.2, 42.1])
rail("5V1 @2.0A", 5.1, 5.6e-6, 0.081, 2.0, [8.4, 16.8, 25.2])
rail("10V", 10.09, 5.6e-6, 0.081, 1.5, [11.1, 12.6, 16.8, 25.2, 42.1])
rail("10V @2.0A", 10.09, 5.6e-6, 0.081, 2.0, [12.6, 16.8, 25.2])

# Feedback dividers (Eq.1, VREF 1.0 V, +-1.5% FPWM over temp)
for vo_name, rt, rb in (("5V", 100e3, 24.3e3), ("10V", 100e3, 11.0e3)):
    v = 1.0 * (1 + rt / rb)
    lo = 0.985 * (1 + rt * 0.99 / (rb * 1.01)); hi = 1.015 * (1 + rt * 1.01 / (rb * 0.99))
    print(f"FB {vo_name}: {rt/1e3:.0f}k/{rb/1e3:.1f}k -> {v:.3f} V ({lo:.2f}..{hi:.2f})")

# EN UVLO divider (Eq.13/14): RENT 301k / RENB 100k ; VEN-H 1.1/1.25/1.4, VEN-L 0.95/1.10/1.22
rt, rb = 301e3, 100e3
for t, vh, vl in (("min", 1.1, 0.95), ("typ", 1.25, 1.10), ("max", 1.4, 1.22)):
    print(f"UVLO {t}: on {vh*(1+rt/rb):.2f} V off {vl*(1+rt/rb):.2f} V")
for vin in (25.2, 42.1):
    print(f"EN at VIN={vin}: {vin*rb/(rt+rb):.2f} V (abs max VIN+0.3)")
print(f"EN divider current at 25.2 V: {25.2/(rt+rb)*1e6:.0f} uA")
# VTX-off FET pulls EN low: NX7002AK Rds(on) <= 3.3 ohm-ish at VGS 3.3 V -> EN
print(f"EN with VTX-off FET on (R~5 ohm) at 42.1 V: {42.1/rt*5*1e3:.2f} mV (VEN-L min 0.95 V)")


def floors(name, vo, L, vins, iout):
    """Worst-case output-current floor (Gate 3 G3R-08): -20 % L, RT/oscillator -20 %, spread spectrum -8 % (lowest fsw = 0.736 x),
    valley limit ILS_MIN + dIL_min/2 and high-side peak limit IHS_MIN - dIL_max/2; the lower one governs."""
    print(f"\n== {name} worst-case current-limit floor (budget {iout} A)")
    for vin in vins:
        D = vo / vin
        dmax = (vin - vo) * D / (L * 0.8 * FSW * 0.8 * 0.92)
        dmin = (vin - vo) * D / (L * 1.2 * FSW * 1.2 * 1.08)
        fl = min(ILS_MIN + dmin / 2, IHS_MIN - dmax / 2)
        print(f"  Vin={vin:5.1f}: dIL max {dmax:.2f} A -> floor {fl:.2f} A ({'OK' if fl >= iout else 'BELOW BUDGET'})")


floors("5V1 rev C", 5.115, 5.6e-6, [8.4, 12.6, 16.8, 25.2], 1.71)
floors("10V rev C", 10.09, 5.6e-6, [16.8, 25.2], 1.3)
