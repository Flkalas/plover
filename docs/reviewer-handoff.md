# Plover — 검토자 인수인계 (Implementation & Run Guide)

**작성일:** 2026-06-01  
**대상:** 설계·코드·시뮬레이션 검토자  
**활성 명세:** [system-architecture.md](system-architecture.md)

---

## 1. 이 문서의 목적

본 저장소에는 **세 계층 시뮬레이터**가 있습니다 (진리 원천: **hwsim → cyclesim → plover_vm**).

| 도구 | 역할 | 검증 대상 |
|------|------|-----------|
| **`hwsim/`** | ns 단위 **전기·타이밍** 시뮬 (74HC netlist) | ALU critical path, CPLD decode, GPR latch setup |
| **`cyclesim/`** | micro phase **구조(netlist)** 시뮬 (`hw/logic`, 지연 0) | CW·Reg_Sel·datapath·574 래치 vs hwsim |
| **`plover_vm/`** | **로직 VM** (ROM/RAM/Mailbox + ISA 실행) | 프로그램·부트·Mailbox; normative ISA는 cyclesim과 동치 |

공유: [`hw/micro/reg_sel.py`](../hw/micro/reg_sel.py), [`hw/logic/`](../hw/logic/). CI: `hwsim run --all`, `cyclesim run --all`, `pytest tests/test_*parity*.py tests/test_alu_netlist_parity.py`.

검토 시 **명세** ↔ **hwsim** ↔ **cyclesim** ↔ **plover_vm** 정합성을 함께 보시면 됩니다.

---

## 2. v0.1 아키텍처 요약

```
SST39SF010A (128K NOR)     boot $0000–$07FF + 8b CW @ Flash $4000
2× IS62C256AL (A15 bank)   64 KB RAM
ATF1504AS                  decode · MAP_MODE · LOAD_R0..3 (조합만)
74HC574×4                  R0–R3 GPR
MMIO Mailbox               $FF00–$FFFB (폴링, IRQ 없음)
RP2350B                    Mailbox copro (펌웨어 stub만)
```

- **Mode A (Boot):** `$0000–$07FF` ROM, `$FFFC` 벡터 → ROM  
- **Mode B (Run):** 전 영역 RAM, `$FFFC` 벡터 → RAM (운영자 DIP + RESET)  
- **8-bit CW:** B7–B4 ALU_OP, B3 REG_WE, B2 Y_OE, B1 MEM_RD, B0 MEM_WR  

상세: [memory-map.md](memory-map.md), [microcode-spec.md](microcode-spec.md)

---

## 3. 환경 · 전제

| 항목 | 값 |
|------|-----|
| Python | **3.10+** |
| 외부 패키지 | **없음** (stdlib + pytest만 선택) |
| OS | Windows / Linux 동일 |
| 작업 디렉터리 | 저장소 **루트** (`D:\Github\plover` 등) |

```bash
# 저장소 루트에서
python --version
python -m hwsim run --all
python -m pytest tests/ -q
```

---

## 4. hwsim — 타이밍 시뮬레이터

### 4.1 실행

```bash
python -m hwsim run --all              # 17 tests (see hw-sim.md; no clock OSC)
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/mem_decode.yaml
```

아티팩트: `build/hwsim/<test>/` — `report.html`, `waves.json`, `timing_report.json`  
뷰어: [hw/viewer/index.html](../hw/viewer/index.html)

**ALU netlist regen (Phase B2):** `gen_alu_decode_netlist.py` → `gen_alu8_netlist.py` → `gen_alu_b3_netlist.py` → `gen_alu_b3_clock_netlist.py` → `gen_alu8_full_test.py` → `gen_alu8_opcode_timing.py` → `gen_opcode_cheatsheet.py` — see [hw-sim.md](hw-sim.md). ALU breadboard: **16** DIP IC ([BOM.md](../BOM.md)).

### 4.2 v2 회귀 테스트 (5건)

| 테스트 | 검증 |
|--------|------|
| `v2_cpld_gpr_decode` | ADD opcode×phase → Reg_Sel, LOAD_R2 |
| `v2_regfile_574` | 574×4 dual-read GPR |
| `v2_mem_decode` | Mode A/B, A15 bank, Mailbox `$FF00` |
| `v2_monitor_poll` | MMIO STATUS / CMD stub |
| `v2_boot_handoff` | Reset `$FFFC`, Run mode RAM vector (manual) |
| `boot_jmp_handoff` (VM) | JMP `$0800` @ `MAP_MODE=0` — [boot-jmp-handoff.md](boot-jmp-handoff.md) |

레거시 baseline: ALU 12건 + `cpld_regfile_dual_read` (v1.3 CPLD regfile)

### 4.3 주요 netlist · 모델

