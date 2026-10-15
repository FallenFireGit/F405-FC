#!/bin/bash
# Release outputs from the routed board (run on the host; KiCad runs in the chroot via kc):
#   fab/   Gerbers + Excellon drill (JLCPCB naming: KiCad Protel extensions), zipped; paste-only stencil set; CPL (JLC columns)
#   bom/   interactive HTML BOM (InteractiveHtmlBom 2.12.0 from PyPI, unpacked at /opt/ibom in the chroot)
#   docs/  schematic PDF, STEP model, 3D renders
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf fab && mkdir -p fab/gerbers fab/stencil docs/renders
kc 'set -e; cd /work/kicad
L="F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
kicad-cli pcb export gerbers --layers "$L" --subtract-soldermask --use-drill-file-origin -o /work/fab/gerbers/ F405FC.kicad_pcb >/dev/null
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    --drill-origin plot -o /work/fab/gerbers/ F405FC.kicad_pcb >/dev/null
kicad-cli pcb export gerbers --layers "F.Paste,B.Paste,Edge.Cuts" -o /work/fab/stencil/ F405FC.kicad_pcb >/dev/null
kicad-cli pcb export pos --format csv --units mm --side both --exclude-dnp --use-drill-file-origin -o /work/fab/F405FC_pos_kicad.csv F405FC.kicad_pcb >/dev/null
kicad-cli sch export pdf -o /work/docs/F405FC_schematic.pdf F405FC.kicad_sch >/dev/null
kicad-cli pcb export step --subst-models --force -o /work/docs/F405FC.step F405FC.kicad_pcb >/dev/null 2>&1 || echo "STEP export reported errors"
for s in top bottom; do kicad-cli pcb render --side $s --width 1600 --height 1600 --quality high -o /work/docs/renders/board_$s.png F405FC.kicad_pcb >/dev/null 2>&1; done
kicad-cli pcb render --rotate "-45,0,45" --width 1600 --height 1200 --quality high -o /work/docs/renders/board_iso.png F405FC.kicad_pcb >/dev/null 2>&1
cd /opt/ibom/interactivehtmlbom-2.12.0 && INTERACTIVE_HTML_BOM_NO_DISPLAY=1 python3 -m InteractiveHtmlBom.generate_interactive_bom --no-browser --dest-dir /work/bom \
    --name-format F405FC_ibom --group-fields "Value,Footprint,MPN" \
    --show-fields "Value,Footprint,MPN,Manufacturer,DigiKey" --blacklist "H*,P*,TP*,R32,R37" /work/kicad/F405FC.kicad_pcb >/dev/null 2>&1 || echo "iBOM failed"
'
python3 - <<'EOF'
import csv
rows = list(csv.DictReader(open("fab/F405FC_pos_kicad.csv")))
with open("fab/F405FC_cpl_jlc.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        w.writerow([r["Ref"], f'{float(r["PosX"]):.3f}mm', f'{float(r["PosY"]):.3f}mm',
                    "Top" if r["Side"] == "top" else "Bottom", f'{float(r["Rot"]):.1f}'])
print("CPL rows", len(rows))
EOF
(cd fab/gerbers && zip -q -r ../F405FC_JLC_gerbers.zip .)
(cd fab/stencil && zip -q -r ../F405FC_stencil.zip .)
ls -la fab bom docs | head -40
