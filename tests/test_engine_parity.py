from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]
NORMATIVE_REGS = [0x12, 0x34, 0x46, 0]


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
        m.fast.regs = [0x12, 0, 0, 0]
        m.fast.pc = 0
    else:
        m.macro.pc = 0
        m.macro._fetch_pending = True
        m.micro.state.regs = [0x12, 0, 0, 0]
    m.run(max_steps=500)
    if engine == "fast":
        return list(m.fast.regs)
    return list(m.micro.state.regs)


def test_micro_matches_fast():
    fast = _run("fast")
    micro = _run("micro")
    assert fast == micro == NORMATIVE_REGS


def _run_program(engine: str, prog_bytes: list[int], init_regs: list[int] | None = None) -> list[int]:
    m = PloverMachine(engine=engine)
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.ram.load(bytes(prog_bytes), 0)
    m.bus.map_mode = 1
    if engine == "fast":
        if init_regs:
            m.fast.regs = list(init_regs)
        m.fast.pc = 0
    else:
        m.macro.pc = 0
        m.macro._fetch_pending = True
        if init_regs:
            m.micro.state.regs = list(init_regs)
    m.run(max_steps=500)
    if engine == "fast":
        return list(m.fast.regs)
    return list(m.micro.state.regs)


def test_mov_parity():
    # MOV 0x20: R2 <- R0
    prog = [0x0C, 0x20, 0x0A]
    init = [0x55, 0, 0, 0]
    assert _run_program("fast", prog, init) == _run_program("micro", prog, init) == [0x55, 0, 0x55, 0]


def test_ldio_stio_parity():
    # LDIO $00 (STATUS); STIO $04 (CMD) with R0=0xAB
    prog = [0x08, 0x00, 0x09, 0x04, 0x0A]
    init = [0xAB, 0, 0, 0]
    fast = _run_program("fast", prog, init)
    micro = _run_program("micro", prog, init)
    assert fast == micro == [0, 0, 0, 0]


def test_sta16_parity():
    # STA16 $0800 with R0=0x42
    prog = [0x0F, 0x00, 0x08, 0x0A]
    init = [0x42, 0, 0, 0]
    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.ram.load(bytes(prog), 0)
    m.bus.map_mode = 1
    m.fast.regs = list(init)
    m.fast.pc = 0
    m.run(max_steps=50)
    assert m.bus.ram.read(0x0800) == 0x42
    fast = _run_program("fast", prog, init)
    micro = _run_program("micro", prog, init)
    assert fast == micro == [0x42, 0, 0, 0]
