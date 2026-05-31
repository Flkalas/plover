# Sim runner (FastAPI + Icarus)

HTTP API that compiles and runs Plover RTL via **Icarus Verilog** (`iverilog` / `vvp`). Used by the [web UI](../web/).

## Requirements

- Python 3.10+
- Icarus Verilog on `PATH`

```bash
sudo apt install iverilog   # WSL / Debian
```

## Setup

```bash
cd sim-runner
pip install -r requirements.txt
```

Or from repo root:

```bash
make sim-server
```

Server: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{ "status", "iverilog" }` |
| POST | `/api/alu` | Body: `{ "a", "b", "alu_sel" }` → `{ "y", "cout", "zero" }` |
| POST | `/api/core/run` | Body: `{ "cycles", "rom_low?", "rom_high?" }` → registers, PC, halt |
| POST | `/api/assemble` | Body: `{ "source" }` → hex words |

## Implementation

- [main.py](main.py) — FastAPI app, temp build dir, invokes `iverilog` from repo root  
- ROM files written to `sim/rom_*.hex` before core runs  

## See also

- [../web/README.md](../web/README.md) — Vite dev proxy to this service  
