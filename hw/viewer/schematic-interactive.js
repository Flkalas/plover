/**
 * Plover schematic SVG: drag chips, net hubs, individual wire bends.
 */
(function () {
  'use strict';

  const DIM_OPACITY = '0.1';
  const HI_OPACITY = '1';
  const HI_WIDTH = '2.4';
  const PWR = new Set(['pwr_vcc', 'pwr_gnd']);
  const ROUTE_STUB = 32;

  function svgRoot(host) {
    return host.querySelector('svg') || host;
  }

  function parsePoints(pts) {
    return pts
      .trim()
      .split(/\s+/)
      .map((p) => {
        const [x, y] = p.split(',');
        return { x: parseFloat(x), y: parseFloat(y) };
      });
  }

  function formatPoints(arr) {
    return arr.map((p) => p.x.toFixed(1) + ',' + p.y.toFixed(1)).join(' ');
  }

  function pinSide(pin) {
    return pin && pin.getAttribute('data-side') === 'right' ? 'right' : 'left';
  }

  /** Left pins exit left; right pins exit right (avoid routing through chip). */
  function routeOrtho(x1, y1, x2, y2, side) {
    const ex = side === 'left' ? x1 - ROUTE_STUB : x1 + ROUTE_STUB;
    return [
      { x: x1, y: y1 },
      { x: ex, y: y1 },
      { x: ex, y: y2 },
      { x: x2, y: y2 },
    ];
  }

  function routeToRail(px, py, railY, side) {
    const ex = side === 'left' ? px - ROUTE_STUB : px + ROUTE_STUB;
    return [
      { x: px, y: py },
      { x: ex, y: py },
      { x: ex, y: railY },
    ];
  }

  function pinCenter(svg, pinEl) {
    const pt = svg.createSVGPoint();
    const ctm = pinEl.getScreenCTM();
    const root = svg.getScreenCTM();
    if (!ctm || !root) {
      return { x: parseFloat(pinEl.getAttribute('cx')), y: parseFloat(pinEl.getAttribute('cy')) };
    }
    pt.x = parseFloat(pinEl.getAttribute('cx'));
    pt.y = parseFloat(pinEl.getAttribute('cy'));
    const s = pt.matrixTransform(ctm);
    const local = svg.createSVGPoint();
    local.x = s.x;
    local.y = s.y;
    return local.matrixTransform(root.inverse());
  }

  function clientToSvg(svg, e) {
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  }

  function allPins(svg) {
    return [...svg.querySelectorAll('circle.pin[data-net]')];
  }

  function wireSeg(svg, net, pkg) {
    return svg.querySelector(
      '.wire-seg[data-net="' + net + '"][data-pkg="' + pkg + '"]'
    );
  }

  function wiresForNet(svg, net) {
    return [...svg.querySelectorAll('.wire-seg[data-net="' + net + '"]')];
  }

  function setWirePoints(svg, net, pkg, pointsStr) {
    const seg = wireSeg(svg, net, pkg);
    const hit = svg.querySelector(
      '.wire-hit[data-net="' + net + '"][data-pkg="' + pkg + '"]'
    );
    if (seg) seg.setAttribute('points', pointsStr);
    if (hit) hit.setAttribute('points', pointsStr);
    syncHandlesForWire(svg, net, pkg);
  }

  function handleLayer(svg) {
    let g = svg.querySelector('#wire-handles');
    if (!g) {
      g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('id', 'wire-handles');
      svg.appendChild(g);
    }
    return g;
  }

  function syncHandlesForWire(svg, net, pkg) {
    const layer = handleLayer(svg);
    layer.querySelectorAll(
      '.wire-handle[data-net="' + net + '"][data-pkg="' + pkg + '"]'
    ).forEach((h) => h.remove());

    const seg = wireSeg(svg, net, pkg);
    if (!seg) return;

    const pts = parsePoints(seg.getAttribute('points') || '');
    const indices = [];
    for (let i = 1; i < pts.length - 1; i++) indices.push(i);
    if (pts.length <= 3 && PWR.has(net) && indices.length === 0) indices.push(1);

    indices.forEach((i) => {
      const p =
        pts.length === 2 && PWR.has(net)
          ? { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 }
          : pts[i];
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('class', 'wire-handle');
      c.setAttribute('data-net', net);
      c.setAttribute('data-pkg', pkg);
      c.setAttribute('data-idx', String(i));
      c.setAttribute('cx', p.x.toFixed(1));
      c.setAttribute('cy', p.y.toFixed(1));
      c.setAttribute('r', '5');
      layer.appendChild(c);
    });
  }

  function rebuildAllHandles(svg) {
    const layer = handleLayer(svg);
    layer.innerHTML = '';
    svg.querySelectorAll('.wire-seg').forEach((seg) => {
      syncHandlesForWire(
        svg,
        seg.getAttribute('data-net'),
        seg.getAttribute('data-pkg')
      );
    });
  }

  function setHandlesVisible(svg, net, pkg, on) {
    const sel =
      pkg != null
        ? '.wire-handle[data-net="' + net + '"][data-pkg="' + pkg + '"]'
        : '.wire-handle[data-net="' + net + '"]';
    svg.querySelectorAll(sel).forEach((h) => {
      if (on) h.classList.add('on');
      else h.classList.remove('on');
    });
  }

  function hideAllHandles(svg) {
    svg.querySelectorAll('.wire-handle').forEach((h) => h.classList.remove('on'));
  }

  function resetWireRoute(svg, net, pkg) {
    const seg = wireSeg(svg, net, pkg);
    if (seg) seg.removeAttribute('data-custom');
  }

  function disableTextSelection(svg) {
    svg.querySelectorAll('text').forEach((t) => {
      t.setAttribute('pointer-events', 'none');
    });
    svg.addEventListener('selectstart', (e) => e.preventDefault());
    svg.addEventListener('dragstart', (e) => e.preventDefault());
    const root = svg.parentElement;
    if (root) {
      root.style.userSelect = 'none';
      root.style.webkitUserSelect = 'none';
    }
  }

  function hubForNet(svg, net) {
    return svg.querySelector('.net-hub[data-net="' + net + '"]');
  }

  function labelForNet(svg, net) {
    return svg.querySelector('.net-label[data-net="' + net + '"]');
  }

  function netsForChip(svg, chipId) {
    const nets = new Set();
    svg.querySelectorAll('.chip[data-id="' + chipId + '"] circle.pin[data-net]').forEach((p) => {
      nets.add(p.getAttribute('data-net'));
    });
    return nets;
  }

  function hubCentroid(svg, net) {
    const pins = allPins(svg).filter((p) => p.getAttribute('data-net') === net);
    if (!pins.length) return null;
    let sx = 0;
    let sy = 0;
    pins.forEach((p) => {
      const c = pinCenter(svg, p);
      sx += c.x;
      sy += c.y;
    });
    return { x: sx / pins.length, y: sy / pins.length };
  }

  function hubCoords(svg, net, repositionAuto) {
    const hubEl = hubForNet(svg, net);
    if (!hubEl) return null;
    if (hubEl.getAttribute('data-manual') === '1' && !repositionAuto) {
      return {
        x: parseFloat(hubEl.getAttribute('cx')),
        y: parseFloat(hubEl.getAttribute('cy')),
      };
    }
    const pos = hubCentroid(svg, net);
    if (!pos) return null;
    hubEl.setAttribute('cx', pos.x.toFixed(1));
    hubEl.setAttribute('cy', pos.y.toFixed(1));
    return pos;
  }

  function pinForWire(svg, net, pkg) {
    return svg.querySelector(
      '.chip[data-id="' + pkg + '"] circle.pin[data-net="' + net + '"]'
    );
  }

  function routeOneWire(svg, net, pkg, hub) {
    const pin = pinForWire(svg, net, pkg);
    if (!pin) return;
    const c = pinCenter(svg, pin);
    const side = pinSide(pin);
    const seg = wireSeg(svg, net, pkg);
    if (!seg) return;

    let pts;
    if (seg.getAttribute('data-custom') === '1') {
      pts = parsePoints(seg.getAttribute('points'));
      if (pts.length < 2) pts = routeOrtho(c.x, c.y, hub.x, hub.y, side);
      else {
        pts[0] = c;
        pts[pts.length - 1] = hub;
      }
    } else {
      pts = routeOrtho(c.x, c.y, hub.x, hub.y, side);
    }
    setWirePoints(svg, net, pkg, formatPoints(pts));
  }

  function routeOnePowerWire(svg, net, pkg, railY) {
    const pin = pinForWire(svg, net, pkg);
    if (!pin) return;
    const c = pinCenter(svg, pin);
    const side = pinSide(pin);
    const seg = wireSeg(svg, net, pkg);
    if (!seg) return;

    let pts;
    if (seg.getAttribute('data-custom') === '1') {
      pts = parsePoints(seg.getAttribute('points'));
      if (pts.length < 2) pts = routeToRail(c.x, c.y, railY, side);
      else {
        pts[0] = c;
        pts[pts.length - 1] = { x: pts[pts.length - 1].x, y: railY };
      }
    } else {
      pts = routeToRail(c.x, c.y, railY, side);
    }
    setWirePoints(svg, net, pkg, formatPoints(pts));
  }

  function routeWiresToHub(svg, net, hub) {
    const lbl = labelForNet(svg, net);
    if (lbl) {
      lbl.setAttribute('x', hub.x.toFixed(1));
      lbl.setAttribute('y', (hub.y - 6).toFixed(1));
    }
    wiresForNet(svg, net).forEach((w) => {
      routeOneWire(svg, net, w.getAttribute('data-pkg'), hub);
    });
  }

  function refreshNet(svg, net) {
    if (PWR.has(net)) {
      const railY = parseFloat(svg.getAttribute('data-rail-vcc-y') || '14');
      const railGnd = parseFloat(svg.getAttribute('data-rail-gnd-y') || '0');
      const y = net === 'pwr_vcc' ? railY : railGnd;
      wiresForNet(svg, net).forEach((w) => {
        routeOnePowerWire(svg, net, w.getAttribute('data-pkg'), y);
      });
      return;
    }

    const hub = hubCoords(svg, net, false);
    if (!hub) return;
    routeWiresToHub(svg, net, hub);
  }

  function clearHighlight(svg) {
    svg.querySelectorAll('.wire-seg').forEach((w) => {
      w.classList.remove('highlight');
      w.style.opacity = '';
      w.style.strokeWidth = '';
    });
    svg.querySelectorAll('.net-hub').forEach((h) => {
      h.classList.remove('highlight');
      h.style.opacity = '';
    });
    svg.querySelectorAll('.net-label').forEach((l) => {
      l.style.opacity = '';
      l.style.fontWeight = '';
    });
    svg.querySelectorAll('.chip').forEach((c) => c.classList.remove('highlight'));
  }

  function dimOthers(svg, activeNets, activeChip) {
    svg.querySelectorAll('.wire-seg').forEach((w) => {
      const n = w.getAttribute('data-net');
      const pkg = w.getAttribute('data-pkg');
      const on = activeNets.has(n) || (activeChip && pkg === activeChip);
      if (!on) {
        w.style.opacity = DIM_OPACITY;
      } else {
        w.style.opacity = HI_OPACITY;
        w.style.strokeWidth = HI_WIDTH;
        w.classList.add('highlight');
      }
    });
    svg.querySelectorAll('.net-hub').forEach((h) => {
      const n = h.getAttribute('data-net');
      h.style.opacity = activeNets.has(n) ? HI_OPACITY : DIM_OPACITY;
      if (activeNets.has(n)) h.classList.add('highlight');
    });
    svg.querySelectorAll('.net-label').forEach((l) => {
      const n = l.getAttribute('data-net');
      if (activeNets.has(n)) {
        l.style.opacity = '1';
        l.style.fontWeight = '600';
      } else {
        l.style.opacity = DIM_OPACITY;
      }
    });
  }

  const CLICK_THRESH = 6;

  function pickTarget(svg, el) {
    if (!el || !el.closest) return null;
    const handle = el.closest('.wire-handle');
    if (handle) {
      return {
        type: 'handle',
        el: handle,
        net: handle.getAttribute('data-net'),
        pkg: handle.getAttribute('data-pkg'),
        idx: parseInt(handle.getAttribute('data-idx'), 10),
      };
    }
    const chip = el.closest('.chip');
    if (chip) {
      return { type: 'chip', el: chip, id: chip.getAttribute('data-id') };
    }
    const hub = el.closest('.net-hub');
    if (hub) {
      return { type: 'hub', el: hub, net: hub.getAttribute('data-net') };
    }
    const wire = el.closest('.wire-hit') || el.closest('.wire-seg');
    if (wire) {
      return {
        type: 'wire',
        el: wire,
        net: wire.getAttribute('data-net'),
        pkg: wire.getAttribute('data-pkg'),
      };
    }
    if (el === svg || (el.tagName === 'rect' && el.getAttribute('fill') === '#0d1117')) {
      return { type: 'background', el: svg };
    }
    return null;
  }

  function targetsMatch(a, b) {
    if (!a || !b || a.type !== b.type) return false;
    if (a.type === 'chip') return a.id === b.id;
    if (a.type === 'hub') return a.net === b.net;
    if (a.type === 'wire') return a.net === b.net && a.pkg === b.pkg;
    if (a.type === 'handle') {
      return a.net === b.net && a.pkg === b.pkg && a.idx === b.idx;
    }
    return false;
  }

  function setupSelection(svg) {
    let selection = null;

    function clearSelectionVisual() {
      svg.querySelectorAll('.selected').forEach((n) => n.classList.remove('selected'));
      hideAllHandles(svg);
    }

    function applySelectionVisual(sel) {
      clearSelectionVisual();
      if (!sel || sel.type === 'background') return;
      if (sel.type === 'chip') {
        sel.el.classList.add('selected');
        netsForChip(svg, sel.id).forEach((n) => setHandlesVisible(svg, n, null, true));
      } else if (sel.type === 'hub') {
        sel.el.classList.add('selected');
        setHandlesVisible(svg, sel.net, null, true);
      } else if (sel.type === 'wire') {
        const seg = wireSeg(svg, sel.net, sel.pkg) || sel.el;
        seg.classList.add('selected');
        setHandlesVisible(svg, sel.net, sel.pkg, true);
      } else if (sel.type === 'handle') {
        sel.el.classList.add('selected');
        const seg = wireSeg(svg, sel.net, sel.pkg);
        if (seg) seg.classList.add('selected');
        setHandlesVisible(svg, sel.net, sel.pkg, true);
      }
    }

    function updateStatus(sel) {
      const status = document.getElementById('sel-status');
      if (!status) return;
      if (!sel || sel.type === 'background') {
        status.textContent = '(nothing selected) — click chip, hub, wire, or bend';
        return;
      }
      if (sel.type === 'chip') {
        status.textContent = 'Selected: chip ' + sel.id + ' — drag to move';
      } else if (sel.type === 'hub') {
        status.textContent = 'Selected: net hub ' + sel.net + ' — drag to move';
      } else if (sel.type === 'wire') {
        status.textContent =
          'Selected: wire ' + sel.net + ' @ ' + sel.pkg + ' — drag wire to move';
      } else if (sel.type === 'handle') {
        status.textContent =
          'Selected: bend on ' + sel.net + ' @ ' + sel.pkg + ' — drag to move';
      }
    }

    function setSelection(sel) {
      selection = sel && sel.type !== 'background' ? sel : null;
      applySelectionVisual(selection);
      updateStatus(selection);
    }

    function getSelection() {
      return selection;
    }

    function isSelected(sel) {
      return selection && sel && targetsMatch(selection, sel);
    }

    return { setSelection, getSelection, isSelected, clearSelectionVisual };
  }

  function setupInteraction(svg, selApi) {
    let dragChip = null;
    let dragHub = null;
    let dragHandle = null;
    let dragWireBody = false;
    let dragNet = null;
    let dragPkg = null;
    let dragIdx = -1;
    let dragStart = null;
    let wireBodyBase = null;
    let baseTransform = { x: 0, y: 0 };
    let pointer = null;
    let dragActive = false;
    let requireMatch = false;

    function parseTranslate(g) {
      const t = g.getAttribute('transform') || '';
      const m = t.match(/translate\(\s*([-\d.]+)(?:[\s,]+([-\d.]+))?\s*\)/);
      if (!m) return { x: 0, y: 0 };
      return { x: parseFloat(m[1]), y: parseFloat(m[2] || 0) };
    }

    function beginDrag(target) {
      dragActive = true;
      if (target.type === 'chip') {
        dragChip = target.el;
        dragChip.style.cursor = 'grabbing';
        baseTransform = parseTranslate(dragChip);
      } else if (target.type === 'hub') {
        dragHub = target.el;
        dragNet = target.net;
        dragHub.setAttribute('data-manual', '1');
      } else if (target.type === 'wireBody') {
        dragWireBody = true;
        dragNet = target.net;
        dragPkg = target.pkg;
        const seg = wireSeg(svg, dragNet, dragPkg);
        if (seg) {
          seg.setAttribute('data-custom', '1');
          wireBodyBase = parsePoints(seg.getAttribute('points') || '');
        }
      } else if (target.type === 'handle') {
        dragHandle = target.el;
        dragNet = target.net;
        dragPkg = target.pkg;
        dragIdx = target.idx;
        const seg = wireSeg(svg, dragNet, dragPkg);
        if (seg) seg.setAttribute('data-custom', '1');
      }
    }

    function dragTargetForWire(target, svgPt) {
      syncHandlesForWire(svg, target.net, target.pkg);
      const seg = wireSeg(svg, target.net, target.pkg);
      if (!seg) return { type: 'wireBody', net: target.net, pkg: target.pkg };
      const pts = parsePoints(seg.getAttribute('points') || '');
      if (pts.length > 2 && svgPt) {
        let best = 1;
        let bd = Infinity;
        for (let i = 1; i < pts.length - 1; i++) {
          const d = (pts[i].x - svgPt.x) ** 2 + (pts[i].y - svgPt.y) ** 2;
          if (d < bd) {
            bd = d;
            best = i;
          }
        }
        if (bd < 28 * 28) {
          const el = svg.querySelector(
            '.wire-handle[data-net="' +
              target.net +
              '"][data-pkg="' +
              target.pkg +
              '"][data-idx="' +
              best +
              '"]'
          );
          if (el) {
            return {
              type: 'handle',
              el: el,
              net: target.net,
              pkg: target.pkg,
              idx: best,
            };
          }
        }
      }
      return { type: 'wireBody', net: target.net, pkg: target.pkg };
    }

    function endDrag() {
      if (dragChip) dragChip.style.cursor = 'grab';
      dragChip = null;
      dragHub = null;
      dragHandle = null;
      dragWireBody = false;
      dragNet = null;
      dragPkg = null;
      dragIdx = -1;
      dragStart = null;
      wireBodyBase = null;
      dragActive = false;
      requireMatch = false;
    }

    function onPointerDown(e) {
      if (e.button !== 0) return;
      const target = pickTarget(svg, e.target);
      if (!target) return;

      if (target.type === 'background') {
        e.preventDefault();
        pointer = {
          target,
          clientX: e.clientX,
          clientY: e.clientY,
          didDrag: false,
        };
        return;
      }

      e.preventDefault();
      e.stopPropagation();

      const sel = selApi.getSelection();
      requireMatch = !!(
        sel &&
        sel.type === 'chip' &&
        target.type === 'chip' &&
        !targetsMatch(sel, target)
      );

      pointer = {
        target,
        clientX: e.clientX,
        clientY: e.clientY,
        didDrag: false,
      };
      dragStart = clientToSvg(svg, e);

      if (target.type === 'wire') {
        beginDrag(dragTargetForWire(target, dragStart));
      } else if (target.type === 'handle') {
        beginDrag(target);
      } else if (target.type === 'hub' || target.type === 'chip') {
        if (!sel || targetsMatch(sel, target)) beginDrag(target);
      }
    }

    function pointerDist(e) {
      if (!pointer) return 0;
      const dx = e.clientX - pointer.clientX;
      const dy = e.clientY - pointer.clientY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    function onPointerMove(e) {
      if (!pointer) return;

      if (!dragActive && pointerDist(e) >= CLICK_THRESH) {
        pointer.didDrag = true;
        const sel = selApi.getSelection();
        if (requireMatch && sel && !targetsMatch(sel, pointer.target)) {
          return;
        }
        if (!sel || !targetsMatch(sel, pointer.target)) {
          selApi.setSelection(pointer.target);
        }
        const t = pointer.target;
        if (t.type === 'wire') {
          beginDrag(dragTargetForWire(t, clientToSvg(svg, e)));
        } else {
          beginDrag(t);
        }
      }

      if (!dragActive || !dragStart) return;
      const cur = clientToSvg(svg, e);

      if (dragChip) {
        const dx = cur.x - dragStart.x;
        const dy = cur.y - dragStart.y;
        dragChip.setAttribute(
          'transform',
          'translate(' +
            (baseTransform.x + dx).toFixed(1) +
            ',' +
            (baseTransform.y + dy).toFixed(1) +
            ')'
        );
        netsForChip(svg, dragChip.getAttribute('data-id')).forEach((n) =>
          refreshNet(svg, n)
        );
        return;
      }

      if (dragHub && dragNet) {
        dragHub.setAttribute('cx', cur.x.toFixed(1));
        dragHub.setAttribute('cy', cur.y.toFixed(1));
        routeWiresToHub(svg, dragNet, { x: cur.x, y: cur.y });
        return;
      }

      if (dragWireBody && dragNet && dragPkg && wireBodyBase) {
        const dx = cur.x - dragStart.x;
        const dy = cur.y - dragStart.y;
        const pts = wireBodyBase.map((p) => ({ x: p.x + dx, y: p.y + dy }));
        setWirePoints(svg, dragNet, dragPkg, formatPoints(pts));
        return;
      }

      if (dragHandle && dragNet && dragPkg && dragIdx >= 0) {
        const seg = wireSeg(svg, dragNet, dragPkg);
        if (!seg) return;
        let pts = parsePoints(seg.getAttribute('points'));
        if (pts.length === 2 && PWR.has(dragNet) && dragIdx === 1) {
          pts = [
            pts[0],
            { x: cur.x, y: pts[0].y },
            { x: cur.x, y: pts[1].y },
            pts[1],
          ];
        } else if (dragIdx >= 1 && dragIdx < pts.length - 1) {
          pts[dragIdx] = { x: cur.x, y: cur.y };
        } else {
          return;
        }
        const s = formatPoints(pts);
        seg.setAttribute('points', s);
        seg.setAttribute('data-custom', '1');
        const hit = svg.querySelector(
          '.wire-hit[data-net="' + dragNet + '"][data-pkg="' + dragPkg + '"]'
        );
        if (hit) hit.setAttribute('points', s);
        syncHandlesForWire(svg, dragNet, dragPkg);
        const nh = svg.querySelector(
          '.wire-handle[data-net="' +
            dragNet +
            '"][data-pkg="' +
            dragPkg +
            '"][data-idx="' +
            dragIdx +
            '"]'
        );
        if (nh) {
          dragHandle = nh;
          selApi.setSelection({
            type: 'handle',
            el: nh,
            net: dragNet,
            pkg: dragPkg,
            idx: dragIdx,
          });
          dragHandle.setAttribute('cx', cur.x.toFixed(1));
          dragHandle.setAttribute('cy', cur.y.toFixed(1));
        }
      }
    }

    function onPointerUp() {
      if (!pointer) return;
      if (!pointer.didDrag && !dragActive) {
        if (pointer.target.type === 'background') {
          selApi.setSelection(null);
        } else {
          selApi.setSelection(pointer.target);
        }
      } else if (dragActive && pointer.target) {
        selApi.setSelection(pointer.target);
      }
      endDrag();
      pointer = null;
    }

    svg.querySelectorAll('.chip').forEach((c) => {
      c.style.cursor = 'grab';
    });
    svg.querySelectorAll('.net-hub').forEach((hub) => {
      hub.style.cursor = 'move';
      const r = parseFloat(hub.getAttribute('r') || '3');
      if (r < 6) hub.setAttribute('r', '6');
      hub.addEventListener('dblclick', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const net = hub.getAttribute('data-net');
        hub.removeAttribute('data-manual');
        wiresForNet(svg, net).forEach((w) =>
          resetWireRoute(svg, net, w.getAttribute('data-pkg'))
        );
        refreshNet(svg, net);
      });
    });

    handleLayer(svg).addEventListener('dblclick', (e) => {
      const t = e.target;
      if (!t.classList.contains('wire-handle')) return;
      e.preventDefault();
      e.stopPropagation();
      const net = t.getAttribute('data-net');
      const pkg = t.getAttribute('data-pkg');
      resetWireRoute(svg, net, pkg);
      if (PWR.has(net)) {
        const railY =
          net === 'pwr_vcc'
            ? parseFloat(svg.getAttribute('data-rail-vcc-y') || '14')
            : parseFloat(svg.getAttribute('data-rail-gnd-y') || '0');
        routeOnePowerWire(svg, net, pkg, railY);
      } else {
        const hub = hubCoords(svg, net, false);
        if (hub) routeOneWire(svg, net, pkg, hub);
      }
    });

    svg.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        selApi.setSelection(null);
        endDrag();
        pointer = null;
      }
    });
  }

  function setupHover(svg, selApi) {
    svg.querySelectorAll('.chip').forEach((chip) => {
      chip.addEventListener('mouseenter', () => {
        clearHighlight(svg);
        chip.classList.add('highlight');
        const nets = netsForChip(svg, chip.getAttribute('data-id'));
        dimOthers(svg, nets, chip.getAttribute('data-id'));
        nets.forEach((n) => setHandlesVisible(svg, n, null, true));
      });
      chip.addEventListener('mouseleave', () => {
        clearHighlight(svg);
        const sel = selApi.getSelection();
        if (!sel || sel.type !== 'chip' || sel.id !== chip.getAttribute('data-id')) {
          hideAllHandles(svg);
          if (sel) selApi.setSelection(sel);
        }
      });
    });

    function wireHover(wire, net, pkg) {
      wire.addEventListener('mouseenter', () => {
        clearHighlight(svg);
        dimOthers(svg, new Set([net]), null);
        setHandlesVisible(svg, net, pkg, true);
      });
      wire.addEventListener('mouseleave', () => {
        clearHighlight(svg);
        const sel = selApi.getSelection();
        const keep =
          sel &&
          ((sel.type === 'wire' && sel.net === net && sel.pkg === pkg) ||
            (sel.type === 'handle' && sel.net === net && sel.pkg === pkg) ||
            (sel.type === 'hub' && sel.net === net));
        if (!keep) setHandlesVisible(svg, net, pkg, false);
      });
    }

    svg.querySelectorAll('.wire-hit').forEach((wire) => {
      wire.style.cursor = 'move';
      wireHover(wire, wire.getAttribute('data-net'), wire.getAttribute('data-pkg'));
    });

    svg.querySelectorAll('.wire-seg').forEach((wire) => {
      if (!svg.querySelector('.wire-hit[data-net="' + wire.getAttribute('data-net') + '"]')) {
        wireHover(wire, wire.getAttribute('data-net'), wire.getAttribute('data-pkg'));
      }
    });

    svg.querySelectorAll('.net-hub').forEach((hub) => {
      hub.addEventListener('mouseenter', () => {
        clearHighlight(svg);
        const net = hub.getAttribute('data-net');
        dimOthers(svg, new Set([net]), null);
        setHandlesVisible(svg, net, null, true);
      });
      hub.addEventListener('mouseleave', () => {
        clearHighlight(svg);
        const sel = selApi.getSelection();
        if (!sel || (sel.type === 'hub' && sel.net !== net)) {
          if (!sel || sel.type !== 'chip') hideAllHandles(svg);
        }
        if (sel) selApi.setSelection(sel);
      });
    });
  }

  window.initSchematicInteractive = function (host) {
    const svg = svgRoot(host);
    if (!svg || svg.getAttribute('data-interactive') === '1') return;
    svg.setAttribute('data-interactive', '1');
    disableTextSelection(svg);
    rebuildAllHandles(svg);
    const selApi = setupSelection(svg);
    setupInteraction(svg, selApi);
    setupHover(svg, selApi);
    selApi.setSelection(null);
  };
})();
