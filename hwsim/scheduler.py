"""Priority-queue event scheduler (time in integer nanoseconds)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(order=True)
class Event:
    time_ns: int
    seq: int
    kind: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)


class Scheduler:
    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._seq = 0
        self.now_ns = 0

    def schedule(self, time_ns: int, kind: str, **payload: Any) -> None:
        if time_ns < self.now_ns:
            time_ns = self.now_ns
        self._seq += 1
        heapq.heappush(self._heap, Event(time_ns, self._seq, kind, payload))

    def schedule_after(self, delay_ns: int, kind: str, **payload: Any) -> None:
        self.schedule(self.now_ns + delay_ns, kind, **payload)

    def run_until(self, end_ns: int, handler: Callable[[Event], None]) -> None:
        while self._heap:
            ev = heapq.heappop(self._heap)
            if ev.time_ns > end_ns:
                heapq.heappush(self._heap, ev)
                break
            self.now_ns = ev.time_ns
            handler(ev)

    def pending(self) -> bool:
        return bool(self._heap)

    def next_time(self) -> int | None:
        if not self._heap:
            return None
        return self._heap[0].time_ns
