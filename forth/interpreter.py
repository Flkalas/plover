"""Minimal Forth interpreter used for S3 bring-up.

This is a host-side implementation that provides a stable behavioral target for
later VM/normative asm ports (S3c). It is intentionally small: enough to run
primitives, colon definitions, and a QUIT-like line evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from kern.audio import AudioDriver
    from kern.input import InputDriver
    from kern.video import VideoDriver
    from plover_vm.memory.bus import MemoryBus


class ForthError(RuntimeError):
    pass


WordImpl = Callable[["Forth"], None]


@dataclass(frozen=True)
class Word:
    name: str
    code: WordImpl
    immediate: bool = False


class Forth:
    def __init__(self, bus: MemoryBus | None = None) -> None:
        self.data: list[int] = []
        self.rstack: list[int] = []
        self.dict: dict[str, Word] = {}
        self.output: list[str] = []
        self.blocks: dict[int, bytearray] = {}
        self.input_bytes: list[int] = []
        self._compile: list[str] | None = None
        self._compile_name: str | None = None
        self._video: VideoDriver | None = None
        self._audio: AudioDriver | None = None
        self._input: InputDriver | None = None
        if bus is not None:
            from kern.audio import AudioDriver
            from kern.input import InputDriver
            from kern.video import VideoDriver

            self._video = VideoDriver(bus)
            self._audio = AudioDriver(bus)
            self._input = InputDriver(bus)
        self._install_core()

    def emit(self, s: str) -> None:
        self.output.append(s)

    def pop(self) -> int:
        if not self.data:
            raise ForthError("stack underflow")
        return self.data.pop()

    def push(self, v: int) -> None:
        self.data.append(v & 0xFFFF)

    def word(self, name: str, fn: WordImpl, *, immediate: bool = False) -> None:
        self.dict[name.upper()] = Word(name.upper(), fn, immediate=immediate)

    def _install_core(self) -> None:
        self.word("DUP", lambda f: f.push(f.data[-1]))
        self.word("DROP", lambda f: f.pop())
        self.word("SWAP", lambda f: (lambda a, b: (f.push(a), f.push(b)))(f.pop(), f.pop()))

        def _add(f: Forth) -> None:
            b = f.pop()
            a = f.pop()
            f.push((a + b) & 0xFFFF)

        def _sub(f: Forth) -> None:
            b = f.pop()
            a = f.pop()
            f.push((a - b) & 0xFFFF)

        def _mul(f: Forth) -> None:
            b = f.pop()
            a = f.pop()
            f.push((a * b) & 0xFFFF)

        self.word("+", _add)
        self.word("-", _sub)
        self.word("*", _mul)

        self.word(".", lambda f: f.emit(str(f.pop())))

        # Console I/O (host simulation)
        self.word("EMIT", self._w_emit)
        self.word("KEY", self._w_key)

        # Block I/O (256B blocks)
        self.word("BLK@", self._w_blk_fetch)
        self.word("BLK!", self._w_blk_store)
        self.word("FLUSH", lambda _f: None)

        if self._video is not None:
            self.word("VCLS", self._w_vcls)
            self.word("VPUT", self._w_vput)
            self.word("VGOTO", self._w_vgoto)
            self.word("GPLOT", self._w_gplot)
            self.word("GRECT", self._w_grect)
            self.word("GVSYNC", self._w_gvsync)

        if self._audio is not None:
            self.word("BEEP", self._w_beep)

        if self._input is not None:
            self.word("MOUSE?", self._w_mouse_q)

        # Compilation control
        self.word(":", self._w_colon, immediate=True)
        self.word(";", self._w_semicolon, immediate=True)

    def _w_colon(self, _f: "Forth") -> None:
        if self._compile is not None:
            raise ForthError("nested ':' not allowed")
        raise ForthError("':' must be handled by parser")

    def _w_semicolon(self, _f: "Forth") -> None:
        if self._compile is None:
            raise ForthError("';' outside definition")
        raise ForthError("';' must be handled by parser")

    def _w_emit(self, _f: "Forth") -> None:
        v = self.pop() & 0xFF
        if self._video is not None:
            self._video.putch(v)
        self.emit(chr(v))

    def _w_vcls(self, _f: "Forth") -> None:
        if self._video is not None:
            self._video.cls()

    def _w_vput(self, _f: "Forth") -> None:
        if self._video is not None:
            self._video.putch(self.pop() & 0xFF)

    def _w_vgoto(self, _f: "Forth") -> None:
        if self._video is not None:
            row = self.pop() & 0xFF
            col = self.pop() & 0xFF
            self._video.goto(col, row)

    def _w_gplot(self, _f: "Forth") -> None:
        if self._video is not None:
            color = self.pop() & 0xFFFF
            y = self.pop() & 0xFF
            x = self.pop() & 0xFF
            self._video.plot(x, y, color)

    def _w_grect(self, _f: "Forth") -> None:
        if self._video is not None:
            color = self.pop() & 0xFFFF
            h = self.pop() & 0xFF
            w = self.pop() & 0xFF
            y = self.pop() & 0xFF
            x = self.pop() & 0xFF
            self._video.fill_rect(x, y, w, h, color)

    def _w_gvsync(self, _f: "Forth") -> None:
        if self._video is not None:
            self._video.vsync()

    def _w_beep(self, _f: "Forth") -> None:
        if self._audio is not None:
            duration = self.pop() & 0xFFFF
            period = self.pop() & 0xFFFF
            self._audio.beep(period, duration)

    def _w_key(self, _f: "Forth") -> None:
        if self._input is not None and self._input.key_pending():
            self.push(self._input.read_key() & 0xFF)
            return
        if not self.input_bytes:
            raise ForthError("KEY: no input")
        self.push(self.input_bytes.pop(0) & 0xFF)

    def _w_mouse_q(self, _f: "Forth") -> None:
        if self._input is not None and self._input.mouse_pending():
            buttons, dx, dy = self._input.read_mouse()
            self.push(buttons & 0xFFFF)
            self.push(dx & 0xFFFF)
            self.push(dy & 0xFFFF)
            return
        self.push(0)
        self.push(0)
        self.push(0)

    def _get_block(self, n: int) -> bytearray:
        if n not in self.blocks:
            self.blocks[n] = bytearray(256)
        return self.blocks[n]

    def _w_blk_fetch(self, _f: "Forth") -> None:
        off = self.pop() & 0xFF
        blk = self.pop() & 0xFFFF
        b = self._get_block(blk)
        self.push(b[off])

    def _w_blk_store(self, _f: "Forth") -> None:
        off = self.pop() & 0xFF
        blk = self.pop() & 0xFFFF
        val = self.pop() & 0xFF
        b = self._get_block(blk)
        b[off] = val

    def _run_token(self, tok: str) -> None:
        u = tok.upper()
        if u in self.dict:
            self.dict[u].code(self)
            return
        try:
            n = int(tok, 0)
        except ValueError:
            raise ForthError(f"unknown word: {tok}")
        self.push(n)

    def eval_line(self, line: str) -> None:
        toks = [t for t in line.replace("\t", " ").split(" ") if t]
        i = 0
        while i < len(toks):
            tok = toks[i]
            u = tok.upper()
            if u == ":":
                if i + 1 >= len(toks):
                    raise ForthError("missing word name after ':'")
                name = toks[i + 1].upper()
                self._compile = []
                self._compile_name = name
                i += 2
                continue
            if u == ";":
                if self._compile is None or self._compile_name is None:
                    raise ForthError("';' outside definition")
                body = list(self._compile)
                name = self._compile_name

                def _colon_word(f: Forth, _body: list[str] = body) -> None:
                    for t in _body:
                        f._run_token(t)

                self.word(name, _colon_word)
                self._compile = None
                self._compile_name = None
                i += 1
                continue

            if self._compile is not None:
                self._compile.append(tok)
            else:
                self._run_token(tok)
            i += 1

