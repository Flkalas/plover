"""Evaluate CUPL ctrl_lut.inc (idx5 LUT) and optional .sim %EQUATION blocks."""

from __future__ import annotations

import re
from pathlib import Path

_EQUATION_BEGIN = "%EQUATION"
_EQUATION_END = "%END"
_IDX5_TERM = re.compile(r"idx5\s*:\s*'b'([01]{7})")


def _split_or_terms(rhs: str) -> list[str]:
    return [part.strip() for part in rhs.split("#") if part.strip()]


def _eval_term(term: str, env: dict[str, int]) -> bool:
    if not term:
        return False
    for raw in term.split("&"):
        lit = raw.strip()
        if not lit:
            continue
        if lit.startswith("!"):
            name = lit[1:].strip()
            if env.get(name, 0) != 0:
                return False
        elif env.get(lit, 0) == 0:
            return False
    return True


def _normalize_rhs(rhs: str) -> str:
    """Flatten CUPL .sim multi-line # continuations."""
    flat = re.sub(r"\s+", " ", rhs.replace("\n", " ")).strip()
    return re.sub(r"\s+#\s+", " # ", flat)


def eval_rhs(rhs: str, env: dict[str, int]) -> bool:
    rhs = _normalize_rhs(rhs)
    if rhs == "0":
        return False
    if rhs == "1":
        return True
    return any(_eval_term(term, env) for term in _split_or_terms(rhs))


def parse_sim_equations(sim_text: str) -> dict[str, str]:
    if _EQUATION_BEGIN not in sim_text:
        raise ValueError("missing %EQUATION section")
    body = sim_text.split(_EQUATION_BEGIN, 1)[1]
    if _EQUATION_END in body:
        body = body.split(_EQUATION_END, 1)[0]
    equations: dict[str, str] = {}
    current: str | None = None
    chunks: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^(\w+)\s+=>\s*$", line)
        if m:
            if current is not None:
                equations[current] = "\n".join(chunks).strip()
            current = m.group(1)
            chunks = []
            continue
        if current is not None:
            chunks.append(line)
    if current is not None:
        equations[current] = "\n".join(chunks).strip()
    return equations


def load_sim_equations(sim_path: Path) -> dict[str, str]:
    return parse_sim_equations(sim_path.read_text(encoding="utf-8", errors="replace"))


def eval_signal(equations: dict[str, str], signal: str, env: dict[str, int]) -> bool:
    if signal not in equations:
        raise KeyError(f"signal {signal} not in .sim")
    return eval_rhs(equations[signal], env)


def parse_ctrl_lut(inc_text: str) -> dict[str, str]:
    # Only join CUPL line-wrap continuations (4-space indent), not blank lines.
    flat = re.sub(r"\n    ", " ", inc_text)
    equations: dict[str, str] = {}
    for line in flat.splitlines():
        line = line.strip()
        if not line or line.startswith("/*") or line.startswith("FIELD"):
            continue
        m = re.match(r"(\w+)\s*=\s*(.+);", line)
        if m:
            equations[m.group(1)] = m.group(2).strip()
    return equations


def load_ctrl_lut_equations(lut_path: Path) -> dict[str, str]:
    return parse_ctrl_lut(lut_path.read_text(encoding="utf-8"))


def idx5_from_opcode_phase(opcode: int, phase: int) -> int:
    return ((opcode & 0x1F) << 2) | (phase & 3)


def opcode_phase_env(opcode: int, phase: int) -> dict[str, int]:
    op = opcode & 0x1F
    ph = phase & 3
    env: dict[str, int] = {f"opc{i}": (op >> i) & 1 for i in range(5)}
    env["ph0"] = ph & 1
    env["ph1"] = (ph >> 1) & 1
    return env


def eval_ctrl_lut_rhs(rhs: str, idx5: int) -> bool:
    rhs = rhs.strip()
    if rhs in ("'b'0", "'b0", "0"):
        return False
    if rhs in ("'b'1", "'b1", "1"):
        return True
    slot = idx5 & 0x7F
    for part in rhs.split("#"):
        m = _IDX5_TERM.search(part.strip())
        if m and int(m.group(1), 2) == slot:
            return True
    return False


def eval_ctrl_lut_signal(
    equations: dict[str, str], signal: str, opcode: int, phase: int
) -> bool:
    if signal not in equations:
        raise KeyError(f"signal {signal} not in ctrl_lut")
    rhs = equations[signal]
    if _IDX5_TERM.search(rhs):
        return eval_ctrl_lut_rhs(rhs, idx5_from_opcode_phase(opcode, phase))
    return eval_rhs(rhs, opcode_phase_env(opcode, phase))
