"""Scenario runner for host-side kernel bring-up (S6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from kern.kernel import Kernel
from plover_vm.memory.bus import MemoryBus


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
            if typ == "boot":
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

