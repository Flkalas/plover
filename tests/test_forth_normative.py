from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_forth_boot_scenario_passes():
    # Host-side Forth core gate (scenario harness)
    import subprocess
    import sys

    scen = ROOT / "hw" / "scenarios" / "vm" / "forth_boot.yaml"
    subprocess.run([sys.executable, "-m", "plover_vm", "scenario", str(scen)], check=True)


def test_micro_engine_still_passes_add_imm():
    # Normative `--engine micro` regression guard (macroasm fixture).
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "macroasm.py"), "--build-fixtures"],
        check=True,
    )
    prog = ROOT / "hw" / "fixtures" / "sram" / "add_imm.sram.hex"
    m = PloverMachine(engine="micro")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(prog, 0)
    m.bus.map_mode = 1
    m.micro.state.regs = [0x12, 0, 0, 0]
    m.macro.pc = 0
    m.macro._fetch_pending = True
    m.run(max_steps=500)
    assert m.macro.halted
    assert m.micro.state.regs == [0x12, 0x34, 0x46, 0]

