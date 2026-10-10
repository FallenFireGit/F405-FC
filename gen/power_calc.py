import math
pi = math.pi

def E96_near(x):
    e96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
    d = 10**math.floor(math.log10(x))
    m = x/d
    best = min(e96, key=lambda v: abs(v-m))
    return best*d

fsw = 800e3
print("RT eq7 (kOhm) =", 101756/(fsw/1e3)**1.008)
for rt in (124e3, 127e3, 130e3):
    print(" RT", rt, "-> fsw eq8 kHz", 92417/((rt/1e3)**0.991))
print("tSS eq6 ms =", 1024/(fsw/1e3))

ton = 135e-9
gmps = 12.0; gmea = 350e-6; vref = 0.8
VFd = 0.45   # PMEG6030EP @2-3A (typ 0.43-0.46 V at 25C)
RDS_hot = 0.15  # TPS54360B Fig 1 ~0.15 ohm at Tj~125C (typ 92 mOhm @25C, max 190 mOhm)
Cj = 120e-12 # PMEG6030EP Cd @10V
ICLmax = 6.8

def rail(name, Vo, Io, L, Rdc, Vin_max, Vin_list, Cout_eff, ESR, dI_step, dV_pct, Ioh, Iol, Vrip):
    print("\n=====", name)
    for Vin in Vin_list:
        D = Vo/Vin
        dIL = Vo*(Vin-Vo)/(Vin*L*fsw)
        print(f" Vin={Vin:5.1f} D={D:.3f} ton={D/fsw*1e9:.0f}ns ripple(eq29)={dIL:.3f}A K={dIL/Io:.2f} Ipk={Io+dIL/2:.2f}A Irms(eq30)={math.sqrt(Io**2+dIL**2/12):.3f}A")
    # max fsw
    for Vin in (25.2, 35.0, 42.1):
        fskip = (Io*Rdc+Vo+VFd)/(ton*(Vin-Io*RDS_hot+VFd))
        fshift = 8*(ICLmax*Rdc+0.1+VFd)/(ton*(Vin-ICLmax*RDS_hot+VFd))
        print(f"  Vin={Vin}: fsw(max skip) eq9={fskip/1e3:.0f}kHz  fsw(shift) eq10={fshift/1e3:.0f}kHz")
    # L min eq28
    for K in (0.3, 0.4, 0.5):
        print(f"  Lmin(K={K}) eq28 = {(Vin_max-Vo)/(Io*K)*Vo/(Vin_max*fsw)*1e6:.2f} uH")
    # Cout
    c32 = 2*dI_step/(fsw*dV_pct*Vo)
    c33 = L*(Ioh**2-Iol**2)/(((1+dV_pct)*Vo)**2-Vo**2)
    dILmax = Vo*(Vin_max-Vo)/(Vin_max*L*fsw)
    c34 = 1/(8*fsw)*1/(Vrip/dILmax)
    resr = Vrip/dILmax
    icrms = Vo*(Vin_max-Vo)/(math.sqrt(12)*Vin_max*L*fsw)
    print(f"  Cout eq32={c32*1e6:.2f}uF eq33={c33*1e6:.2f}uF eq34={c34*1e6:.2f}uF  ESRmax eq35={resr*1e3:.1f}mOhm  Icout_rms eq36={icrms*1e3:.0f}mA")
    # compensation
    fp = Io/(2*pi*Vo*Cout_eff)
    fz = 1/(2*pi*ESR*Cout_eff)
    fco1 = math.sqrt(fp*fz); fco2 = math.sqrt(fp*fsw/2)
    fco = min(fco1, fco2)
    R4 = (2*pi*fco*Cout_eff/gmps)*(Vo/(vref*gmea))
    R4s = E96_near(R4)
    C5 = 1/(2*pi*R4s*fp)
    C8a = Cout_eff*ESR/R4s; C8b = 1/(R4s*fsw*pi)
    print(f"  fp(mod) eq44={fp:.0f}Hz fz(mod) eq45={fz/1e3:.0f}kHz fco eq46={fco1/1e3:.1f}k eq47={fco2/1e3:.1f}k -> fco={fco/1e3:.1f}kHz")
    print(f"  R4 eq48={R4:.0f} -> {R4s:.0f}  C5 eq49={C5*1e9:.2f}nF  C8 eq50={C8a*1e12:.1f}pF eq51={C8b*1e12:.1f}pF")
    return

