"""Scenario runner for host-side kernel bring-up (S6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from kern.kernel import Kernel
from kern.vfdd import VfddDriver
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import CMD_READ, MB_BUFFER, MB_CMD, MB_PARAM
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


@dataclass
class KernelScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


def run_kernel_scenario(doc: dict) -> KernelScenarioResult:
    bus = MemoryBus()
    k = Kernel(bus)
    try:
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "stage0_load_sector0":
                img = Path(action.get("image", "hw/fixtures/vfdd/dos_boot.img"))
                sectors = int(action.get("sectors", 64))
                dev = VirtualFdd(VfdConfig(path=img, sector_count=sectors))
                drv = VfddDriver(dev)
                # Simulated BIOS mailbox read of sector0.
                bus.mailbox.set_sector_stub(drv.read_sector(0))
                bus.write_cpu(MB_PARAM, 0)
                bus.write_cpu(MB_CMD, CMD_READ)
                # Copy mailbox payload to RAM 0x0800.
                for i in range(248):
                    bus.write_cpu(0x0800 + i, bus.read_cpu(MB_BUFFER + i))
                k.kprint("bios_stage0_ok")
            elif typ == "stage1_gpio_smoke":
                # Bare-metal style: switch input controls LED output bit0.
                sw_on = int(action.get("switch", 1)) & 1
                k.gpio.direction = 0x0F  # low nibble output
                # bit5 is switch input
                k.gpio.set_input_bits(mask=(1 << 5), values=(sw_on << 5))
                if k.gpio.get_bit(5):
                    k.gpio.set_bit(0)
                    k.kprint("gpio_smoke_led_on")
                else:
                    k.gpio.clear_bit(0)
                    k.kprint("gpio_smoke_led_off")
            elif typ == "boot":
                k.boot()
            elif typ == "alloc":
                k.kmalloc(int(action.get("bytes", 0)))
            else:
                raise ValueError(f"unknown kernel action: {typ}")
    except Exception as e:  # noqa: BLE001
        return KernelScenarioResult(ok=False, output=list(k.state.output), error=str(e))

    exp = doc.get("expect", {})
    ok = True
    if "output_contains" in exp:
        for s in exp["output_contains"]:
            if not any(s in line for line in k.state.output):
                ok = False
    return KernelScenarioResult(ok=ok, output=list(k.state.output))

