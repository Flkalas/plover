"""Tests for APU silent drop during vFDD busy."""

from plover_vm.memory.apu import CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, WAVE_SQUARE
from plover_vm.memory.mailbox import CMD_READ, CMD_WRITE, Mailbox, ST_BUSY, ST_ERROR


def test_apu_silent_drop_during_read():
    mb = Mailbox()
    mb._cmd = CMD_READ
    mb._param = 0
    mb._handle_cmd()
    assert mb._status & ST_BUSY == 0

    mb._vfdd_busy = True
    mb._status = ST_BUSY
    mb.issue_apu(CMD_APU_CH_WRITE, buffer=bytes([0, 22, 0, 15, WAVE_SQUARE]))
    assert mb.apu.channels[0].period == 0
    assert mb._status & ST_ERROR == 0


def test_apu_silent_drop_during_write():
    mb = Mailbox()
    mb._vfdd_busy = True
    mb._status = ST_BUSY
    mb.issue_apu(CMD_APU_CH_SYNC)
    assert mb.apu.channels[0].period == 0
    assert mb._status & ST_ERROR == 0


def test_apu_accept_after_vfdd_idle():
    mb = Mailbox()
    mb.issue_apu(CMD_APU_CH_WRITE, buffer=bytes([0, 22, 0, 15, WAVE_SQUARE]))
    mb.issue_apu(CMD_APU_CH_SYNC)
    assert mb.apu.channels[0].period == 22
