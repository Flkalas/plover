"""Tests for kern InputDriver."""

from kern.input import InputDriver, SIG_HID
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import ST_HID_KEY_PENDING, ST_HID_MOUSE_PENDING


def test_input_driver_key_round_trip():
    bus = MemoryBus()
    inp = InputDriver(bus)
    inp.inject_key(ord("K"))
    assert inp.key_pending()
    assert bus.read_cpu(0xFF00) & ST_HID_KEY_PENDING
    assert inp.read_key() == ord("K")
    assert not inp.key_pending()


def test_input_driver_mouse_round_trip():
    bus = MemoryBus()
    inp = InputDriver(bus)
    inp.inject_mouse(0x03, -1, 4)
    assert inp.mouse_pending()
    buttons, dx, dy = inp.read_mouse()
    assert buttons == 0x03
    assert dx == -1
    assert dy == 4


def test_input_driver_poll():
    bus = MemoryBus()
    inp = InputDriver(bus)
    inp.inject_key(ord("A"))
    inp.inject_mouse(1, 0, 0)
    kd, md = inp.poll()
    assert kd == 1
    assert md == 1


def test_sig_hid_in_kernel_map():
    from kern.kernel import DRIVER_BY_SIG

    assert DRIVER_BY_SIG[SIG_HID] == "hid"
