"""Circuit model -> hierarchical KiCad 10 schematic.

Layout (readable for review): every IC / connector is the anchor of a block. Two-pin parts that share a local net with an
anchor pin (decoupling caps, pull-ups, dividers, filters) are drawn next to that pin and joined to it by a wire; their far
end gets a GND power symbol or a net label. Nets between blocks use global labels. Each block has a title. Connectivity is
identical to the circuit model (checked by gen/netcheck.py)."""
import json
import os
import uuid

import symlib
from sexpr import Sym, dump

NS = uuid.UUID("6f1f1b6e-2d0c-4b1e-9a52-f405fc000000")


def uid(*parts):
    """Deterministic UUIDs so regenerated files diff cleanly and PCB links stay stable."""
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def S(x):
    return Sym(x)


def font(size=1.27):
    return [S("font"), [S("size"), size, size]]


def prop(name, value, x, y, angle=0, hide=False, justify=None):
    eff = [S("effects"), font()]
    if justify:
        eff.append([S("justify"), S(justify)])
    if hide:
        eff.append([S("hide"), S("yes")])
    return [S("property"), name, value, [S("at"), x, y, angle], eff]


class Part:
    def __init__(self, sheet, ref, lib_id, value, footprint, conn, fields=None, dnp=False, symbol=None, unit=1):
        self.sheet, self.ref, self.lib_id, self.value = sheet, ref, lib_id, value
        self.footprint, self.conn, self.fields = footprint, dict(conn), dict(fields or {})
        self.dnp, self.symbol, self.unit = dnp, symbol, unit


class Circuit:
    def __init__(self, name, title, rev="A"):
        self.name, self.title, self.rev = name, title, rev
        self.sheets = []  # (name, filename)
        self.parts = []
        self.custom_symbols = {}  # lib_id -> tree
        self.power_nets = set()
        self.notes = {}  # sheet -> [text]

    def sheet(self, name):
        if name not in [s for s, _ in self.sheets]:
            self.sheets.append((name, name.lower().replace(" ", "_").replace("/", "_") + ".kicad_sch"))
        return name

    def add(self, sheet, ref, lib_id, value, footprint, conn, **kw):
        if any(p.ref == ref for p in self.parts):
            raise ValueError("duplicate ref " + ref)
        p = Part(sheet, ref, lib_id, value, footprint, conn, **kw)
        self.parts.append(p)
        return p

    def note(self, sheet, text):
        self.notes.setdefault(sheet, []).append(text)

    # ---- resolution -------------------------------------------------------
    def symbol_tree(self, lib_id):
        if lib_id in self.custom_symbols:
            return self.custom_symbols[lib_id]
        return symlib.load_symbol(lib_id)

    def resolve(self):
        """Return {ref: {pin_number: net}} and a list of problems."""
        out, problems = {}, []
        for p in self.parts:
            pl = symlib.pins(self.symbol_tree(p.lib_id), p.unit)
            by_num = {x["number"]: x for x in pl}
            by_name = {}
            for x in pl:
                by_name.setdefault(x["name"], []).append(x["number"])
            m = {}
            for key, net in p.conn.items():
                key = str(key)
                if key in by_num:
                    nums = [key]
                elif key in by_name:
                    nums = by_name[key]
                else:
                    problems.append(f"{p.ref}: no pin '{key}'")
                    continue
                for n in nums:
                    if n in m and m[n] != net:
                        problems.append(f"{p.ref} pin {n}: {m[n]} vs {net}")
                    m[n] = net
            for n in by_num:
                if n not in m:
                    problems.append(f"{p.ref} pin {n} ({by_num[n]['name']}) unassigned")
            out[p.ref] = m
        return out, problems

    def nets(self):
        res, _ = self.resolve()
        nets = {}
        for ref, m in res.items():
            for n, net in m.items():
                if net is None:
                    continue
                nets.setdefault(net, []).append((ref, n))
        return nets


