"""Merge clock + rom_fetch + pc + local_ctrl + flg_latch + alu_decode + regfile + alu8."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _split(text: str) -> tuple[str, str]:
    _, rest = text.split("instances:", 1)
    inst, nets = rest.split("nets:", 1)
    return inst, nets


def merge(blocks: list[Path], block_name: str, out: Path) -> None:
    inst_parts: list[str] = []
    net_parts: list[str] = []
    for path in blocks:
        inst, nets = _split(path.read_text(encoding="utf-8"))
        inst_parts.append(inst)
        net_parts.append(nets)
    text = (
        f"version: 1\nblock: {block_name}\ninstances:"
        + "".join(inst_parts)
        + "nets:"
        + "".join(net_parts)
    )
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clock", action="store_true", help="Include clock.yaml")
    args = ap.parse_args()
    blocks_dir = ROOT / "hw" / "netlist" / "blocks"
    tail = [
        blocks_dir / "local_ctrl.yaml",
        blocks_dir / "flg_latch.yaml",
        blocks_dir / "alu_decode.yaml",
        blocks_dir / "regfile_halt.yaml",
        blocks_dir / "alu8.yaml",
    ]
    head = [blocks_dir / "rom_fetch.yaml", blocks_dir / "pc.yaml"]
    body = head + tail
    if args.clock:
        body = [blocks_dir / "clock.yaml", *body]
        merge(body, "cpu_datapath_p3_clock", blocks_dir / "cpu_datapath_p3_clock.yaml")
    merge(body, "cpu_datapath_p3", blocks_dir / "cpu_datapath_p3.yaml")


if __name__ == "__main__":
    main()
