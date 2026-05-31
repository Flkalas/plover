# Plover — 로드맵

**버전:** 0.1 · **2026-06-01**

---

## 현재

| 영역 | 상태 |
|------|------|
| ALU hwsim | ✅ baseline |
| **v0.1 명세** | ✅ normative docs |
| v0.1 hwsim | ✅ GPR · decode · mailbox · boot |
| CPU 실기 | ⏳ B3 + cpu |

---

## 경로

```mermaid
flowchart LR
  B3[B3 ALU breadboard]
  Gate[v0.1 gate hwsim]
  CPU[cpu integrate]
  OS[Monitor / DOS path]

  B3 --> Gate --> CPU --> OS
```

| # | 작업 | 문서 |
|---|------|------|
| 1 | B3 실기 | [hw-bringup-b3.md](hw-bringup-b3.md) |
| 2 | v0.1 hwsim gate | [system-architecture.md](system-architecture.md) |
| 3 | Mailbox + boot | [bootloader.md](bootloader.md) |
| 4 | RP2350 bring-up | [rp2350-coprocessor.md](rp2350-coprocessor.md) |

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
| 2026-06-01 | v0.1 baseline — 64KB · single NOR · system CPLD |
| 2026-05-31 | v1.1 ACC pivot |
