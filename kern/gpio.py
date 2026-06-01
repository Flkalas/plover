"""GPIO controller model for low-speed integrated I/O."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GpioController:
    direction: int = 0x0F  # bit0-3 out by default
    port_a: int = 0x00

    def read_port(self) -> int:
        return self.port_a & 0xFF

    def write_port(self, val: int) -> None:
        out_mask = self.direction & 0xFF
        v = val & 0xFF
        # output bits updated by host writes
        self.port_a = ((self.port_a & (~out_mask & 0xFF)) | (v & out_mask)) & 0xFF

    def set_input_bits(self, mask: int, values: int) -> None:
        # only bits configured as input can be externally driven
        in_mask = (~self.direction) & 0xFF
        m = mask & in_mask
        self.port_a = (self.port_a & (~m & 0xFF)) | (values & m)
        self.port_a &= 0xFF

    def set_bit(self, bit: int) -> None:
        if bit < 0 or bit > 7:
            raise ValueError("bit out of range")
        self.write_port(self.port_a | (1 << bit))

    def clear_bit(self, bit: int) -> None:
        if bit < 0 or bit > 7:
            raise ValueError("bit out of range")
        self.write_port(self.port_a & ~(1 << bit))

    def get_bit(self, bit: int) -> int:
        if bit < 0 or bit > 7:
            raise ValueError("bit out of range")
        return 1 if (self.port_a & (1 << bit)) else 0

