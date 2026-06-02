"""Run cyclesim YAML tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dataclasses import dataclass

from cyclesim.engine import CycleContext, build_context
from cyclesim.micro_driver import apply_micro_phase, should_pulse_clock
from cyclesim.trace import VALUE_NAMES
from hwsim import yaml_util

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PhaseSnapshot:
    nets: dict[str, int]
    gpr: list[int] | None


def _capture(ctx: CycleContext) -> PhaseSnapshot:
    gpr = list(ctx.regfile._regs) if ctx.regfile is not None else None
    return PhaseSnapshot(dict(ctx.nets), gpr)


def _resolve_path(test_path: Path, rel: str) -> Path:
    p = (test_path.parent / rel).resolve()
    if p.is_file():
        return p
    p2 = (ROOT / rel).resolve()
    return p2 if p2.is_file() else p


def run_test(test_path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    data = yaml_util.load_file(str(test_path))
    if not isinstance(data, dict):
        raise ValueError(f"{test_path}: expected mapping")

    nl_path = _resolve_path(test_path, str(data["netlist"]))
    ctx = build_context(nl_path, repo_root)
    errors: list[str] = []

    init = data.get("init") or {}
    if gpr := init.get("gpr"):
        if ctx.regfile is None:
            errors.append("init.gpr but no REGFILE_574_GPR in netlist")
        else:
            for idx, val in gpr.items():
                ctx.regfile.set_gpr(int(idx), int(val))

    driver = data.get("driver", "stimulus")
    trace_phases = data.get("trace_phases", True)
    snapshots: dict[int, PhaseSnapshot] = {}

    if driver == "micro":
        _run_micro(ctx, data, snapshots, trace_phases)
    else:
        _run_stimulus(ctx, data, snapshots, trace_phases)

    _check_expect(snapshots, data, errors)
    _check_checks(snapshots, data, errors)

    waves = ctx.trace.to_json_dict() if trace_phases else {}
    return {
        "test": test_path.stem,
        "passed": not errors and not ctx.violations,
        "errors": errors + ctx.violations,
        "waves": waves,
    }


def _run_micro(
    ctx: CycleContext,
    data: dict[str, Any],
    snapshots: dict[int, PhaseSnapshot],
    trace: bool,
) -> None:
    opcode = int(data.get("opcode", 0)) & 0xFF
    operand = int(data.get("operand", 0)) & 0xFF
    n_phases = int(data.get("phases", 1))

    for ph in range(n_phases):
        ctx._stuck_nets.clear()
        ctx.reset_float_nets()
        apply_micro_phase(ctx, opcode, ph, operand)
        _drive_operand_b(ctx, opcode, ph, operand)
        ctx.comb_fixup()
        if should_pulse_clock(ctx, opcode, ph):
            ctx.pulse_clock()
        snapshots[ph] = _capture(ctx)
        if trace:
            ctx.trace.record_phase(ctx, ph, ctx.nl)


def _drive_operand_b(ctx: CycleContext, opcode: int, phase: int, operand: int) -> None:
    imm: int | None = None
    if opcode == 0x04 and phase == 0:
        imm = operand & 0xFF
    elif opcode == 0x0D and phase == 1:
        imm = operand & 0xFF
    if imm is None:
        return
    for i in range(8):
        ctx.set_net(f"net_b{i}", (imm >> i) & 1, stuck=True)


def _run_stimulus(
    ctx: CycleContext,
    data: dict[str, Any],
    snapshots: dict[int, PhaseSnapshot],
    trace: bool,
) -> None:
    for entry in data.get("stimulus", []) or []:
        ph = int(entry.get("at_phase", 0))
        mapping = entry.get("set") or {}
        ctx._stuck_nets.clear()
        ctx.reset_float_nets()
        ctx.apply_set({str(k): int(v) for k, v in mapping.items()})
        ctx.comb_fixup()
        if entry.get("clock"):
            ctx.pulse_clock()
        snapshots[ph] = _capture(ctx)
        if trace:
            ctx.trace.record_phase(ctx, ph, ctx.nl)


def _net_at(snapshots: dict[int, PhaseSnapshot], ph: int, net: str) -> int:
    snap = snapshots.get(ph)
    if snap is None:
        return 2
    return snap.nets.get(net, 2)


def _check_expect(snapshots: dict[int, PhaseSnapshot], data: dict[str, Any], errors: list[str]) -> None:
    for entry in data.get("expect", []) or []:
        ph = int(entry.get("at_phase", 0))
        for key, want in entry.items():
            if key == "at_phase":
                continue
            if key == "gpr" and isinstance(want, dict):
                snap = snapshots.get(ph)
                if snap is None or snap.gpr is None:
                    errors.append(f"phase {ph}: gpr expect but no snapshot/regfile")
                    continue
                for idx, exp in want.items():
                    got = snap.gpr[int(idx) & 3]
                    if got != (int(exp) & 0xFF):
                        errors.append(f"phase {ph}: gpr[{idx}] want 0x{exp:02X} got 0x{got:02X}")
                continue
            if key.startswith("net_"):
                got = _net_at(snapshots, ph, key)
                w = int(want) & 1
                if got != w:
                    errors.append(
                        f"phase {ph}: {key} want {VALUE_NAMES.get(w, '?')} "
                        f"got {VALUE_NAMES.get(got, '?')}"
                    )


def _check_checks(snapshots: dict[int, PhaseSnapshot], data: dict[str, Any], errors: list[str]) -> None:
    for chk in data.get("checks", []) or []:
        typ = chk.get("type")
        ph = int(chk.get("at_phase", 0))
        if typ == "y_bus_gate":
            y_net = str(chk["y_net"])
            d_net = str(chk["d_net"])
            y_oe = int(chk["y_oe"])
            yv = _net_at(snapshots, ph, y_net)
            dv = _net_at(snapshots, ph, d_net)
            if y_oe == 1:
                if dv != yv:
                    errors.append(f"y_bus_gate: {d_net}={dv} != {y_net}={yv}")
            else:
                if dv != 3:
                    errors.append(f"y_bus_gate: {d_net} should be Z got {VALUE_NAMES.get(dv, '?')}")
