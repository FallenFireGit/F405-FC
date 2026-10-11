"""Circuit model -> hierarchical KiCad 10 schematic (labels on every pin)."""
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
    page_sizes = [("A4", 297, 210), ("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594)]

    for si, (sname, fname) in enumerate(c.sheets):
        sheet_uuid = uid(c.name, "sheet", sname)
        parts = [p for p in c.parts if p.sheet == sname]
        lib_syms, items = {}, []
        # layout: shelf packing
        boxes = []
        for p in parts:
            tree = c.symbol_tree(p.lib_id)
            lib_syms[p.lib_id] = tree
            pl = symlib.pins(tree, p.unit)
            x0, y0, x1, y1 = _bbox(pl)
            lw = max([_label_len(str(res[p.ref].get(q["number"]) or "")) for q in pl] + [4])
            boxes.append((p, pl, x0 - lw, y0 - 6, x1 + lw, y1 + 6))
        for (pname, W, H) in page_sizes:
            margin, x, y, rowh, placed, ok = 15.24, 15.24, 25.4, 0, [], True
            for p, pl, bx0, by0, bx1, by1 in boxes:
                w, h = bx1 - bx0, by1 - by0
                if x + w > W - margin:
                    x, y, rowh = margin, y + rowh + 5.08, 0
                if y + h > H - 20:
                    ok = False
                    break
                ox = round((x - bx0) / 2.54) * 2.54
                oy = round((y - by0) / 2.54) * 2.54
                placed.append((p, pl, ox, oy))
                x += w + 5.08
                rowh = max(rowh, h)
            if ok:
                break
        else:
            raise SystemExit(f"sheet {sname} too big")
        for p, pl, ox, oy in placed:
            items.append(_symbol_instance(c, p, pl, ox, oy, root_uuid, sheet_uuid))
            seen = set()
            for q in pl:
                px, py = round(ox + q["x"], 2), round(oy - q["y"], 2)
                if (px, py) in seen:
                    continue
                seen.add((px, py))
                net = res[p.ref].get(q["number"])
                if net is None:
                    items.append([S("no_connect"), [S("at"), px, py], [S("uuid"), uid(c.name, p.ref, q["number"], "nc")]])
                else:
                    a = LABEL_ANGLE[q["angle"] % 360]
                    items.append([S("global_label"), net, [S("shape"), S("passive")], [S("at"), px, py, a],
                                  [S("effects"), font(1.0), [S("justify"), S("right" if a == 180 else "left") if a in (0, 180) else S("left")]],
                                  [S("uuid"), uid(c.name, p.ref, q["number"], "lbl")],
                                  prop("Intersheetrefs", "${INTERSHEET_REFS}", px, py, 0, hide=True)])
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


def _symbol_instance(c, p, pl, ox, oy, root_uuid, sheet_uuid):
    tree = c.symbol_tree(p.lib_id)
    sym_uuid = uid(c.name, "sym", p.ref)
    x0, y0, x1, y1 = _bbox(pl)
    props = [prop("Reference", p.ref, ox, oy + y0 - 2.54, 0),
             prop("Value", p.value, ox, oy + y1 + 2.54, 0),
             prop("Footprint", p.footprint, ox, oy, 0, hide=True),
             prop("Datasheet", p.fields.get("Datasheet", ""), ox, oy, 0, hide=True),
             prop("Description", p.fields.get("Description", ""), ox, oy, 0, hide=True)]
    for k, v in p.fields.items():
        if k not in ("Datasheet", "Description"):
            props.append(prop(k, v, ox, oy, 0, hide=True))
    pins = [[S("pin"), q["number"], [S("uuid"), uid(c.name, p.ref, "pin", q["number"])]] for q in pl]
    return ([S("symbol"), [S("lib_id"), p.lib_id], [S("at"), ox, oy, 0], [S("unit"), p.unit],
             [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no") if p.fields.get("InBOM") == "no" else S("yes")],
             [S("on_board"), S("yes")],
             [S("dnp"), S("yes") if p.dnp else S("no")], [S("uuid"), sym_uuid]] + props + pins +
            [[S("instances"), [S("project"), c.name,
                               [S("path"), f"/{root_uuid}/{sheet_uuid}", [S("reference"), p.ref], [S("unit"), p.unit]]]]])


def write_project(c, outdir, netclasses=None):
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
    pro["sheets"] = [[uid(c.name, "root"), "Root"]] + [[uid(c.name, "sheet", s), s] for s, _ in c.sheets]
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
