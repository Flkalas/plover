from pathlib import Path

from plover_asm.assemble import assemble
from plover_asm.emit import write_hex

ROOT = Path(__file__).resolve().parents[1]


def test_add_imm_byte_exact():
    src = (ROOT / "hw" / "fixtures" / "sw" / "add_imm.pls").read_text(encoding="utf-8")
    result = assemble(src, origin=0)
    assert result.bytes == [0x01, 0x05, 0x0C, 0x02, 0x01, 0x03, 0x0C, 0x02, 0x0A]


def test_labels_and_jmp():
    src = """
        .ORG $100
loop:   ADD 1
        CMP 5
        BEQ done
        JMP loop
done:   HALT
"""
    result = assemble(src, origin=0x100)
    assert result.symbols["LOOP"] == 0x100
    assert result.symbols["DONE"] == 0x10A


def test_build_fixture_matches_golden():
    src = (ROOT / "hw" / "fixtures" / "sw" / "add_imm.pls").read_text(encoding="utf-8")
    result = assemble(src, origin=0)
    out = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    write_hex(result, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert lines == ["01", "05", "0C", "02", "01", "03", "0C", "02", "0A"]
