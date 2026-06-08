"""Scenario runner for HID mailbox bring-up."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_vm.machine import PloverMachine
from plover_vm.memory.hid import CMD_HID_INJECT, CMD_HID_KEY_READ, CMD_HID_MOUSE_READ, CMD_HID_POLL, INJECT_KEY, INJECT_MOUSE


def _as_int(v: object, default: int = 0) -> int:
    if v is None:
        return default
    if isinstance(v, str):
        return int(v, 0)
    return int(v)


@dataclass
class HidScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


def run_hid_scenario(doc: dict, *, root: Path) -> HidScenarioResult:
    m = PloverMachine(engine="fast")
    m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.map_mode = 1
    mb = m.bus.mailbox
    out: list[str] = []

    try:
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "hid_inject_key":
                ch = _as_int(action.get("char", 0)) & 0xFF
                mb.issue_hid(CMD_HID_INJECT, buffer=bytes([INJECT_KEY, ch]))
            elif typ == "hid_inject_mouse":
                buttons = int(action.get("buttons", 0)) & 0x07
                dx = _as_int(action.get("dx", 0)) & 0xFF
                dy = _as_int(action.get("dy", 0)) & 0xFF
                mb.issue_hid(CMD_HID_INJECT, buffer=bytes([INJECT_MOUSE, buttons, dx, dy]))
            elif typ == "hid_poll":
                mb.issue_hid(CMD_HID_POLL)
            elif typ == "hid_read_mouse":
                mb.issue_hid(CMD_HID_MOUSE_READ)
            elif typ == "run_pls":
                pls = root / action.get("path", "hw/fixtures/sw/hid_smoke.pls")
                res = assemble_file(str(pls), origin=_as_int(action.get("origin", 0x1000)))
                base = _as_int(action.get("origin", 0x1000))
                for i, b in enumerate(res.bytes):
                    m.bus.ram.write(base + i, b)
                m.macro.pc = base
                m.fast.pc = base
                m.run(max_steps=int(action.get("max_steps", 500)))
            else:
                raise ValueError(f"unknown hid action: {typ}")
    except Exception as e:  # noqa: BLE001
        return HidScenarioResult(ok=False, output=out, error=str(e))

    exp = doc.get("expect", {})
    ok = True
    hid = mb.hid

    if "key_queue" in exp:
        want = int(exp["key_queue"])
        got = len(hid.key_queue)
        if got != want:
            ok = False
            out.append(f"key_queue {got} != {want}")

    if "last_key" in exp:
        want = _as_int(exp["last_key"])
        if hid.last_key != want:
            ok = False
            out.append(f"last_key 0x{hid.last_key:02X} != 0x{want:02X}")

    if "key_pending" in exp:
        want = bool(exp["key_pending"])
        if hid.key_pending != want:
            ok = False
            out.append(f"key_pending {hid.key_pending} != {want}")

    if "mouse_event" in exp:
        me = exp["mouse_event"]
        want_b = int(me.get("buttons", 0))
        want_dx = _as_int(me.get("dx", 0))
        want_dy = _as_int(me.get("dy", 0))
        ev = hid.last_mouse
        dx = ev.dx if ev.dx >= 0 else ev.dx
        if ev.buttons != want_b or ev.dx != want_dx or ev.dy != want_dy:
            ok = False
            out.append(f"mouse ({ev.buttons},{ev.dx},{ev.dy}) != ({want_b},{want_dx},{want_dy})")

    return HidScenarioResult(ok=ok, output=out)
