from __future__ import annotations

from pathlib import Path

from kern.plfs import Plfs
from kern.vfdd import VfddDriver
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


def test_plfs_create_read_delete(tmp_path: Path):
    img = tmp_path / "disk.img"
    dev = VirtualFdd(VfdConfig(path=img, sector_count=64))
    fs = Plfs(VfddDriver(dev))
    fs.format()

    fs.create("HELLO.TXT", b"hello")
    assert fs.read("HELLO.TXT") == b"hello"
    assert [e.name11 for e in fs.list()] == [b"HELLO   TXT"]

    fs.delete("HELLO.TXT")
    assert fs.list() == []

