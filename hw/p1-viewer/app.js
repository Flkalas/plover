(function () {
  const state = {
    meta: null,
    cycles: [],
    result: null,
    timeNs: 0,
  };

  const el = {
    aluOp: document.getElementById("alu-op"),
    srcReg: document.getElementById("src-reg"),
    dstReg: document.getElementById("dst-reg"),
    busEn: document.getElementById("bus-en"),
    cycleCount: document.getElementById("cycle-count"),
    status: document.getElementById("status"),
    regDisplay: document.getElementById("reg-display"),
    aluY: document.getElementById("alu-y"),
    cmpN: document.getElementById("cmp-n"),
    violations: document.getElementById("violations"),
    checksBody: document.querySelector("#checks tbody"),
    svgHost: document.getElementById("svg-host"),
    timeSlider: document.getElementById("time-slider"),
    timeLabel: document.getElementById("time-label"),
    waveLegend: document.getElementById("wave-legend"),
    zoomWindow: document.getElementById("zoom-window"),
    groupWaves: document.getElementById("group-waves"),
  };

  const dpCanvas = document.getElementById("datapath");
  const dpCtx = dpCanvas.getContext("2d");
  const waveCanvas = document.getElementById("waves");
  const waveCtx = waveCanvas.getContext("2d");

  document.getElementById("btn-queue").addEventListener("click", queueCycle);
  document.getElementById("btn-clear").addEventListener("click", () => {
    state.cycles = [];
    updateCycleCount();
  });
  document.getElementById("btn-simulate").addEventListener("click", () => simulate(false));
  document.getElementById("btn-step").addEventListener("click", () => {
    queueCycle();
    simulate(false);
    state.cycles = [];
    updateCycleCount();
  });
  document.getElementById("btn-preset-demo").addEventListener("click", () => simulate(true, "clock_add_demo"));
  el.timeSlider.addEventListener("input", () => {
    state.timeNs = Number(el.timeSlider.value);
    el.timeLabel.textContent = `${state.timeNs} ns`;
    renderDatapath();
  });
  el.zoomWindow.addEventListener("change", renderWaves);
  el.groupWaves.addEventListener("change", renderWaves);

  init();

  async function init() {
    try {
      const res = await fetch("/api/meta");
      state.meta = await res.json();
      fillOpcodes(state.meta.opcodes);
      const svg = await fetch("/api/wiring-filtered.svg");
      el.svgHost.innerHTML = await svg.text();
      setStatus("Ready — queue cycles or run preset");
    } catch (e) {
      setStatus("Start server: python -m hwsim serve", true);
    }
  }

  function fillOpcodes(opcodes) {
    el.aluOp.innerHTML = "";
    opcodes.forEach((op) => {
      const opt = document.createElement("option");
      opt.value = op.id;
      opt.textContent = `${op.id} (${op.hex}) ${op.name}`;
      el.aluOp.appendChild(opt);
    });
    el.aluOp.value = "1";
  }

  function queueCycle() {
    state.cycles.push({
      alu_op: Number(el.aluOp.value),
      src_reg: Number(el.srcReg.value),
      dst_reg: Number(el.dstReg.value),
      bus_en: Number(el.busEn.value),
    });
    updateCycleCount();
  }

  function updateCycleCount() {
    el.cycleCount.textContent = String(state.cycles.length);
  }

  async function simulate(preset, presetId) {
    setStatus("Running…");
    const body = preset
      ? { preset: presetId || "clock_add_demo", timing: "max" }
      : { preset: "custom", cycles: state.cycles, timing: "max" };
    if (!preset && !body.cycles.length) {
      setStatus("Queue at least one cycle", true);
      return;
    }
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      state.result = data;
      state.timeNs = Math.max(0, data.duration_ns - 200);
      el.timeSlider.max = String(data.duration_ns);
      el.timeSlider.value = String(state.timeNs);
      el.timeLabel.textContent = `${state.timeNs} ns`;
      renderAll();
      setStatus(data.passed ? "PASS" : "FAIL", !data.passed);
    } catch (e) {
      setStatus(String(e.message), true);
    }
  }

  function setStatus(msg, err) {
    el.status.textContent = msg;
    el.status.className = "status " + (err ? "fail" : "pass");
  }

  function renderAll() {
    renderOutputs();
    renderChecks();
    renderDatapath();
    renderWaves();
  }

  function renderOutputs() {
    const r = state.result;
    if (!r) return;
    const dst = lastCycleDst();
    el.regDisplay.innerHTML = "";
    ["R0", "R1", "R2", "R3"].forEach((name, i) => {
      const val = r.registers[name] ?? 0;
      const div = document.createElement("div");
      div.className = "reg-cell" + (dst === i ? " active" : "");
      div.innerHTML = `<h3>${name}</h3><div class="hex">0x${val.toString(16).toUpperCase().padStart(2, "0")}</div>`;
      el.regDisplay.appendChild(div);
    });
    el.aluY.textContent = "0x" + (r.alu_y ?? 0).toString(16).toUpperCase().padStart(2, "0");
    el.cmpN.textContent = r.cw_decode?.net_cmp_n ?? "—";
    el.violations.innerHTML = (r.violations || []).map((v) => `<div>${v}</div>`).join("");
  }

  function lastCycleDst() {
    if (!state.result) return -1;
    const waves = state.result.waves || {};
    for (let b = 1; b >= 0; b--) {
      const rows = waves[`net_dst_reg${b}`];
      if (rows && rows.length) {
        const v = sampleAt(rows, state.timeNs);
        if (b === 1) return (v << 1) | sampleAt(waves["net_dst_reg0"], state.timeNs);
      }
    }
    return Number(el.dstReg.value);
  }

  function renderChecks() {
    el.checksBody.innerHTML = "";
    (state.result?.checks || []).forEach((c) => {
      const tr = document.createElement("tr");
      const detail = Object.entries(c)
        .filter(([k]) => k !== "type" && k !== "passed")
        .map(([k, v]) => `${k}=${v}`)
        .join(", ");
      tr.innerHTML = `<td>${c.type}</td><td class="${c.passed ? "pass" : "fail"}">${c.passed ? "PASS" : "FAIL"}</td><td>${detail}</td>`;
      el.checksBody.appendChild(tr);
    });
  }

  function renderDatapath() {
    const w = dpCanvas.width;
    const h = dpCanvas.height;
    dpCtx.fillStyle = "#0d1117";
    dpCtx.fillRect(0, 0, w, h);
    const dst = lastCycleDst();
    const src = sampleRegSelect("src");
    const cmp = sampleAt(state.result?.waves?.net_cmp_n, state.timeNs);
    const isCmp = cmp === 0;

    drawBox(20, 40, 100, 50, "CW stub", "#8b949e");
    drawBox(140, 40, 90, 50, "Decode", "#a371f7");
    drawBox(260, 20, 80, 45, "A MUX", src === 0 ? "#58a6ff" : "#30363d");
    drawBox(260, 75, 80, 45, "B MUX", dst >= 0 ? "#58a6ff" : "#30363d");
    drawBox(370, 40, 70, 50, "ALU", "#d29922");
    drawBox(470, 30, 150, 70, "Regfile", "#3fb950");

    arrow(120, 65, 140, 65);
    arrow(230, 65, 260, 42);
    arrow(230, 65, 260, 98);
    arrow(340, 65, 370, 65);
    arrow(440, 65, 470, 65);

    ["R0", "R1", "R2", "R3"].forEach((name, i) => {
      const x = 490 + i * 32;
      const active = i === dst;
      dpCtx.fillStyle = active ? "#238636" : "#21262d";
      dpCtx.strokeStyle = active ? "#3fb950" : "#30363d";
      dpCtx.fillRect(x, 50, 28, 36);
      dpCtx.strokeRect(x, 50, 28, 36);
      dpCtx.fillStyle = "#e6edf3";
      dpCtx.font = "11px system-ui";
      dpCtx.fillText(name, x + 4, 72);
    });

    dpCtx.setLineDash(isCmp ? [4, 4] : []);
    dpCtx.strokeStyle = isCmp ? "#f85149" : "#3fb950";
    dpCtx.beginPath();
    dpCtx.moveTo(545, 86);
    dpCtx.lineTo(545, 120);
    dpCtx.lineTo(400, 120);
    dpCtx.lineTo(400, 90);
    dpCtx.stroke();
    dpCtx.setLineDash([]);

    dpCtx.fillStyle = "#8b949e";
    dpCtx.font = "11px system-ui";
    dpCtx.fillText(isCmp ? "CP masked (CMP)" : "Y → D(dst) latch", 410, 115);
    dpCtx.fillText(`t = ${state.timeNs} ns`, 20, h - 12);
  }

  function sampleRegSelect(kind) {
    const waves = state.result?.waves || {};
    const b = sampleAt(waves[`net_${kind}_reg1`], state.timeNs);
    const a = sampleAt(waves[`net_${kind}_reg0`], state.timeNs);
    return (b << 1) | a;
  }

  function drawBox(x, y, bw, bh, label, color) {
    dpCtx.fillStyle = "#161b22";
    dpCtx.strokeStyle = color;
    dpCtx.lineWidth = 2;
    dpCtx.fillRect(x, y, bw, bh);
    dpCtx.strokeRect(x, y, bw, bh);
    dpCtx.fillStyle = "#e6edf3";
    dpCtx.font = "12px system-ui";
    dpCtx.fillText(label, x + 8, y + bh / 2 + 4);
  }

  function arrow(x1, y1, x2, y2) {
    dpCtx.strokeStyle = "#484f58";
    dpCtx.lineWidth = 1.5;
    dpCtx.beginPath();
    dpCtx.moveTo(x1, y1);
    dpCtx.lineTo(x2, y2);
    dpCtx.stroke();
  }

  function netGroup(name) {
    if (name.includes("alu_op") || name.includes("src_reg") || name.includes("dst_reg") || name.includes("bus_en")) return "CW";
    if (name.startsWith("net_a") || name.startsWith("net_b")) return "MUX";
    if (name.includes("_q")) return "Reg";
    if (name.startsWith("net_y") || name.includes("sub_en") || name.includes("cmp")) return "ALU";
    if (name.includes("clk")) return "Clock";
    return "Other";
  }

  function renderWaves() {
    const waves = state.result?.waves;
    if (!waves) return;
    let nets = Object.keys(waves);
    if (el.groupWaves.checked) {
      const order = ["CW", "MUX", "Reg", "ALU", "Clock", "Other"];
      nets.sort((a, b) => order.indexOf(netGroup(a)) - order.indexOf(netGroup(b)) || a.localeCompare(b));
    }
    const tMax = state.result.duration_ns;
    const win = Number(el.zoomWindow.value) || tMax;
    const tMin = Math.max(0, tMax - win);

    const rowH = Math.min(22, Math.floor(360 / Math.max(nets.length, 1)));
    waveCanvas.height = 30 + nets.length * rowH;
    waveCtx.fillStyle = "#0d1117";
    waveCtx.fillRect(0, 0, waveCanvas.width, waveCanvas.height);
    const colors = { CW: "#58a6ff", MUX: "#a371f7", Reg: "#3fb950", ALU: "#d29922", Clock: "#f85149", Other: "#8b949e" };

    nets.forEach((net, i) => {
      const y0 = 24 + i * rowH;
      const grp = netGroup(net);
      waveCtx.fillStyle = "#8b949e";
      waveCtx.font = "10px ui-monospace, monospace";
      waveCtx.fillText(net.replace("net_", ""), 4, y0 + rowH / 2 + 3);
      const samples = waves[net];
      let prevT = tMin;
      let prevV = sampleAt(samples, tMin);
      samples.forEach((s) => {
        if (s.t < tMin) {
          prevT = s.t;
          prevV = s.v === "1" ? 1 : 0;
          return;
        }
        if (s.t > tMax) return;
        const x0 = 130 + ((prevT - tMin) / win) * (waveCanvas.width - 150);
        const x1 = 130 + ((s.t - tMin) / win) * (waveCanvas.width - 150);
        const high = prevV === 1;
        waveCtx.strokeStyle = colors[grp] || "#8b949e";
        waveCtx.lineWidth = s.t === state.timeNs ? 3 : 1.5;
        waveCtx.beginPath();
        waveCtx.moveTo(x0, y0 + (high ? 4 : rowH - 6));
        waveCtx.lineTo(x1, y0 + (high ? 4 : rowH - 6));
        waveCtx.stroke();
        prevT = s.t;
        prevV = s.v === "1" ? 1 : 0;
      });
    });
    const cursorX = 130 + ((state.timeNs - tMin) / win) * (waveCanvas.width - 150);
    waveCtx.strokeStyle = "#f85149";
    waveCtx.lineWidth = 1;
    waveCtx.beginPath();
    waveCtx.moveTo(cursorX, 0);
    waveCtx.lineTo(cursorX, waveCanvas.height);
    waveCtx.stroke();
    el.waveLegend.textContent = `Window ${tMin}–${tMax} ns · ${nets.length} signals · cursor ${state.timeNs} ns`;
  }

  function sampleAt(rows, t) {
    if (!rows || !rows.length) return 0;
    let v = 0;
    for (const row of rows) {
      if (row.t > t) break;
      v = row.v === "1" ? 1 : 0;
    }
    return v;
  }
})();
