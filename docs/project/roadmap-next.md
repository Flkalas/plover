# Plover — 로드맵

**버전:** 1.0 · **2026-06-10**

---

## 현재

| 영역 | 상태 |
|------|------|
| ALU hwsim | ✅ baseline |
| **v1.0 명세** | ✅ normative docs ([system-architecture](../hardware/system-architecture.md)) |
| v1.0 hwsim | ✅ CPLD GPR · 138×2 decode · mailbox · boot |
| CPU 실기 | ⏳ M1–M5 breadboard ([hw-bringup](../hw-bringup/README.md)) |
| Software VM | ✅ plover_vm · BASIC · PL-DOS path ([software-roadmap](../software/software-roadmap.md)) |

---

## 경로

```mermaid
flowchart LR
  M1[M1 ALU breadboard]
  M2[M2 CPLD GPR + memory]
  M3[M3 CW + fetch]
  M4[M4 boot]
  M5[M5 E2E]
  SW[Software S0-S7]

  M1 --> M2 --> M3 --> M4 --> M5
  M5 --> SW
```

| # | 작업 | 문서 |
|---|------|------|
| 1 | M1 ALU 실기 | [M1-b3-procedure.md](../hw-bringup/M1-b3-procedure.md) · [b3-opcode.md](../hw-bringup/b3-opcode.md) |
| 2 | M2–M5 CPU gate | [hw-bringup/README.md](../hw-bringup/README.md) |
| 3 | Mailbox + boot | [bootloader.md](../boot/bootloader.md) · [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) |
| 4 | RP2350 bring-up | [rp2350-coprocessor.md](../copro/rp2350-coprocessor.md) |
| 5 | VM / BASIC / DOS | [software-roadmap.md](../software/software-roadmap.md) |

---

## 성능 (stretch @ 2 MHz)

| Profile | MIPS |
|---------|------|
| GPR loop | ~0.8–1.0 |
| OS mix + MMIO poll | ~0.3–0.5 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-10 | v1.0 — CPLD GPR ~40 MC + 138×2 + 10b CW |
| 2026-06-01 | v0.1 baseline — archived ([pre-v0.1](../archive/pre-v0.1/README.md)) |
| 2026-05-31 | v1.1 ACC pivot — archived |
