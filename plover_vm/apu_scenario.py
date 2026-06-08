"""Scenario runner for APU PSG mailbox bring-up."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_vm.machine import PloverMachine
from plover_vm.memory.apu import CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, CMD_APU_SET_CTRL, WAVE_SQUARE


def _as_int(v: object, default: int = 0) -> int:
    if v is None:
        return default
    if isinstance(v, str):
        return int(v, 0)
    return int(v)


@dataclass
class ApuScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: str | None = None


def run_apu_scenario(doc: dict, *, root: Path) -> ApuScenarioResult:
    m = PloverMachine(engine="fast")
    m.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
    m.bus.map_mode = 1
    mb = m.bus.mailbox
    out: list[str] = []

    try:
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "apu_set_ctrl":
                vol = int(action.get("vol", 15)) & 0x0F
                mute = 1 if action.get("mute", False) else 0
                mb.issue_apu(CMD_APU_SET_CTRL, buffer=bytes([vol, mute]))
            elif typ == "apu_ch_write":
                ch = int(action.get("ch", 0)) & 0x03
                period = _as_int(action.get("period", 0)) & 0xFFFF
                vol = int(action.get("vol", 15)) & 0x0F
                wave = int(action.get("wave", WAVE_SQUARE)) & 0x03
                buf = bytes([ch, period & 0xFF, (period >> 8) & 0xFF, vol, wave])
                mb.issue_apu(CMD_APU_CH_WRITE, buffer=buf)
            elif typ == "apu_sync":
                mb.issue_apu(CMD_APU_CH_SYNC)
            elif typ == "run_pls":
                pls = root / action.get("path", "hw/fixtures/sw/apu_smoke.pls")
                res = assemble_file(str(pls), origin=_as_int(action.get("origin", 0x1000)))
                base = _as_int(action.get("origin", 0x1000))
                for i, b in enumerate(res.bytes):
                    m.bus.ram.write(base + i, b)
                m.macro.pc = base
                m.fast.pc = base
                m.run(max_steps=int(action.get("max_steps", 500)))
            else:
                raise ValueError(f"unknown apu action: {typ}")
    except Exception as e:  # noqa: BLE001
        return ApuScenarioResult(ok=False, output=out, error=str(e))

    exp = doc.get("expect", {})
    ok = True
    apu = mb.apu

    if "ch0_period" in exp:
        want = _as_int(exp["ch0_period"])
        got = apu.channels[0].period
        if got != want:
            ok = False
            out.append(f"ch0 period {got} != {want}")

    if "ch0_vol" in exp:
        want = int(exp["ch0_vol"])
        got = apu.channels[0].volume
        if got != want:
            ok = False
            out.append(f"ch0 vol {got} != {want}")

    if "master_vol" in exp:
        want = int(exp["master_vol"])
        if apu.master_vol != want:
            ok = False
            out.append(f"master_vol {apu.master_vol} != {want}")

    if "mix_contains_freq" in exp:
        freq = float(exp["mix_contains_freq"])
        n = int(exp.get("mix_samples", 2205))
        samples = apu.mix_samples(n)
        crosses = apu.zero_crossings(samples)
        expected = int(freq * n / apu.sample_rate * 2)
        lo = int(expected * 0.7)
        hi = int(expected * 1.3) + 1
        if not (lo <= crosses <= hi):
            ok = False
            out.append(f"mix crossings {crosses} not in [{lo},{hi}] for {freq} Hz")

    return ApuScenarioResult(ok=ok, output=out)
