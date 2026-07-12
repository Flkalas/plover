"""Tests for P12 mailbox copy B/s desk constants."""

from __future__ import annotations

import pytest

from mailbox_copy_bps import SYS_PER_BYTE, bytes_per_sec


def test_p12_matches_pe1_fe2_copy():
    assert SYS_PER_BYTE["p12"] == SYS_PER_BYTE["pe1"] == SYS_PER_BYTE["fe2"] == 7
    assert bytes_per_sec("p12") == pytest.approx(2_000_000 / 7)


def test_stretch_slower_copy():
    assert SYS_PER_BYTE["p12_stretch"] == 9
    assert bytes_per_sec("p12_stretch") < bytes_per_sec("p12")


def test_p12_faster_than_gi1():
    assert bytes_per_sec("p12") > bytes_per_sec("gi1")
