"""Generate hw/netlist/blocks/local_ctrl.yaml — bus_en=00 LOCAL ctrl decode (74HC04/08/32)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "netlist" / "blocks" / "local_ctrl.yaml"


class NetlistGen:
    def __init__(self) -> None:
        self.instances: list[str] = []
        self.internal_nets: set[str] = set()
        self._n04 = 0
        self._n08 = 0
        self._n32 = 0

    def _new04(self) -> str:
        self._n04 += 1
        return f"U_LC_04_{self._n04}"

    def _new08(self) -> str:
        self._n08 += 1
        return f"U_LC_08_{self._n08}"

    def _new32(self) -> str:
        self._n32 += 1
        return f"U_LC_32_{self._n32}"

    def _add(self, ref: str, part: str, pins: dict[str, str]) -> None:
        lines = [f"  - ref: {ref}", f"    part: {part}", "    pins:"]
        for k, v in pins.items():
            lines.append(f"      {k}: {v}")
        self.instances.append("\n".join(lines))

    def _fresh(self, prefix: str) -> str:
        n = f"net_lc_{prefix}_{self._n04 + self._n08 + self._n32}"
        self.internal_nets.add(n)
        return n

    def _not(self, src: str) -> str:
        if src == "pwr_vcc":
            return "pwr_gnd"
        if src == "pwr_gnd":
            return "pwr_vcc"
        out = self._fresh("n")
        self._add(
            self._new04(),
            "74HC04",
            {"A": src, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )
        return out

    def _and(self, a: str, b: str) -> str:
        if a == "pwr_gnd" or b == "pwr_gnd":
            return "pwr_gnd"
        if a == "pwr_vcc":
            return b
        if b == "pwr_vcc":
            return a
        out = self._fresh("a")
        self._add(
            self._new08(),
            "74HC08",
            {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )
        return out

    def _and3(self, a: str, b: str, c: str) -> str:
        return self._and(self._and(a, b), c)

    def _or(self, a: str, b: str) -> str:
        if a == "pwr_gnd":
            return b
        if b == "pwr_gnd":
            return a
        out = self._fresh("o")
        self._add(
            self._new32(),
            "74HC32",
            {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )
        return out

    def _or3(self, a: str, b: str, c: str) -> str:
        return self._or(self._or(a, b), c)

    def build(self) -> str:
        bus_en0 = "net_bus_en0"
        bus_en1 = "net_bus_en1"
        c5 = "net_ctrl5"
        c4 = "net_ctrl4"
        c3 = "net_ctrl3"
        c2 = "net_ctrl2"
        c1 = "net_ctrl1"
        z_prev = "net_z_prev"

        local_en = self._and(self._not(bus_en1), self._not(bus_en0))
        self._add(
            "U_LC_LOCAL_BUF",
            "74HC08",
            {"A": local_en, "B": local_en, "Y": "net_local_en", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

        halt = self._and(local_en, c1)
        self._add(
            "U_LC_HALT_BUF",
            "74HC08",
            {"A": halt, "B": halt, "Y": "net_halt", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )
        not_halt = self._not(halt)

        jmp = self._and3(local_en, c5, self._not(c4))
        beq = self._and3(local_en, self._not(c5), c4)
        bne = self._and3(local_en, c5, c4)
        normal = self._and3(local_en, self._not(c5), self._not(c4))

        branch_taken = self._or3(jmp, self._and(beq, z_prev), self._and(bne, self._not(z_prev)))
        pc_load = self._and(branch_taken, not_halt)
        self._add(
            "U_LC_LOAD_BUF",
            "74HC08",
            {"A": pc_load, "B": pc_load, "Y": "net_pc_load", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

        not_load = self._not(pc_load)
        normal_inc = self._and(normal, c2)
        beq_skip = self._and(beq, self._not(z_prev))
        bne_skip = self._and(bne, z_prev)
        pc_count = self._and(
            not_halt,
            self._and(not_load, self._or3(normal_inc, beq_skip, bne_skip)),
        )
        self._add(
            "U_LC_COUNT_BUF",
            "74HC08",
            {"A": pc_count, "B": pc_count, "Y": "net_pc_count_en", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

        flg_we = self._and(self._and(local_en, c3), not_halt)
        self._add(
            "U_LC_FLG_BUF",
            "74HC08",
            {"A": flg_we, "B": flg_we, "Y": "net_flg_we", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

        normal_hold = self._and(normal, self._not(c2))
        self._add(
            "U_LC_HOLD_BUF",
            "74HC08",
            {"A": normal_hold, "B": normal_hold, "Y": "net_pc_hold", "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

        nets = [
            "  - name: net_bus_en0",
            "    width: 1",
            "  - name: net_bus_en1",
            "    width: 1",
        ]
        for i in range(6):
            nets += [f"  - name: net_ctrl{i}", "    width: 1"]
        nets += [
            "  - name: net_z_prev",
            "    width: 1",
            "  - name: net_local_en",
            "    width: 1",
            "  - name: net_halt",
            "    width: 1",
            "  - name: net_flg_we",
            "    width: 1",
            "  - name: net_pc_load",
            "    width: 1",
            "  - name: net_pc_count_en",
            "    width: 1",
            "  - name: net_pc_hold",
            "    width: 1",
            "  - name: pwr_vcc",
            "    width: 1",
            "  - name: pwr_gnd",
            "    width: 1",
        ]
        for n in sorted(self.internal_nets):
            nets += [f"  - name: {n}", "    width: 1"]

        return (
            "version: 1\nblock: local_ctrl\ninstances:\n"
            + "\n".join(self.instances)
            + "\nnets:\n"
            + "\n".join(nets)
            + "\n"
        )


def main() -> None:
    OUT.write_text(NetlistGen().build(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
