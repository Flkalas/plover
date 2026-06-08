"""Tests for HID silent drop during vFDD busy."""

from plover_vm.memory.hid import CMD_HID_INJECT, INJECT_KEY
from plover_vm.memory.mailbox import CMD_READ, Mailbox, ST_BUSY, ST_ERROR


def test_hid_silent_drop_during_vfdd_busy():
    mb = Mailbox()
    mb._vfdd_busy = True
    mb._status = ST_BUSY
    mb.issue_hid(CMD_HID_INJECT, buffer=bytes([INJECT_KEY, ord("X")]))
    assert not mb.hid.key_pending
    assert mb._status & ST_ERROR == 0


def test_hid_accept_after_vfdd_idle():
    mb = Mailbox()
    mb.issue_hid(CMD_HID_INJECT, buffer=bytes([INJECT_KEY, ord("Y")]))
    assert mb.hid.key_pending
    assert mb.read(0xFF00) & 0x10  # HID_KEY_PENDING
