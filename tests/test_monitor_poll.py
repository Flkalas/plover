from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import CMD_READ, MB_CMD, MB_PARAM, MB_STATUS, ST_READY


def test_mailbox_read_sets_ready():
    bus = MemoryBus()
    bus.mailbox.set_sector_stub(bytes([0xAB] * 512))
    bus.mailbox.write(MB_PARAM, 0)
    bus.mailbox.write(MB_CMD, CMD_READ)
    assert bus.mailbox.read(MB_STATUS) & ST_READY
    assert bus.read_cpu(0xFF04) == 0xAB


def test_poll_sequence():
    bus = MemoryBus()
    bus.mailbox.set_sector_stub(bytes([0xCD] * 512))
    bus.mailbox.write(MB_PARAM, 0)
    bus.mailbox.write(MB_CMD, CMD_READ)
    status = bus.read_cpu(MB_STATUS)
    assert status & 1
    assert bus.read_cpu(0xFF04) == 0xCD
