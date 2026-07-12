#!/usr/bin/env python3
"""Mailbox LDIO+STA16 copy bandwidth desk (Gi1 / FE2 / PE1 / P12).

stdlib only. Busy/SD poll excluded — CPU copy ceiling after DataReady.
"""

from __future__ import annotations

F_SYS_HZ = 2_000_000

# SYS per payload byte: LDIO then STA16.
SYS_PER_BYTE = {
    "gi1": 9,
    "fe2": 7,
    "pe1": 7,
    "p12": 7,  # same DATA-bound ceiling as PE1/FE2
    "p12_stretch": 9,  # +1 on LDIO and +1 on STA16 first stretch
}


def bytes_per_sec(mode: str, f_sys_hz: int = F_SYS_HZ) -> float:
    return f_sys_hz / SYS_PER_BYTE[mode]


def main() -> None:
    print(f"F_SYS = {F_SYS_HZ / 1e6:.1f} MHz  (copy only, no Busy)\n")
    for mode, sys_b in SYS_PER_BYTE.items():
        bps = bytes_per_sec(mode)
        print(f"  {mode:12s}  SYS/B={sys_b}  →  {bps/1e3:.1f} KB/s  ({bps/1e6:.3f} MB/s)")


if __name__ == "__main__":
    main()
