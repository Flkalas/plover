# Plover

**Plover**는 74HC 디스크리트 로직 8-bit CPU 프로젝트입니다.

**활성 설계:** [v0.1 system architecture](docs/system-architecture.md) — TTL GPR + ATF1504AS system CPLD

---

## 한 줄 요약

| 항목 | 내용 |
|------|------|
| **지금** | ALU hwsim + CPU gate + **plover_vm** logic VM |
| **시뮬** | [hwsim](docs/hw-sim.md) (15 tests) · [plover_vm](docs/reviewer-handoff.md#5-plover_vm--로직-vm) |
| **CPU** | 574×4 GPR · 8b microcode CW · 2×32K SRAM (64 KB) |
| **BOM** | ~48 74HC + **ATF1504AS** + **SST39×1** + **IS62×2** |

---

## 아키텍처 (v0.1)

```
Flash 8b CW ──→ alu8 + CPLD LOAD_R*
574×4 R0–R3 ──→ ALU A/B
ATF1504AS ────→ decode · 64KB · Mailbox $FF00
SST39SF010A ──→ boot + microcode + utility
```

명세: [docs/system-architecture.md](docs/system-architecture.md)

---

## hwsim

```bash
python -m hwsim run --all
python -m hwsim run hw/tests/mem_decode.yaml
```

결과: `build/hwsim/<test>/` — [hw-sim.md](docs/hw-sim.md)

---

## plover_vm (로직 VM)

```bash
python -m pytest tests/ -q
python tools/run_fib_demo.py
python tools/run_fib_20000_demo.py
```

검토자용 전체 가이드: [docs/reviewer-handoff.md](docs/reviewer-handoff.md)

---

## 문서

| 파일 | 내용 |
|------|------|
| [docs/README.md](docs/README.md) | v0.1 인덱스 |
| [BOM.md](BOM.md) | v0.1 **5 V 빵판** 부품 명세 (1세트) |
| [BOM-3v3.md](BOM-3v3.md) | v0.1 **3.3 V PCB** 부품 명세 ([BOM.md](BOM.md) 대응) |
| [docs/microcode-spec.md](docs/microcode-spec.md) | 8b CW · ISA |
| [docs/memory-map.md](docs/memory-map.md) | Mode A/B map |
| [docs/fpga-target-guide.md](docs/fpga-target-guide.md) | FPGA 타깃 · 교육 보드 · 향후 RTL 기준 |

구세대 명세: [docs/archive/pre-v0.1/](docs/archive/pre-v0.1/README.md)

---

## 상태

- [x] ALU bringup hwsim (10 tests)
- [x] **v0.1** normative docs · BOM
- [x] CPU gate hwsim: GPR 574, mem decode, mailbox, boot handoff
- [x] JMP boot chain-load (`boot_rom.hex`, LDIO/STA16, `test_boot_jmp_handoff`)
- [x] **plover_vm** logic VM + Fibonacci 데모 (8b/16b)
- [ ] B3 실기 · full `cpu` netlist integration

---

## 라이선스

미정.
