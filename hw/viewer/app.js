(function () {
  const summary = document.getElementById("summary");
  const checksBody = document.querySelector("#checks tbody");
  const svgHost = document.getElementById("svg-host");
  const canvas = document.getElementById("waves");
  const legend = document.getElementById("wave-legend");
  const ctx = canvas.getContext("2d");

  let report = null;
  let waves = null;

  document.getElementById("file-report").addEventListener("change", (e) =>
    readJson(e.target.files[0], (d) => {
      report = d;
      renderSummary();
      renderChecks();
    })
  );
  document.getElementById("file-waves").addEventListener("change", (e) =>
    readJson(e.target.files[0], (d) => {
      waves = d;
      renderWaves();
    })
  );
  document.getElementById("file-svg").addEventListener("change", (e) =>
    readText(e.target.files[0], (t) => {
      svgHost.innerHTML = t;
    })
  );

  function readJson(file, cb) {
    if (!file) return;
    const r = new FileReader();
    r.onload = () => cb(JSON.parse(r.result));
    r.readAsText(file);
  }

  function readText(file, cb) {
    if (!file) return;
    const r = new FileReader();
    r.onload = () => cb(r.result);
    r.readAsText(file);
  }

  function renderSummary() {
    if (!report) return;
    const cls = report.passed ? "pass" : "fail";
    summary.innerHTML =
      `<h2 class="${cls}">${report.passed ? "PASS" : "FAIL"}: ${report.test}</h2>` +
      `<p>Block <code>${report.block}</code> · timing ${report.timing_mode}</p>` +
      (report.errors && report.errors.length
        ? `<ul>${report.errors.map((e) => `<li>${e}</li>`).join("")}</ul>`
        : "");
  }

  function renderChecks() {
    checksBody.innerHTML = "";
    (report.checks || []).forEach((c) => {
      const tr = document.createElement("tr");
      const detail = Object.entries(c)
        .filter(([k]) => k !== "type" && k !== "passed")
        .map(([k, v]) => `${k}=${v}`)
        .join(", ");
      tr.innerHTML = `<td>${c.type}</td><td class="${c.passed ? "pass" : "fail"}">${
        c.passed ? "PASS" : "FAIL"
      }</td><td>${detail}</td>`;
      checksBody.appendChild(tr);
    });
  }

  function renderWaves() {
    if (!waves) return;
    const nets = Object.keys(waves);
    if (!nets.length) return;
    let tMax = 0;
    nets.forEach((n) => {
      const s = waves[n];
      if (s.length) tMax = Math.max(tMax, s[s.length - 1].t);
    });
    tMax = Math.max(tMax, 1);
    const rowH = Math.min(40, Math.floor(280 / nets.length));
    canvas.height = 40 + nets.length * rowH;
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const colors = ["#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7"];
    nets.forEach((net, i) => {
      const y0 = 30 + i * rowH;
      ctx.fillStyle = "#8b949e";
      ctx.font = "12px system-ui";
      ctx.fillText(net, 4, y0 + rowH / 2 + 4);
      const samples = waves[net];
      let prevT = 0;
      let prevV = 0;
      samples.forEach((s, j) => {
        const x0 = 120 + (prevT / tMax) * (canvas.width - 140);
        const x1 = 120 + (s.t / tMax) * (canvas.width - 140);
        const high = prevV === "1" || prevV === 1;
        ctx.strokeStyle = colors[i % colors.length];
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x0, y0 + (high ? 6 : rowH - 8));
        ctx.lineTo(x1, y0 + (high ? 6 : rowH - 8));
        ctx.stroke();
        prevT = s.t;
        prevV = s.v;
      });
    });
    legend.textContent = `Time span: 0–${tMax} ns · ${nets.length} signals`;
  }
})();
