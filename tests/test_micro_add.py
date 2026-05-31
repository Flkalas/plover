from pathlib import Path

from plover_vm.memory.bus import MemoryBus
from plover_vm.micro.engine import MicroEngine


ROOT = Path(__file__).resolve().parents[1]


def _load_cw(bus: MemoryBus) -> None:
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.pack_control_store import build_all

    bus.nor.patch_cw_region(build_all())


def test_add_r0_r1_to_r2():
    bus = MemoryBus()
    _load_cw(bus)
    micro = MicroEngine(bus)
    micro.reset_micro(0x01, 0)
    micro.state.regs = [3, 5, 0, 0]
    for _ in range(3):
        micro.step()
    assert micro.state.regs[2] == 8
