"""Cross-check design/circuit.py against the netlist KiCad exports from the schematic.

Usage (inside the KiCad chroot):  kc 'python3 gen/netcheck.py'
Exports kicad/F405FC.net with kicad-cli, parses it, and compares every (ref, pin) -> net mapping and every
footprint with the circuit model. Exit code 1 on any mismatch.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gen"))
sys.path.insert(0, os.path.join(ROOT, "design"))

from sexpr import find, findall, parse  # noqa: E402
import circuit  # noqa: E402


def main():
    sch = os.path.join(ROOT, "kicad", "F405FC.kicad_sch")
    net = os.path.join(ROOT, "kicad", "F405FC.net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, sch], check=True,
                   stdout=subprocess.DEVNULL)
    tree = parse(open(net, encoding="utf8").read())
    comps = {}
    for comp in findall(find(tree, "components"), "comp"):
        ref = find(comp, "ref")[1]
        fp = find(comp, "footprint")
        comps[ref] = fp[1] if fp else ""
    exported = {}
    for n in findall(find(tree, "nets"), "net"):
        name = find(n, "name")[1].lstrip("/")
        for node in findall(n, "node"):
            ref, pin = find(node, "ref")[1], find(node, "pin")[1]
            exported[(ref, pin)] = name

    c = circuit.c
    res, _ = c.resolve()
    errors = []
    model = {}
    for p in c.parts:
        if p.ref.startswith("#"):
            continue
        if p.ref not in comps:
            errors.append(f"{p.ref}: missing from exported netlist")
            continue
        if comps[p.ref] != p.footprint:
            errors.append(f"{p.ref}: footprint {comps[p.ref]!r} != model {p.footprint!r}")
        for pin, nname in res[p.ref].items():
            model[(p.ref, pin)] = nname
    for key, nname in model.items():
        got = exported.get(key)
        if nname is None:
            if got is not None and not got.startswith("unconnected-"):
                errors.append(f"{key}: model NC but exported on net {got}")
            continue
        if got != nname:
            errors.append(f"{key}: model {nname} != exported {got}")
    extra = [k for k in exported if k not in model and not k[0].startswith("#")]
    for k in extra:
        errors.append(f"{k}: in exported netlist but not in model ({exported[k]})")
    # single-pin nets (would be dangling labels)
    count = {}
    for k, nname in exported.items():
        count.setdefault(nname, []).append(k)
    singles = [n for n, ks in count.items() if len(ks) == 1 and not n.startswith("unconnected-")]
    print(f"model pins={len(model)} exported pins={len(exported)} nets={len(count)} parts={len(comps)}")
    if singles:
        print("single-pin nets:", singles)
    if errors:
        print("MISMATCHES:\n  " + "\n  ".join(errors))
        raise SystemExit(1)
    print("netcheck: OK (model == exported netlist)")


if __name__ == "__main__":
    main()
