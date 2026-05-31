"""Local HTTP server for Phase1 p1-viewer (static + hwsim API)."""

from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from hwsim.export_svg import export_svg
from hwsim.netlist import load_netlist
from hwsim.scenario import (
    CLOCK_PERIOD_NS,
    MAX_INTERACTIVE_DURATION_NS,
    load_alu_opcodes,
    simulate_request,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def viewer_dir(root: Path) -> Path:
    return root / "hw" / "p1-viewer"


def netlist_path(root: Path) -> Path:
    view = root / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_view.yaml"
    if view.is_file():
        return view
    return root / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_clock.yaml"


def build_meta(root: Path) -> dict[str, Any]:
    nl = load_netlist(netlist_path(root))
    return {
        "block": nl.block,
        "registers": ["R0", "R1", "R2", "R3"],
        "clock_period_ns": CLOCK_PERIOD_NS,
        "max_duration_ns": MAX_INTERACTIVE_DURATION_NS,
        "opcodes": load_alu_opcodes(root),
        "presets": [
            {
                "id": "clock_add_demo",
                "label": "INC R0, INC R2×2, ADD",
                "description": "2 MHz RMW demo → R2 = 0x02",
            },
        ],
        "probe_nets": sorted(nl.probe_nets()),
    }


class P1ViewerHandler(BaseHTTPRequestHandler):
    root: Path = repo_root()
    vdir: Path = viewer_dir(repo_root())

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/meta":
            self._send_json(build_meta(self.root))
            return
        if path == "/api/wiring.svg":
            nl = load_netlist(netlist_path(self.root))
            svg = export_svg(nl).encode("utf-8")
            self._send_bytes(svg, "image/svg+xml")
            return
        if path == "/api/wiring-filtered.svg":
            nl = load_netlist(netlist_path(self.root))
            filtered = [i for i in nl.instances if _show_instance(i.ref)]
            nl.instances = filtered
            svg = export_svg(nl).encode("utf-8")
            self._send_bytes(svg, "image/svg+xml")
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/simulate":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            body = self._read_json_body()
            result = simulate_request(body, self.root)
            self._send_json(result)
        except (ValueError, KeyError) as exc:
            self._send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def _serve_static(self, path: str) -> None:
        if path in ("/", ""):
            path = "/index.html"
        rel = path.lstrip("/").replace("..", "")
        file_path = self.vdir / rel
        if not file_path.is_file():
            self._send_json({"error": "not found"}, 404)
            return
        data = file_path.read_bytes()
        ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self._send_bytes(data, ctype)


def _show_instance(ref: str) -> bool:
    prefixes = ("U_REG_R", "U_MUX_", "U_ALU_", "U_DEC_", "U_CP_", "U_CLK_", "U_IMM", "U_DST")
    return ref.startswith(prefixes)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    root = repo_root()
    P1ViewerHandler.root = root
    P1ViewerHandler.vdir = viewer_dir(root)
    httpd = ThreadingHTTPServer((host, port), P1ViewerHandler)
    url = f"http://{host}:{port}/"
    print(f"P1 viewer at {url}")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        httpd.server_close()
