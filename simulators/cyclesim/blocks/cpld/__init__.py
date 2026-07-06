"""Dual CPLD functional blocks (Gi1 v1.0 CU + DP)."""

from simulators.cyclesim.blocks.cpld.cu import BranchAnd, CpldCu, GicMerge, LutRom
from simulators.cyclesim.blocks.cpld.dp import CpldDp
from simulators.cyclesim.blocks.cpld.gic import GicStrobes, decode_g_ic

__all__ = [
    "BranchAnd",
    "CpldCu",
    "CpldDp",
    "GicMerge",
    "GicStrobes",
    "LutRom",
    "decode_g_ic",
]
