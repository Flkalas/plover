from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def _ensure_fixtures():
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "macroasm.py"), "--build-fixtures"], check=True)
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_control_store.py"), "--build-fixtures"],
        check=True,
    )


def test_add_imm_fast():
    _ensure_fixtures()
    prog = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    m.fast.pc = 0
    m.run(max_steps=100)
    assert m.fast.halted
    assert m.fast.regs[0] == 8


def test_add_imm_micro():
    _ensure_fixtures()
    prog = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    m = PloverMachine(engine="micro")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    m.macro.pc = 0
    m.macro._fetch_pending = True
    m.run(max_steps=500)
    assert m.macro.halted
    assert m.micro.state.regs[0] == 8
