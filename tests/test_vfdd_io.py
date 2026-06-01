from __future__ import annotations

from pathlib import Path

from plover_vm.memory.vfdd import SECTOR_SIZE, VfdConfig, VirtualFdd


def test_vfdd_sector_roundtrip(tmp_path: Path):
    img = tmp_path / "disk.img"
    dev = VirtualFdd(VfdConfig(path=img, sector_count=8))
    data = bytes([0xA5]) * SECTOR_SIZE
    dev.write_sector(3, data)
    out = dev.read_sector(3)
    assert out == data


def test_vfdd_bounds(tmp_path: Path):
    img = tmp_path / "disk.img"
    dev = VirtualFdd(VfdConfig(path=img, sector_count=1))
    try:
        dev.read_sector(1)
        assert False, "expected IndexError"
    except IndexError:
        pass