# 5 V rail: XGL5030-472MEC, DCR max 24.5 mOhm. Cout 2x22uF 25V X5R 1206 est ~14uF each at 5.1V -> 28uF eff; ESR ~2.5mOhm parallel
rail("5V1", 5.1, 2.5, 4.7e-6, 0.0245, 25.2, [6.0, 8.4, 12.6, 16.8, 25.2], 28e-6, 0.0025, 1.0, 0.04, 2.0, 0.5, 0.0255)
# 10 V rail: XGL5030-682MEC, DCR max 32.1 mOhm; Cout 3x22uF 25V X5R est ~9uF each at 10V -> 27uF
rail("10V", 10.0, 2.0, 8.2e-6, 0.041, 25.2, [11.0, 12.6, 16.8, 20.0, 25.2], 27e-6, 0.0025, 1.0, 0.04, 2.0, 0.5, 0.05)

# FB dividers eq3
for Vo, RLS in ((5.1, 10.2e3), (10.0, 10.0e3)):
    RHS = RLS*(Vo-0.8)/0.8
    RHSs = E96_near(RHS)
    print(f"\nFB Vo={Vo}: RHS eq3={RHS:.0f} -> {RHSs:.0f}, Vout actual = {0.8*(1+RHSs/RLS):.4f}  range(0.792..0.808 & 1% R) {0.792*(1+RHSs*0.99/(RLS*1.01)):.3f}..{0.808*(1+RHSs*1.01/(RLS*0.99)):.3f}")

# UVLO eq4/5
I1 = 1.2e-6; Ihys = 3.4e-6; Ven = 1.2
for name, Vstart, Vstop in (("5V", 6.0, 5.2), ("10V", 6.0, 5.2)):
    R1 = (Vstart-Vstop)/Ihys
    R1s = E96_near(R1)
    R2 = Ven/((Vstart-Ven)/R1s + I1)
    R2s = E96_near(R2)
    # actual thresholds
    # rising: EN reaches 1.2 with only I1: Vstart = Ven + R1*(Ven/R2 - I1)
    vst = Ven + R1s*(Ven/R2s - I1)
    vsp = Ven + R1s*(Ven/R2s - I1 - Ihys)
    print(f"\nUVLO {name}: R1 eq4={R1:.0f} -> {R1s:.0f}; R2 eq5={R2:.0f} -> {R2s:.0f}; Vstart={vst:.2f} Vstop={vsp:.2f}")
    for Vin in (25.2, 35.0, 42.1):
        # EN node: (Vin - Ven)/R1 + (I1+Ihys) = Ven/R2  -> Ven = (Vin/R1 + I1+Ihys)/(1/R1+1/R2)
        ven = (Vin/R1s + I1 + Ihys)/(1/R1s + 1/R2s)
        print(f"   EN at Vin={Vin}: {ven:.2f} V (abs max 8.4 V)")

# Vin min eq1
def vinmin(Vo, Io, Rdc, Rds=0.15, Vf=0.45):
    return (Vo + Vf + Rdc*Io)/0.99 + Rds*Io - Vf
print("\nVinmin eq1: 5V1@2.5A", vinmin(5.1, 2.5, 0.0245), " 5V1@1.2A", vinmin(5.1,1.2,0.0245))
print("Vinmin eq1: 10V@2A", vinmin(10,2,0.041), " 10V@1A", vinmin(10,1,0.041))
# dropout output: invert eq1 for Vout
def vout_drop(Vin, Io, Rdc, Rds=0.15, Vf=0.45):
    return 0.99*(Vin - Rds*Io + Vf) - Vf - Rdc*Io
for Vin in (6.0, 7.4, 8.4):
    print(f" 10V rail in dropout Vin={Vin}: Vout@2A={vout_drop(Vin,2,0.041):.2f}  @1A={vout_drop(Vin,1,0.041):.2f}")
for Vin in (5.0, 5.5):
    print(f" 5V rail in dropout Vin={Vin}: Vout@2.5A={vout_drop(Vin,2.5,0.0245):.2f} @1A={vout_drop(Vin,1.0,0.0245):.2f}")

