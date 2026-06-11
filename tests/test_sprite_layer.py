"""Tests for GFX v0.2 layer/OAM mailbox commands."""

from plover_vm.memory.mailbox import Mailbox
from plover_vm.memory.vdu import (
    CMD_GFX_FRAME_FLUSH,
    CMD_GFX_LAYER_CFG,
    CMD_GFX_OAM_WRITE,
    CMD_GFX_SET_TILE_PAL,
    CMD_GFX_TILEMAP_SET,
    GFX_W,
)


def test_set_tile_palette():
    mb = Mailbox()
    color = 0x07E0
    mb.issue_vdu(CMD_GFX_SET_TILE_PAL, 1, aux=2, buffer=bytes([color & 0xFF, color >> 8]))
    assert mb.vdu.tile_palettes[1][2] == color


def test_tilemap_and_flush():
    mb = Mailbox()
    mb.issue_vdu(CMD_GFX_LAYER_CFG, 0, aux=1, buffer=bytes([0, 0]))
    mb.issue_vdu(CMD_GFX_TILEMAP_SET, 0, aux=5, buffer=bytes([3, 2]))
    mb.vdu.tile_palettes[0][2] = 0x001F
    mb.issue_vdu(CMD_GFX_FRAME_FLUSH)
    px = mb.vdu.bitmap[3 * 8 * GFX_W + 5 * 8]
    assert px == 0x001F


def test_oam_sprite():
    mb = Mailbox()
    mb.vdu.tile_palettes[0][4] = 0xFFE0
    payload = bytes([10, 20, 4, 0, 0, 1])
    mb.issue_vdu(CMD_GFX_OAM_WRITE, 0, buffer=payload)
    mb.issue_vdu(CMD_GFX_FRAME_FLUSH)
    assert mb.vdu.bitmap[20 * GFX_W + 10] == 0xFFE0
