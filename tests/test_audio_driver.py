"""Tests for kern AudioDriver."""

from kern.audio import AudioDriver, SIG_AUDIO
from plover_vm.memory.apu import WAVE_SQUARE
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import ST_APU_READY


def test_audio_driver_set_ctrl_and_channel():
    bus = MemoryBus()
    aud = AudioDriver(bus)
    aud.set_master(12)
    aud.write_channel(0, 22, 10, WAVE_SQUARE)
    aud.sync()
    assert bus.mailbox.apu.master_vol == 12
    assert bus.mailbox.apu.channels[0].period == 22
    assert bus.mailbox.apu.channels[0].volume == 10


def test_audio_driver_beep():
    bus = MemoryBus()
    aud = AudioDriver(bus)
    aud.beep(22, 100)
    assert bus.mailbox.apu.channels[0].period == 22
    assert bus.mailbox.apu.beep_ticks == 100


def test_audio_driver_apu_ready():
    bus = MemoryBus()
    aud = AudioDriver(bus)
    aud.sync()
    assert aud.apu_ready()
    assert bus.read_cpu(0xFF00) & ST_APU_READY


def test_sig_audio_in_kernel_map():
    from kern.kernel import DRIVER_BY_SIG

    assert DRIVER_BY_SIG[SIG_AUDIO] == "audio"
