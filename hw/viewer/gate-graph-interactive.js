/**
 * ALU8 gate connectivity graph: drag gates/nets, hover/click net highlight, pan/zoom.
 */
(function () {
  'use strict';

  const CLICK_THRESH = 4;
  const DIM = '0.1';
  const WIRE_DIM = '0.08';
  const HI_WIDTH = '2.4';

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

  function dedupePoints(arr) {
    if (!arr.length) return arr;
    const out = [arr[0]];
    for (let i = 1; i < arr.length; i++) {
      const a = out[out.length - 1];
      const b = arr[i];
      if (Math.abs(a.x - b.x) > 0.01 || Math.abs(a.y - b.y) > 0.01) out.push(b);
    }
    return out;
  }

  function clientToSvg(svg, e) {
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    return pt.matrixTransform(ctm.inverse());
  }

  function parseTranslate(g) {
    const t = g.getAttribute('transform') || '';
    const m = t.match(/translate\(\s*([-\d.]+)(?:[\s,]+([-\d.]+))?\s*\)/);
    if (!m) return { x: 0, y: 0 };
    return { x: parseFloat(m[1]), y: parseFloat(m[2] || 0) };
  }

  function setTranslate(g, x, y) {
    g.setAttribute('transform', 'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ')');
  }

  function portCenter(svg, portEl) {
    const pt = svg.createSVGPoint();
    pt.x = parseFloat(portEl.getAttribute('cx'));
    pt.y = parseFloat(portEl.getAttribute('cy'));
    const ctm = portEl.getScreenCTM();
    const root = svg.getScreenCTM();
    if (!ctm || !root) {
      return { x: pt.x, y: pt.y };
    }
    const s = pt.matrixTransform(ctm);
    const local = svg.createSVGPoint();
    local.x = s.x;
    local.y = s.y;
    return local.matrixTransform(root.inverse());
  }

  function sortAnchors(anchors) {
    if (anchors.length < 2) return anchors;
    const xs = anchors.map((a) => a.x);
    const ys = anchors.map((a) => a.y);
    if (Math.max(...xs) - Math.min(...xs) < 1) {
      return [...anchors].sort((a, b) => a.y - b.y);
    }
    if (Math.max(...ys) - Math.min(...ys) < 1) {
      return [...anchors].sort((a, b) => a.x - b.x);
    }
    return [...anchors].sort((a, b) => a.x - b.x || a.y - b.y);
  }

  function routeOrtho(anchors) {
    const sorted = sortAnchors(anchors);
    if (sorted.length < 2) return sorted;
    const out = [{ x: sorted[0].x, y: sorted[0].y }];
    for (let i = 1; i < sorted.length; i++) {
      const x0 = sorted[i - 1].x;
      const y0 = sorted[i - 1].y;
      const x1 = sorted[i].x;
      const y1 = sorted[i].y;
      const lx = out[out.length - 1].x;
      const ly = out[out.length - 1].y;
      if (Math.abs(x1 - lx) < 0.01 && Math.abs(y1 - ly) < 0.01) continue;
      if (Math.abs(x1 - lx) < 0.01 || Math.abs(y1 - ly) < 0.01) {
        out.push({ x: x1, y: y1 });
      } else {
        const midX = (x0 + x1) / 2;
        if (Math.abs(midX - lx) > 0.01 || Math.abs(y0 - ly) > 0.01) {
          out.push({ x: midX, y: y0 });
        }
        if (Math.abs(midX - x1) > 0.01 || Math.abs(y1 - y0) > 0.01) {
          out.push({ x: midX, y: y1 });
        }
        out.push({ x: x1, y: y1 });
      }
    }
    return dedupePoints(out);
  }

  const BOTTOM_STUB = 16.0;
  const BOTTOM_STUB_STEP = 8.0;
  const BRANCH_LEAD = 14.0;
  const COLUMN_X_TOL = 36.0;
  const COLUMN_Y_SPAN = 80.0;
  const CONTROL_PREFIXES = ['net_lgc', 'net_153_s', 'net_y_mux_sel', 'net_b_sel', 'net_b_const', 'net_cin'];

  function portStubY(portEl, py) {
    const sy = portEl.getAttribute('data-stub-y');
    if (sy != null && sy !== '') return parseFloat(sy);
    return py + BOTTOM_STUB;
  }

  function bottomStubY(py, index) {
    return py + BOTTOM_STUB + index * BOTTOM_STUB_STEP;
  }

  function portRouteX(portEl) {
    const rx = portEl.getAttribute('data-route-x');
    if (rx != null && rx !== '') return parseFloat(rx);
    return parseFloat(portEl.getAttribute('cx'));
  }

  function isControlNet(net) {
    return CONTROL_PREFIXES.some((p) => net === p || net.startsWith(p));
  }

  function isOperandBitNet(net) {
    return /^net_[ab]\d+$/.test(net);
  }

  function splitIoGate(anchors) {
    const io = anchors.find((a) => a.side === 'io') || null;
    const gates = anchors.filter((a) => a.side !== 'io');
    return { io, gates };
  }

  function layoutInvLink(gates) {
    if (gates.length < 2) return gates.map((g) => ({ x: g.x, y: g.y }));
    const src = gates.find((g) => g.side === 'right') || gates[0];
    const dst = gates.find((g) => g.side === 'left') || gates[gates.length - 1];
    const path = [
      { x: src.x, y: src.y },
      { x: src.routeX, y: src.y },
      { x: dst.routeX, y: src.y },
    ];
    if (Math.abs(src.y - dst.y) > 0.5) path.push({ x: dst.routeX, y: dst.y });
    path.push({ x: dst.x, y: dst.y });
    return dedupePoints(path);
  }

  function spokeBottomFromTrunk(px, py, rx, ioX, stubY) {
    const pts = [{ x: ioX, y: stubY }, { x: rx, y: stubY }, { x: rx, y: py }];
    if (Math.abs(px - rx) > 0.01) pts.push({ x: px, y: py });
    return dedupePoints(pts);
  }

  function routeToHub(px, py, side, rx, hx, hy, stubYOpt) {
    if (side === 'io') {
      if (Math.abs(py - hy) < 0.01) return [{ x: px, y: py }, { x: hx, y: hy }];
      return [{ x: px, y: py }, { x: px, y: hy }, { x: hx, y: hy }];
    }
    if (side === 'left' || side === 'right') {
      return dedupePoints([
        { x: px, y: py },
        { x: rx, y: py },
        { x: rx, y: hy },
        { x: hx, y: hy },
      ]);
    }
    const stubY = stubYOpt != null ? stubYOpt : py + BOTTOM_STUB;
    return dedupePoints([
      { x: px, y: py },
      { x: px, y: stubY },
      { x: rx, y: stubY },
      { x: rx, y: hy },
      { x: hx, y: hy },
    ]);
  }

  function layoutLink(anchors, net) {
    const { io, gates } = splitIoGate(anchors);
    if (net.startsWith('net_b_inv')) {
      return {
        topology: 'link',
        hub: null,
        junctions: [],
        segments: [{ role: 'link', endpoint: '', points: layoutInvLink(gates) }],
      };
    }
    if (anchors.length === 2) {
      const a = anchors[0];
      const b = anchors[1];
      let points;
      if (a.side === 'right' || b.side === 'right') {
        points = layoutInvLink(a.side === 'right' ? [a, b] : [b, a]);
      } else {
        points = [{ x: a.x, y: a.y }, { x: b.x, y: b.y }];
      }
      return {
        topology: 'link',
        hub: null,
        junctions: [],
        segments: [{ role: 'link', endpoint: '', points: dedupePoints(points) }],
      };
    }
    const ordered = (io ? [io] : []).concat([...gates].sort((a, b) => a.routeX - b.routeX || a.x - b.x));
    const path = [];
    ordered.forEach((p, i) => {
      if (i === 0) {
        path.push({ x: p.x, y: p.y });
        if (p.side === 'left' || p.side === 'right') path.push({ x: p.routeX, y: p.y });
        return;
      }
      const prev = ordered[i - 1];
      if (p.side === 'left') {
        path.push({ x: p.routeX, y: path[path.length - 1].y }, { x: p.routeX, y: p.y }, { x: p.x, y: p.y });
      } else if (p.side === 'right') {
        path.push({ x: prev.routeX, y: p.y }, { x: p.routeX, y: p.y }, { x: p.x, y: p.y });
      } else {
        const stubY = p.stubY != null ? p.stubY : p.y + BOTTOM_STUB;
        path.push({ x: p.x, y: stubY }, { x: p.routeX, y: stubY }, { x: p.routeX, y: p.y });
        if (Math.abs(p.x - p.routeX) > 0.01) path.push({ x: p.x, y: p.y });
      }
    });
    return {
      topology: 'link',
      hub: null,
      junctions: [],
      segments: [{ role: 'link', endpoint: '', points: dedupePoints(path) }],
    };
  }

  function partitionSides(gates) {
    return {
      left: gates.filter((g) => g.side === 'left'),
      right: gates.filter((g) => g.side === 'right'),
      bottom: gates.filter((g) => g.side === 'bottom'),
    };
  }

  function isColumnFanout(left) {
    if (left.length < 3) return false;
    const xs = left.map((g) => g.x);
    const ys = left.map((g) => g.y);
    return Math.max(...xs) - Math.min(...xs) <= COLUMN_X_TOL && Math.max(...ys) - Math.min(...ys) >= COLUMN_Y_SPAN;
  }

  function spokeLeftFromColumn(px, py, rx, trunkX) {
    return dedupePoints([{ x: trunkX, y: py }, { x: rx, y: py }, { x: px, y: py }]);
  }

  function layoutBusMixed(io, left, bottom) {
    const busY = io.y;
    const junctions = [];
    const segments = [];
    let trunkEnd = io.x;
    if (left.length) {
      left.forEach((g) => {
        const forkX = Math.min(g.routeX, g.x - BRANCH_LEAD);
        trunkEnd = Math.max(trunkEnd, g.routeX, forkX);
      });
      segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: busY }, { x: trunkEnd, y: busY }] });
      left.sort((a, b) => a.routeX - b.routeX).forEach((g) => {
        junctions.push({ x: g.routeX, y: busY, endpoint: g.unit });
        segments.push({
          role: 'spoke',
          endpoint: g.unit,
          points: [{ x: g.routeX, y: busY }, { x: g.routeX, y: g.y }, { x: g.x, y: g.y }],
        });
      });
    }
    const spineX = Math.max(trunkEnd, ...bottom.map((g) => g.routeX));
    const stubYs = bottom.map((g) => (g.stubY != null ? g.stubY : g.y + BOTTOM_STUB));
    const spineFar = Math.max(...stubYs);
    if (left.length && Math.abs(spineX - trunkEnd) > 0.01) {
      segments.push({ role: 'trunk', endpoint: '', points: [{ x: trunkEnd, y: busY }, { x: spineX, y: busY }] });
    }
    if (!left.length) {
      segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: busY }, { x: spineX, y: busY }] });
    }
    segments.push({ role: 'trunk', endpoint: '', points: [{ x: spineX, y: busY }, { x: spineX, y: spineFar }] });
    bottom
      .sort((a, b) => (a.stubY != null ? a.stubY : a.y) - (b.stubY != null ? b.stubY : b.y) || a.routeX - b.routeX)
      .forEach((g) => {
        const stubY = g.stubY != null ? g.stubY : g.y + BOTTOM_STUB;
        junctions.push({ x: spineX, y: stubY, endpoint: g.unit });
        segments.push({
          role: 'spoke',
          endpoint: g.unit,
          points: spokeBottomFromTrunk(g.x, g.y, g.routeX, spineX, stubY),
        });
      });
    return { topology: 'bus_mixed', hub: null, junctions, segments };
  }

  function layoutBus(io, gates) {
    const { left, bottom } = partitionSides(gates);
    if (left.length && bottom.length) return layoutBusMixed(io, left, bottom);

    const busY = io.y;
    const junctions = [];
    const segments = [];
    if (left.length) {
      let trunkEnd = io.x;
      left.forEach((g) => {
        const forkX = Math.min(g.routeX, g.x - BRANCH_LEAD);
        trunkEnd = Math.max(trunkEnd, g.routeX, forkX);
      });
      segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: busY }, { x: trunkEnd, y: busY }] });
      left.sort((a, b) => a.routeX - b.routeX).forEach((g) => {
        junctions.push({ x: g.routeX, y: busY, endpoint: g.unit });
        segments.push({
          role: 'spoke',
          endpoint: g.unit,
          points: [{ x: g.routeX, y: busY }, { x: g.routeX, y: g.y }, { x: g.x, y: g.y }],
        });
      });
      return { topology: 'bus_horizontal', hub: null, junctions, segments };
    }
    return layoutCorridor(io, gates);
  }

  function columnTrunkX(left) {
    return Math.min(...left.map((g) => g.routeX)) - BRANCH_LEAD;
  }

  function layoutColumnVertical(left, io) {
    const junctions = [];
    const segments = [];
    const ys = left.map((g) => g.y);
    const portTop = Math.min(...ys);
    const portBot = Math.max(...ys);
    const trunkX = columnTrunkX(left);
    if (io) {
      if (io.y >= portBot - 0.5) {
        if (Math.abs(io.x - trunkX) > 0.01) {
          segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: io.y }, { x: trunkX, y: io.y }] });
        }
        segments.push({ role: 'trunk', endpoint: '', points: [{ x: trunkX, y: portTop }, { x: trunkX, y: io.y }] });
      } else if (io.y <= portTop + 0.5) {
        if (Math.abs(io.x - trunkX) > 0.01) {
          segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: io.y }, { x: trunkX, y: io.y }] });
        }
        segments.push({ role: 'trunk', endpoint: '', points: [{ x: trunkX, y: io.y }, { x: trunkX, y: portBot }] });
      } else {
        if (Math.abs(io.x - trunkX) > 0.01) {
          segments.push({ role: 'trunk', endpoint: 'io', points: [{ x: io.x, y: io.y }, { x: trunkX, y: io.y }] });
        }
        segments.push({ role: 'trunk', endpoint: '', points: [{ x: trunkX, y: portTop }, { x: trunkX, y: portBot }] });
      }
    } else {
      segments.push({ role: 'trunk', endpoint: '', points: [{ x: trunkX, y: portTop }, { x: trunkX, y: portBot }] });
    }
    left.sort((a, b) => a.y - b.y).forEach((g) => {
      junctions.push({ x: trunkX, y: g.y, endpoint: g.unit });
      segments.push({
        role: 'spoke',
        endpoint: g.unit,
        points: spokeLeftFromColumn(g.x, g.y, g.routeX, trunkX),
      });
    });
    return { topology: 'column_vertical', hub: null, junctions, segments };
  }

  function layoutCorridor(io, gates) {
    const bottom = gates
      .filter((g) => g.side === 'bottom')
      .sort((a, b) => (a.stubY != null ? a.stubY : a.y) - (b.stubY != null ? b.stubY : b.y) || a.routeX - b.routeX);
    if (!bottom.length) return layoutStar(io, gates);
    const junctions = [];
    const segments = [];
    const stubYs = bottom.map((g) => (g.stubY != null ? g.stubY : g.y + BOTTOM_STUB));
    const trunkFar = io.y >= Math.max(...stubYs) ? Math.min(...stubYs) : Math.max(...stubYs);
    segments.push({
      role: 'trunk',
      endpoint: 'io',
      points: [{ x: io.x, y: io.y }, { x: io.x, y: trunkFar }],
    });
    bottom.forEach((g) => {
      const stubY = g.stubY != null ? g.stubY : g.y + BOTTOM_STUB;
      junctions.push({ x: io.x, y: stubY, endpoint: g.unit });
      segments.push({
        role: 'spoke',
        endpoint: g.unit,
        points: spokeBottomFromTrunk(g.x, g.y, g.routeX, io.x, stubY),
      });
    });
    return { topology: 'corridor_vertical', hub: null, junctions, segments };
  }

  function layoutStar(io, gates) {
    if (!gates.length && io) return { topology: 'link', hub: null, junctions: [], segments: [] };
    let hubX = gates.reduce((s, g) => s + g.x, 0) / gates.length;
    let hubY = gates.reduce((s, g) => s + g.y, 0) / gates.length;
    if (io && gates.length) {
      hubX = (io.x + hubX) / 2;
      hubY = (io.y + hubY) / 2;
    }
    const hub = { x: hubX, y: hubY };
    const endpoints = (io ? [io] : []).concat([...gates].sort((a, b) => a.routeX - b.routeX || a.x - b.x));
    const segments = endpoints.map((p) => ({
      role: 'spoke',
      endpoint: p.unit,
      points: routeToHub(p.x, p.y, p.side, p.routeX, hubX, hubY, p.stubY),
    }));
    return {
      topology: 'star',
      hub,
      junctions: [{ x: hubX, y: hubY, endpoint: 'hub' }],
      segments,
    };
  }

  function layoutBranchNet(anchors, net) {
    if (anchors.length < 2) return { topology: 'link', hub: null, junctions: [], segments: [] };
    const { io, gates } = splitIoGate(anchors);
    const { left, bottom } = partitionSides(gates);
    if (net.startsWith('net_b_inv')) return layoutLink(anchors, net);
    if (anchors.length === 2) return layoutLink(anchors, net);
    const operand = isOperandBitNet(net);
    const control = isControlNet(net);
    if (io && operand) return layoutBus(io, gates);
    if (io && control) {
      if (bottom.length && left.length) return layoutBusMixed(io, left, bottom);
      if (bottom.length) return layoutCorridor(io, gates);
      if (left.length && isColumnFanout(left)) return layoutColumnVertical(left, io);
      if (left.length) return layoutBus(io, gates);
    }
    if (!io && left.length && !bottom.length && isColumnFanout(left)) {
      return layoutColumnVertical(left, null);
    }
    if (gates.length === 2 && !io) return layoutLink(anchors, net);
    return layoutStar(io, gates);
  }

  function netAnchors(svg, net) {
    const anchors = [];
    svg.querySelectorAll('.port[data-net="' + net + '"]').forEach((p) => {
      const c = portCenter(svg, p);
      const side = p.getAttribute('data-port-side') || 'left';
      anchors.push({
        x: c.x,
        y: c.y,
        routeX: portRouteX(p),
        stubY: side === 'bottom' ? portStubY(p, c.y) : c.y,
        side: side,
        unit: p.getAttribute('data-unit') || '',
      });
    });
    const io = svg.querySelector('.io-net[data-net="' + net + '"] circle');
    if (io) {
      const ix = parseFloat(io.getAttribute('cx'));
      const iy = parseFloat(io.getAttribute('cy'));
      anchors.push({
        x: ix,
        y: iy,
        routeX: ix,
        stubY: iy,
        side: 'io',
        unit: 'io',
      });
    }
    return anchors;
  }

  function netGroup(svg, net) {
    let g = svg.querySelector('.net[data-net="' + net + '"]');
    if (!g) {
      g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'net');
      g.setAttribute('data-net', net);
      const layer = svg.querySelector('#wires');
      if (layer) layer.appendChild(g);
    }
    return g;
  }

  function wireColor(svg, net) {
    const port = svg.querySelector('.port[data-net="' + net + '"]');
    if (port) return port.getAttribute('fill') || '#8b949e';
    const io = svg.querySelector('.io-net[data-net="' + net + '"] circle');
    if (io) return io.getAttribute('fill') || '#8b949e';
    const w = svg.querySelector('.wire-seg[data-net="' + net + '"], .wire-trunk[data-net="' + net + '"]');
    return w ? w.getAttribute('stroke') || '#8b949e' : '#8b949e';
  }

  function wireStrokeWidth(svg, net) {
    if (isControlNet(net)) return '1.8';
    const w = svg.querySelector('.wire-seg[data-net="' + net + '"], .wire-trunk[data-net="' + net + '"]');
    return w ? w.getAttribute('stroke-width') || '1.3' : '1.3';
  }

  function wireSegs(svg, net) {
    return [...svg.querySelectorAll('.wire-seg[data-net="' + net + '"], .wire-trunk[data-net="' + net + '"]')];
  }

  function wireHits(svg, net) {
    return [...svg.querySelectorAll('.wire-hit[data-net="' + net + '"]')];
  }

  function segKey(seg) {
    const role =
      seg.getAttribute('data-role') ||
      (seg.classList.contains('wire-trunk') ? 'trunk' : 'spoke');
    return (seg.getAttribute('data-end') || '') + ':' + role;
  }

  function renderNetGroup(svg, net, branch, customPts) {
    const group = netGroup(svg, net);
    group.setAttribute('data-topology', branch.topology);
    const color = wireColor(svg, net);
    const sw = wireStrokeWidth(svg, net);
    group.innerHTML = '';

    if (branch.hub) {
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('class', 'net-hub');
      c.setAttribute('data-net', net);
      c.setAttribute('cx', branch.hub.x.toFixed(1));
      c.setAttribute('cy', branch.hub.y.toFixed(1));
      c.setAttribute('r', '3');
      c.setAttribute('fill', color);
      c.setAttribute('opacity', '0.9');
      group.appendChild(c);
    }

    branch.junctions.forEach((j) => {
      if (j.endpoint === 'hub') return;
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('class', 'net-junction');
      c.setAttribute('data-net', net);
      c.setAttribute('data-end', j.endpoint);
      c.setAttribute('cx', j.x.toFixed(1));
      c.setAttribute('cy', j.y.toFixed(1));
      c.setAttribute('r', '2.5');
      c.setAttribute('fill', color);
      c.setAttribute('opacity', '0.85');
      group.appendChild(c);
    });

    branch.segments.forEach((seg) => {
      const cls = seg.role === 'trunk' ? 'wire-trunk' : 'wire-seg';
      const key = (seg.endpoint || '') + ':' + seg.role;
      const pts = customPts[key] ? parsePoints(customPts[key]) : seg.points;
      const points = formatPoints(pts);
      const vis = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      vis.setAttribute('class', cls);
      vis.setAttribute('data-net', net);
      if (seg.endpoint) vis.setAttribute('data-end', seg.endpoint);
      vis.setAttribute('data-role', seg.role);
      vis.setAttribute('points', points);
      vis.setAttribute('fill', 'none');
      vis.setAttribute('stroke', color);
      vis.setAttribute('stroke-width', sw);
      vis.setAttribute('opacity', seg.role === 'trunk' ? '0.8' : '0.65');
      vis.setAttribute('pointer-events', 'none');
      if (customPts[key]) vis.setAttribute('data-custom', '1');
      if (!vis.getAttribute('data-base-sw')) vis.setAttribute('data-base-sw', sw);
      group.appendChild(vis);

      const hit = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      hit.setAttribute('class', 'wire-hit');
      hit.setAttribute('data-net', net);
      if (seg.endpoint) hit.setAttribute('data-end', seg.endpoint);
      hit.setAttribute('data-role', seg.role);
      hit.setAttribute('points', points);
      hit.setAttribute('fill', 'none');
      hit.setAttribute('stroke', 'transparent');
      hit.setAttribute('stroke-width', '14');
      if (customPts[key]) hit.setAttribute('data-custom', '1');
      group.appendChild(hit);
    });
  }

  function rebuildWireHandles(svg, net) {
    const layer = svg.querySelector('#wire-handles');
    if (!layer) return;
    layer.querySelectorAll('.wire-handle[data-net="' + net + '"]').forEach((el) => el.remove());
    wireSegs(svg, net).forEach((wire) => {
      if (wire.getAttribute('data-custom') === '1') return;
      const n = wire.getAttribute('data-net');
      const end = wire.getAttribute('data-end') || '';
      const pts = dedupePoints(parsePoints(wire.getAttribute('points') || ''));
      for (let i = 1; i < pts.length - 1; i++) {
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('class', 'wire-handle');
        c.setAttribute('data-net', n);
        c.setAttribute('data-end', end);
        c.setAttribute('data-idx', String(i));
        c.setAttribute('cx', pts[i].x.toFixed(1));
        c.setAttribute('cy', pts[i].y.toFixed(1));
        c.setAttribute('r', '4');
        layer.appendChild(c);
      }
    });
  }

  function rebuildAllWireHandles(svg) {
    const layer = svg.querySelector('#wire-handles');
    if (!layer) return;
    layer.innerHTML = '';
    const nets = new Set();
    svg.querySelectorAll('.wire-seg[data-net], .wire-trunk[data-net]').forEach((w) => {
      nets.add(w.getAttribute('data-net'));
    });
    nets.forEach((net) => rebuildWireHandles(svg, net));
  }

  function refreshNet(svg, net) {
    const group = netGroup(svg, net);
    const customPts = {};
    group.querySelectorAll('.wire-seg[data-custom="1"], .wire-trunk[data-custom="1"]').forEach((w) => {
      customPts[segKey(w)] = w.getAttribute('points');
    });
    const anchors = netAnchors(svg, net);
    if (anchors.length < 2) return;
    const branch = layoutBranchNet(anchors, net);
    if (!branch.segments.length) return;
    renderNetGroup(svg, net, branch, customPts);
    rebuildWireHandles(svg, net);
  }

  function netsForGate(gate) {
    const nets = new Set();
    gate.querySelectorAll('.port[data-net]').forEach((p) => {
      const n = p.getAttribute('data-net');
      if (n) nets.add(n);
    });
    return nets;
  }

  function relatedUnits(svg, netOrNets) {
    const nets = Array.isArray(netOrNets) ? netOrNets : [netOrNets];
    const units = new Set();
    nets.forEach((net) => {
      svg.querySelectorAll('.port[data-net="' + net + '"]').forEach((p) => {
        const uid = p.getAttribute('data-unit') || '';
        if (uid) units.add(uid);
      });
    });
    return units;
  }

  function expandNets(svg, net) {
    if (!net) return [];
    const io = svg.querySelector('.io-net[data-net="' + net + '"]');
    const bus = io && io.getAttribute('data-nets');
    if (bus) return bus.trim().split(/\s+/).filter(Boolean);
    return [net];
  }

  function netsFromElement(el) {
    const io = el.closest('.io-net');
    if (io) {
      const bus = io.getAttribute('data-nets');
      if (bus) return bus.trim().split(/\s+/).filter(Boolean);
      const n = io.getAttribute('data-net');
      return n ? [n] : [];
    }
    const n = el.getAttribute && el.getAttribute('data-net');
    return n ? [n] : [];
  }

  function clearNetHighlight(svg) {
    svg.querySelectorAll('.gate-node, .wire-seg, .wire-trunk, .wire-hit, .io-net, .port, .wire-handle, .net-hub, .net-junction').forEach((el) => {
      el.style.opacity = '';
      el.classList.remove('highlight');
    });
    svg.querySelectorAll('.wire-seg, .wire-trunk').forEach((w) => {
      w.setAttribute('stroke-width', w.getAttribute('data-base-sw') || '1.3');
    });
    svg.querySelectorAll('.port').forEach((p) => {
      p.setAttribute('r', '2.5');
    });
    svg.querySelectorAll('.io-net circle').forEach((c) => {
      c.setAttribute('r', '3');
    });
  }

  function applyNetHighlight(svg, net) {
    if (!net) {
      clearNetHighlight(svg);
      return;
    }
    const nets = new Set(expandNets(svg, net));
    const units = relatedUnits(svg, [...nets]);
    svg.querySelectorAll('.port').forEach((p) => {
      const n = p.getAttribute('data-net') || '';
      const uid = p.getAttribute('data-unit') || '';
      if (nets.has(n) || units.has(uid)) units.add(uid);
    });

    svg.querySelectorAll('.gate-node').forEach((g) => {
      const id = g.getAttribute('data-unit-id') || '';
      const on = units.has(id);
      g.style.opacity = on ? '1' : DIM;
      g.classList.toggle('highlight', on);
    });

    svg.querySelectorAll('.wire-seg, .wire-trunk').forEach((w) => {
      const n = w.getAttribute('data-net') || '';
      const on = nets.has(n);
      w.style.opacity = on ? '0.95' : WIRE_DIM;
      w.setAttribute('stroke-width', on ? HI_WIDTH : w.getAttribute('data-base-sw') || '1.3');
      w.classList.toggle('highlight', on);
    });

    svg.querySelectorAll('.wire-hit, .wire-handle, .net-hub, .net-junction').forEach((w) => {
      const n = w.getAttribute('data-net') || '';
      w.style.opacity = nets.has(n) ? '1' : WIRE_DIM;
      w.classList.toggle('highlight', nets.has(n));
    });

    svg.querySelectorAll('.io-net').forEach((io) => {
      const ioNets = netsFromElement(io);
      const on = ioNets.some((n) => nets.has(n));
      io.style.opacity = on ? '1' : DIM;
      io.classList.toggle('highlight', on);
      const c = io.querySelector('circle');
      if (c) c.setAttribute('r', on ? '5' : '3');
    });
    svg.querySelectorAll('.io-trunk').forEach((t) => {
      const on = nets.has('net_b0');
      t.style.opacity = on ? '1' : WIRE_DIM;
    });

    svg.querySelectorAll('.port').forEach((p) => {
      const n = p.getAttribute('data-net') || '';
      const uid = p.getAttribute('data-unit') || '';
      const onPort = nets.has(n);
      const onGate = units.has(uid);
      p.style.opacity = onPort || onGate ? '1' : DIM;
      p.classList.toggle('highlight', onPort);
      p.setAttribute('r', onPort ? '4' : '2.5');
    });
  }

  function dist2(a, b) {
    return (a.x - b.x) ** 2 + (a.y - b.y) ** 2;
  }

  function pickTarget(svg, el) {
    const handle = el.closest('.wire-handle');
    if (handle) {
      return {
        type: 'handle',
        el: handle,
        net: handle.getAttribute('data-net'),
        end: handle.getAttribute('data-end') || '',
        idx: parseInt(handle.getAttribute('data-idx'), 10),
      };
    }
    const port = el.closest('.port');
    if (port) {
      return { type: 'port', el: port, net: port.getAttribute('data-net') };
    }
    const io = el.closest('.io-net');
    if (io) return { type: 'io', el: io, net: io.getAttribute('data-net') };
    const hub = el.closest('.net-hub');
    if (hub) return { type: 'hub', el: hub, net: hub.getAttribute('data-net') };
    const hit = el.closest('.wire-hit') || el.closest('.wire-seg') || el.closest('.wire-trunk');
    if (hit) return { type: 'wire', el: hit, net: hit.getAttribute('data-net') };
    const body = el.closest('.gate-body');
    if (body) {
      return { type: 'gate', el: body.closest('.gate-node') };
    }
    return { type: 'bg', el: svg };
  }

  function wireSegForEndpoint(svg, net, end, role) {
    const sel =
      (role === 'trunk' ? '.wire-trunk' : '.wire-seg') +
      '[data-net="' + net + '"][data-end="' + end + '"]';
    let w = svg.querySelector(sel);
    if (!w && !end) {
      w = svg.querySelector((role === 'trunk' ? '.wire-trunk' : '.wire-seg') + '[data-net="' + net + '"]');
    }
    return w;
  }

  function wireDragTarget(svg, net, svgPt) {
    const io = svg.querySelector('.io-net[data-net="' + net + '"]');
    if (io) return { type: 'io', el: io, net: net };

    const hits = wireHits(svg, net);
    if (!hits.length) return null;

    let bestHit = hits[0];
    let bestSeg = wireSegs(svg, net)[0];
    let bestIdx = 1;
    let bd = Infinity;

    hits.forEach((hit) => {
      const end = hit.getAttribute('data-end') || '';
      const role = hit.getAttribute('data-role') || 'spoke';
      const seg =
        wireSegForEndpoint(svg, net, end, role === 'trunk' ? 'trunk' : 'spoke') ||
        svg.querySelector('.wire-seg[data-net="' + net + '"], .wire-trunk[data-net="' + net + '"]');
      const pts = dedupePoints(parsePoints(hit.getAttribute('points') || ''));
      if (pts.length <= 2) {
        const d = dist2(svgPt, pts[0]) + dist2(svgPt, pts[pts.length - 1]);
        if (d < bd) {
          bd = d;
          bestHit = hit;
          bestSeg = seg;
          bestIdx = 1;
        }
        return;
      }
      for (let i = 1; i < pts.length - 1; i++) {
        const d = dist2(svgPt, pts[i]);
        if (d < bd) {
          bd = d;
          bestHit = hit;
          bestSeg = seg;
          bestIdx = i;
        }
      }
    });

    if (bestSeg && dedupePoints(parsePoints(bestHit.getAttribute('points') || '')).length <= 2) {
      return { type: 'wire', el: bestHit, net: net, end: bestHit.getAttribute('data-end') || '' };
    }
    return {
      type: 'handle',
      net: net,
      end: bestHit.getAttribute('data-end') || '',
      idx: bestIdx,
      el: null,
    };
  }

  function setStatus(msg) {
    const el = document.getElementById('sel-status');
    if (el) el.textContent = msg;
  }

  function initGateGraphInteractive(host) {
    const svg = svgRoot(host);
    if (!svg || svg.getAttribute('data-gate-graph') !== '1') return;
    if (svg.getAttribute('data-interactive') === '1') return;
    svg.setAttribute('data-interactive', '1');

    const scrollHost = svg.closest('#wrap') || svg.parentElement;
    let selectedNet = null;
    let hoverNet = null;

    function refreshHighlight() {
      applyNetHighlight(svg, hoverNet || selectedNet);
    }

    svg.querySelectorAll('.wire-seg, .wire-trunk').forEach((w) => {
      if (!w.getAttribute('data-base-sw')) {
        w.setAttribute('data-base-sw', w.getAttribute('stroke-width') || '1.3');
      }
    });
    rebuildAllWireHandles(svg);

    svg.querySelectorAll('.gate-node').forEach((g) => {
      if (!g.getAttribute('transform')) setTranslate(g, 0, 0);
    });

    let pointer = null;
    let dragActive = false;
    let didDrag = false;
    let dragPan = false;
    let panBase = null;
    let dragGate = null;
    let dragIo = null;
    let dragHub = null;
    let dragHandle = null;
    let dragNet = null;
    let dragEnd = '';
    let dragStart = null;
    let gateBase = { x: 0, y: 0 };
    let handleIdx = -1;
    let handleBase = null;
    let ioBase = { x: 0, y: 0 };
    let hubBase = { x: 0, y: 0 };

    function endDrag() {
      if (dragGate) dragGate.style.cursor = '';
      dragGate = null;
      dragIo = null;
      dragHub = null;
      dragHandle = null;
      dragNet = null;
      dragStart = null;
      handleIdx = -1;
      handleBase = null;
      dragActive = false;
      dragPan = false;
      panBase = null;
      pointer = null;
      if (scrollHost) scrollHost.style.cursor = '';
    }

    function beginDrag(target) {
      didDrag = true;
      dragActive = true;
      if (target.type === 'bg') {
        dragPan = true;
        if (scrollHost) {
          panBase = {
            x: pointer.clientX,
            y: pointer.clientY,
            sl: scrollHost.scrollLeft,
            st: scrollHost.scrollTop,
          };
          scrollHost.style.cursor = 'grabbing';
        }
        return;
      }
      if (target.type === 'gate') {
        dragGate = target.el;
        dragGate.style.cursor = 'grabbing';
        gateBase = parseTranslate(dragGate);
        setStatus('Dragging gate ' + (dragGate.getAttribute('data-unit-id') || ''));
      } else if (target.type === 'io') {
        dragIo = target.el;
        dragNet = target.net;
        netGroup(svg, dragNet).querySelectorAll('.wire-seg, .wire-trunk').forEach((w) => {
          w.removeAttribute('data-custom');
        });
        const c = dragIo.querySelector('circle');
        ioBase = {
          x: parseFloat(c.getAttribute('cx')),
          y: parseFloat(c.getAttribute('cy')),
        };
        setStatus('Dragging net ' + dragNet);
      } else if (target.type === 'hub') {
        dragHub = target.el;
        dragNet = target.net;
        hubBase = {
          x: parseFloat(dragHub.getAttribute('cx')),
          y: parseFloat(dragHub.getAttribute('cy')),
        };
        setStatus('Dragging hub ' + dragNet);
      } else if (target.type === 'handle') {
        dragNet = target.net;
        dragEnd = target.end || '';
        handleIdx = target.idx;
        const role =
          svg
            .querySelector(
              '.wire-hit[data-net="' + dragNet + '"][data-end="' + dragEnd + '"]'
            )
            ?.getAttribute('data-role') || 'spoke';
        const wire = wireSegForEndpoint(svg, dragNet, dragEnd, role === 'trunk' ? 'trunk' : 'spoke');
        if (wire) {
          wire.setAttribute('data-custom', '1');
          handleBase = dedupePoints(parsePoints(wire.getAttribute('points') || ''));
          const hit = svg.querySelector(
            '.wire-hit[data-net="' + dragNet + '"][data-end="' + dragEnd + '"]'
          );
          if (hit) hit.setAttribute('data-custom', '1');
        }
        dragHandle =
          target.el ||
          svg.querySelector(
            '.wire-handle[data-net="' + target.net + '"][data-idx="' + target.idx + '"]'
          );
        setStatus('Dragging bend on ' + dragNet);
      }
    }

    function pointerDist(e) {
      if (!pointer) return 0;
      const dx = e.clientX - pointer.clientX;
      const dy = e.clientY - pointer.clientY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    function netFromTarget(t) {
      if (!t) return null;
      if (t.net) return t.net;
      return null;
    }

    function onPointerDown(e) {
      if (e.button === 1) {
        e.preventDefault();
        pointer = { clientX: e.clientX, clientY: e.clientY, target: { type: 'bg' } };
        didDrag = false;
        beginDrag({ type: 'bg' });
        return;
      }
      if (e.button !== 0) return;
      const target = pickTarget(svg, e.target);
      if (target.type === 'bg') {
        pointer = { clientX: e.clientX, clientY: e.clientY, target };
        didDrag = false;
        return;
      }
      e.preventDefault();
      pointer = { clientX: e.clientX, clientY: e.clientY, target };
      dragStart = clientToSvg(svg, e);
      didDrag = false;
    }

    function onPointerMove(e) {
      if (!pointer) return;

      if (!dragActive && pointerDist(e) >= CLICK_THRESH) {
        let t = pointer.target;
        if (t.type === 'wire') {
          t = wireDragTarget(svg, t.net, clientToSvg(svg, e));
        }
        if (t) beginDrag(t);
      }
      if (!dragActive) return;

      if (dragPan && panBase && scrollHost) {
        scrollHost.scrollLeft = panBase.sl - (e.clientX - panBase.x);
        scrollHost.scrollTop = panBase.st - (e.clientY - panBase.y);
        return;
      }

      if (!dragStart) return;
      const cur = clientToSvg(svg, e);
      const dx = cur.x - dragStart.x;
      const dy = cur.y - dragStart.y;

      if (dragGate) {
        setTranslate(dragGate, gateBase.x + dx, gateBase.y + dy);
        netsForGate(dragGate).forEach((n) => refreshNet(svg, n));
      }

      if (dragIo && dragNet) {
        const c = dragIo.querySelector('circle');
        const t = dragIo.querySelector('text');
        const nx = ioBase.x + dx;
        const ny = ioBase.y + dy;
        c.setAttribute('cx', nx.toFixed(1));
        c.setAttribute('cy', ny.toFixed(1));
        if (t) {
          const mid = t.getAttribute('text-anchor') === 'middle';
          const anchor = t.getAttribute('text-anchor') === 'end' ? -8 : 8;
          t.setAttribute('x', mid ? nx.toFixed(1) : (nx + anchor).toFixed(1));
          t.setAttribute('y', (ny + (mid ? 12 : 3)).toFixed(1));
        }
        refreshNet(svg, dragNet);
      }

      if (dragHub && dragNet) {
        const nx = hubBase.x + dx;
        const ny = hubBase.y + dy;
        dragHub.setAttribute('cx', nx.toFixed(1));
        dragHub.setAttribute('cy', ny.toFixed(1));
        wireSegs(svg, dragNet).forEach((wire) => {
          if (wire.getAttribute('data-custom') === '1') return;
          const pts = dedupePoints(parsePoints(wire.getAttribute('points') || ''));
          if (!pts.length) return;
          pts[pts.length - 1] = { x: nx, y: ny };
          const s = formatPoints(pts);
          wire.setAttribute('points', s);
          const hit = svg.querySelector(
            '.wire-hit[data-net="' + dragNet + '"][data-end="' + (wire.getAttribute('data-end') || '') + '"]'
          );
          if (hit) hit.setAttribute('points', s);
        });
        rebuildWireHandles(svg, dragNet);
      }

      if (dragHandle && dragNet && handleBase && handleIdx >= 0) {
        const moved = handleBase.map((p, i) =>
          i === handleIdx ? { x: p.x + dx, y: p.y + dy } : { x: p.x, y: p.y }
        );
        const points = formatPoints(moved);
        const role =
          svg
            .querySelector(
              '.wire-hit[data-net="' + dragNet + '"][data-end="' + dragEnd + '"]'
            )
            ?.getAttribute('data-role') || 'spoke';
        const wire = wireSegForEndpoint(svg, dragNet, dragEnd, role === 'trunk' ? 'trunk' : 'spoke');
        const hit = svg.querySelector(
          '.wire-hit[data-net="' + dragNet + '"][data-end="' + dragEnd + '"]'
        );
        if (wire) wire.setAttribute('points', points);
        if (hit) hit.setAttribute('points', points);
        if (dragHandle) {
          dragHandle.setAttribute('cx', moved[handleIdx].x.toFixed(1));
          dragHandle.setAttribute('cy', moved[handleIdx].y.toFixed(1));
        } else {
          rebuildWireHandles(svg, dragNet);
        }
      }
    }

    function onPointerUp() {
      if (pointer && !didDrag) {
        const net = netFromTarget(pointer.target);
        if (net) {
          selectedNet = selectedNet === net ? null : net;
          refreshHighlight();
          setStatus(
            selectedNet ? 'Selected net ' + selectedNet + ' (Esc to clear)' : 'Net selection cleared'
          );
        } else if (pointer.target.type === 'bg') {
          selectedNet = null;
          refreshHighlight();
          setStatus('Drag gates · hover/click net to highlight');
        }
      }
      endDrag();
    }

    function onNetEnter(net) {
      hoverNet = net;
      refreshHighlight();
      if (!selectedNet) setStatus('Net ' + net);
    }

    function onNetLeave() {
      hoverNet = null;
      refreshHighlight();
      if (!selectedNet) setStatus('Drag gates · hover/click net to highlight');
    }

    svg.querySelectorAll('.wire-hit, .wire-seg, .wire-trunk, .io-net, .port, .net-hub, .net-junction').forEach((el) => {
      const ns = netsFromElement(el);
      if (!ns.length) {
        const n = el.getAttribute('data-net');
        if (n) ns.push(n);
      }
      if (!ns.length) return;
      el.addEventListener('mouseenter', () => {
        hoverNet = ns[0];
        applyNetHighlight(svg, ns[0]);
        if (!selectedNet) setStatus('B bus' + (ns.length > 1 ? ' (8 bits)' : ': ' + ns[0]));
      });
      el.addEventListener('mouseleave', () => onNetLeave());
    });

    svg.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    svg.addEventListener('dragstart', (e) => e.preventDefault());
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        selectedNet = null;
        hoverNet = null;
        clearNetHighlight(svg);
        setStatus('Drag gates · hover/click net to highlight');
      }
    });
    svg.addEventListener('mouseleave', () => {
      hoverNet = null;
      refreshHighlight();
    });

    setStatus('Drag gates · drag IO/bends · hover/click net to highlight');
  }

  window.initGateGraphInteractive = initGateGraphInteractive;
  window.applyNetHighlight = applyNetHighlight;
  window.clearNetHighlight = clearNetHighlight;
})();
