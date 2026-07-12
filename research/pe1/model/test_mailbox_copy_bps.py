"""Tests for mailbox copy B/s desk constants."""

from __future__ import annotations

import pytest

from mailbox_copy_bps import SYS_PER_BYTE, bytes_per_sec


def test_gi1_nine_sys_per_byte():
    assert SYS_PER_BYTE["gi1"] == 9
    assert bytes_per_sec("gi1") == pytest.approx(2_000_000 / 9)


def test_fe2_pe1_same_copy_ceiling():
    assert SYS_PER_BYTE["fe2"] == SYS_PER_BYTE["pe1"] == 7
    assert bytes_per_sec("pe1") == pytest.approx(2_000_000 / 7)


def test_pe1_faster_than_gi1_copy():
    assert bytes_per_sec("pe1") > bytes_per_sec("gi1")
