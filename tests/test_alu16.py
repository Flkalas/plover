"""16-bit ALU tests."""

from plover_vm.alu16 import add16, cmp16_u


def test_add16():
    r = add16(10946, 6765)
    assert r.y == 17711
    assert not r.cout


def test_cmp16_limit():
    r = cmp16_u(17711, 20001)
    assert not r.cout
    r2 = cmp16_u(28657, 20001)
    assert r2.cout
