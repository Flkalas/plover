"""Tests for HidState FIFO queues."""

from plover_vm.memory.hid import (
    CMD_HID_INJECT,
    CMD_HID_KEY_READ,
    CMD_HID_MOUSE_READ,
    CMD_HID_POLL,
    INJECT_KEY,
    INJECT_MOUSE,
    KEY_MAX,
    MOUSE_MAX,
    HidState,
)


def test_hid_inject_and_read_key():
    hid = HidState()
    assert hid.dispatch(CMD_HID_INJECT, bytearray([INJECT_KEY, ord("Z")]))
    assert hid.key_pending
    buf = bytearray(8)
    hid.dispatch(CMD_HID_POLL, buf)
    assert buf[0] == 1
    hid.dispatch(CMD_HID_KEY_READ, buf)
    assert buf[0] == ord("Z")
    assert not hid.key_pending


def test_hid_inject_and_read_mouse():
    hid = HidState()
    assert hid.dispatch(CMD_HID_INJECT, bytearray([INJECT_MOUSE, 0x01, 0xFE, 0x05]))
    assert hid.mouse_pending
    buf = bytearray(8)
    hid.dispatch(CMD_HID_MOUSE_READ, buf)
    assert buf[0] == 0x01
    assert buf[1] == 0xFE  # -2 as unsigned byte
    assert buf[2] == 0x05


def test_hid_empty_read_returns_zero():
    hid = HidState()
    buf = bytearray(8)
    hid.dispatch(CMD_HID_KEY_READ, buf)
    assert buf[0] == 0
    hid.dispatch(CMD_HID_MOUSE_READ, buf)
    assert buf[0] == buf[1] == buf[2] == 0


def test_hid_overflow_drop_oldest():
    hid = HidState()
    for i in range(KEY_MAX + 5):
        hid.enqueue_key(0x30 + (i % 10))
    assert len(hid.key_queue) == KEY_MAX
    buf = bytearray(8)
    hid.dispatch(CMD_HID_KEY_READ, buf)
    assert buf[0] == 0x30 + 5  # first 5 dropped

    for i in range(MOUSE_MAX + 3):
        hid.enqueue_mouse(0, i & 0xFF, 0)
    assert len(hid.mouse_queue) == MOUSE_MAX


def test_hid_invalid_inject():
    hid = HidState()
    assert not hid.dispatch(CMD_HID_INJECT, bytearray([99, 0]))
    assert not hid.dispatch(CMD_HID_INJECT, bytearray([INJECT_MOUSE, 0]))