# ---- writer ---------------------------------------------------------------
LABEL_ANGLE = {0: 180, 180: 0, 90: 270, 270: 90}  # pin angle (lib) -> label angle (sch)


def _bbox(pl):
    xs = [p["x"] for p in pl] or [0]
    ys = [-p["y"] for p in pl] or [0]
    return min(xs), min(ys), max(xs), max(ys)


def _label_len(name):
    return len(name) * 1.0 + 4


def write(c, outdir):
    res, problems = c.resolve()
    hard = [p for p in problems if "unassigned" not in p]
    if hard:
        raise SystemExit("circuit errors:\n  " + "\n  ".join(hard))
    root_uuid = uid(c.name, "root")
    os.makedirs(outdir, exist_ok=True)
    page_sizes = [("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594)]

    for si, (sname, fname) in enumerate(c.sheets):
        sheet_uuid = uid(c.name, "sheet", sname)
        parts = [p for p in c.parts if p.sheet == sname]
        lib_syms, items = {}, []
        lib_syms = {}
        for p in parts:
            lib_syms[p.lib_id] = c.symbol_tree(p.lib_id)
        placed_items, pname, W, H = _layout(c, res, parts, page_sizes, root_uuid, sheet_uuid, lib_syms)
        items.extend(placed_items)
        for i, t in enumerate(c.notes.get(sname, [])):
            items.append([S("text"), t, [S("exclude_from_sim"), S("no")], [S("at"), 15.24, H - 12 - 4 * (len(c.notes[sname]) - 1 - i), 0],
                          [S("effects"), font(1.5), [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid(c.name, sname, "note", i)]])
        tree = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "f405fc_gen"], [S("generator_version"), "10.0"],
                [S("uuid"), sheet_uuid], [S("paper"), pname],
                [S("title_block"), [S("title"), f"{c.title} - {sname}"], [S("rev"), c.rev], [S("company"), "F405-FC"]],
                [S("lib_symbols")] + list(lib_syms.values())] + items + [[S("embedded_fonts"), S("no")]]
        with open(os.path.join(outdir, fname), "w", encoding="utf8", newline="\n") as f:
            f.write(dump(tree) + "\n")

    # root
    sheets = []
    for i, (sname, fname) in enumerate(c.sheets):
        x, y = 25.4 + (i % 4) * 63.5, 38.1 + (i // 4) * 45.72
        sheets.append([S("sheet"), [S("at"), x, y], [S("size"), 50.8, 30.48],
                       [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")], [S("dnp"), S("no")],
                       [S("stroke"), [S("width"), 0.1524], [S("type"), S("solid")]], [S("fill"), [S("color"), 0, 0, 0, 0.0]],
                       [S("uuid"), uid(c.name, "sheet", sname)],
                       prop("Sheetname", sname, x, y - 0.8, 0, justify="left"),
                       prop("Sheetfile", fname, x, y + 31.2, 0, justify="left"),
                       [S("instances"), [S("project"), c.name, [S("path"), "/" + root_uuid, [S("page"), str(i + 2)]]]]])
    root = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "f405fc_gen"], [S("generator_version"), "10.0"],
            [S("uuid"), root_uuid], [S("paper"), "A4"],
            [S("title_block"), [S("title"), c.title], [S("rev"), c.rev], [S("company"), "F405-FC"]],
            [S("lib_symbols")]] + sheets + [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]], [S("embedded_fonts"), S("no")]]
    with open(os.path.join(outdir, c.name + ".kicad_sch"), "w", encoding="utf8", newline="\n") as f:
        f.write(dump(root) + "\n")
    return problems


GRID = 2.54


def _g(v):
    return round(v / GRID) * GRID


def _wire(c, key, a, b):
    return [S("wire"), [S("pts"), [S("xy"), round(a[0], 2), round(a[1], 2)], [S("xy"), round(b[0], 2), round(b[1], 2)]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid(c.name, "wire", *key)]]


