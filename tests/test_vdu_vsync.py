"""Tests for VDU_VSYNC and VDU_MODE."""

from plover_vm.memory.mailbox import Mailbox
from plover_vm.memory.vdu import CMD_VDU_MODE, CMD_VDU_VSYNC, MODE_BITMAP, MODE_BOTH, MODE_TEXT
from plover_vm.memory.mailbox import ST_ERROR


def test_vsync_increments_frame():
    mb = Mailbox()
    assert mb.vdu.frame == 0
    mb.issue_vdu(CMD_VDU_VSYNC)
    assert mb.vdu.frame == 1
    mb.issue_vdu(CMD_VDU_VSYNC)
    assert mb.vdu.frame == 2


def test_vdu_mode():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_MODE, MODE_TEXT)
    assert mb.vdu.mode == MODE_TEXT
    mb.issue_vdu(CMD_VDU_MODE, MODE_BITMAP)
    assert mb.vdu.mode == MODE_BITMAP
    mb.issue_vdu(CMD_VDU_MODE, MODE_BOTH)
    assert mb.vdu.mode == MODE_BOTH


def test_vdu_mode_invalid():
    mb = Mailbox()
    mb.issue_vdu(CMD_VDU_MODE, 99)
    assert mb.read(0xFF00) & ST_ERROR
