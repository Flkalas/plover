"""G-IC bundle — CPLD-CU to CPLD-DP (Gi1, 1 wire)."""

from __future__ import annotations

from dataclasses import dataclass

# Net names (G-IC)
NET_GIC_REG_WE = "net_gic_reg_we"

# LUT layer (CU internal)
NET_REG_WE_LUT = "net_reg_we_lut"


@dataclass(frozen=True)
class GicStrobes:
    reg_we: bool


def decode_g_ic(*, reg_we_lut: bool = False) -> GicStrobes:
    """CU merge policy: reg_we = lut only (Gi1 — no TFR)."""
    return GicStrobes(reg_we=reg_we_lut)
