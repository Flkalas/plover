#!/usr/bin/env python3
"""Mailbox LDIO+STA16 copy bandwidth desk (Gi1 / FE2 / PE1).

stdlib only. Busy/SD poll excluded — CPU copy ceiling after DataReady.
"""

from __future__ import annotations

F_SYS_HZ = 2_000_000

# SYS per payload byte: fetch+exec for LDIO then STA16 (shared-clock accounting).
SYS_PER_BYTE = {
    "gi1": 9,  # LDIO 2+2, STA16 3+2
    "fe2": 7,  # F kept, E packed
    "pe1": 7,  # LDIO~3 + STA16~4; DATA-bound, little IF overlap win
}


def bytes_per_sec(mode: str, f_sys_hz: int = F_SYS_HZ) -> float:
    return f_sys_hz / SYS_PER_BYTE[mode]


def main() -> None:
    print(f"F_SYS = {F_SYS_HZ / 1e6:.1f} MHz  (copy only, no Busy)\n")
    for mode, sys_b in SYS_PER_BYTE.items():
        bps = bytes_per_sec(mode)
        print(f"  {mode:4s}  SYS/B={sys_b}  →  {bps/1e3:.1f} KB/s  ({bps/1e6:.3f} MB/s)")


if __name__ == "__main__":
    main()
