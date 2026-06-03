"""Scenario runner for PL-DOS acceptance (S7d)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shlex

from kern.kernel import Kernel
from kern.plfs import Plfs
from kern.plr import PlrImage, pack_plr
from kern.spawn import spawn
from kern.vfdd import VfddDriver
from plover_asm.assemble import assemble, assemble_file
from plover_cc.codegen import program_to_asm
from plover_cc.parse import parse as cc_parse
from plover_ld.format import read_plx
from plover_ld.linker import link_objects
from plover_vm.machine import PloverMachine
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


@dataclass
class DosScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class DosRuntime:
    fs: Plfs
    machine: PloverMachine
    kernel: Kernel
    root: Path
    output: list[str] = field(default_factory=list)
    prompt: str = "PL-DOS>"
    last_link_map: dict[str, int] = field(default_factory=dict)
    last_link_reloc_count: int = 0

    def _emit(self, s: str, acc: list[str]) -> None:
        self.output.append(s)
        acc.append(s)

    def _reset_exec_state(self) -> None:
        self.machine.fast.regs = [0, 0, 0, 0]
        self.machine.fast.halted = False
        self.machine.fast.pc = 0
        self.machine.micro.state.regs = [0, 0, 0, 0]
        self.machine.micro.state.flag_z = False
        self.machine.micro.state.flag_c = False
        self.machine.macro.halted = False
        self.machine.macro.pc = 0
        self.machine.macro._fetch_pending = True

    def stage1_boot(self) -> list[str]:
        out: list[str] = []
        self.kernel.boot()
        self._emit("stage1_kernel_ready", out)
        return out

    def stage2_shell_start(self) -> list[str]:
        out: list[str] = []
        self._emit("stage2_shell_ready", out)
        self._emit(self.prompt, out)
        return out

    def _run_plr_bytes(self, plr_name: str, plr_bytes: bytes, out: list[str]) -> None:
        if self.fs._find(plr_name) is not None:  # noqa: SLF001
            self.fs.delete(plr_name)
        self.fs.create(plr_name, plr_bytes)
        self._reset_exec_state()
        r = spawn(self.machine, self.fs, plr_name)
        self._emit(f"R0_{r.r0}", out)

    def _run_linked_plx(self, plx_paths: list[Path], out: list[str]) -> None:
        objs = [read_plx(p) for p in plx_paths]
        lr = link_objects(objs, text_base=0x2800)
        self.last_link_map = dict(lr.symbols)
        self.last_link_reloc_count = lr.reloc_applied
        entry_addr = lr.symbols.get(lr.entry_symbol, 0x2800)
        plr = pack_plr(
            PlrImage(load_addr=0x2800, entry_off=(entry_addr - 0x2800) & 0xFFFF, code=lr.final_code())
        )
        self._run_plr_bytes("LDRUN.PLR", plr, out)

    def run_command(self, line: str) -> list[str]:
        out: list[str] = []
        parts = shlex.split(line.strip())
        if not parts:
            self._emit(self.prompt, out)
            return out
        cmd = parts[0].lower()
        if cmd == "dir":
            for e in self.fs.list():
                self._emit(e.name11.decode("ascii", errors="replace").strip(), out)
        elif cmd == "run":
            if len(parts) < 2:
                self._emit("ERR missing filename", out)
            else:
                target = parts[1]
                if target.lower().endswith(".plx"):
                    src = (self.root / target).resolve() if not Path(target).is_absolute() else Path(target)
                    if not src.is_file():
                        self._emit(f"ERR missing file: {src}", out)
                    else:
                        self._run_linked_plx([src], out)
                else:
                    self._reset_exec_state()
                    r = spawn(self.machine, self.fs, target)
                    self._emit(f"R0_{r.r0}", out)
        elif cmd == "ldrun":
            if len(parts) < 2:
                self._emit("ERR usage: ldrun <obj1.plx> [obj2.plx ...]", out)
            else:
                paths: list[Path] = []
                bad = False
                for p in parts[1:]:
                    src = (self.root / p).resolve() if not Path(p).is_absolute() else Path(p)
                    if not src.is_file():
                        self._emit(f"ERR missing file: {src}", out)
                        bad = True
                        break
                    paths.append(src)
                if not bad:
                    self._run_linked_plx(paths, out)
        elif cmd == "type":
            if len(parts) < 2:
                self._emit("ERR missing filename", out)
            else:
                data = self.fs.read(parts[1])
                self._emit(data.decode("ascii", errors="replace"), out)
        elif cmd == "del":
            if len(parts) < 2:
                self._emit("ERR missing filename", out)
            else:
                self.fs.delete(parts[1])
                self._emit("OK", out)
        elif cmd == "mon":
            if len(parts) == 1 or parts[1].lower() == "cpu":
                s = self.machine.snapshot()
                self._emit(
                    f"PC_{s.pc:04X} R0_{s.regs[0]:02X} R1_{s.regs[1]:02X} R2_{s.regs[2]:02X} R3_{s.regs[3]:02X} HALT_{int(s.halted)}",
                    out,
                )
            elif parts[1].lower() == "ram":
                snap = self.machine.bus.ram.snapshot()
                nz = sum(1 for b in snap if b != 0)
                self._emit(f"RAM_USED_{nz}B RAM_FREE_{len(snap)-nz}B", out)
            elif parts[1].lower() == "vfdd":
                entries = self.fs.list()
                used = 2
                for e in entries:
                    used += (e.size_bytes + 511) // 512
                self._emit(f"VFDD_FILES_{len(entries)} VFDD_USED_SECT_{used} VFDD_TOTAL_SECT_64", out)
            elif parts[1].lower() == "gpio":
                port = self.kernel.gpio.read_port()
                self._emit(f"GPIO_PORTA_{port:02X}", out)
            elif parts[1].lower() == "serial":
                st = self.kernel.serial.status()
                self._emit(
                    f"SERIAL_SIG_{self.kernel.serial.signature:02X} STATUS_{st:02X} TXQ_{len(self.kernel.serial.tx_fifo)} RXQ_{len(self.kernel.serial.rx_fifo)}",
                    out,
                )
            elif parts[1].lower() == "dev":
                if not self.kernel.state.device_table:
                    self._emit("DEV empty", out)
                else:
                    for slot, drv in sorted(self.kernel.state.device_table.items()):
                        sig = self.kernel.state.slot_signatures.get(slot, 0xFF)
                        self._emit(f"DEV_SLOT_{slot} SIG_{sig:02X} DRV_{drv}", out)
            elif parts[1].lower() == "map":
                if not self.last_link_map:
                    self._emit("MAP empty", out)
                else:
                    for k, v in sorted(self.last_link_map.items()):
                        self._emit(f"{k}_${v:04X}", out)
            elif parts[1].lower() == "sym":
                if not self.last_link_map:
                    self._emit("SYM empty", out)
                else:
                    self._emit("SYM " + " ".join(sorted(self.last_link_map.keys())), out)
            elif parts[1].lower() == "rel":
                self._emit(f"RELOC_APPLIED_{self.last_link_reloc_count}", out)
            else:
                self._emit("ERR usage: mon [cpu|ram|vfdd|gpio|serial|dev|map|sym|rel]", out)
        elif cmd == "asmrun":
            if len(parts) < 2:
                self._emit("ERR usage: asmrun <path.asm>", out)
            else:
                src = (self.root / parts[1]).resolve() if not Path(parts[1]).is_absolute() else Path(parts[1])
                if not src.is_file():
                    self._emit(f"ERR missing file: {src}", out)
                else:
                    res = assemble_file(str(src), origin=0)
                    plr = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(res.bytes)))
                    self._run_plr_bytes("ASMRUN.PLR", plr, out)
        elif cmd == "ccrun":
            if len(parts) < 2:
                self._emit("ERR usage: ccrun <path.c>", out)
            else:
                src = (self.root / parts[1]).resolve() if not Path(parts[1]).is_absolute() else Path(parts[1])
                if not src.is_file():
                    self._emit(f"ERR missing file: {src}", out)
                else:
                    text = src.read_text(encoding="utf-8")
                    prog = cc_parse(text)
                    asm = program_to_asm(prog)
                    res = assemble(asm, origin=0)
                    plr = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(res.bytes)))
                    self._run_plr_bytes("CCRUN.PLR", plr, out)
        elif cmd == "help":
            self._emit(
                "dir run ldrun type del mon [cpu|ram|vfdd|gpio|serial|dev|map|sym|rel] asmrun ccrun help exit",
                out,
            )
        elif cmd == "exit":
            self._emit("BYE", out)
            return out
        else:
            self._emit(f"ERR unknown:{parts[0]}", out)
        self._emit(self.prompt, out)
        return out


def _prepare_runtime(root: Path, *, img_name: str = "dos_boot.img") -> DosRuntime:
    img_path = root / "hw" / "fixtures" / "vfdd" / img_name
    dev = VirtualFdd(VfdConfig(path=img_path, sector_count=64))
    fs = Plfs(VfddDriver(dev))
    fs.format()

    # Stage1 kernel binary at sector0 placeholder payload
    stage1 = b"PLDOS_STAGE1".ljust(512, b"\x00")
    fs.drv.write_sector(0, stage1)

    # HELLO.PLR app
    res = assemble(
        "        .ORG 0\n        ADD 7\n        MOV 2\n        HALT\n",
        origin=0,
    )
    hello = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(res.bytes)))
    fs.create("HELLO.PLR", hello)
    fs.create("README.TXT", b"PL-DOS VM")

    # COMMAND.PLR shell payload marker (stage2 entry representation)
    command = pack_plr(PlrImage(load_addr=0x3000, entry_off=0, code=b"\x0A"))
    fs.create("COMMAND.PLR", command)

    m = PloverMachine(engine="micro")
    m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
    k = Kernel(MemoryBus())
    return DosRuntime(fs=fs, machine=m, kernel=k, root=root, output=[])


def run_dos_scenario(doc: dict, *, root: Path) -> DosScenarioResult:
    try:
        rt = _prepare_runtime(root)
        rt.stage1_boot()
        rt.stage2_shell_start()
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "command":
                rt.run_command(str(action.get("line", "")))
            elif typ == "dir":
                rt.run_command("dir")
            elif typ == "run":
                rt.run_command(f"run {action.get('name', 'HELLO.PLR')}")
            else:
                raise ValueError(f"unknown dos action: {typ}")
    except Exception as e:  # noqa: BLE001
        return DosScenarioResult(ok=False, output=[], error=str(e))

    exp = doc.get("expect", {})
    ok = True
    if "output_contains" in exp:
        for s in exp["output_contains"]:
            if not any(s in line for line in rt.output):
                ok = False
    return DosScenarioResult(ok=ok, output=rt.output)

