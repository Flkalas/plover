"""Tests for GFX bitmap mailbox commands."""

from plover_vm.memory.mailbox import ST_ERROR, Mailbox
from plover_vm.memory.vdu import (
    CMD_GFX_BLIT,
    CMD_GFX_CLS,
    CMD_GFX_FILLRECT,
    CMD_GFX_GETPIX,
    CMD_GFX_HLINE,
    CMD_GFX_PLOT,
    CMD_GFX_TILE8,
    GFX_H,
    GFX_W,
)


def test_gfx_cls():
    mb = Mailbox()
    mb.issue_vdu(CMD_GFX_CLS, buffer=bytes([0xFF, 0x07]))
    assert mb.vdu.bitmap[0] == 0x07FF
    assert mb.vdu.bitmap[-1] == 0x07FF


def test_gfx_plot():
    mb = Mailbox()
    color = 0xF800
    mb.issue_vdu(CMD_GFX_PLOT, buffer=bytes([10, 20, color & 0xFF, color >> 8]))
    assert mb.vdu.bitmap[20 * GFX_W + 10] == color


def test_gfx_plot_out_of_bounds():
    mb = Mailbox()
    mb.issue_vdu(CMD_GFX_PLOT, buffer=bytes([0, 200, 0, 0]))
    assert mb.read(0xFF00) & ST_ERROR


def test_gfx_hline():
    mb = Mailbox()
    color = 0x001F
    mb.issue_vdu(CMD_GFX_HLINE, buffer=bytes([5, 10, 15, color & 0xFF, color >> 8]))
    for x in range(5, 16):
        assert mb.vdu.bitmap[10 * GFX_W + x] == color


def test_gfx_fillrect():
    mb = Mailbox()
    color = 0x07E0
    mb.issue_vdu(
        CMD_GFX_FILLRECT,
        buffer=bytes([0, 0, 4, 3, color & 0xFF, color >> 8]),
    )
    assert mb.vdu.bitmap[0] == color
    assert mb.vdu.bitmap[2 * GFX_W + 3] == color


def test_gfx_blit():
    mb = Mailbox()
    pixels = bytes([0x00, 0xF8, 0xFF, 0x00])  # red, yellow LE
    payload = bytes([50, 60]) + pixels
    mb.issue_vdu(CMD_GFX_BLIT, len(payload), buffer=payload)
    assert mb.vdu.bitmap[60 * GFX_W + 50] == 0xF800
    assert mb.vdu.bitmap[60 * GFX_W + 51] == 0x00FF


def test_gfx_getpix():
    mb = Mailbox()
    color = 0xFFE0
    mb.vdu.bitmap[30 * GFX_W + 7] = color
    mb.issue_vdu(CMD_GFX_GETPIX, buffer=bytes([7, 30, 0, 0]))
    assert mb.read(0xFF04 + 2) == color & 0xFF
    assert mb.read(0xFF04 + 3) == (color >> 8) & 0xFF


def test_gfx_tile8():
    mb = Mailbox()
    tile = bytearray(32)
    tile[0] = 0xFF
    tile[1] = 0xFF
    payload = bytes([100, 50]) + bytes(tile)
    mb.issue_vdu(CMD_GFX_TILE8, 0, buffer=payload)
    assert mb.vdu.bitmap[50 * GFX_W + 100] == mb.vdu.tile_palettes[0][0x0F]


def test_snapshot_bitmap_size():
    mb = Mailbox()
    snap = mb.vdu.snapshot_bitmap()
    assert len(snap) == GFX_W * GFX_H * 2