# losses
def losses(Vin, Vo, Io, L, Rdc, Rds=RDS_hot, Vf=VFd, core=0.05):
    D = Vo/Vin
    pcond = Io**2*Rds*D                      # eq52
    trise = Vin*0.16e-9 + 3e-9
    psw = Vin*fsw*Io*trise                   # eq53
    pgd = Vin*3e-9*fsw                       # eq54
    pq = Vin*146e-6                          # eq55
    pic = pcond+psw+pgd+pq
    pdi = (Vin-Vo)*Io*Vf/Vin + Cj*fsw*(Vin+Vf)**2/2   # eq37
    dIL = Vo*(Vin-Vo)/(Vin*L*fsw)
    pl = (Io**2 + dIL**2/12)*Rdc + core
    pout = Vo*Io
    tot = pic+pdi+pl
    return dict(pcond=pcond,psw=psw,pgd=pgd,pq=pq,pic=pic,pdi=pdi,pl=pl,tot=tot,eff=pout/(pout+tot),pin=pout+tot,iin=(pout+tot)/Vin)

print()
for case, Io5, Io10 in (("WORST", 2.5, 2.0), ("TYPICAL", 1.2, 1.0)):
    for Vin in (6.0, 8.4, 12.6, 16.8, 25.2):
        r5 = losses(Vin, 5.1, Io5, 4.7e-6, 0.0245)
        if Vin > 10.6:
            r10 = losses(Vin, 10.0, Io10, 8.2e-6, 0.041)
        else:
            r10 = None
        s = f"{case} Vin={Vin:5.1f} | 5V: IC={r5['pic']:.3f} (cond {r5['pcond']:.3f} sw {r5['psw']:.3f} gd {r5['pgd']:.3f}) D={r5['pdi']:.3f} L={r5['pl']:.3f} tot={r5['tot']:.3f} eff={r5['eff']*100:.1f}% Iin={r5['iin']:.3f}"
        if r10:
            s += f" | 10V: IC={r10['pic']:.3f} D={r10['pdi']:.3f} L={r10['pl']:.3f} tot={r10['tot']:.3f} eff={r10['eff']*100:.1f}% Iin={r10['iin']:.3f}"
        print(s)

# Input caps eq38/39
for name, Vo, Io in (("5V1", 5.1, 2.5), ("10V", 10.0, 2.0)):
    # worst rms at D=0.5 -> Vin = 2Vo when in range
    for Vin in (6.0, 10.2, 12.6, 20.0, 25.2):
        if Vin <= Vo*1.05: continue
        irms = Io*math.sqrt(Vo/Vin*(Vin-Vo)/Vin)
        print(f" Cin rms {name} Vin={Vin}: {irms:.2f} A")
    for Ceff in (4.5e-6, 9e-6):
        print(f"  dVin eq39 Ceff={Ceff*1e6}uF: {Io*0.25/(Ceff*fsw)*1e3:.0f} mV")

# TVS
Vbrmax = 31.9; Vc = 42.1; Ipp = 14.3
Rd = (Vc-Vbrmax)/Ipp
print(f"\nTVS SMBJ26A dynamic R ~ {Rd:.3f} ohm; Vclamp@5A~{Vbrmax+5*Rd:.1f}V @1A~{Vbrmax+Rd:.1f}")
# ADC
print("VBAT divider: ratio", (10+1)/1, " Vmax ADC full scale 3.3V ->", 3.3*11)
Rth = 10e3*1e3/(11e3); print(" filter fc", 1/(2*pi*Rth*100e-9))
print(" ADC pin at 42.1V clamp:", 42.1/11, " injection if pin clamps at 3.6V:", (42.1-3.6)/10e3 - 3.6/1e3)
print(" Divider current at 25.2V", 25.2/11e3*1e3, "mA, power", 25.2**2/11e3*1e3, "mW; 10k dissipation", (25.2*10/11)**2/10e3*1e3, "mW")
print(" CURR RC 10k/10nF fc", 1/(2*pi*10e3*10e-9), " inj at 25.2V miswire", (25.2-3.6)/10e3*1e3, "mA")
# LDO
for I in (0.15, 0.21, 0.25):
    for vin in (5.1, 4.65):
        print(f" LP38692 I={I} Vin={vin}: P={(vin-3.3)*I:.3f} W dT(68.5C/W)={(vin-3.3)*I*68.5:.1f}")
print(" LP5907 P", (5.1-3.3)*0.010)
# USB diode
print(" USB diode PMEG4030ER P at 0.5A Vf~0.34:", 0.5*0.34, " at 1A Vf 0.38-0.44:", 1*0.44)
# load switch
for I in (1.0, 2.0):
    print(f" TPS22810 I={I}: P typ {I*I*0.079:.3f} max(105C) {I*I*0.115:.3f}  dT@182C/W {I*I*0.115*182:.0f}")
