from plover_ld.format import PlxObject, Reloc, Symbol
from plover_ld.linker import link_objects


def test_linker_rel8_patch():
    # text[0] will be rel8 displacement to label in same object
    obj = PlxObject(
        name="r",
        text=[0x00, 0x0A],  # rel8 placeholder, HALT
        symbols=[Symbol(name="L1", section="text", offset=1, binding="local", type="func")],
        relocs=[Reloc(section="text", offset=0, kind="rel8", symbol="L1")],
    )
    lr = link_objects([obj], text_base=0x2800)
    assert lr.text[0] == 0  # target (0x2801) - (patch+1=0x2801)

