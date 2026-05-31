"""Tests mirroring hw/tests/mem_decode.yaml decode truth table."""

from plover_vm.decode import MapDecoder


def _dec(addr: int, map_mode: int = 0, reset: bool = False):
    return MapDecoder().decode(addr, map_mode, reset)


def test_reset_vector_region_mode_a():
    d = _dec(0xFFFC, 0, False)
    assert d.mailbox is False
    assert d.rom_cpu is True
    assert d.ram2 is False


def test_boot_rom_low():
    d = _dec(0x0000, 0, False)
    assert d.rom_cpu is True
    assert d.ram1 is False


def test_boot_rom_0100():
    d = _dec(0x0100, 0, False)
    assert d.rom_cpu is True
    assert d.ram1 is False


def test_ram1_0900_mode_a():
    d = _dec(0x0900, 0, False)
    assert d.rom_cpu is False
    assert d.ram1 is True
    assert d.ram2 is False


def test_ram2_8100():
    d = _dec(0x8100, 0, False)
    assert d.ram2 is True
    assert d.rom_cpu is False


def test_mailbox_ff00():
    d = _dec(0xFF00, 0, False)
    assert d.mailbox is True
    assert d.ram2 is False
    assert d.rom_cpu is False


def test_vector_not_mailbox_fffc():
    d = _dec(0xFFFC, 0, False)
    assert d.mailbox is False


def test_run_mode_fffc_ram2():
    d = _dec(0xFFFC, 1, False)
    assert d.ram2 is True
    assert d.rom_cpu is False


def test_reset_force_fffc():
    d = _dec(0x0100, 0, True)
    assert d.force_fffc is True
    assert d.rom_cpu is False
    assert d.ram1 is False
