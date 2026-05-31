"""Structured execution trace."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TraceEntry:
    step: int
    pc: int
    phase: int
    opcode: int
    cw: int
    regs: list[int]
    halted: bool
    extra: dict[str, Any] = field(default_factory=dict)


class Tracer:
    def __init__(self) -> None:
        self.entries: list[TraceEntry] = []
        self._step = 0

    def record(
        self,
        pc: int,
        phase: int,
        opcode: int,
        cw: int,
        regs: list[int],
        halted: bool,
        **extra: Any,
    ) -> None:
        self.entries.append(
            TraceEntry(
                step=self._step,
                pc=pc,
                phase=phase,
                opcode=opcode,
                cw=cw,
                regs=list(regs),
                halted=halted,
                extra=extra,
            )
        )
        self._step += 1

    def write_jsonl(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(asdict(e)) + "\n")
