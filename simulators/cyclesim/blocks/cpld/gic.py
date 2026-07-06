"""G-IC bundle — CPLD-CU to CPLD-DP (rev G, 6 wires)."""

from __future__ import annotations

from dataclasses import dataclass

from simulators.cyclesim.data.isa import decode_tfr, is_tfr_valid

# Net names (G-IC)
NET_GIC_REG_WE = "net_gic_reg_we"
NET_GIC_W_SEL0 = "net_gic_w_sel0"
NET_GIC_W_SEL1 = "net_gic_w_sel1"
NET_GIC_TFR_VALID = "net_gic_tfr_valid"
NET_GIC_SRC0 = "net_gic_src0"
NET_GIC_SRC1 = "net_gic_src1"

# LUT layer (CU internal)
NET_REG_WE_LUT = "net_reg_we_lut"
NET_W_SEL0_LUT = "net_w_sel0_lut"
NET_W_SEL1_LUT = "net_w_sel1_lut"


@dataclass(frozen=True)
class GicStrobes:
    reg_we: bool
    w_sel: int
    tfr_valid: bool
    src: int


def decode_g_ic(opcode: int, *, reg_we_lut: bool = False, w_sel_lut: int = 0) -> GicStrobes:
    """CU merge policy: TFR comb overrides w_sel; reg_we = lut | tfr_valid."""
    op = opcode & 0x1F
    if is_tfr_valid(op):
        src, dst = decode_tfr(op)
        return GicStrobes(reg_we=True, w_sel=dst, tfr_valid=True, src=src)
    return GicStrobes(
        reg_we=reg_we_lut,
        w_sel=w_sel_lut & 0x3,
        tfr_valid=False,
        src=0,
    )
