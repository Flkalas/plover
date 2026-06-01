from plover_ld.format import PlxObject, Reloc, Symbol
from plover_ld.linker import link_objects


def test_linker_resolves_global_abs16():
    a = PlxObject(
        name="a",
        text=[0x05, 0x00, 0x00, 0x0A],  # JMP imm16 + HALT
        symbols=[Symbol(name="main", section="text", offset=0, binding="global", type="func")],
        relocs=[Reloc(section="text", offset=1, kind="abs16", symbol="target")],
        entry_symbol="main",
    )
    b = PlxObject(
        name="b",
        text=[0x01, 0x07, 0x0A],
        symbols=[Symbol(name="target", section="text", offset=0, binding="global", type="func")],
    )
    lr = link_objects([a, b], text_base=0x2800)
    target_addr = lr.symbols["target"]
    assert lr.text[1] == (target_addr & 0xFF)
    assert lr.text[2] == ((target_addr >> 8) & 0xFF)

