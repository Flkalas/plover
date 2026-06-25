# Plover

**Plover**는 74HC 디스크리트 로직 8-bit CPU 프로젝트입니다.

**활성 설계:** [v1.0 system architecture](docs/normative/hardware/system-architecture.md) — CPLD GPR + 138×2 + FSM-only idx5

**외부 문서:** [docs/normative/README.md](docs/normative/README.md) · **개발자:** [docs/developer/README.md](docs/developer/README.md)

---

## 한 줄 요약

| 항목 | 내용 |
|------|------|
| **지금** | ALU hwsim + breadboard CPU gate + **plover_vm** |
| **시뮬** | [hwsim](docs/simulation/hw-sim.md) · [plover_vm Rust](docs/simulation/vm-rust.md) |
| **CPU** | ATF1504 GPR · **10b CW** · 2×32K SRAM · 138×2 CE |
| **BOM** | ~48 74HC + **ATF1504AS** + **SST39×1** + **IS62×2** |

---

## 아키텍처 (v1.0)

```
Flash 10b CW (CW_L/CW_H) ──→ alu8 + CPLD REG_SEL
ATF1504 GPR q_a/q_b ────────→ ALU A/B
138×2 + glue ───────────────→ RAM/ROM /CE · mailbox
SST39SF010A ────────────────→ boot + microcode
```

명세: [docs/hardware/system-architecture.md](docs/hardware/system-architecture.md) · 배선: [breadboard-wiring.md](docs/hw-bringup/breadboard-wiring.md)

---

## hwsim

```bash
python -m hwsim run --all
python -m hwsim run hw/tests/mem_decode_breadboard.yaml
```

결과: `build/hwsim/<test>/` — [hw-sim.md](docs/simulation/hw-sim.md)
