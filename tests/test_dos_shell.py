from pathlib import Path


def test_dos_boot_scenario():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    scen = root / "hw" / "scenarios" / "vm" / "dos_boot.yaml"
    subprocess.run([sys.executable, "-m", "plover_vm", "scenario", str(scen)], check=True)


def test_interactive_dos_shell_smoke():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input="dir\nrun HELLO.PLR\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "A>" in out
    assert "HELLO" in out
    assert "R0_7" in out
    # no stale replay lines after exit
    assert "BYE" in out


def test_shell_monitor_and_compile_commands():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input="mon\nplsrun hw/fixtures/sw/add_imm.pls\nccrun hw/fixtures/sw/cc_smoke.c\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "PC_" in out and "R0_" in out
    # add_imm.pls => R0 should end at 8
    assert "R0_8" in out
    # cc_smoke.c => return add(2,3) = 5
    assert "R0_5" in out


def test_run_hello_after_asm_cc_is_stable():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input="plsrun hw/fixtures/sw/add_imm.pls\nccrun hw/fixtures/sw/cc_smoke.c\nrun HELLO.PLR\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "R0_8" in out
    assert "R0_5" in out
    assert "R0_7" in out


def test_monitor_ram_and_vfdd():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input="mon ram\nmon vfdd\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "RAM_USED_" in out and "RAM_FREE_" in out
    assert "DRV_A" in out and "USED_SECT_" in out


def test_monitor_gpio_dev_serial():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input="mon dev\nmon gpio\nmon serial\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "DEV_SLOT_" in out
    assert "GPIO_PORTA_" in out
    assert "SERIAL_SIG_D4" in out


def test_ldrun_and_link_monitors():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    obj = root / "hw" / "fixtures" / "sw" / "add_imm.pls"
    build_dir = root / "build" / "tmp_obj"
    build_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "plover_asm", "obj", str(obj), "-o", str(build_dir)],
        cwd=root,
        check=True,
    )
    plx_rel = "build/tmp_obj/add_imm.plx"
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input=f"ldrun {plx_rel}\nmon map\nmon sym\nmon rel\nexit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "R0_8" in out
    assert "MAP" in out or "_$" in out
    assert "SYM" in out
    assert "RELOC_APPLIED_" in out

