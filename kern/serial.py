"""UART-like serial module model (polling mode)."""

from __future__ import annotations

from dataclasses import dataclass, field

SIG_UART = 0xD4

ST_RX_READY = 0x01
ST_TX_READY = 0x02
ST_ERR = 0x04


@dataclass
class SerialModule:
    signature: int = SIG_UART
    tx_fifo: list[int] = field(default_factory=list)
    rx_fifo: list[int] = field(default_factory=list)
    ctrl: int = 0x00

    def status(self) -> int:
        st = ST_TX_READY
        if self.rx_fifo:
            st |= ST_RX_READY
        return st & 0xFF

    def tx(self, b: int) -> None:
        self.tx_fifo.append(b & 0xFF)

    def write(self, data: bytes | bytearray) -> None:
        for b in data:
            self.tx(b)

    def inject_rx(self, data: bytes | bytearray) -> None:
        for b in data:
            self.rx_fifo.append(b & 0xFF)

    def rx_ready(self) -> bool:
        return bool(self.rx_fifo)

    def rx(self) -> int:
        if not self.rx_fifo:
            raise RuntimeError("serial rx empty")
        return self.rx_fifo.pop(0) & 0xFF

