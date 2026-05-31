"""Generate hw/netlist/blocks/alu_decode.yaml — 4-bit alu_op to ALU control (74HC04/08/32)."""
from __future__ import annotations

from pathlib import Path

from alu_opcode_decode import CTRL_NETS, op_bits, truth_table

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "netlist" / "blocks" / "alu_decode.yaml"


class NetlistGen:
    def __init__(self) -> None:
        self.instances: list[str] = []
        self.internal_nets: set[str] = set()
        self._n04 = 0
        self._n08 = 0
        self._n32 = 0

    def _new04(self) -> str:
        self._n04 += 1
        return f"U_DEC_04_{self._n04}"

    def _new08(self) -> str:
        self._n08 += 1
        return f"U_DEC_08_{self._n08}"

    def _new32(self) -> str:
        self._n32 += 1
        return f"U_DEC_32_{self._n32}"

    def _add(self, ref: str, part: str, pins: dict[str, str]) -> None:
        lines = [f"  - ref: {ref}", f"    part: {part}", "    pins:"]
        for k, v in pins.items():
            lines.append(f"      {k}: {v}")
        self.instances.append("\n".join(lines))

    def _fresh(self, prefix: str) -> str:
        n = f"net_dec_{prefix}_{self._n04 + self._n08 + self._n32}"
        self.internal_nets.add(n)
        return n

    def _literal(self, bit: int, val: int) -> str:
        src = f"net_alu_op{bit}"
        if val == 1:
            return src
        out = self._fresh(f"n{bit}")
        ref = self._new04()
        self._add(ref, "74HC04", {"A": src, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        return out

    def _and(self, a: str, b: str) -> str:
        if a == "pwr_gnd" or b == "pwr_gnd":
            return "pwr_gnd"
        if a == "pwr_vcc":
            return b
        if b == "pwr_vcc":
            return a
        out = self._fresh("a")
        ref = self._new08()
        self._add(ref, "74HC08", {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        return out

    def _and_many(self, terms: list[str]) -> str:
        cur = terms[0]
        for t in terms[1:]:
            cur = self._and(cur, t)
        return cur

    def _or(self, a: str, b: str) -> str:
        if a == "pwr_gnd":
            return b
        if b == "pwr_gnd":
            return a
        out = self._fresh("o")
        ref = self._new32()
        self._add(ref, "74HC32", {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        return out

    def _or_many(self, terms: list[str]) -> str:
        cur = terms[0]
        for t in terms[1:]:
            cur = self._or(cur, t)
        return cur

    def _match_op(self, op: int) -> str:
        b0, b1, b2, b3 = op_bits(op)
        return self._and_many(
            [self._literal(0, b0), self._literal(1, b1), self._literal(2, b2), self._literal(3, b3)]
        )

    def _buf(self, src: str, dst: str) -> None:
        if src == dst:
            return
        ref = self._new08()
        self._add(
            ref,
            "74HC08",
            {"A": src, "B": "pwr_vcc", "Y": dst, "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

    def build(self) -> None:
        table = truth_table()

        for sig in CTRL_NETS:
            ops = [r["op"] for r in table if r.get(sig, 0) == 1]
            if ops:
                term = self._or_many([self._match_op(op) for op in ops])
                self._buf(term, sig)
            else:
                self._buf("pwr_gnd", sig)

        ops_hi = [r["op"] for r in table if r.get("b_const_hi", 0) == 1]
        if ops_hi:
            term = self._or_many([self._match_op(op) for op in ops_hi])
            self._buf(term, "net_b_const_hi")
        else:
            self._buf("pwr_gnd", "net_b_const_hi")

        for i in range(1, 8):
            self._buf("net_b_const_hi", f"net_b_const_bit{i}")

        # cmp_n active low on CMP (op 11)
        m11 = self._match_op(11)
        ref = self._new04()
        self._add(
            ref,
            "74HC04",
            {"A": m11, "Y": "net_cmp_n", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

    def write(self) -> None:
        self.build()
        nets = [
            "  - name: net_alu_op0",
            "    width: 1",
            "    probes: [alu_op0]",
            "  - name: net_alu_op1",
            "    width: 1",
            "  - name: net_alu_op2",
            "    width: 1",
            "  - name: net_alu_op3",
            "    width: 1",
        ]
        for sig in CTRL_NETS:
            nets += [f"  - name: {sig}", "    width: 1"]
        for i in range(1, 8):
            nets += [f"  - name: net_b_const_bit{i}", "    width: 1"]
        nets += [
            "  - name: net_b_const_hi",
            "    width: 1",
            "  - name: net_cmp_n",
            "    width: 1",
            "    probes: [cmp_n]",
            "  - name: pwr_vcc",
            "    width: 1",
            "  - name: pwr_gnd",
            "    width: 1",
        ]
        for n in sorted(self.internal_nets):
            nets += [f"  - name: {n}", "    width: 1"]

        text = (
            "version: 1\nblock: alu_decode\ninstances:\n"
            + "\n".join(self.instances)
            + "\nnets:\n"
            + "\n".join(nets)
            + "\n"
        )
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT} ({self._n04}x04 {self._n08}x08 {self._n32}x32)")


def main() -> None:
    NetlistGen().write()


if __name__ == "__main__":
    main()
