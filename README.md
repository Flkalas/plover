# Plover

**Plover**는 74HC 디스크리트 로직 8-bit CPU 프로젝트입니다.

**활성 설계:** [v1.0 system architecture](docs/normative/hardware/system-architecture.md) — CPLD GPR + 138×2 + FSM-only idx5

**외부 문서:** [docs/normative/README.md](docs/normative/README.md) · **개발자:** [docs/developer/README.md](docs/developer/README.md)

---

## 한 줄 요약

| 항목 | 내용 |
|------|------|
| **지금** | M1–M5 breadboard bring-up (normative) |
| **개발** | [hwsim](docs/developer/simulation/hw-sim.md) · [plover_vm](docs/developer/simulation/vm-rust.md) |
| **CPU** | ATF1504 GPR · **FSM-only idx5** · 2×32K SRAM · 138×2 CE |
| **BOM** | ~48 74HC + **ATF1504AS** + **SST39×1** + **IS62×2** |

---

## 아키텍처 (v1.0)

```
IR[4:0] ──► CPLD idx5 FSM ──► alu8 + GPR (R0–R2)
138×2 + glue ───────────────► RAM/ROM /CE · mailbox
SST39SF010A ────────────────► boot ROM (Flash $4000 CW 미사용)
```

명세: [docs/normative/hardware/system-architecture.md](docs/normative/hardware/system-architecture.md) · 배선: [docs/normative/hw-bringup/breadboard-wiring.md](docs/normative/hw-bringup/breadboard-wiring.md)

---

## 개발자 (시뮬·VM)

```bash
python -m hwsim run --all
```

[developer/simulation/hw-sim.md](docs/developer/simulation/hw-sim.md) · [verification-gates.md](docs/developer/verification-gates.md)
