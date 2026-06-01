"""PLX linker MVP -> PLR."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kern.plr import PlrImage, pack_plr
from plover_ld.format import PlxObject, Symbol, read_plx


@dataclass
class LinkResult:
    text_base: int
    data_base: int
    text: bytearray
    data: bytearray
    symbols: dict[str, int] = field(default_factory=dict)
    reloc_applied: int = 0
    entry_symbol: str = "main"

    def final_code(self) -> bytes:
        return bytes(self.text + self.data)


def _symbol_abs(sym: Symbol, text_base: int, data_base: int, obj_text_base: int, obj_data_base: int) -> int:
    if sym.section == "text":
        return obj_text_base + sym.offset
    if sym.section == "data":
        return obj_data_base + sym.offset
    if sym.section == "abs":
        return sym.offset
    raise KeyError(f"undefined symbol: {sym.name}")


def link_objects(objects: list[PlxObject], *, text_base: int = 0x2800, data_base: int | None = None) -> LinkResult:
    text_total = sum(len(o.text) for o in objects)
    if data_base is None:
        data_base = text_base + text_total

    lr = LinkResult(text_base=text_base, data_base=data_base, text=bytearray(), data=bytearray())
    obj_text_bases: list[int] = []
    obj_data_bases: list[int] = []

    cur_t = text_base
    cur_d = data_base
    for o in objects:
        obj_text_bases.append(cur_t)
        obj_data_bases.append(cur_d)
        lr.text.extend(bytes(o.text))
        lr.data.extend(bytes(o.data))
        cur_t += len(o.text)
        cur_d += len(o.data)

    # Global symbol table
    for idx, o in enumerate(objects):
        for s in o.symbols:
            if s.section == "undef":
                continue
            if s.binding != "global":
                continue
            if s.name in lr.symbols:
                raise ValueError(f"duplicate global symbol: {s.name}")
            lr.symbols[s.name] = _symbol_abs(s, text_base, data_base, obj_text_bases[idx], obj_data_bases[idx])

    # choose entry symbol
    for o in objects:
        if o.entry_symbol:
            lr.entry_symbol = o.entry_symbol
            break

    # Relocation
    text_cursor = 0
    data_cursor = 0
    for idx, o in enumerate(objects):
        local_syms: dict[str, int] = {}
        for s in o.symbols:
            if s.section == "undef":
                continue
            local_syms[s.name] = _symbol_abs(s, text_base, data_base, obj_text_bases[idx], obj_data_bases[idx])

        for r in o.relocs:
            target = local_syms.get(r.symbol, lr.symbols.get(r.symbol))
            if target is None:
                raise ValueError(f"undefined symbol: {r.symbol}")
            if r.section == "text":
                buf = lr.text
                base = obj_text_bases[idx]
                patch = text_cursor + r.offset
            elif r.section == "data":
                buf = lr.data
                base = obj_data_bases[idx]
                patch = data_cursor + r.offset
            else:
                raise ValueError(f"bad section in reloc: {r.section}")

            if r.kind == "abs16":
                buf[patch] = target & 0xFF
                buf[patch + 1] = (target >> 8) & 0xFF
            elif r.kind == "rel8":
                disp = target - ((base + r.offset) + 1)
                if disp < -128 or disp > 127:
                    raise ValueError("rel8 overflow")
                buf[patch] = disp & 0xFF
            else:
                raise ValueError(f"unknown relocation kind: {r.kind}")
            lr.reloc_applied += 1

        text_cursor += len(o.text)
        data_cursor += len(o.data)

    return lr


def link_paths_to_plr(
    paths: list[Path],
    out_plr: Path,
    *,
    text_base: int = 0x2800,
    entry_symbol: str | None = None,
    map_path: Path | None = None,
) -> LinkResult:
    objs = [read_plx(p) for p in paths]
    lr = link_objects(objs, text_base=text_base)
    if entry_symbol:
        lr.entry_symbol = entry_symbol
    entry_addr = lr.symbols.get(lr.entry_symbol, text_base)
    img = PlrImage(load_addr=text_base, entry_off=(entry_addr - text_base) & 0xFFFF, code=lr.final_code())
    out_plr.parent.mkdir(parents=True, exist_ok=True)
    out_plr.write_bytes(pack_plr(img))
    if map_path is not None:
        lines = [f"{k} = ${v:04X}" for k, v in sorted(lr.symbols.items())]
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lr

