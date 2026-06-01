"""Scenario runner for PL-DOS acceptance (S7d)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kern.plfs import Plfs
from kern.plr import PlrImage, pack_plr
from kern.spawn import spawn
from kern.vfdd import VfddDriver
from plover_asm.assemble import assemble
from plover_vm.machine import PloverMachine
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


@dataclass
class DosScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


def run_dos_scenario(doc: dict, *, root: Path) -> DosScenarioResult:
    out: list[str] = []
    try:
        img_path = root / "hw" / "fixtures" / "vfdd" / "dos.img"
        dev = VirtualFdd(VfdConfig(path=img_path, sector_count=64))
        fs = Plfs(VfddDriver(dev))
        fs.format()

        # Build a demo HELLO.PLR: ADD 7; HALT
        res = assemble("        .ORG 0\n        ADD 7\n        HALT\n", origin=0)
        plr = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(res.bytes)))
        fs.create("HELLO.PLR", plr)

        m = PloverMachine(engine="micro")
        m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")

        out.append("PLDOS")

        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "dir":
                for e in fs.list():
                    out.append(e.name11.decode("ascii", errors="replace").strip())
            elif typ == "run":
                name = action.get("name", "HELLO.PLR")
                r = spawn(m, fs, name, engine="micro")
                out.append(f"R0_{r.r0}")
            else:
                raise ValueError(f"unknown dos action: {typ}")
    except Exception as e:  # noqa: BLE001
        return DosScenarioResult(ok=False, output=out, error=str(e))

    exp = doc.get("expect", {})
    ok = True
    if "output_contains" in exp:
        for s in exp["output_contains"]:
            if not any(s in line for line in out):
                ok = False
    return DosScenarioResult(ok=ok, output=out)

