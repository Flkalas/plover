from plover_vm.memory.bus import MemoryBus
from kern.kernel import Kernel, SIG_FDD, SIG_GPIO, SIG_UART


def test_devmgr_signature_scan():
    k = Kernel(MemoryBus())
    k.state.slot_signatures = {0: SIG_FDD, 1: SIG_GPIO, 2: SIG_UART, 3: 0xFF}
    table = k.devmgr_scan(slots=4)
    assert table[0] == "vfdd"
    assert table[1] == "gpio"
    assert table[2] == "serial"
    assert 3 not in table

