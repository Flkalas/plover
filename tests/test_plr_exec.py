from __future__ import annotations

from pathlib import Path

from kern.plfs import Plfs
from kern.plr import PlrImage, pack_plr
from kern.spawn import spawn
from kern.vfdd import VfddDriver
from plover_asm.assemble import assemble
from plover_vm.machine import PloverMachine
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


def test_plr_exec_via_plfs(tmp_path: Path):
    img = tmp_path / "disk.img"
    dev = VirtualFdd(VfdConfig(path=img, sector_count=64))
    fs = Plfs(VfddDriver(dev))
    fs.format()

    asm = "        .ORG 0\n        ADD 7\n        HALT\n"
    res = assemble(asm, origin=0)
    plr = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(res.bytes)))
    fs.create("HELLO.PLR", plr)

    m = PloverMachine(engine="micro")
    m.load_cw(Path(__file__).resolve().parents[1] / "hw" / "fixtures" / "control" / "cw.hex")
    out = spawn(m, fs, "HELLO.PLR", engine="micro")
    assert out.halted
    assert out.r0 == 7

