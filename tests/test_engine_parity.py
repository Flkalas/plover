from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def _run(engine: str) -> list[int]:
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "macroasm.py"), "--build-fixtures"], check=True)
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_control_store.py"), "--build-fixtures"],
        check=True,
    )
    prog = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    m = PloverMachine(engine=engine)
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    if engine == "fast":
        m.fast.pc = 0
    else:
        m.macro.pc = 0
        m.macro._fetch_pending = True
    m.run(max_steps=500)
    if engine == "fast":
        return list(m.fast.regs)
    return list(m.micro.state.regs)


def test_micro_matches_fast():
    fast = _run("fast")
    micro = _run("micro")
    assert fast[0] == micro[0]
