"""FastAPI backend: compile and run Plover RTL with Icarus Verilog."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
RTL_ALU = [
    ROOT / "rtl/alu/hc283_cascade.v",
    ROOT / "rtl/alu/hc153_mux4.v",
    ROOT / "rtl/alu/alu8.v",
]
RTL_CORE = RTL_ALU + [
    ROOT / "rtl/reg/hc574.v",
    ROOT / "rtl/reg/regfile.v",
    ROOT / "rtl/bus/databus.v",
    ROOT / "rtl/mem/control_rom.v",
    ROOT / "rtl/mem/sram256.v",
    ROOT / "rtl/cpu/plover_core.v",
]

app = FastAPI(title="Plover Sim Runner", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AluRequest(BaseModel):
    a: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)
    alu_sel: int = Field(ge=0, le=15)


class SimCoreRequest(BaseModel):
    cycles: int = Field(default=32, ge=1, le=10000)
    rom_low: str | None = None
    rom_high: str | None = None


def find_iverilog() -> str:
    for name in ("iverilog", "iverilog.exe"):
        p = shutil.which(name)
        if p:
            return p
    raise HTTPException(
        503,
        "iverilog not found. Install Icarus Verilog (apt install iverilog / choco install iverilog).",
    )


def run_cmd(cmd: list[str], cwd: Path) -> None:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise HTTPException(
            500,
            f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}",
        )


def parse_vcd_states(vcd_path: Path, signals: list[str]) -> list[dict[str, Any]]:
    """Minimal VCD parser for selected signal names at each #timestamp."""
    if not vcd_path.is_file():
        return []

    text = vcd_path.read_text(encoding="utf-8", errors="replace")
    id_to_name: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("$var"):
            parts = line.split()
            if len(parts) >= 5:
                id_to_name[parts[3]] = parts[4]

    name_to_id = {v: k for k, v in id_to_name.items() if v in signals}
    history: list[dict[str, Any]] = []
    cur: dict[str, int] = {}
    time_ps = 0

    for line in text.splitlines():
        if line.startswith("#"):
            if cur:
                history.append({"time": time_ps, **cur})
            time_ps = int(line[1:].strip())
            continue
        m = re.match(r"b([01]+) (\S+)", line)
        if m:
            vid, val = m.group(2), int(m.group(1), 2)
            for sig, sid in name_to_id.items():
                if sid == vid:
                    cur[sig] = val
            continue
        m = re.match(r"(\d+) (\S+)", line)
        if m and not line.startswith("$"):
            val, vid = int(m.group(1)), m.group(2)
            for sig, sid in name_to_id.items():
                if sid == vid:
                    cur[sig] = val

    return history


@app.get("/health")
def health() -> dict[str, str]:
    iverilog = shutil.which("iverilog") or shutil.which("iverilog.exe")
    return {"status": "ok", "iverilog": iverilog or "missing"}


@app.post("/api/alu")
def sim_alu(req: AluRequest) -> dict[str, Any]:
    find_iverilog()
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        tb = tdir / "tb_alu_api.v"
        tb.write_text(
            f"""
`timescale 1ns/1ps
module tb_alu_api;
    reg [7:0] a = 8'h{req.a:02x};
    reg [7:0] b = 8'h{req.b:02x};
    reg [3:0] alu_sel = 4'd{req.alu_sel};
    wire [7:0] y;
    wire cout, zero;
    alu8 dut(.a(a),.b(b),.alu_sel(alu_sel),.y(y),.cout(cout),.zero(zero));
    initial begin
        #1;
        $display("Y=%02x C=%b Z=%b", y, cout, zero);
        $finish;
    end
endmodule
""",
            encoding="utf-8",
        )
        sources = [str(p) for p in RTL_ALU] + [str(tb)]
        out = tdir / "sim.vvp"
        run_cmd([find_iverilog(), "-o", str(out), *sources], ROOT)
        r = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, capture_output=True, text=True
        )
        m = re.search(r"Y=([0-9a-fA-F]+)\s+C=([01])\s+Z=([01])", r.stdout)
        if not m:
            raise HTTPException(500, f"unexpected vvp output: {r.stdout} {r.stderr}")
        return {
            "y": int(m.group(1), 16),
            "cout": m.group(2) == "1",
            "zero": m.group(3) == "1",
        }


