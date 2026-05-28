# Web UI (`web`)

React + Vite front end for the Plover simulator. Talks to [sim-runner](../sim-runner/) during development.

## Requirements

- Node.js 18+

## Development

Terminal 1 (API):

```bash
cd ..
make sim-server
```

Terminal 2 (UI):

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite proxies `/api` and `/health` to port 8000 ([vite.config.ts](vite.config.ts)).

## Tabs

| Tab | Function |
|-----|----------|
| ALU Lab | POST `/api/alu` — try operands and `alu_sel` |
| Core | POST `/api/core/run` — run core with assembled ROM |
| Microcode | POST `/api/assemble` — edit `.micro` text, assemble, optional run |

## Build

```bash
npm run build
```

Output: `dist/` (gitignored).

## See also

- [../README.md](../README.md) — WSL setup  
- [../sim-runner/README.md](../sim-runner/README.md)  
