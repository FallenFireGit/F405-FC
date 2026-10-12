"""Print DRC violations with positions (board mm) from /tmp/drc.json (run gen/drc_summary.py first). Optional type filter args."""
import json
import sys
d = json.load(open("/opt/kroot/tmp/drc.json" if len(sys.argv) > 1 and sys.argv[1] == "--host" else "/tmp/drc.json"))
skip = {"silk_overlap", "silk_over_copper", "unconnected_items"}
want = [a for a in sys.argv[1:] if not a.startswith("--")]
for v in d["violations"]:
    if v["type"] in skip or (want and v["type"] not in want):
        continue
    items = "; ".join(f'{i["description"][:60]} @({i["pos"]["x"]-100:.2f},{i["pos"]["y"]-100:.2f})' for i in v["items"])
    print(v["type"], "|", items)