def _glabel(c, key, net, x, y, a):
    just = S("right" if a in (180, 270) else "left")      # KiCad: 180/270 labels are right-justified
    return [S("global_label"), net, [S("shape"), S("passive")], [S("at"), round(x, 2), round(y, 2), a],
            [S("effects"), font(1.0), [S("justify"), just]], [S("uuid"), uid(c.name, "lbl", *key)],
            prop("Intersheetrefs", "${INTERSHEET_REFS}", x, y, 0, hide=True)]


_PWR_N = [0]


def _gnd(c, key, x, y, rot, root_uuid, sheet_uuid):
    _PWR_N[0] += 1
    ref = f"#PWR{_PWR_N[0]:03d}"
    return [S("symbol"), [S("lib_id"), "power:GND"], [S("at"), round(x, 2), round(y, 2), rot], [S("unit"), 1],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")], [S("dnp"), S("no")],
            [S("uuid"), uid(c.name, "gnd", *key)],
            prop("Reference", ref, x, y + (6.35 if rot == 0 else -6.35), 0, hide=True),
            prop("Value", "GND", x, y + (3.81 if rot == 0 else -3.81), 0),
            prop("Footprint", "", x, y, 0, hide=True), prop("Datasheet", "", x, y, 0, hide=True),
            [S("pin"), "1", [S("uuid"), uid(c.name, "gndpin", *key)]],
            [S("instances"), [S("project"), c.name, [S("path"), f"/{root_uuid}/{sheet_uuid}", [S("reference"), ref], [S("unit"), 1]]]]]


def _pinpos(q, rot):
    """Pin connection point relative to the symbol origin, schematic coordinates (y down), for rotation 0 or 180."""
    x, y = q["x"], -q["y"]
    return (-x, -y) if rot == 180 else (x, y)


def _side(q):
    """Which side of the body a pin leaves from: L, R, T, B (lib pin angle: 0 -> left side, 180 -> right side,
    90 -> bottom, 270 -> top)."""
    return {0: "L", 180: "R", 90: "B", 270: "T"}[q["angle"] % 360]


def _layout(c, res, parts, page_sizes, root_uuid, sheet_uuid, lib_syms):
    pins = {p.ref: symlib.pins(c.symbol_tree(p.lib_id), p.unit) for p in parts}
    netsize = {}
    for p in parts:
        for n in res[p.ref].values():
            if n:
                netsize[n] = netsize.get(n, 0) + 1
    anchors = [p for p in parts if len(pins[p.ref]) > 3]
    order = {p.ref: i for i, p in enumerate(parts)}
    sats = {a.ref: [] for a in anchors}
    loose = [p for p in parts if p not in anchors]
    for p in list(loose):
        pl = pins[p.ref]
        if len(pl) != 2 or p.lib_id.startswith("power:"):
            continue
        nets = [res[p.ref].get(q["number"]) for q in pl]
        if None in nets:
            continue
        horiz = any(_side(q) in ("L", "R") for q in pl)
        if horiz:
            continue
        best = None
        for a in anchors:
            for q in pins[a.ref]:
                n = res[a.ref].get(q["number"])
                if _side(q) not in ("L", "R"):
                    continue      # top/bottom pins are power pins: their caps go to the rail's decoupling bank
                if n and n != "GND" and n in nets:
                    score = (netsize.get(n, 99), abs(order[a.ref] - order[p.ref]))
                    if best is None or score < best[0]:
                        best = (score, a, n)
        if best:
            sats[best[1].ref].append((p, best[2]))
            loose.remove(p)
    # capacitor banks: loose two-pin vertical parts between a rail and GND, grouped per rail
    banks = {}
    for p in list(loose):
        pl = pins[p.ref]
        if len(pl) != 2 or any(_side(q) in ("L", "R") for q in pl) or p.lib_id.startswith("power:"):
            continue
        nets = [res[p.ref].get(q["number"]) for q in pl]
        if "GND" in nets and None not in nets and nets[0] != nets[1]:
            rail = nets[0] if nets[1] == "GND" else nets[1]
            banks.setdefault(rail, []).append(p)
            loose.remove(p)
    blocks = []
    for a in anchors:
        blocks.append(_block(c, res, a, pins, sats[a.ref], root_uuid, sheet_uuid))
    for rail, ps in banks.items():
        blocks.append(_bank(c, res, rail, ps, pins, root_uuid, sheet_uuid))
    for p in loose:
        blocks.append(_block(c, res, p, pins, [], root_uuid, sheet_uuid))
    for (pname, W, H) in page_sizes:
        margin, x, y, rowh, placed, ok = 12.7, 12.7, 20.32, 0, [], True
        for bl in blocks:
            w, h = bl["x1"] - bl["x0"], bl["y1"] - bl["y0"]
            if x + w > W - margin:
                x, y, rowh = margin, y + rowh + 7.62, 0
            if y + h > H - 25:
                ok = False
                break
            placed.append((bl, _g(x - bl["x0"]), _g(y - bl["y0"])))
            x += w + 7.62
            rowh = max(rowh, h)
        if ok:
            break
    else:
        raise SystemExit("sheet too big")
    items = []
    for bl, dx, dy in placed:
        for it in bl["make"](dx, dy):
            items.append(it)
    if any(it[0] == "symbol" and it[1][1] == "power:GND" for it in items):
        lib_syms["power:GND"] = symlib.load_symbol("power:GND")
    return items, pname, W, H


