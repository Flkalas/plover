"""Forth VDU word smoke tests."""

from forth.interpreter import Forth
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.vdu import GFX_W


def test_forth_vput_and_gplot():
    bus = MemoryBus()
    f = Forth(bus)
    f.eval_line("72 VPUT")
    assert bus.mailbox.vdu.chars[0][0] == ord("H")
    f.eval_line("10 20 65535 GPLOT")
    assert bus.mailbox.vdu.bitmap[20 * GFX_W + 10] == 0xFFFF


def test_forth_vgoto_vcls_gvsync():
    bus = MemoryBus()
    f = Forth(bus)
    f.eval_line("VCLS")
    f.eval_line("5 3 VGOTO")
    f.eval_line("90 VPUT")
    assert bus.mailbox.vdu.chars[3][5] == ord("Z")
    f.eval_line("GVSYNC")
    assert bus.mailbox.vdu.frame == 1


def test_forth_grect():
    bus = MemoryBus()
    f = Forth(bus)
    f.eval_line("0 0 2 2 31 GRECT")
    assert bus.mailbox.vdu.bitmap[0] == 31
