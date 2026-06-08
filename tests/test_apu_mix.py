"""Tests for ApuState mix_samples tone detection."""

from plover_vm.memory.apu import CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, WAVE_SQUARE, ApuState, SAMPLE_RATE


def test_apu_mix_1khz():
    apu = ApuState()
    apu.dispatch(CMD_APU_CH_WRITE, 0, bytearray([0, 22, 0, 15, WAVE_SQUARE]))
    apu.dispatch(CMD_APU_CH_SYNC, 0, bytearray())
    n = SAMPLE_RATE // 10
    samples = apu.mix_samples(n)
    crosses = apu.zero_crossings(samples)
    expected = int(1000 * n / SAMPLE_RATE * 2)
    lo = int(expected * 0.7)
    hi = int(expected * 1.3) + 1
    assert lo <= crosses <= hi, f"crossings {crosses} not in [{lo},{hi}]"


def test_apu_mix_mute():
    apu = ApuState()
    apu.mute = True
    apu.dispatch(CMD_APU_CH_WRITE, 0, bytearray([0, 22, 0, 15, WAVE_SQUARE]))
    apu.dispatch(CMD_APU_CH_SYNC, 0, bytearray())
    samples = apu.mix_samples(100)
    assert all(b == 128 for b in samples)
