"""Tests for ApuState PSG commands."""

from plover_vm.memory.apu import (
    CMD_APU_CH_OFF,
    CMD_APU_CH_SYNC,
    CMD_APU_CH_WRITE,
    CMD_APU_SET_CTRL,
    WAVE_NOISE,
    WAVE_SQUARE,
    ApuState,
)


def test_apu_set_ctrl():
    apu = ApuState()
    assert apu.dispatch(CMD_APU_SET_CTRL, 0, bytearray([10, 0]))
    assert apu.master_vol == 10
    assert not apu.mute
    assert apu.dispatch(CMD_APU_SET_CTRL, 0, bytearray([5, 1]))
    assert apu.master_vol == 5
    assert apu.mute


def test_apu_ch_write_sync():
    apu = ApuState()
    buf = bytearray([0, 22, 0, 15, WAVE_SQUARE])
    assert apu.dispatch(CMD_APU_CH_WRITE, 0, buf)
    assert apu.channels[0].period == 0
    assert apu.dispatch(CMD_APU_CH_SYNC, 0, bytearray())
    assert apu.channels[0].period == 22
    assert apu.channels[0].volume == 15
    assert apu.channels[0].wave == WAVE_SQUARE


def test_apu_ch_off():
    apu = ApuState()
    apu.dispatch(CMD_APU_CH_WRITE, 0, bytearray([0, 30, 0, 10, WAVE_SQUARE]))
    apu.dispatch(CMD_APU_CH_SYNC, 0, bytearray())
    assert apu.dispatch(CMD_APU_CH_OFF, 0, bytearray())
    assert apu.channels[0].period == 0
    assert apu.channels[0].wave == 0


def test_apu_ch3_noise_only():
    apu = ApuState()
    assert apu.dispatch(CMD_APU_CH_WRITE, 0, bytearray([3, 10, 0, 8, WAVE_NOISE]))
    assert not apu.dispatch(CMD_APU_CH_WRITE, 0, bytearray([3, 10, 0, 8, WAVE_SQUARE]))
    apu.dispatch(CMD_APU_CH_SYNC, 0, bytearray())
    assert apu.channels[3].wave == WAVE_NOISE
