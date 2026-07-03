"""Pure gate logic shared by hwsim (timed) and cyclesim (zero-delay)."""

from __future__ import annotations

from typing import Callable

ReadBit = Callable[[str], int]
ReadPin = Callable[[str], int]
HasPin = Callable[[str], bool]

L, H, X, Z = 0, 1, 2, 3


def eval_hc283(read_bit: ReadBit, read: ReadPin) -> tuple[int, int] | None:
    if any(read(f"A{i}") > 1 for i in range(4)):
        return None
    if any(read(f"B{i}") > 1 for i in range(4)):
        return None
    a = sum(read_bit(f"A{i}") << i for i in range(4))
    b = sum(read_bit(f"B{i}") << i for i in range(4))
    c0 = read_bit("C0")
    total = a + b + c0
    return total & 0xF, (total >> 4) & 1


def eval_alu_153_slice(read_bit: ReadBit) -> int | None:
    g = read_bit("G")
    if g == 1:
        return L
    a, b = read_bit("A"), read_bit("B")
    if a > 1 or b > 1:
        return None
    sel = a | (b << 1)
    if sel > 3:
        return None
    val = read_bit(f"C{sel}")
    if val > 1:
        return None
    return val


def eval_alu_y_mux_sel(read_bit: ReadBit) -> int | None:
    s0, s1 = read_bit("S0"), read_bit("S1")
    if s0 > 1 or s1 > 1:
        return None
    return H if (s0 or s1) else L


def eval_alu_cmp_from_sub(read_bit: ReadBit) -> tuple[int, int] | None:
    """CMP when SUB path active: cin=1 and bctrl=1100 (~B pattern)."""
    if read_bit("CIN") != 1:
        return None
    sub_pat = (1, 1, 0, 0)
    got = (
        read_bit("BCTRL0"),
        read_bit("BCTRL1"),
        read_bit("BCTRL2"),
        read_bit("BCTRL3"),
    )
    if any(x > 1 for x in got) or got != sub_pat:
        return None
    ys = [read_bit(f"Y{i}") for i in range(8)]
    if any(y > 1 for y in ys):
        return None
    z = H if all(y == 0 for y in ys) else L
    c_hi = read_bit("C_HI")
    if c_hi > 1:
        return None
    return z, c_hi


def eval_y_bus_buf(
    read_bit: ReadBit,
    has_pin: HasPin,
    *,
    width: int = 8,
) -> dict[str, int] | None:
    oe = read_bit("Y_OE")
    if oe > 1:
        return None
    out: dict[str, int] = {}
    for i in range(width):
        pin_y, pin_d = f"Y{i}", f"D{i}"
        if not has_pin(pin_y) or not has_pin(pin_d):
            continue
        if oe == 1:
            y = read_bit(pin_y)
            if y > 1:
                return None
            out[pin_d] = y
        else:
            out[pin_d] = Z
    return out


def regfile_sel(read_bit: ReadBit, prefix: str) -> int:
    return read_bit(f"{prefix}0") | (read_bit(f"{prefix}1") << 1)


def regfile_read_ports(regs: list[int], read_bit: ReadBit) -> tuple[int, int]:
    ra = regfile_sel(read_bit, "RA") & 3
    rb = regfile_sel(read_bit, "RB") & 3
    return regs[ra] & 0xFF, regs[rb] & 0xFF


def regfile_maybe_write(
    regs: list[int],
    read_bit: ReadBit,
    has_pin: HasPin,
) -> list[int] | None:
    if read_bit("REG_WE") == 0:
        return None
    val = sum(read_bit(f"D{i}") << i for i in range(8))
    out = list(regs)
    for r in range(4):
        pin = f"LOAD_R{r}"
        if has_pin(pin) and read_bit(pin):
            out[r] = val & 0xFF
            return out
    return None