@app.post("/api/core/run")
def sim_core(req: SimCoreRequest) -> dict[str, Any]:
    find_iverilog()
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        sim_dir = tdir / "sim"
        sim_dir.mkdir()
        low = req.rom_low or (ROOT / "sim/rom_low.hex").read_text(encoding="utf-8")
        high = req.rom_high or (ROOT / "sim/rom_high.hex").read_text(encoding="utf-8")
        rom_target = ROOT / "sim"
        rom_target.mkdir(exist_ok=True)
        (rom_target / "rom_low.hex").write_text(low, encoding="utf-8")
        (rom_target / "rom_high.hex").write_text(high, encoding="utf-8")

        tb = tdir / "tb_core_api.v"
        tb.write_text(
            f"""
`timescale 1ns/1ps
`default_nettype none
module tb_core_api;
    reg clk=0, rst_n=0;
    always #5 clk=~clk;
    wire [15:0] pc;
    wire halted;
    wire [7:0] r0,r1,r2,r3,r4,r5,r6;
    plover_core dut(
        .clk(clk),.rst_n(rst_n),.pc(pc),.flag_c(),.flag_z(),.halted(halted),
        .probe_bus(),.probe_alu_y(),.probe_cw(),
        .probe_r0(r0),.probe_r1(r1),.probe_r2(r2),.probe_r3(r3),
        .probe_r4(r4),.probe_r5(r5),.probe_r6(r6)
    );
    initial begin
        $dumpfile("{tdir.as_posix()}/wave.vcd");
        $dumpvars(0, tb_core_api);
        rst_n=0; #20; rst_n=1;
        repeat ({req.cycles}) @(posedge clk);
        $display("PC=%04x HALT=%b R0=%02x R1=%02x R2=%02x R3=%02x R4=%02x R5=%02x R6=%02x",
            pc, halted, r0,r1,r2,r3,r4,r5,r6);
        $finish;
    end
endmodule
`default_nettype wire
""",
            encoding="utf-8",
        )

        inc = str(ROOT / "rtl/cpu")
        out = tdir / "sim.vvp"
        run_cmd(
            [find_iverilog(), "-I", inc, "-o", str(out)]
            + [str(p) for p in RTL_CORE]
            + [str(tb)],
            ROOT,
        )
        env = {**subprocess.os.environ}
        r = subprocess.run(
            ["vvp", str(out)], cwd=ROOT, capture_output=True, text=True, env=env
        )
        m = re.search(
            r"PC=([0-9a-fA-F]+)\s+HALT=([01])\s+R0=([0-9a-fA-F]+)\s+R1=([0-9a-fA-F]+)\s+"
            r"R2=([0-9a-fA-F]+)\s+R3=([0-9a-fA-F]+)\s+R4=([0-9a-fA-F]+)\s+"
            r"R5=([0-9a-fA-F]+)\s+R6=([0-9a-fA-F]+)",
            r.stdout,
        )
        if not m:
            raise HTTPException(500, f"vvp failed: {r.stdout}\n{r.stderr}")

        vcd = Path(tdir) / "wave.vcd"
        waves = parse_vcd_states(
            vcd,
            ["pc", "halted", "r0", "r1", "r5"],
        ) if vcd.is_file() else []

        return {
            "pc": int(m.group(1), 16),
            "halted": m.group(2) == "1",
            "registers": {
                "r0": int(m.group(3), 16),
                "r1": int(m.group(4), 16),
                "r2": int(m.group(5), 16),
                "r3": int(m.group(6), 16),
                "r4": int(m.group(7), 16),
                "r5": int(m.group(8), 16),
                "r6": int(m.group(9), 16),
            },
            "waves": waves[-64:],
            "log": r.stdout + r.stderr,
        }


@app.post("/api/assemble")
def assemble_endpoint(body: dict[str, str]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from microasm import assemble

    src = body.get("source", "")
    words = assemble(src)
    return {
        "words": [{"addr": a, "cw": f"{c:04x}"} for a, c in words],
        "rom_low": "\n".join(f"{(c & 0xFF):02x}" for _, c in sorted(words)),
        "rom_high": "\n".join(f"{(c >> 8) & 0xFF:02x}" for _, c in sorted(words)),
    }
