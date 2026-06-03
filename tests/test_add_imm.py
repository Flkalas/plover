from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]
NORMATIVE_REGS = [0x12, 0x34, 0x46, 0]


def _ensure_fixtures():
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "macroasm.py"), "--build-fixtures"], check=True)
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_control_store.py"), "--build-fixtures"],
        check=True,
    )


def _run(engine: str) -> list[int]:
    prog = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    m = PloverMachine(engine=engine)
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    if engine == "fast":
        m.fast.regs = [0x12, 0, 0, 0]
        m.fast.pc = 0
    else:
        m.macro.pc = 0
        m.macro._fetch_pending = True
        m.micro.state.regs = [0x12, 0, 0, 0]
    m.run(max_steps=100)
    if engine == "fast":
        return list(m.fast.regs)
    return list(m.micro.state.regs)


def test_add_imm_fast():
    _ensure_fixtures()
    assert _run("fast") == NORMATIVE_REGS


def test_add_imm_micro():
    _ensure_fixtures()
    assert _run("micro") == NORMATIVE_REGS
