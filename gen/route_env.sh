# Router environment used for the released rev D routes (source before gen/pathfinder.py, gen/pflocal.py or gen/tidy.py).
# AVOID keeps foreign nets off B.Cu inside the U1/U2 buck courtyards (Gate 4 G4D-02; router-only, there is no DRC rule for it,
# so any re-route must use these values or G4D-02 can silently come back - Gate 4 re-review G4D2-03).
export ESCAPE_LANES=0 ROUTE_RES=0.025 PWR_OUTER_EXEMPT=5V NET_LCOST="BEEPER:F=4,5V:In2=4,5V:In3=4" GND_NEED=kicad/gnd_need.json
export AVOID="B:6.42,22.86,13.97,28.34:BST_5V|EN_5V|FB_5V|RT_5V|SW_5V|VBAT;B:22.83,21.86,30.38,27.34:BST_10V|EN_10V|FB_10V|RT_10V|SW_10V|VBAT"
