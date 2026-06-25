/**
 * Filter full ALU8 schematic to a gate-combination unit (gate pins + nets).
 */
(function () {
  'use strict';

  const DIM = '0.06';
  const CHIP_DIM = '0.14';
  const PWR = new Set(['pwr_vcc', 'pwr_gnd']);

  function gatePinKey(pkg, dip) {
    return pkg + ':' + dip;
  }

  function buildGatePinSet(scope) {
    const out = new Set();
    (scope.gate_pins || []).forEach((p) => {
      out.add(gatePinKey(p.pkg, String(p.dip)));
    });
    return out;
  }

  function pinInGateScope(pin, gatePins, nets) {
    const pkg = pin.getAttribute('data-pkg') || '';
    const dip = pin.getAttribute('data-dip') || '';
    if (gatePins.has(gatePinKey(pkg, dip))) return true;
    const net = pin.getAttribute('data-net') || '';
    const extras = (pin.getAttribute('data-nets') || '').trim().split(/\s+/).filter(Boolean);
    return nets.has(net) || extras.some((n) => nets.has(n));
  }

  function applyUnitScope(svg, scope) {
    if (!svg || !scope) return;
    const nets = new Set(scope.nets || []);
    const gatePins = buildGatePinSet(scope);

    svg.querySelectorAll('.chip, .wire-seg, .wire-hit, .net-hub, .net-label, .pin, .lbl-pin, .io-row, .io-hub').forEach((el) => {
      el.style.opacity = '';
      if (el.classList && el.classList.contains('wire-seg')) {
        el.setAttribute('stroke-width', '1.2');
      }
    });

    svg.querySelectorAll('.chip rect').forEach((rect) => {
      rect.style.opacity = CHIP_DIM;
    });
    svg.querySelectorAll('.chip text').forEach((txt) => {
      txt.style.opacity = '0.35';
    });

    svg.querySelectorAll('.pin').forEach((pin) => {
      const on = pinInGateScope(pin, gatePins, nets);
      pin.style.opacity = on ? '1' : DIM;
      const dip = pin.getAttribute('data-dip') || '';
      const chip = pin.closest('.chip');
      if (chip) {
        chip.querySelectorAll('.lbl-pin').forEach((lbl) => {
          if (lbl.textContent.trim() === dip) {
            lbl.style.opacity = on ? '0.9' : DIM;
          }
        });
      }
    });

    svg.querySelectorAll('.io-row, .io-hub').forEach((el) => {
      const net = el.getAttribute('data-net') || '';
      el.style.opacity = nets.has(net) ? '1' : DIM;
    });

    svg.querySelectorAll('#io-panel rect, #io-panel .io-section, #io-panel .io-title').forEach((el) => {
      el.style.opacity = '0.5';
    });

    svg.querySelectorAll('.wire-seg, .wire-hit').forEach((wire) => {
      const net = wire.getAttribute('data-net') || '';
      if (PWR.has(net)) {
        wire.style.opacity = '0.12';
        return;
      }
      const on = nets.has(net);
      wire.style.opacity = on ? '0.9' : DIM;
      if (wire.classList.contains('wire-seg')) {
        wire.setAttribute('stroke-width', on ? '2.2' : '1.2');
      }
    });

    svg.querySelectorAll('.net-hub').forEach((hub) => {
      const net = hub.getAttribute('data-net') || '';
      if (PWR.has(net)) {
        hub.style.opacity = '0.1';
        return;
      }
      hub.style.opacity = nets.has(net) ? '1' : DIM;
    });

    svg.querySelectorAll('.net-label').forEach((lbl) => {
      lbl.style.opacity = nets.has(lbl.getAttribute('data-net') || '') ? '0.85' : DIM;
    });
  }

  window.applyUnitScope = applyUnitScope;
})();
