import { useCallback, useEffect, useState } from "react";

const ALU_OPS: Record<string, number> = {
  NOP: 0,
  ADD: 1,
  SUB: 2,
  AND: 3,
  OR: 4,
  XOR: 5,
  NOT: 6,
  PASS_A: 7,
  PASS_B: 8,
  INC: 9,
  DEC: 10,
  CMP: 11,
};

const DEFAULT_MICRO = `; Increment R1 then halt
@0000
alu INC | reg R1<=ALU | bus ALU_TO_REG | branch INC
alu NOP | branch HALT
`;

type Tab = "alu" | "core" | "micro";

export default function App() {
  const [tab, setTab] = useState<Tab>("alu");
  const [health, setHealth] = useState<string>("…");
  const [a, setA] = useState(0x12);
  const [b, setB] = useState(0x34);
  const [aluSel, setAluSel] = useState("ADD");
  const [aluOut, setAluOut] = useState<string>("");
  const [cycles, setCycles] = useState(16);
  const [coreOut, setCoreOut] = useState<string>("");
  const [regs, setRegs] = useState<Record<string, number> | null>(null);
  const [microSrc, setMicroSrc] = useState(DEFAULT_MICRO);
  const [asmOut, setAsmOut] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((j: { iverilog: string }) =>
        setHealth(j.iverilog === "missing" ? "iverilog 없음" : "iverilog OK")
      )
      .catch(() => setHealth("sim-runner 미연결"));
  }, []);

  const runAlu = useCallback(async () => {
    setBusy(true);
    setErr("");
    try {
      const r = await fetch("/api/alu", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          a,
          b,
          alu_sel: ALU_OPS[aluSel] ?? 0,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail ?? r.statusText);
      setAluOut(
        `Y = 0x${j.y.toString(16).padStart(2, "0")}  C = ${j.cout}  Z = ${j.zero}`
      );
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }, [a, b, aluSel]);

  const runCore = useCallback(async () => {
    setBusy(true);
    setErr("");
    try {
      let rom_low: string | undefined;
      let rom_high: string | undefined;
      if (asmOut) {
        const lines = asmOut.split("\n").filter(Boolean);
        const lows: string[] = [];
        const highs: string[] = [];
        for (const line of lines) {
          const m = line.match(/@([0-9a-f]+)\s+([0-9a-f]+)/i);
          if (m) {
            const cw = parseInt(m[2], 16);
            lows.push((cw & 0xff).toString(16).padStart(2, "0"));
            highs.push(((cw >> 8) & 0xff).toString(16).padStart(2, "0"));
          }
        }
        if (lows.length) {
          rom_low = lows.join("\n") + "\n";
          rom_high = highs.join("\n") + "\n";
        }
      }
      const r = await fetch("/api/core/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cycles, rom_low, rom_high }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail ?? r.statusText);
      setRegs(j.registers);
      setCoreOut(
        `PC = 0x${j.pc.toString(16).padStart(4, "0")}  halted = ${j.halted}\n${j.log ?? ""}`
      );
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }, [cycles, asmOut]);

  const assemble = useCallback(async () => {
    setBusy(true);
    setErr("");
    try {
      const r = await fetch("/api/assemble", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: microSrc }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail ?? r.statusText);
      setAsmOut(
        j.words.map((w: { addr: number; cw: string }) => `@${w.addr.toString(16).padStart(4, "0")}  ${w.cw}`).join("\n")
      );
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }, [microSrc]);

  return (
    <div className="app">
      <header>
        <h1>Plover Simulator</h1>
        <p>
          8-bit VLIW-RISC · Verilog (Icarus) ·{" "}
          <span className={health.includes("OK") ? "status-ok" : ""}>
            {health}
          </span>
        </p>
      </header>

      <nav className="tabs">
        {(
          [
            ["alu", "ALU Lab"],
            ["core", "Core"],
            ["micro", "Microcode"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "active" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {err && <p className="error">{err}</p>}

      {tab === "alu" && (
        <section className="panel">
          <h2>ALU Lab (alu8)</h2>
          <div className="row">
            <label>
              A
              <input
                type="number"
                min={0}
                max={255}
                value={a}
                onChange={(e) => setA(Number(e.target.value))}
              />
            </label>
            <label>
              B
              <input
                type="number"
                min={0}
                max={255}
                value={b}
                onChange={(e) => setB(Number(e.target.value))}
              />
            </label>
            <label>
              alu_sel
              <select value={aluSel} onChange={(e) => setAluSel(e.target.value)}>
                {Object.keys(ALU_OPS).map((op) => (
                  <option key={op} value={op}>
                    {op}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="action" disabled={busy} onClick={runAlu}>
              Run ALU
            </button>
          </div>
          {aluOut && <div className="result">{aluOut}</div>}
        </section>
      )}

      {tab === "core" && (
        <section className="panel">
          <h2>Core (plover_core)</h2>
          <div className="row">
            <label>
              cycles
              <input
                type="number"
                min={1}
                max={1000}
                value={cycles}
                onChange={(e) => setCycles(Number(e.target.value))}
              />
            </label>
            <button type="button" className="action" disabled={busy} onClick={runCore}>
              Run Core
            </button>
          </div>
          {regs && (
            <div className="regs">
              {Object.entries(regs).map(([k, v]) => (
                <div key={k} className="reg">
                  <span>{k}</span>
                  {v.toString(16).padStart(2, "0").toUpperCase()}
                </div>
              ))}
            </div>
          )}
          {coreOut && <div className="result">{coreOut}</div>}
        </section>
      )}

      {tab === "micro" && (
        <section className="panel">
          <h2>Microcode</h2>
          <textarea value={microSrc} onChange={(e) => setMicroSrc(e.target.value)} />
          <div className="row">
            <button type="button" className="action" disabled={busy} onClick={assemble}>
              Assemble
            </button>
            <button
              type="button"
              className="action"
              disabled={busy || !asmOut}
              onClick={() => {
                setTab("core");
                void runCore();
              }}
            >
              Assemble &amp; Run Core
            </button>
          </div>
          {asmOut && <div className="result">{asmOut}</div>}
        </section>
      )}
    </div>
  );
}
