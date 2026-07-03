# Plover

**Plover**는 74HC 디스크리트 로직 8-bit CPU 프로젝트입니다.

**활성 설계:** [v1.0 system architecture](docs/normative/hardware/system-architecture.md) — CPLD GPR + 138×2 + FSM-only idx5

| Audience | Entry |
|----------|-------|
| Breadboard / learners | [docs/normative/README.md](docs/normative/README.md) |
| Archived sim & code | [docs/developer/archived-code-guide.md](docs/developer/archived-code-guide.md) |
| BOM | [BOM.md](BOM.md) · [BOM-3v3.md](BOM-3v3.md) |

---

## 한 줄 요약

| 항목 | 내용 |
|------|------|
| **지금** | M1–M5 breadboard bring-up (normative MD + lab) |
| **코드** | `archive/bundles/*.tar.gz` (optional restore) |
| **CPU** | ATF1504 GPR · **FSM-only idx5** · 2×32K SRAM · 138×2 CE |
| **BOM** | ~48 74HC + **ATF1504AS** + **SST39×1** + **IS62×2** |

---

## 아키텍처 (v1.0)

```
IR[4:0] ──► CPLD idx5 FSM ──► alu8 + GPR (R0–R2)
138×2 + glue ───────────────► RAM/ROM /CE · mailbox
SST39SF010A ────────────────► boot ROM (Flash $4000 CW 미사용)
```

명세: [system-architecture.md](docs/normative/hardware/system-architecture.md) · 배선: [breadboard-wiring.md](docs/normative/hw-bringup/breadboard-wiring.md) · bring-up: [verification-gates.md](docs/developer/verification-gates.md)

Burn images (frozen hex in MD): [fixtures/README.md](docs/normative/fixtures/README.md)
