"""Tests for kern VideoDriver."""

from kern.video import VideoDriver
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.vdu import GFX_W


def test_video_driver_putch_and_goto():
    bus = MemoryBus()
    vid = VideoDriver(bus)
    vid.cls(0x07)
    vid.goto(5, 3)
    vid.putch(ord("Z"))
    assert bus.mailbox.vdu.chars[3][5] == ord("Z")
    assert bus.mailbox.vdu.cursor_col == 6


def test_video_driver_print():
    bus = MemoryBus()
    vid = VideoDriver(bus)
    vid.print("HI")
    assert bus.mailbox.vdu.chars[0][0] == ord("H")
    assert bus.mailbox.vdu.chars[0][1] == ord("I")


def test_video_driver_plot_and_fill():
    bus = MemoryBus()
    vid = VideoDriver(bus)
    vid.plot(1, 2, 0xF800)
    assert bus.mailbox.vdu.bitmap[2 * GFX_W + 1] == 0xF800
    vid.fill_rect(0, 0, 2, 2, 0x001F)
    assert bus.mailbox.vdu.bitmap[0] == 0x001F


def test_video_driver_vsync():
    bus = MemoryBus()
    vid = VideoDriver(bus)
    vid.vsync()
    assert bus.mailbox.vdu.frame == 1
