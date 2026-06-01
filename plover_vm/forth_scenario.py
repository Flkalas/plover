"""Scenario runner for host-side Forth bring-up (S3)."""

from __future__ import annotations

from dataclasses import dataclass, field

from forth.interpreter import Forth, ForthError


@dataclass
class ForthScenarioResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    stack: list[int] = field(default_factory=list)
    error: str | None = None


def run_forth_scenario(doc: dict) -> ForthScenarioResult:
    f = Forth()
    try:
        for action in doc.get("actions", []):
            typ = action.get("type")
            if typ == "eval":
                f.eval_line(action.get("line", ""))
            elif typ == "reset":
                f = Forth()
            else:
                raise ForthError(f"unknown action type: {typ}")
    except ForthError as e:
        return ForthScenarioResult(ok=False, output=list(f.output), stack=list(f.data), error=str(e))

    exp = doc.get("expect", {})
    ok = True
    if "stack" in exp and list(exp["stack"]) != list(f.data):
        ok = False
    if "output" in exp and list(exp["output"]) != list(f.output):
        ok = False
    return ForthScenarioResult(ok=ok, output=list(f.output), stack=list(f.data))