# inrush
CT = 10e-9
SR = 46.62/(CT*1e12)  # V/us
print(f" TPS22810 CT=10nF SR={SR*1e3:.2f} V/ms, 10-90% of 10V = {8/SR/1e3:.2f} ms; inrush into 100uF = {100e-6*SR*1e6:.3f} A, 470uF={470e-6*SR*1e6:.2f}A")
# buzzer
print(" Buzzer FET PMV40UN2 at 100mA: P", 0.1**2*0.053)
print("RT 121k -> fsw", 92417/(121**0.991), "kHz; tss", 1024/(92417/(121**0.991)))
print("5V FB 54.9k/10.2k:", 0.8*(1+54.9/10.2))
for Vin in (11.0,):
    print("10V ripple at 11V with 8.2uH", 10*(Vin-10)/(Vin*8.2e-6*800e3))
# Cout eq32 for 5V with 1 A step at 4%

# ---- part 2: UVLO tolerance, thermal, budgets ----
I1=1.2e-6; Ih=3.4e-6; Ven=1.2
Vstart, Vstop = 6.0, 4.8
R1=(Vstart-Vstop)/Ih; R2=Ven/((Vstart-Ven)/357e3+I1)
print("R1 eq4", R1, "R2 eq5 (with R1=357k)", R2)
R1s, R2s = 357e3, 88.7e3
vst = Ven + R1s*(Ven/R2s - I1); vsp = Ven + R1s*(Ven/R2s - I1 - Ih)
print("Vstart", vst, "Vstop", vsp)
# tolerance: Ven 1.1..1.3, I1 0.58..1.8u, Ih 2.2..4.5u (datasheet min/max)
import itertools
sts=[];sps=[]
for v,i1,ih in itertools.product((1.1,1.3),(0.58e-6,1.8e-6),(2.2e-6,4.5e-6)):
    sts.append(v + R1s*(v/R2s - i1)); sps.append(v + R1s*(v/R2s - i1 - ih))
print("Vstart range", min(sts), max(sts), "Vstop range", min(sps), max(sps))
for Vin in (25.2, 35, 42.1):
    ven=(Vin/R1s + I1 + Ih)/(1/R1s+1/R2s)
    print("EN unclamped at", Vin, ven, " Thevenin R", 1/(1/R1s+1/R2s), " zener I if 6.2V:", max(0,(ven-6.2)/(1/(1/R1s+1/R2s))))
# dual-diode 5V_SYS
for i in (0.35, 0.51):
    print("D_OR2 at", i, "A: Vf~0.35 -> 5V_SYS =", 5.106-0.35, " P=", i*0.35)
print("LP38692 from 4.75V @0.25A", (4.756-3.3)*0.25, "W  dT", (4.756-3.3)*0.25*68.5)
print("LP38692 from 4.75V @0.175A", (4.756-3.3)*0.175, "W")
# Junction temps worst 25.2V, Ta=50C
Ta=50
for name,P,th in (("U5V TPS54360B",0.608,42),("U5V TPS54360B small board",0.608,55),("U10V",0.586,42),("U10V small",0.586,55),
                   ("D 5V PMEG6030EP 4L est",0.929,70),("D 5V PMEG6030EP 1cm2 1-sided",0.929,120),
                   ("D 10V 4L",0.574,70),("D 10V 1cm2",0.574,120),("LDO",0.364,68.5),("TPS22810 2A",0.46,182),("TPS22810 2A est 4L",0.46,110),("TPS22810 1A",0.115,182)):
    print(f"{name}: P={P} th={th} Tj={Ta+P*th:.0f}")
# typical at 16.8V
for name,P,th in (("U5V",0.200,55),("D5V",0.390,70),("U10V",0.209,55),("D10V",0.196,70),("LDO 175mA",0.255,68.5),("SW 1A",0.115,182)):
    print(f"TYP {name}: Tj={Ta+P*th:.0f}")
# board totals
worst = 1.743+1.377+0.364+0.46+0.018+0.058+0.18
typ = 0.678+0.497+0.255+0.08+0.018+0.025+0.12
print("board worst", worst, "typ", typ)
# input currents
print("6S worst Iin total", (12.766+1.743 + 20+1.377 + 0.06)/25.2)
print("4S typ Iin", (5.106*1.2+0.678 + 10*1+0.497)/16.8)
print("2S 6.0V: 5V rail Iin 2.33A worst + VTX at ~5.6V; VTX constant-power 9W ->", 9/5.56, "A")
