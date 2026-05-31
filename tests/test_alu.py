"""ALU vectors aligned with alu8.md sel table."""

from plover_vm.alu import alu8


def test_add():
    r = alu8(0x12, 0x34, 1)
    assert r.y == 0x46
    assert r.cout is False


def test_sub():
    r = alu8(0x10, 0x03, 2)
    assert r.y == 0x0D


def test_and_or_xor():
    assert alu8(0xF0, 0x0F, 3).y == 0x00
    assert alu8(0xF0, 0x0F, 4).y == 0xFF
    assert alu8(0xFF, 0x0F, 5).y == 0xF0


def test_not_pass_inc_dec():
    assert alu8(0x55, 0, 6).y == 0xAA
    assert alu8(0x42, 0, 7).y == 0x42
    assert alu8(0, 0x99, 8).y == 0x99
    assert alu8(0xFE, 0, 9).y == 0xFF
    assert alu8(0x01, 0, 10).y == 0x00


def test_cmp_flags():
    r = alu8(5, 5, 11)
    assert r.zero is True
