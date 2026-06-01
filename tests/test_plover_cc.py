from pathlib import Path

from plover_asm.assemble import assemble
from plover_asm.emit import write_hex
from plover_cc.codegen import program_to_asm
from plover_cc.parse import parse
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_cc_smoke_compile_run_fast():
    src = (ROOT / "hw" / "fixtures" / "sw" / "cc_smoke.c").read_text(encoding="utf-8")
    prog = parse(src)
    asm = program_to_asm(prog)
    res = assemble(asm, origin=0)
    out = ROOT / "hw" / "fixtures" / "sram" / "cc_smoke.sram.hex"
    write_hex(res, out)

    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(out, 0)
    m.bus.map_mode = 1
    m.fast.pc = 0
    m.run(max_steps=100)
    assert m.fast.halted
    assert m.fast.regs[0] == 5


def test_cc_smoke_compile_run_micro():
    out = ROOT / "hw" / "fixtures" / "sram" / "cc_smoke.sram.hex"
    if not out.is_file():
        test_cc_smoke_compile_run_fast()
    m = PloverMachine(engine="micro")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(out, 0)
    m.bus.map_mode = 1
    m.macro.pc = 0
    m.macro._fetch_pending = True
    m.run(max_steps=200)
    assert m.macro.halted
    assert m.micro.state.regs[0] == 5

