from pathlib import Path

from plover_asm.assemble import assemble
from plover_asm.emit import write_hex
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def _ensure_cw():
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_control_store.py"), "--build-fixtures"],
        check=True,
    )


def test_call_ret_fast():
    src = (ROOT / "hw" / "fixtures" / "sw" / "call_ret.asm").read_text(encoding="utf-8")
    result = assemble(src, origin=0)
    prog = ROOT / "hw" / "fixtures" / "sram" / "call_ret.sram.hex"
    write_hex(result, prog)
    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    m.fast.pc = 0
    m.run(max_steps=200)
    assert m.fast.halted
    assert m.fast.regs[0] == 11


def test_call_ret_micro():
    _ensure_cw()
    prog = ROOT / "hw" / "fixtures" / "sram" / "call_ret.sram.hex"
    if not prog.is_file():
        test_call_ret_fast()
    m = PloverMachine(engine="micro")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    m.macro.pc = 0
    m.macro._fetch_pending = True
    m.run(max_steps=500)
    assert m.macro.halted
    assert m.micro.state.regs[0] == 11


def test_nested_call_fast():
    src = """
        .ORG 0
        CALL a
        HALT
a:      ADD 1
        MOV 2
        CALL b
        RET
b:      ADD 2
        MOV 2
        RET
"""
    result = assemble(src, origin=0)
    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.ram.load(bytes(result.bytes), 0)
    m.bus.map_mode = 1
    m.fast.pc = 0
    m.run(max_steps=300)
    assert m.fast.halted
    assert m.fast.regs[0] == 3
