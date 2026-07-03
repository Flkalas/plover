(function () {
  "use strict";

  const data = typeof MANIFEST !== "undefined" ? MANIFEST : null;
  if (!data) {
    document.body.innerHTML = "<p>No manifest embedded.</p>";
    return;
  }

  const netByName = Object.fromEntries(data.nets.map((n) => [n.name, n]));
  let selectedNet = null;
  let filterMode = "all";
  let searchQuery = "";

  const el = {
    title: document.getElementById("block-title"),
    desc: document.getElementById("block-desc"),
    summary: document.getElementById("summary"),
    search: document.getElementById("search"),
    netGroups: document.getElementById("net-groups"),
    instanceSummary: document.getElementById("instance-summary"),
    tracePanel: document.getElementById("trace-panel"),
    traceTitle: document.getElementById("trace-title"),
    traceCards: document.getElementById("trace-cards"),
    panelNets: document.getElementById("panel-nets"),
    panelInstances: document.getElementById("panel-instances"),
    tabNets: document.getElementById("tab-nets"),
    tabInstances: document.getElementById("tab-instances"),
  };

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatConn(c) {
    const cls = c.dir === "drive" ? "conn-drive" : "conn-load";
    const arrow = c.dir === "drive" ? "→" : "←";
    return (
      '<span class="conn ' +
      cls +
      '" title="' +
      escapeHtml(c.dir) +
      '">' +
      escapeHtml(c.ref + "." + c.pin) +
      " " +
      arrow +
      "</span>"
    );
  }

  function netMatchesFilter(net) {
    if (filterMode === "ports" && !net.is_port) return false;
    if (filterMode === "probes" && (!net.probes || net.probes.length === 0))
      return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    if (net.name.toLowerCase().includes(q)) return true;
    if ((net.probes || []).some((p) => p.toLowerCase().includes(q))) return true;
    return net.connections.some(
      (c) =>
        c.ref.toLowerCase().includes(q) || c.pin.toLowerCase().includes(q)
    );
  }

  function renderHeader() {
    el.title.textContent = data.block;
    el.desc.textContent = data.description || "";
    const s = data.summary;
    el.summary.innerHTML =
      "<span><strong>" +
      s.instance_count +
      "</strong> instances</span>" +
      "<span><strong>" +
      s.net_count +
      "</strong> nets</span>" +
      "<span><strong>" +
      s.unit_count +
      "</strong> units</span>";
  }

  function renderNetRow(net) {
    const probes = (net.probes || [])
      .map((p) => '<span class="badge badge-probe">' + escapeHtml(p) + "</span>")
      .join("");
    const conflict = net.conflict
      ? '<span class="badge badge-conflict">multi-drive</span>'
      : "";
    const conns = net.connections.map(formatConn).join("");
    const classes = ["net-row"];
    if (net.is_port) classes.push("is-port");
    if (selectedNet === net.name) classes.push("selected");

    return (
      "<tr class=\"" +
      classes.join(" ") +
      '" data-net="' +
      escapeHtml(net.name) +
      '">' +
      '<td class="net-name">' +
      escapeHtml(net.name) +
      conflict +
      "</td>" +
      "<td>" +
      net.width +
      "</td>" +
      "<td>" +
      (probes || "—") +
      "</td>" +
      "<td>" +
      (conns || '<span class="empty">—</span>') +
      "</td>" +
      "</tr>"
    );
  }

  function renderNets() {
    let html = "";
    for (const group of data.groups) {
      const rows = group.nets
        .map((name) => netByName[name])
        .filter(Boolean)
        .filter(netMatchesFilter)
        .map(renderNetRow)
        .join("");
      if (!rows) continue;
      html +=
        '<section class="group">' +
        '<h3 class="group-header" data-group="' +
        escapeHtml(group.id) +
        '">' +
        '<span class="chevron">▼</span> ' +
        escapeHtml(group.label) +
        " (" +
        group.nets.filter((n) => netByName[n] && netMatchesFilter(netByName[n]))
          .length +
        ")" +
        "</h3>" +
        '<div class="net-table-wrap"><table>' +
        "<thead><tr><th>Net</th><th>Width</th><th>Probes</th><th>Connections</th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table></div></section>";
    }
    el.netGroups.innerHTML =
      html || '<p class="empty">No nets match the current filter.</p>';

    el.netGroups.querySelectorAll(".net-row").forEach((row) => {
      row.addEventListener("click", () => selectNet(row.dataset.net));
    });
    el.netGroups.querySelectorAll(".group-header").forEach((hdr) => {
      hdr.addEventListener("click", () => {
        hdr.parentElement.classList.toggle("collapsed");
        const ch = hdr.querySelector(".chevron");
        ch.textContent = hdr.parentElement.classList.contains("collapsed")
          ? "▶"
          : "▼";
      });
    });
  }

  function renderInstances() {
    const counts = data.summary.part_counts;
    const rows = Object.entries(counts)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(
        ([part, n]) =>
          "<tr><td>" + escapeHtml(part) + "</td><td>" + n + "</td></tr>"
      )
      .join("");
    el.instanceSummary.innerHTML =
      "<table><thead><tr><th>Part</th><th>Count</th></tr></thead><tbody>" +
      rows +
      "</tbody></table>";
  }

  function selectNet(name) {
    selectedNet = name;
    renderNets();
    const net = netByName[name];
    if (!net) {
      el.tracePanel.hidden = true;
      return;
    }
    el.tracePanel.hidden = false;
    el.traceTitle.textContent = "Net trace: " + name;
    el.traceCards.innerHTML = net.connections
      .map((c) => {
        const inst = data.instances[c.ref];
        const unit = inst && inst.unit ? inst.unit.label : "";
        return (
          '<div class="trace-card">' +
          '<div class="ref">' +
          escapeHtml(c.ref) +
          "</div>" +
          '<div class="part">' +
          escapeHtml(inst ? inst.part : "?") +
          "</div>" +
          '<div class="pin-highlight">' +
          escapeHtml(c.pin) +
          " (" +
          escapeHtml(c.dir) +
          ")</div>" +
          (unit
            ? '<div class="unit-label">' + escapeHtml(unit) + "</div>"
            : "") +
          "</div>"
        );
      })
      .join("");
  }

  el.search.addEventListener("input", () => {
    searchQuery = el.search.value.trim();
    renderNets();
  });

  document.querySelectorAll('input[name="filter"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      filterMode = radio.value;
      renderNets();
    });
  });

  el.tabNets.addEventListener("click", () => {
    el.tabNets.classList.add("active");
    el.tabInstances.classList.remove("active");
    el.panelNets.hidden = false;
    el.panelInstances.hidden = true;
  });

  el.tabInstances.addEventListener("click", () => {
    el.tabInstances.classList.add("active");
    el.tabNets.classList.remove("active");
    el.panelInstances.hidden = false;
    el.panelNets.hidden = true;
  });

  renderHeader();
  renderNets();
  renderInstances();
})();
