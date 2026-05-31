"""Generate HTML timing reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_report(out_dir: Path, result: dict[str, Any]) -> None:
    timing_report = {
        "test": result.get("test"),
        "block": result.get("block"),
        "timing_mode": result.get("timing_mode"),
        "passed": result.get("passed"),
        "errors": result.get("errors", []),
        "checks": result.get("checks", []),
        "violations": result.get("violations", []),
    }
    (out_dir / "timing_report.json").write_text(
        json.dumps(timing_report, indent=2), encoding="utf-8"
    )

    checks_rows = ""
    for c in result.get("checks", []):
        status = "PASS" if c.get("passed") else "FAIL"
        detail = ", ".join(f"{k}={v}" for k, v in c.items() if k not in ("type", "passed"))
        checks_rows += f"<tr><td>{c.get('type')}</td><td>{status}</td><td>{detail}</td></tr>\n"

    errors_html = ""
    for e in result.get("errors", []):
        errors_html += f"<li>{e}</li>\n"

    viol_html = ""
    for v in result.get("violations", []):
        viol_html += f"<li>{v}</li>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>hwsim report — {result.get('test')}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #0f1419; color: #e6edf3; }}
    .pass {{ color: #3fb950; }}
    .fail {{ color: #f85149; }}
    table {{ border-collapse: collapse; margin: 1rem 0; }}
    td, th {{ border: 1px solid #30363d; padding: 0.4rem 0.8rem; }}
  </style>
</head>
<body>
  <h1>hwsim: {result.get('test')}</h1>
  <p class="{'pass' if result.get('passed') else 'fail'}">
    {'PASS' if result.get('passed') else 'FAIL'} — block {result.get('block')} ({result.get('timing_mode')})
  </p>
  <h2>Checks</h2>
  <table><tr><th>Type</th><th>Status</th><th>Detail</th></tr>
  {checks_rows}
  </table>
  <h2>Errors</h2>
  <ul>{errors_html or '<li>none</li>'}</ul>
  <h2>Setup/Hold violations</h2>
  <ul>{viol_html or '<li>none</li>'}</ul>
  <p>See <a href="waves.json">waves.json</a>, <a href="wiring.svg">wiring.svg</a>, <a href="timing_report.json">timing_report.json</a></p>
</body>
</html>
"""
    (out_dir / "report.html").write_text(html, encoding="utf-8")