| 경로 | 내용 |
|------|------|
| [hw/netlist/blocks/cpld_system_ctrl.yaml](../hw/netlist/blocks/cpld_system_ctrl.yaml) | CPLD decode |
| [hw/netlist/blocks/regfile_574.yaml](../hw/netlist/blocks/regfile_574.yaml) | GPR 574 |
| [hw/netlist/blocks/sram256_dual.yaml](../hw/netlist/blocks/sram256_dual.yaml) | 64KB + Mailbox |
| [hwsim/models/base.py](../hwsim/models/base.py) | `CpldSystemCtrl`, `Regfile574Gpr`, `MailboxMmio` |

문서: [hw-sim.md](hw-sim.md)

---

## 5. plover_vm — 로직 VM

### 5.1 패키지 구조

```
plover_vm/
  alu.py, alu16.py          # 8-bit / 16-bit ALU (combinational)
  decode.py                   # MapDecoder (CpldSystemCtrl 포팅)
  memory/                     # NorFlash, Ram64K, Mailbox, MemoryBus
  micro/                      # 8b CW micro-phase engine
  macro/                      # MacroEngine + MacroFastPath
  machine.py                  # PloverMachine (run/reset/snapshot)
  cli.py                      # run · step · scenario
```

### 5.2 실행 엔진

| `--engine` | 설명 |
|------------|------|
| `micro` | 8b CW micro-phase (pack_control_store 연동) |
| `macro` | micro와 동일 (MacroEngine 위임) |
| `fast` | ISA 직접 실행 (bring-up·데모용, **기본 권장**) |

```bash
python -m plover_vm run hw/fixtures/sram/add_imm.sram.hex --engine fast --map run --max-steps 500
python -m plover_vm scenario hw/scenarios/vm/add_imm.yaml
python -m plover_vm scenario hw/scenarios/vm/boot_run.yaml
python -m plover_vm scenario hw/scenarios/vm/boot_jmp_handoff.yaml
python -m pytest tests/test_boot_jmp_handoff.py -q
```

### 5.3 pytest (23 tests)

```bash
python -m pytest tests/ -q
```

| 파일 | Gate |
|------|------|
| `test_memory_map.py` | v2 decode truth table |
| `test_alu.py` / `test_alu16.py` | ALU 8/16-bit |
| `test_micro_add.py` | R2 ← R0+R1 (micro) |
| `test_add_imm.py` | add_imm.sram.hex → HALT |
| `test_boot_handoff.py` | Manual ROM: Run + RESET → PC=$0800 |
| `test_boot_jmp_handoff.py` | Product ROM: JMP chain @ Boot mode |
| `test_monitor_poll.py` | Mailbox READ sector |
| `test_engine_parity.py` | fast vs micro (R0 일치) |

---

## 6. ISA · macroasm · CW

### 6.1 v0.1 normative ISA ([microcode-spec.md](microcode-spec.md))

| Op | Mnemonic | 비고 |
|----|----------|------|
| 0x01 | ADD | micro: R0+R1→R2; fast: R0+=imm |
| 0x02–0x09 | LDA, STA, BEQ, JMP, … | fast path 구현 |
| 0x0A | HALT | |

### 6.2 VM bring-up 확장 opcode ([tools/macroasm.py](../tools/macroasm.py))

**8-bit wide GPR (fast 전용):**

| Mnemonic | Op | 설명 |
|----------|-----|------|
| ADD_RR | 0x0B | R2 ← R0+R1 |
| MOV | 0x0C | imm=(dst<<4)\|src |
| CMP | 0x0D | R0 − imm, flags |
| BCS | 0x0E | carry 분기 (unsigned ≥) |

**16-bit 레지스터 W0–W3 (fast 전용):**

| Mnemonic | Op | 설명 |
|----------|-----|------|
| WADD_RR | 0x10 | W2 ← W0+W1 (mod 65536) |
| WMOV | 0x11 | 16-bit MOV |
| WCMP16 | 0x12 | W0 vs imm16 (**3바이트** 명령) |

> **검토 포인트:** 위 확장 opcode는 **실기 ISA가 아니라 VM bring-up·데모용**입니다. 실제 v0.1 하드웨어는 8b CW + micro-phase만 normative입니다.

### 6.3 어셈블 · CW 패킹

```bash
python tools/macroasm.py hw/fixtures/sw/fib_to_200.asm -o out.hex
python tools/pack_control_store.py --build-fixtures   # hw/fixtures/control/cw.hex
python tools/gen_boot_fixtures.py                        # hw/fixtures/boot/*.hex
```

명령 형식: **opcode byte + operand byte(s)** (little-endian). `WCMP16`만 **op + imm_lo + imm_hi** 3바이트.

---

## 7. 데모 프로그램 (검토자 재현용)

### 7.1 ADD immediate (`add_imm`)

```bash
python tools/macroasm.py --build-fixtures
python -m plover_vm scenario hw/scenarios/vm/add_imm.yaml
```

**기대:** `halted=true`, `regs=[0x12,0x34,0x46,0]` (normative ADD: R2←R0+R1, imm→R1)

### 7.2 Fibonacci — 8-bit, 200 이하

```bash
python tools/run_fib_demo.py
```

