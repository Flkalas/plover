"""Dual CPLD functional blocks (rev G CU + DP)."""

from simulators.cyclesim.blocks.cpld.cu import BranchAnd, CpldCu, GicMerge, LutRom, TfrDetect
from simulators.cyclesim.blocks.cpld.dp import CpldDp
from simulators.cyclesim.blocks.cpld.gic import GicStrobes, decode_g_ic

__all__ = [
    "BranchAnd",
    "CpldCu",
    "CpldDp",
    "GicMerge",
    "GicStrobes",
    "LutRom",
    "TfrDetect",
    "decode_g_ic",
]
