"""Pytest defaults — fail fast if a CPU integration test spins."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _cpu_wall_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cap ProgramRunner.run_until_halt at 15s unless a test passes wall_s=."""
    from simulators.cyclesim import program

    orig = program.ProgramRunner.run_until_halt

    def bounded(self, max_steps: int = 500, *, wall_s: float = 15.0) -> int:
        return orig(self, max_steps, wall_s=min(wall_s, 15.0))

    monkeypatch.setattr(program.ProgramRunner, "run_until_halt", bounded)
