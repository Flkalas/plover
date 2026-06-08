"""Scenario runner for VDU/GFX mailbox bring-up."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_vm.machine import PloverMachine
from plover_vm.memory.vdu import CMD_GFX_FILLRECT, CMD_VDU_CLS, CMD_VDU_PRINT, CMD_VDU_VSYNC


def _as_int(v: object, default: int = 0) -> int:
    if v is None:
        return default
    if isinstance(v, str):
        return int(v, 0)
    return int(v)


@dataclass
class VduScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


def run_vdu_scenario(doc: dict, *, root: Path) -> VduScenarioResult:
    m = PloverMachine(engine="fast")
    m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.map_mode = 1
    mb = m.bus.mailbox
    out: list[str] = []

    try:
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "vdu_cls":
                mb.issue_vdu(CMD_VDU_CLS, int(action.get("attr", 0x07)))
            elif typ == "vdu_print":
                text = str(action.get("text", ""))
                mb.issue_vdu(CMD_VDU_PRINT, len(text), buffer=text.encode("ascii"))
            elif typ == "gfx_fillrect":
                color = _as_int(action.get("color", 0)) & 0xFFFF
                buf = bytes(
                    [
                        int(action.get("x", 0)) & 0xFF,
                        int(action.get("y", 0)) & 0xFF,
                        int(action.get("w", 1)) & 0xFF,
                        int(action.get("h", 1)) & 0xFF,
                        color & 0xFF,
                        (color >> 8) & 0xFF,
                    ]
                )
                mb.issue_vdu(CMD_GFX_FILLRECT, buffer=buf)
            elif typ == "vsync":
                mb.issue_vdu(CMD_VDU_VSYNC)
            elif typ == "run_pls":
                pls = root / action.get("path", "hw/fixtures/sw/vdu_smoke.pls")
                res = assemble_file(str(pls), origin=_as_int(action.get("origin", 0x1000)))
                base = _as_int(action.get("origin", 0x1000))
                for i, b in enumerate(res.bytes):
                    m.bus.ram.write(base + i, b)
                m.macro.pc = base
                m.fast.pc = base
                m.run(max_steps=int(action.get("max_steps", 500)))
            else:
                raise ValueError(f"unknown vdu action: {typ}")
    except Exception as e:  # noqa: BLE001
        return VduScenarioResult(ok=False, output=out, error=str(e))

    exp = doc.get("expect", {})
    ok = True
    vdu = mb.vdu

    if "text_contains" in exp:
        text = vdu.compose_text()
        for s in exp["text_contains"]:
            if s not in text:
                ok = False
                out.append(f"missing text: {s}")

    if "pixel" in exp:
        px = exp["pixel"]
        x = int(px["x"])
        y = int(px["y"])
        want = _as_int(px["color"])
        got = vdu.bitmap[y * 320 + x]
        if got != want:
            ok = False
            out.append(f"pixel ({x},{y}): 0x{got:04X} != 0x{want:04X}")

    if "frame" in exp:
        if vdu.frame != int(exp["frame"]):
            ok = False
            out.append(f"frame {vdu.frame} != {exp['frame']}")

    if "char_at" in exp:
        ca = exp["char_at"]
        row = int(ca["row"])
        col = int(ca["col"])
        ch = _as_int(ca["char"])
        if vdu.chars[row][col] != ch:
            ok = False
            out.append(f"char[{row}][{col}] mismatch")

    return VduScenarioResult(ok=ok, output=out)
