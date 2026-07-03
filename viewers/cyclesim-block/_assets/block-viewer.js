(function () {
  "use strict";

  const data = typeof MANIFEST !== "undefined" ? MANIFEST : null;
  if (!data) {
    document.body.innerHTML = "<p>No manifest embedded.</p>";
    return;
  }

  const netByName = Object.fromEntries(data.nets.map((n) => [n.name, n]));
  let scale = 1;
  let highlightNet = null;
  let highlightRef = null;

  const el = {
    title: document.getElementById("block-title"),
    desc: document.getElementById("block-desc"),
    summary: document.getElementById("summary"),
    search: document.getElementById("search"),
    wrap: document.getElementById("wrap"),
    stage: document.getElementById("stage"),
    inspectorEmpty: document.getElementById("inspector-empty"),
    inspectorBody: document.getElementById("inspector-body"),
    zoomLabel: document.getElementById("zoom-label"),
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function applyScale() {
    el.stage.style.transform = "scale(" + scale + ")";
    el.zoomLabel.textContent = Math.round(scale * 100) + "%";
  }

  function clearHighlight() {
    document.querySelectorAll(".net.highlight, .symbol.highlight").forEach((n) => {
      n.classList.remove("highlight");
    });
  }

  function highlightNetName(net) {
    clearHighlight();
    highlightNet = net;
    highlightRef = null;
    document.querySelectorAll('.net[data-net="' + CSS.escape(net) + '"]').forEach((g) => {
      g.classList.add("highlight");
    });
    showNetInspector(net);
  }

  function highlightRefName(ref) {
    clearHighlight();
    highlightRef = ref;
    highlightNet = null;
    document.querySelectorAll('.symbol[data-ref="' + CSS.escape(ref) + '"]').forEach((g) => {
      g.classList.add("highlight");
    });
    showRefInspector(ref);
  }

  function showNetInspector(netName) {
    const net = netByName[netName];
    if (!net) return;
    el.inspectorEmpty.hidden = true;
    el.inspectorBody.hidden = false;
    const probes =
      net.probes && net.probes.length
        ? " · probes: " + net.probes.join(", ")
        : "";
    const port = net.is_port ? " · port" : "";
    const items = net.connections
      .map(
        (c) =>
          "<li>" +
          escapeHtml(c.ref + "." + c.pin) +
          " (" +
          escapeHtml(c.dir) +
          ")</li>"
      )
      .join("");
    el.inspectorBody.innerHTML =
      '<div class="insp-title">' +
      escapeHtml(netName) +
      "</div>" +
      '<div class="insp-meta">width ' +
      net.width +
      port +
      probes +
      (net.conflict ? " · multi-drive" : "") +
      "</div>" +
      "<ul class=\"insp-list\">" +
      items +
      "</ul>";
  }

  function showRefInspector(ref) {
    const inst = data.instances[ref];
    if (!inst) return;
    el.inspectorEmpty.hidden = true;
    el.inspectorBody.hidden = false;
    const unit = inst.unit ? "<div class=\"insp-meta\">" + escapeHtml(inst.unit.label) + "</div>" : "";
    const pins = Object.entries(inst.pins)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(
        ([pin, net]) =>
          "<li>" + escapeHtml(pin) + " → " + escapeHtml(net) + "</li>"
      )
      .join("");
    el.inspectorBody.innerHTML =
      '<div class="insp-title">' +
      escapeHtml(ref) +
      "</div>" +
      '<div class="insp-meta">' +
      escapeHtml(inst.part) +
      "</div>" +
      unit +
      "<ul class=\"insp-list\">" +
      pins +
      "</ul>";
  }

  function flashNet(net) {
    highlightNetName(net);
    const hub = document.querySelector('.net-hub[data-net="' + CSS.escape(net) + '"]');
    if (hub) {
      const g = hub.closest(".net");
      if (g) {
        g.classList.add("flash");
        setTimeout(() => g.classList.remove("flash"), 1200);
      }
      hub.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
    }
  }

  function renderHeader() {
    el.title.textContent = data.block;
    el.desc.textContent = data.description || "";
    const s = data.summary;
    el.summary.innerHTML =
      "<span><strong>" +
      s.instance_count +
      "</strong> symbols</span>" +
      "<span><strong>" +
      s.net_count +
      "</strong> nets</span>";
  }

  function bindSchematic() {
    el.stage.querySelectorAll(".wire-hit, .net-hub, .net-label").forEach((node) => {
      node.addEventListener("click", (e) => {
        e.stopPropagation();
        const net = node.getAttribute("data-net");
        if (net) highlightNetName(net);
      });
    });
    el.stage.querySelectorAll(".symbol").forEach((sym) => {
      sym.addEventListener("click", (e) => {
        e.stopPropagation();
        const ref = sym.getAttribute("data-ref");
        if (ref) highlightRefName(ref);
      });
    });
    el.stage.querySelectorAll(".global-label").forEach((lbl) => {
      lbl.addEventListener("click", (e) => {
        e.stopPropagation();
        const net = lbl.getAttribute("data-net");
        if (net) highlightNetName(net);
      });
    });
  }

  el.search.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const q = el.search.value.trim().toLowerCase();
    if (!q) return;
    const net = data.nets.find((n) => n.name.toLowerCase().includes(q));
    if (net) {
      flashNet(net.name);
      return;
    }
    const ref = Object.keys(data.instances).find((r) => r.toLowerCase().includes(q));
    if (ref) highlightRefName(ref);
  });

  document.getElementById("btn-zin").addEventListener("click", () => {
    scale *= 1.15;
    applyScale();
  });
  document.getElementById("btn-zout").addEventListener("click", () => {
    scale /= 1.15;
    applyScale();
  });
  document.getElementById("btn-reset").addEventListener("click", () => {
    scale = 1;
    applyScale();
  });
  document.getElementById("btn-fit").addEventListener("click", () => {
    const svg = el.stage.querySelector("svg");
    if (!svg || !data.schematic) return;
    const pad = 24;
    const sx = (el.wrap.clientWidth - pad) / data.schematic.width;
    const sy = (el.wrap.clientHeight - pad) / data.schematic.height;
    scale = Math.min(sx, sy, 1.5);
    applyScale();
  });

  el.wrap.addEventListener(
    "wheel",
    (e) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        scale *= e.deltaY < 0 ? 1.1 : 1 / 1.1;
        applyScale();
      }
    },
    { passive: false }
  );

  renderHeader();
  bindSchematic();
  document.getElementById("btn-fit").click();
})();
