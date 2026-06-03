"""CLI for Plover logic VM."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from plover_vm.machine import PloverMachine


def _apply_init_regs(m: PloverMachine, regs: list[int]) -> None:
    r = [int(v) & 0xFF for v in regs[:4]]
    while len(r) < 4:
        r.append(0)
    m.micro.state.regs = list(r)
    m.fast.regs = list(r)


def _apply_init_pc(m: PloverMachine, pc: int) -> None:
    pc &= 0xFFFF
    m.macro.pc = pc
    m.macro._fetch_pending = True
    m.fast.pc = pc


def cmd_run(args: argparse.Namespace) -> int:
    m = PloverMachine(engine=args.engine)
    root = Path(__file__).resolve().parents[1]
    if args.nor:
        m.load_nor(args.nor)
    else:
        m.load_nor(root / "hw" / "fixtures" / "boot" / "boot_rom.hex", 0)
        vec = root / "hw" / "fixtures" / "boot" / "boot_vector.hex"
        if vec.is_file():
            m.load_nor(vec, 0xFFFC)
    if args.cw:
        m.load_cw(args.cw)
    else:
        m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
    if args.program:
        base = 0x0800 if args.map == "run" else 0
        m.load_ram_program(args.program, base)
    m.bus.map_mode = 0 if args.map == "boot" else 1
    if args.reset:
        m.reset(m.bus.map_mode)
    snap = m.run(max_steps=args.max_steps)
    out = {
        "pc": snap.pc,
        "regs": snap.regs,
        "halted": snap.halted,
        "map_mode": snap.map_mode,
    }
    if args.trace:
        m.tracer.write_jsonl(args.trace)
    print(json.dumps(out, indent=2))
    return 0 if snap.halted or args.allow_running else 0


def cmd_step(args: argparse.Namespace) -> int:
    m = PloverMachine(engine=args.engine)
    if args.state:
        state = json.loads(Path(args.state).read_text(encoding="utf-8"))
        m.bus.map_mode = state.get("map_mode", 0)
        m.macro.pc = state.get("pc", 0)
        m.micro.state.regs = state.get("regs", [0, 0, 0, 0])
    m.step_once()
    snap = m.snapshot()
    print(json.dumps({"pc": snap.pc, "regs": snap.regs, "halted": snap.halted}, indent=2))
    return 0


def cmd_scenario(args: argparse.Namespace) -> int:
    from hwsim import yaml_util

    doc = yaml_util.load_file(str(args.scenario))
    if doc.get("kind") == "forth":
        from plover_vm.forth_scenario import run_forth_scenario

        res = run_forth_scenario(doc)
        if res.ok:
            print("PASS")
            return 0
        print("FAIL")
        if res.error:
            print(f"ERROR: {res.error}")
        if "expect" in doc:
            print(f"expect: {doc.get('expect')}")
        print(f"stack: {res.stack}")
        print(f"output: {res.output}")
        return 1
    if doc.get("kind") == "kernel":
        from plover_vm.kernel_scenario import run_kernel_scenario

        res = run_kernel_scenario(doc)
        if res.ok:
            print("PASS")
            return 0
        print("FAIL")
        if res.error:
            print(f"ERROR: {res.error}")
        print(f"output: {res.output}")
        return 1
    if doc.get("kind") == "dos":
        from plover_vm.dos_scenario import run_dos_scenario

        root = Path(__file__).resolve().parents[1]
        res = run_dos_scenario(doc, root=root)
        if res.ok:
            print("PASS")
            return 0
        print("FAIL")
        if res.error:
            print(f"ERROR: {res.error}")
        print(f"output: {res.output}")
        return 1
    m = PloverMachine(engine=doc.get("engine", "fast"))
    root = Path(__file__).resolve().parents[1]
    for key, rel in doc.get("load", {}).items():
        p = root / rel
        if key == "nor":
            m.load_nor(p, 0)
            vec = root / "hw" / "fixtures" / "boot" / "boot_vector.hex"
            if vec.is_file():
                m.load_nor(vec, 0xFFFC)
        elif key == "cw":
            m.load_cw(p)
        elif key == "program":
            m.load_ram_program(p, doc.get("program_base", 0))
    for item in doc.get("ram_init", []):
        addr = int(item["addr"], 0) if isinstance(item["addr"], str) else item["addr"]
        for i, b in enumerate(item.get("bytes", [])):
            m.bus.ram.write(addr + i, b)
    m.bus.map_mode = doc.get("map_mode", 0)
    init = doc.get("init", {})
    init_regs = init.get("regs")
    init_pc = init.get("pc")
    for action in doc.get("actions", []):
        if action["type"] == "reset":
            m.reset(action.get("map_mode", m.bus.map_mode))
            if init_regs is not None:
                _apply_init_regs(m, init_regs)
            if init_pc is not None:
                _apply_init_pc(m, int(init_pc))
        elif action["type"] == "set_map":
            m.set_map_mode(action["mode"])
        elif action["type"] == "run":
            m.run(max_steps=action.get("max_steps", 10_000))
    exp = doc.get("expect", {})
    snap = m.snapshot()
    ok = True
    if "pc" in exp and snap.pc != exp["pc"]:
        print(f"FAIL pc: {snap.pc} != {exp['pc']}")
        ok = False
    if "halted" in exp and snap.halted != exp["halted"]:
        print(f"FAIL halted: {snap.halted} != {exp['halted']}")
        ok = False
    if "regs" in exp:
        for i, v in enumerate(exp["regs"]):
            if snap.regs[i] != v:
                print(f"FAIL regs[{i}]: {snap.regs[i]} != {v}")
                ok = False
    if ok:
        print("PASS")
    return 0 if ok else 1


def cmd_dos_shell(args: argparse.Namespace) -> int:
    from plover_vm.dos_scenario import _prepare_runtime

    root = Path(__file__).resolve().parents[1]
    rt = _prepare_runtime(root, img_name=args.image_name)
    for line in rt.stage1_boot():
        print(line)
    for line in rt.stage2_shell_start():
        print(line)
    while True:
        try:
            line = input(f"{rt.prompt} ")
        except EOFError:
            break
        for item in rt.run_command(line):
            print(item)
        if line.strip().lower() == "exit":
            break
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plover_vm")
    sub = ap.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run program to completion or max steps")
    run.add_argument("program", type=Path, nargs="?")
    run.add_argument("--nor", type=Path)
    run.add_argument("--cw", type=Path)
    run.add_argument("--map", choices=("boot", "run"), default="boot")
    run.add_argument("--engine", choices=("micro", "macro", "fast"), default="fast")
    run.add_argument("--max-steps", type=int, default=10_000)
    run.add_argument("--reset", action="store_true", default=True)
    run.add_argument("--allow-running", action="store_true")
    run.add_argument("--trace", type=Path)
    run.set_defaults(func=cmd_run)

    step = sub.add_parser("step", help="Single step")
    step.add_argument("--state", type=Path)
    step.add_argument("--engine", choices=("micro", "macro", "fast"), default="micro")
    step.set_defaults(func=cmd_step)

    scen = sub.add_parser("scenario", help="Run YAML scenario")
    scen.add_argument("scenario", type=Path)
    scen.set_defaults(func=cmd_scenario)

    shell = sub.add_parser("dos-shell", help="Interactive PL-DOS shell")
    shell.add_argument("--image-name", default="dos_boot.img")
    shell.set_defaults(func=cmd_dos_shell)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
