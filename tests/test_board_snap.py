"""Board snap coordinates."""

from hwsim.placement.boards.mb102 import snap_dip_mb102, overlaps, DipFootprint
from hwsim.placement.boards.perfboard import snap_dip_perfboard


def test_mb102_snap_non_negative():
    c = snap_dip_mb102(16, 50.0, 30.0)
    assert c.row >= 0 and c.col >= 0


def test_dip_overlap_detection():
    a = DipFootprint(16, 10, 5)
    b = DipFootprint(16, 12, 5)
    assert overlaps(a, b, 0, 0)


def test_perfboard_snap():
    c = snap_dip_perfboard(14, 25.0, 25.0)
    assert c.row >= 0
