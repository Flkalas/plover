"""Forth BEEP smoke."""

from forth.interpreter import Forth
from plover_vm.memory.bus import MemoryBus


def test_forth_beep():
    bus = MemoryBus()
    f = Forth(bus)
    f.eval_line("22 100 BEEP")
    apu = bus.mailbox.apu
    assert apu.channels[0].period == 22
    assert apu.beep_ticks == 100