def _bank(c, res, rail, ps, pins, root_uuid, sheet_uuid):
    """Row of parts between one rail and GND: rail wire on top with one net label, GND symbols below."""
    geo, x = [], 0.0
    for p in ps:
        spl = pins[p.ref]
        r_pin = next(q for q in spl if res[p.ref][q["number"]] == rail)
        g_pin = next(q for q in spl if q is not r_pin)
        rot = 0 if _pinpos(r_pin, 0)[1] < _pinpos(g_pin, 0)[1] else 180
        rx, ry = _pinpos(r_pin, rot)
        gx, gy = _pinpos(g_pin, rot)
        ox, oy = x - rx, 0 - ry
        geo.append((p, spl, rot, ox, oy, (ox + gx, oy + gy)))
        x = _g(x + _txtw(p) + 2.54)
    lab = _label_len(rail)
    caps = all(p.lib_id.startswith("Device:C") for p in ps)
    title = f"{rail} decoupling / bulk" if caps else f"{rail} to GND"

    def make(dx, dy):
        out = [[S("text"), title, [S("exclude_from_sim"), S("no")], [S("at"), round(dx - 7.62, 2), round(dy - 5.08, 2), 0],
                [S("effects"), font(1.6), [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid(c.name, "banktitle", rail)]]]
        # one segment per part: KiCad joins a pin to a wire only at the wire's end points
        xs = [-5.08] + [ox for p, spl, rot, ox, oy, g in geo]
        for i in range(len(xs) - 1):
            out.append(_wire(c, ("bank", rail, i), (dx + xs[i], dy), (dx + xs[i + 1], dy)))
        out.append(_glabel(c, ("bank", rail), rail, dx - 5.08, dy, 180))
        for p, spl, rot, ox, oy, g in geo:
            out.append(_symbol_instance(c, p, spl, dx + ox, dy + oy, root_uuid, sheet_uuid, rot))
            out.append(_gnd(c, (p.ref, "bank"), dx + g[0], dy + g[1], 0, root_uuid, sheet_uuid))
        return out
    return {"x0": -7.62 - lab, "y0": -7.62, "x1": max(x + 2.54, -7.62 + 1.4 * len(title)), "y1": 16.0, "make": make}


def _txtw(p):
    """Width of the ref / value text printed to the right of a small part."""
    return 3.81 + 1.05 * max(len(p.ref), len(str(p.value)))


def _lane(lanes, lo, hi, wire_at, gap, net):
    """First lane where the satellite interval [lo, hi] is free (plus gap) and the wire that runs out to it does not pass
    over a pin or body of another net in the nearer lanes (a wire over a pin end would connect it). Records both.
    Satellites are placed farthest-from-the-wire-origin first (see _block), so a free lane always exists."""
    for k in range(64):
        while len(lanes) <= k:
            lanes.append([])
        own = all(hi + gap <= l0 or lo - gap >= l1 for l0, l1, nn in lanes[k])
        path = all(all(nn == net or wire_at + 0.6 <= l0 or wire_at - 0.6 >= l1 for l0, l1, nn in lanes[j])
                   for j in range(k))
        if own and path:
            lanes[k].append((lo, hi, net))
            for j in range(k):
                lanes[j].append((wire_at - 0.01, wire_at + 0.01, net))
            return k
    raise SystemExit(f"schematic layout: no free lane for net {net} at {wire_at}: {lanes}")


def _block(c, res, a, pins, sats, root_uuid, sheet_uuid):
    """Anchor symbol at (0, 0) with its satellites. Returns bbox and a factory that emits items at an offset."""
    pl = pins[a.ref]
    x0, y0, x1, y1 = _bbox(pl)
    lw = {"L": 4.0, "R": 4.0, "T": 4.0, "B": 4.0}
    for q in pl:
        n = res[a.ref].get(q["number"])
        if n:
            lw[_side(q)] = max(lw[_side(q)], _label_len(str(n)))
    # satellites: pick an anchor pin carrying the shared net (spread over pins of the same net)
    use = {}
    plan = []          # (sat part, anchor pin, side)
    for p, n in sats:
        cand = [q for q in pl if res[a.ref].get(q["number"]) == n]
        q = cand[use.get(n, 0) % len(cand)]
        use[n] = use.get(n, 0) + 1
        plan.append((p, q, _side(q)))
    lanes = {"L": [], "R": [], "T": [], "B": []}     # per side: list of occupied intervals per lane
    pitch = {sd: max([12.7] + [_g(_txtw(p) + 3.81) for p, q, side in plan if side == sd]) for sd in lanes}
    geo = []
    # placement order that keeps every wire clear of the parts already placed in nearer lanes: L/R lowest pin first
    # (parts hang down), T/B rightmost pin first (ref/value text sits to the right of each part)
    plan.sort(key=lambda t: t[1]["y"] if t[2] in ("L", "R") else -t[1]["x"])
    for p, q, side in plan:
        spl = pins[p.ref]
        net = res[a.ref][q["number"]]
        s_pin = next(x for x in spl if res[p.ref][x["number"]] == net)
        o_pin = next(x for x in spl if x is not s_pin)
        px, py = q["x"], -q["y"]
        # satellite hangs away from the body: down for L/R/B sides, up for T
        want_s_upper = side in ("L", "R", "B")
        rot = 0
        sy0 = _pinpos(s_pin, 0)[1]
        oy0 = _pinpos(o_pin, 0)[1]
        if (sy0 < oy0) != want_s_upper:
            rot = 180
        spx, spy = _pinpos(s_pin, rot)
        opx, opy = _pinpos(o_pin, rot)
        span = abs(opy - spy)
        k = 0
        if side in ("L", "R"):
            onet0 = res[p.ref][o_pin["number"]]
            tail = 0 if onet0 in (None, "GND") else _label_len(str(onet0))   # far-end label hangs below the part
            lo, hi = py, py + span + (5.08 if onet0 == "GND" else tail)
            k = _lane(lanes[side], lo, hi, py, 2.54, net)
            dist = lw[side] + 5.08 + pitch[side] * (k + (1 if side == "L" else 0))   # text sits right of each part
            tx = _g(px - dist) if side == "L" else _g(px + dist)
            ty = py
            wires = [((px, py), (tx, ty))]
        else:
            lo, hi = px - 1.27, px + 1.27 + _txtw(p)
            k = _lane(lanes[side], lo, hi, px, 0.0, net)
            dist = lw[side] + 2.54 + (span + 7.62) * k
            tx = px
            ty = _g(py - dist) if side == "T" else _g(py + dist)
            wires = [((px, py), (tx, ty))]
        ox, oy = tx - spx, ty - spy
        far = (ox + opx, oy + opy)
        geo.append((p, rot, ox, oy, far, res[p.ref][o_pin["number"]], wires, spl, side, net))
    # nets that live entirely inside this block's wiring need no label
    members = {}
    for ref, m in res.items():
        for num, n in m.items():
            if n:
                members.setdefault(n, set()).add((ref, num))
    inside = {}
    for p, q, side in plan:
        n = res[a.ref][q["number"]]
        inside.setdefault(n, set()).add((a.ref, q["number"]))
        inside[n] |= {(p.ref, x["number"]) for x in pins[p.ref] if res[p.ref][x["number"]] == n}
    local = {n: members[n] <= v for n, v in inside.items()}
    # bbox
    xs = [x0 - lw["L"], x1 + lw["R"]]
    ys = [y0 - lw["T"] - 5.08, y1 + lw["B"]]
    for p, rot, ox, oy, far, onet, wires, spl, side, _n in geo:
        xs += [ox - 3, ox + 3 + _txtw(p), far[0] - _label_len(onet or ""), far[0] + _label_len(onet or "")]
        ys += [oy - 6, oy + 6, far[1] - 7, far[1] + 7]
    title = a.ref + "  " + str(a.value) + (("  -  " + a.fields["Description"]) if a.fields.get("Description") and len(pl) > 3 else "")

    bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    if len(pl) > 3:
        bx1 = max(bx1, bx0 + 1.4 * len(title))

    def make(dx, dy):
        out = [_symbol_instance(c, a, pl, dx, dy, root_uuid, sheet_uuid)]
        if len(pl) > 3:
            out.append([S("text"), title, [S("exclude_from_sim"), S("no")], [S("at"), round(dx + bx0, 2), round(dy + by0 + 2.0, 2), 0],
                        [S("effects"), font(1.6), [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid(c.name, "title", a.ref)]])
        wired = {(a.ref, q["number"]) for p, q, side in plan}
        seen = set()
        gnd_bottom = []
        for q in pl:
            pxy = (round(dx + q["x"], 2), round(dy - q["y"], 2))
            if pxy in seen:
                continue
            seen.add(pxy)
            n = res[a.ref].get(q["number"])
            if n is None:
                out.append([S("no_connect"), [S("at"), *pxy], [S("uuid"), uid(c.name, a.ref, q["number"], "nc")]])
            elif n == "GND" and _side(q) == "B":
                gnd_bottom.append(pxy)
            elif (a.ref, q["number"]) in wired and n != "GND" and local.get(n):
                # net lives only on this wire: name it at both ends (KiCad needs two labels to keep the model net name)
                out.append(_glabel(c, (a.ref, q["number"]), n, pxy[0], pxy[1], LABEL_ANGLE[q["angle"] % 360]))
                tw = next((g for g in geo if g[9] == n), None)
                if tw is not None:
                    end = tw[6][-1][1]
                    out.append(_glabel(c, (a.ref, q["number"], "far"), n, dx + end[0], dy + end[1], 90 if tw[8] != "T" else 270))
            else:
                out.append(_glabel(c, (a.ref, q["number"]), n, pxy[0], pxy[1], LABEL_ANGLE[q["angle"] % 360]))
        # bottom GND pins: one ground symbol, the other pins joined to it by short wires
        if gnd_bottom:
            gnd_bottom.sort()
            for i in range(len(gnd_bottom) - 1):
                u, v = gnd_bottom[i], gnd_bottom[i + 1]
                if u[1] == v[1]:
                    out.append(_wire(c, (a.ref, "gndbus", i), u, v))
                else:
                    out.append(_gnd(c, (a.ref, "gndb", i), v[0], v[1], 0, root_uuid, sheet_uuid))
            out.append(_gnd(c, (a.ref, "gndb"), gnd_bottom[0][0], gnd_bottom[0][1], 0, root_uuid, sheet_uuid))
        for p, rot, ox, oy, far, onet, wires, spl, side, _n in geo:
            out.append(_symbol_instance(c, p, spl, dx + ox, dy + oy, root_uuid, sheet_uuid, rot))
            for i, (u, v) in enumerate(wires):
                out.append(_wire(c, (p.ref, i), (dx + u[0], dy + u[1]), (dx + v[0], dy + v[1])))
            fx, fy = dx + far[0], dy + far[1]
            upper = far[1] < oy
            if onet is None:
                out.append([S("no_connect"), [S("at"), fx, fy], [S("uuid"), uid(c.name, p.ref, "far", "nc")]])
            elif onet == "GND":
                out.append(_gnd(c, (p.ref, "far"), fx, fy, 180 if upper else 0, root_uuid, sheet_uuid))
            else:
                out.append(_glabel(c, (p.ref, "far"), onet, fx, fy, 90 if upper else 270))
        return out
    return {"x0": bx0, "y0": by0, "x1": bx1, "y1": by1, "make": make}


def _symbol_instance(c, p, pl, ox, oy, root_uuid, sheet_uuid, rot=0):
    tree = c.symbol_tree(p.lib_id)
    sym_uuid = uid(c.name, "sym", p.ref)
    x0, y0, x1, y1 = _bbox(pl)
    if len(pl) <= 3:      # small parts: ref and value beside the body
        props = [prop("Reference", p.ref, ox + 2.54, oy - 1.27, 0, justify="left"),
                 prop("Value", p.value, ox + 2.54, oy + 1.27, 0, justify="left")]
    else:
        props = [prop("Reference", p.ref, ox, oy + y0 - 2.54, 0),
                 prop("Value", p.value, ox, oy + y1 + 2.54, 0)]
    props += [prop("Footprint", p.footprint, ox, oy, 0, hide=True),
             prop("Datasheet", p.fields.get("Datasheet", ""), ox, oy, 0, hide=True),
             prop("Description", p.fields.get("Description", ""), ox, oy, 0, hide=True)]
    for k, v in p.fields.items():
        if k not in ("Datasheet", "Description"):
            props.append(prop(k, v, ox, oy, 0, hide=True))
    pins = [[S("pin"), q["number"], [S("uuid"), uid(c.name, p.ref, "pin", q["number"])]] for q in pl]
    return ([S("symbol"), [S("lib_id"), p.lib_id], [S("at"), round(ox, 2), round(oy, 2), rot], [S("unit"), p.unit],
             [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no") if p.fields.get("InBOM") == "no" else S("yes")],
             [S("on_board"), S("yes")],
             [S("dnp"), S("yes") if p.dnp else S("no")], [S("uuid"), sym_uuid]] + props + pins +
            [[S("instances"), [S("project"), c.name,
                               [S("path"), f"/{root_uuid}/{sheet_uuid}", [S("reference"), p.ref], [S("unit"), p.unit]]]]])


def write_project(c, outdir, netclasses=None, patterns=None):
    """Create or update the .kicad_pro. Existing content (board design settings written by pcbnew, ERC settings)
    is merged, never discarded (Gate 1 G1N-01)."""
    path = os.path.join(outdir, c.name + ".kicad_pro")
    pro = {}
    if os.path.exists(path):
        with open(path) as f:
            pro = json.load(f)
    pro.setdefault("meta", {"filename": c.name + ".kicad_pro", "version": 3})
    pro.setdefault("board", {"design_settings": {}})
    pro.setdefault("schematic", {"meta": {"version": 1}})
    if netclasses is not None:
        ns = pro.setdefault("net_settings", {"meta": {"version": 4}})
        ns["classes"] = netclasses
    if patterns is not None:
        pro.setdefault("net_settings", {"meta": {"version": 4}})["netclass_patterns"] = [
            {"netclass": k, "pattern": v} for k, v in patterns]
    pro["sheets"] = [[uid(c.name, "root"), "Root"]] + [[uid(c.name, "sheet", s), s] for s, _ in c.sheets]
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
