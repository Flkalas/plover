"""HID input state for Mailbox keyboard/mouse queues."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

CMD_HID_POLL = 0x40
CMD_HID_KEY_READ = 0x41
CMD_HID_MOUSE_READ = 0x42
CMD_HID_INJECT = 0x43

INJECT_KEY = 0
INJECT_MOUSE = 1

KEY_MAX = 64
MOUSE_MAX = 32


@dataclass
class MouseEvent:
    buttons: int = 0
    dx: int = 0
    dy: int = 0


@dataclass
class HidState:
    """Keyboard ASCII FIFO + mouse event queue."""

    key_queue: deque[int] = field(default_factory=deque)
    mouse_queue: deque[MouseEvent] = field(default_factory=deque)
    last_key: int = 0
    last_mouse: MouseEvent = field(default_factory=MouseEvent)

    @property
    def key_pending(self) -> bool:
        return len(self.key_queue) > 0

    @property
    def mouse_pending(self) -> bool:
        return len(self.mouse_queue) > 0

    def enqueue_key(self, ch: int) -> None:
        if len(self.key_queue) >= KEY_MAX:
            self.key_queue.popleft()
        self.key_queue.append(ch & 0xFF)

    def enqueue_mouse(self, buttons: int, dx: int, dy: int) -> None:
        if len(self.mouse_queue) >= MOUSE_MAX:
            self.mouse_queue.popleft()
        self.mouse_queue.append(
            MouseEvent(buttons=buttons & 0x07, dx=_sign8(dx), dy=_sign8(dy))
        )

    def poll(self, buffer: bytearray) -> bool:
        buffer[0] = min(len(self.key_queue), 255)
        buffer[1] = min(len(self.mouse_queue), 255)
        return True

    def read_key(self, buffer: bytearray) -> bool:
        if self.key_queue:
            self.last_key = self.key_queue.popleft()
        else:
            self.last_key = 0
        buffer[0] = self.last_key & 0xFF
        return True

    def read_mouse(self, buffer: bytearray) -> bool:
        if self.mouse_queue:
            ev = self.mouse_queue.popleft()
            self.last_mouse = ev
            buffer[0] = ev.buttons & 0xFF
            buffer[1] = ev.dx & 0xFF
            buffer[2] = ev.dy & 0xFF
        else:
            self.last_mouse = MouseEvent()
            buffer[0] = 0
            buffer[1] = 0
            buffer[2] = 0
        return True

    def inject(self, buffer: bytearray | bytes) -> bool:
        if len(buffer) < 2:
            return False
        typ = buffer[0] & 0xFF
        if typ == INJECT_KEY:
            self.enqueue_key(buffer[1])
            return True
        if typ == INJECT_MOUSE:
            if len(buffer) < 4:
                return False
            self.enqueue_mouse(buffer[1], buffer[2], buffer[3])
            return True
        return False

    def dispatch(self, cmd: int, buffer: bytearray) -> bool:
        """Return True if command accepted, False if silent drop."""
        if cmd == CMD_HID_POLL:
            return self.poll(buffer)
        if cmd == CMD_HID_KEY_READ:
            return self.read_key(buffer)
        if cmd == CMD_HID_MOUSE_READ:
            return self.read_mouse(buffer)
        if cmd == CMD_HID_INJECT:
            return self.inject(buffer)
        return False


def _sign8(v: int) -> int:
    x = v & 0xFF
    return x if x < 128 else x - 256