| 항목 | 값 |
|------|-----|
| 마지막 항 (≤200) | **144** |
| 스텝 | ~85 |
| 소스 | [hw/fixtures/sw/fib_to_200.asm](../hw/fixtures/sw/fib_to_200.asm) |

초기값: RAM `0x20=0`, `0x21=1` (스크립트가 설정)

### 7.3 Fibonacci — 16-bit, 20000 이하

```bash
python tools/run_fib_20000_demo.py
```

| 항목 | 값 |
|------|-----|
| 마지막 항 (≤20000) | **17711** (0x452F) |
| 종료 직전 W2 | **28657** (>20000) |
| 스텝 | ~152 |
| 소스 | [hw/fixtures/sw/fib_to_20000.asm](../hw/fixtures/sw/fib_to_20000.asm) |

초기값: `W0=0`, `W1=1` (스크립트가 설정). `WCMP16 20001` + `BCS`로 루프 종료.

### 7.4 Boot → Run handoff

```bash
python tools/gen_boot_fixtures.py
python -m plover_vm scenario hw/scenarios/vm/boot_run.yaml
```

**기대:** Mode B reset 후 `pc=0x0800` (RAM `$FFFC` 벡터)

---

## 8. Fixture · 시나리오 맵

```
hw/fixtures/
  boot/           boot_rom.hex, boot_vector.hex, ram_kernel.hex
  control/        cw.hex, nor_cw_region.hex
  sram/           add_imm, fib_to_200, fib_to_20000 (.sram.hex)
  sw/             *.asm (macroasm 소스)
hw/scenarios/vm/  add_imm.yaml, boot_run.yaml, boot_jmp_handoff.yaml, boot_jmp_kernel.yaml
firmware/rp2350/mailbox_stub/main.c   RP2350 stub (normative doc 참조)
```

---

## 9. 구현 범위 vs 미구현

### 9.1 완료 (검토 가능)

- [x] v0.1 normative 문서 8종 + BOM/README 갱신  
- [x] hwsim: system CPLD decode, 574 GPR, mem decode, mailbox, boot handoff  
- [x] plover_vm: NOR/RAM/Mailbox, micro/macro/fast, CLI, pytest  
- [x] `pack_control_store.py`, boot fixtures, RP2350 mailbox stub  
- [x] Fibonacci 데모 (8-bit / 16-bit VM)

### 9.2 미구현 · 알려진 한계

| 항목 | 상태 |
|------|------|
| **실기 B3/B4 breadboard** | 미착수 |
| **cpu 통합 netlist** (ALU+GPR+CPLD+SRAM 한 블록) | stub만 ([cpu.yaml](../hw/netlist/blocks/cpu.yaml)) |
| **12 opcode × phase Reg_Sel 전表** | ADD 등 draft; [reg_sel.py](../plover_vm/micro/reg_sel.py) 부분 |
| **micro vs fast** | normative `0x01`–`0x0A` / CMP `0x0D`: `test_engine_parity.py` (ADD → R2) |
| **16-bit VM opcode** | 실기 비규격; 데모 전용 |
| **ns 타이밍 in VM** | hwsim 전담 |
| **RP2350 GPU/HID** | Mailbox sector stub만 |

---

## 10. 검토 체크리스트 (제안)

1. **명세** — [system-architecture.md](system-architecture.md) vs [BOM.md](../BOM.md) vs [memory-map.md](memory-map.md) 일치  
2. **hwsim** — `python -m hwsim run --all` → **17/17 PASS** (74HC comb; no OSC — VM + scope for clock/CPLD timing)  
3. **VM** — `python -m pytest tests/ -q` → **23/23 PASS**  
4. **Decode** — `v2_mem_decode` 파형 vs [MapDecoder](../plover_vm/decode.py) truth table  
5. **CW** — [pack_control_store.py](../tools/pack_control_store.py) 8b map vs [microcode-spec.md](microcode-spec.md)  
6. **데모** — `run_fib_demo.py`, `run_fib_20000_demo.py` 출력 수치  
7. **레거시** — `cpld_regfile.yaml` LEGACY 주석, v1 문서 superseded 표기  

---

## 11. 한 줄 검증 스크립트 (복사용)

```bash
python -m hwsim run --all && python -m pytest tests/ -q && python tools/run_fib_demo.py && python tools/run_fib_20000_demo.py
```

성공 시: hwsim 16 PASS, pytest 23 PASS, Fib last=144, Fib16 last=17711.

---

## 12. 관련 문서 · 계획 (참고)

| 문서 | 비고 |
|------|------|
| [hw-sim.md](hw-sim.md) | hwsim + plover_vm CLI 요약 |
| [roadmap-next.md](roadmap-next.md) | v2 로드맵 |
| `.cursor/plans/final_system_spec_rollout_*.plan.md` | v2 spec rollout (완료) |
| `.cursor/plans/plover_logic_vm_*.plan.md` | VM rollout (완료) |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | 초판 — hwsim v2 + plover_vm + Fib 데모 |
