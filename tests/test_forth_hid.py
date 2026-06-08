"""Forth KEY and MOUSE? via Mailbox HID."""

from forth.interpreter import Forth
from plover_vm.memory.bus import MemoryBus


def test_forth_key_via_hid():
    bus = MemoryBus()
    f = Forth(bus)
    from kern.input import InputDriver

    InputDriver(bus).inject_key(ord("Q"))
    f.eval_line("KEY EMIT")
    assert f.output[-1] == "Q"


def test_forth_key_fallback_input_bytes():
    bus = MemoryBus()
    f = Forth(bus)
    f.input_bytes = [ord("Z")]
    f.eval_line("KEY EMIT")
    assert f.output[-1] == "Z"


def test_forth_mouse_q():
    bus = MemoryBus()
    f = Forth(bus)
    from kern.input import InputDriver

    InputDriver(bus).inject_mouse(0x01, -2, 3)
    f.eval_line("MOUSE? . . .")
    assert f.output == ["3", "65534", "1"]


def test_forth_mouse_q_empty():
    bus = MemoryBus()
    f = Forth(bus)
    f.eval_line("MOUSE? . . .")
    assert f.output == ["0", "0", "0"]
