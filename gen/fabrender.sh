#!/bin/bash
# Fab+courtyard PNGs (both as seen from the top) for placement iteration: docs/renders/p_fab_{top,bottom}.png
cd /home/user/F405-FC
kc 'cd kicad && kicad-cli pcb export pdf --layers "F.Fab,Edge.Cuts,F.CrtYd" --mode-single -o /work/docs/renders/fab_top.pdf F405FC.kicad_pcb >/dev/null 2>&1; kicad-cli pcb export pdf --layers "B.Fab,Edge.Cuts,B.CrtYd" --mode-single -o /work/docs/renders/fab_bottom.pdf F405FC.kicad_pcb >/dev/null 2>&1'
cd docs/renders && for f in fab_top fab_bottom; do pdftoppm -r 250 -png -singlefile $f.pdf p_$f && rm $f.pdf && convert p_$f.png -trim -resize 1300x1300 p_$f.png; done
