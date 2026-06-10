# Verilog simulator (archived)

This tree was the **active** Plover simulation stack before **hwsim** (electrical netlist + timing). It remains runnable from this directory.

## Requirements

- [Icarus Verilog](http://iverilog.icarus.com/) (`iverilog`, `vvp`)
- Python 3.10+ (microasm, sim-runner)
- Node.js 18+ (web UI)

## Quick start

From **`archive/verilog-sim/`**:

```bash
make test
make rom
python3 tools/microasm.py lib/inc_r1.micro -o sim
```

### Web UI (two terminals)

```bash
# Terminal A
cd sim-runner && pip install -r requirements.txt && uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Terminal B
cd web && npm install && npm run dev
```

Open http://127.0.0.1:5173 — API proxied to port 8000.

### CI workflow

The original GitHub Actions workflow is preserved at `.github/workflows/sim.yml` (not run from repo root after archive).

## Layout

| Path | Role |
|------|------|
| `rtl/` | Verilog models |
| `sim/` | Testbenches, ROM hex |
| `lib/` | Example `.micro` programs |
| `tools/` | `microasm.py`, `pack_rom.py` |
| `sim-runner/` | FastAPI → Icarus |
| `web/` | React simulator UI |
| `docs/hardware/microcode-spec.md` | 16-bit control word spec |

## See also

- [../../docs/simulation/hw-sim.md](../../docs/simulation/hw-sim.md) — current electrical simulator
- [../../hwsim/](../../hwsim/) — `python -m hwsim run --all`
