"""Generate EEPROM CW image from production fsm_table (read-only)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIT_STUDY = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FIT_STUDY) not in sys.path:
    sys.path.insert(0, str(FIT_STUDY))

from sim.eeprom_cw import EepromCtrlStore  # noqa: E402


def main() -> int:
    store = EepromCtrlStore()
    out = Path(__file__).resolve().parents[1] / "fit-logs" / "eeprom_cw_image.hex"
    data = store.image_bytes()
    lines = [f"{i:04X}: {' '.join(f'{b:02X}' for b in data[i : i + 16])}" for i in range(0, len(data), 16)]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
