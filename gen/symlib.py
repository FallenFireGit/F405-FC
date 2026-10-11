"""Load KiCad symbols (stock or generated) and expose pin geometry."""
import copy
import os
import re

from sexpr import Sym, find, findall, parse

KICAD_SYM_DIR = os.environ.get("KICAD_SYMBOL_DIR", r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
_cache = {}


def _load_lib(path):
    if path not in _cache:
        with open(path, encoding="utf8") as f:
            tree = parse(f.read())
        _cache[path] = {x[1]: x for x in findall(tree, "symbol")}
    return _cache[path]


def _rename_units(sym, old, new):
    for sub in findall(sym, "symbol"):
        if sub[1].startswith(old + "_"):
            sub[1] = new + sub[1][len(old):]


def load_symbol(lib_id, extra_libs=None):
    """Return a deep-copied symbol tree named 'lib:name' with extends resolved."""
    lib, name = lib_id.split(":", 1)
    path = (extra_libs or {}).get(lib) or os.path.join(KICAD_SYM_DIR, lib + ".kicad_sym")
    syms = _load_lib(path)
    sym = copy.deepcopy(syms[name])
    ext = find(sym, "extends")
    if ext:
        base = copy.deepcopy(syms[ext[1]])
        _rename_units(base, ext[1], name)
        # child properties override base properties
        props = {p[1]: p for p in findall(sym, "property")}
        out = [Sym("symbol"), name]
        for item in base[2:]:
            if isinstance(item, list) and item[0] == "property" and item[1] in props:
                out.append(props.pop(item[1]))
            else:
                out.append(item)
        out.extend(props.values())
        sym = out
    sym[1] = lib_id
    return sym


def pins(sym, unit=1):
    """List of dicts: number, name, type, x, y, angle, hidden (lib coords, y up)."""
    res = []
    base = sym[1].split(":", 1)[-1]
    for sub in findall(sym, "symbol"):
        m = re.match(re.escape(base) + r"_(\d+)_(\d+)$", sub[1])
        if not m:
            continue
        u, style = int(m.group(1)), int(m.group(2))
        if u not in (0, unit) or style not in (0, 1):
            continue
        for p in findall(sub, "pin"):
            at = find(p, "at")
            hidden = any(x == "hide" for x in p) or (find(p, "hide") is not None and find(p, "hide")[1:] in ([], [Sym("yes")]))
            res.append(dict(
                number=str(find(p, "number")[1]), name=str(find(p, "name")[1]),
                type=str(p[1]), x=float(at[1]), y=float(at[2]), angle=int(float(at[3])),
                length=float(find(p, "length")[1]), hidden=hidden))
    return res


def _pin_tree(num, name, ptype, x, y, angle, length=2.54):
    eff = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    return [Sym("pin"), Sym(ptype), Sym("line"), [Sym("at"), x, y, angle],
            [Sym("length"), length], [Sym("name"), name, eff], [Sym("number"), num, eff]]


def make_box_symbol(lib_id, ref_prefix, left, right, top=(), bottom=(), description=""):
    """Generate a rectangle symbol. Each pin spec: (number, name, type)."""
    name = lib_id.split(":", 1)[1]
    pitch = 2.54
    nside = max(len(left), len(right), 1)
    longest = max([len(p[1]) for p in list(left) + list(right)] + [4])
    w = max(10.16, round((longest * 1.27 * 2 + 5.08) / 2.54) * 2.54)
    w = max(w, (max(len(top), len(bottom)) + 1) * pitch)
    h = (nside + 1) * pitch
    x0, x1 = -w / 2, w / 2
    y0 = h / 2
    y0 = round(y0 / 1.27) * 1.27
    pinlist = []
    for i, (n, nm, t) in enumerate(left):
        pinlist.append(_pin_tree(n, nm, t, x0 - 2.54, y0 - pitch * (i + 1), 0))
    for i, (n, nm, t) in enumerate(right):
        pinlist.append(_pin_tree(n, nm, t, x1 + 2.54, y0 - pitch * (i + 1), 180))
    for i, (n, nm, t) in enumerate(top):
        pinlist.append(_pin_tree(n, nm, t, x0 + pitch * (i + 1), y0 + 2.54, 270))
    yb = y0 - pitch * (nside + 1)
    for i, (n, nm, t) in enumerate(bottom):
        pinlist.append(_pin_tree(n, nm, t, x0 + pitch * (i + 1), yb - 2.54, 90))
    hidef = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("hide"), Sym("yes")]]
    vis = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    rect = [Sym("rectangle"), [Sym("start"), x0, y0], [Sym("end"), x1, yb],
            [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
            [Sym("fill"), [Sym("type"), Sym("background")]]]
    return [Sym("symbol"), lib_id,
            [Sym("pin_names"), [Sym("offset"), 1.016]],
            [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
            [Sym("property"), "Reference", ref_prefix, [Sym("at"), x0, y0 + 1.27, 0], vis],
            [Sym("property"), "Value", name, [Sym("at"), x0, yb - 1.27, 0], vis],
            [Sym("property"), "Footprint", "", [Sym("at"), 0, 0, 0], hidef],
            [Sym("property"), "Datasheet", "", [Sym("at"), 0, 0, 0], hidef],
            [Sym("property"), "Description", description, [Sym("at"), 0, 0, 0], hidef],
            [Sym("symbol"), name + "_0_1", rect],
            [Sym("symbol"), name + "_1_1"] + pinlist,
            [Sym("embedded_fonts"), Sym("no")]]
