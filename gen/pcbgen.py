"""Build/refresh a .kicad_pcb from the circuit model using pcbnew (run with KiCad's python)."""
import os

import pcbnew

import schgen
import symlib

FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"


def mm(v):
    return pcbnew.FromMM(v)


def load_fp(fpid, local_libs):
    lib, name = fpid.split(":", 1)
    path = local_libs.get(lib) or os.path.join(FP_DIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"footprint not found: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def build(c, board_path, local_libs=None, existing=None):
    """Create footprints for every non-virtual part and assign pad nets.

    If `existing` board given, keep positions of footprints already present.
    """
    local_libs = local_libs or {}
    res, _ = c.resolve()
    board = existing or pcbnew.BOARD()
    old = {fp.GetReference(): fp for fp in board.GetFootprints()}
    netinfo = {}

    def net(name):
        if name not in netinfo:
            ni = board.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, name)
                board.Add(ni)
            netinfo[name] = ni
        return netinfo[name]

    root = schgen.uid(c.name, "root")
    wanted = set()
    for p in c.parts:
        if p.ref.startswith("#") or not p.footprint:
            continue
        wanted.add(p.ref)
        fp = old.get(p.ref)
        if fp is None or fp.GetFPID().GetUniStringLibItemName() != p.footprint.split(":", 1)[1]:
            pos, rot, layer = None, None, None
            if fp is not None:
                pos, rot, layer = fp.GetPosition(), fp.GetOrientationDegrees(), fp.GetLayer()
                board.Remove(fp)
            fp = load_fp(p.footprint, local_libs)
            board.Add(fp)
            if pos is not None:
                fp.SetPosition(pos)
                if layer == pcbnew.B_Cu:
                    fp.Flip(pos, pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
                fp.SetOrientationDegrees(rot)
        fp.SetReference(p.ref)
        fp.SetValue(p.value)
        sheet_uuid = schgen.uid(c.name, "sheet", p.sheet)
        fp.SetPath(pcbnew.KIID_PATH(f"/{sheet_uuid}/{schgen.uid(c.name, 'sym', p.ref)}"))
        fp.SetSheetname(p.sheet)
        fp.SetSheetfile([f for s, f in c.sheets if s == p.sheet][0])
        fp.SetDNP(bool(p.dnp))
        for k, v in p.fields.items():
            if k in ("MPN", "Manufacturer", "DigiKey"):
                fp.SetField(k, v)
        pinmap = res[p.ref]
        pnames = {q["number"]: q["name"] for q in symlib.pins(c.symbol_tree(p.lib_id), p.unit)}
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num == "" or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            n = pinmap.get(num)
            if n is None:
                if num not in pinmap:
                    print(f"WARN {p.ref} pad {num} has no symbol pin")
                    pad.SetNetCode(0)
                else:
                    # match the name eeschema gives a no-connect pin so parity stays clean
                    pad.SetNet(net(f"unconnected-({p.ref}-{pnames[num]}-Pad{num})"))
            else:
                pad.SetNet(net(n))
    for ref, fp in old.items():
        if ref not in wanted:
            board.Remove(fp)
    board.Save(board_path)
    return board
