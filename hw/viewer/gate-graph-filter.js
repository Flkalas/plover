/**
 * Highlight one gate unit on the full gate connectivity graph.
 */
(function () {
  'use strict';

  const DIM = '0.1';
  const WIRE_DIM = '0.08';

  function applyGateHighlight(svg, unit) {
    if (!svg || !unit) return;
    const nets = new Set(unit.nets || []);
    const relatedUnits = new Set([unit.id]);

    svg.querySelectorAll('.gate-node, .wire-seg, .wire-trunk, .io-net, .port, .net-hub, .net-junction, .port-fixed').forEach((el) => {
      el.style.opacity = '';
    });

    // Expand to gates that share a highlighted net
    svg.querySelectorAll('.port').forEach((p) => {
      const net = p.getAttribute('data-net') || '';
      const uid = p.getAttribute('data-unit') || '';
      if (nets.has(net)) relatedUnits.add(uid);
    });

    svg.querySelectorAll('.gate-node').forEach((g) => {
      const id = g.getAttribute('data-unit-id') || '';
      const on = relatedUnits.has(id);
      g.style.opacity = on ? '1' : DIM;
    });

    svg.querySelectorAll('.wire-seg, .wire-trunk').forEach((w) => {
      const net = w.getAttribute('data-net') || '';
      w.style.opacity = nets.has(net) ? '0.9' : WIRE_DIM;
      w.setAttribute('stroke-width', nets.has(net) ? '2.2' : w.getAttribute('data-base-sw') || '1.3');
    });

    svg.querySelectorAll('.net-hub, .net-junction').forEach((j) => {
      const net = j.getAttribute('data-net') || '';
      j.style.opacity = nets.has(net) ? '1' : WIRE_DIM;
    });

    svg.querySelectorAll('.io-net').forEach((io) => {
      const net = io.getAttribute('data-net') || '';
      io.style.opacity = nets.has(net) ? '1' : WIRE_DIM;
    });

    svg.querySelectorAll('.port').forEach((p) => {
      const net = p.getAttribute('data-net') || '';
      const uid = p.getAttribute('data-unit') || '';
      const on = nets.has(net) || uid === unit.id;
      p.style.opacity = on ? '1' : DIM;
    });
  }

  window.applyGateHighlight = applyGateHighlight;
})();
