"""Breadboard memory decode parity (gates + 138×2 ideal comb)."""

from hw.logic.cpld_decode import decode_addr, decode_ce_breadboard
from hw.logic.mem_glue import mailbox_en


def test_decode_ce_breadboard_matches_decode_addr_exhaustive():
    for addr in range(0x10000):
        for map_mode in (0, 1):
            for reset in (False, True):
                direct = decode_addr(addr, map_mode, reset)
                bb = decode_ce_breadboard(addr, map_mode, reset)
                assert bb == direct, (hex(addr), map_mode, reset)


def test_mailbox_gates_spots():
    assert mailbox_en(0xFEFF) == 0
    assert mailbox_en(0xFF00) == 1
    assert mailbox_en(0xFFFB) == 1
    assert mailbox_en(0xFFFC) == 0
    assert mailbox_en(0xFFFF) == 0
    assert mailbox_en(0x0100) == 0
