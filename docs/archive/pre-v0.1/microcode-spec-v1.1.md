# Plover v1.1 — 마이크로코드·ISA (ACC machine)

**버전:** 1.1 · **기준일:** 2026-05-31  
**상속:** Von Neumann · Flash CW · Phase Collapsing — [arch-bom-tradeoffs-v1.1.md](arch-bom-tradeoffs-v1.1.md)

v1.0 GPR 명세는 **superseded**. 참고: [microcode-spec-v1.0.md](microcode-spec-v1.0.md) (archived intent).

---

## 1. 프로그램 모델

| 장치 | 역할 |
|------|------|
| **IS62C256** | 코드 + data (Von Neumann) |
| **SST39×2** | `{opcode, phase}` → 16b micro-CW |
| **ACC** | `74HC574×1` — 유일한 GPR |
| **MBR** | `74HC574×1` — IR/MDR 시분할 |
| **PCL** | `161×2` — 8-bit program counter |
| **PCH** | `574×1` — page high (A15..8) |

---

## 2. 매크로 ISA (8-bit opcode + 8-bit operand)

Fetch: **2 byte** (opcode @ PC, operand @ PC+1) — MBR latch ×2 per instruction header.

| op | Mnemonic | 동작 |
|----|----------|------|
| 0x01 | ADD_IMM | ACC ← ACC + imm8 |
| 0x02 | LDA | ACC ← MEM[eff] |
| 0x03 | STA | MEM[eff] ← ACC |
| 0x04 | BEQ | if Z: PCL ← imm8 (same page) |
| 0x05 | JMP | PCL ← imm8 |
| 0x06 | JMP_FAR | µseq: PCL←imm, PCH←next byte |
| 0x07 | CALL | µseq: push PCL/PCH (SW stack), JMP |
| 0x08 | RET | µseq: pop → PCL/PCH |
| 0x09 | LDX_ZP | ACC ← MEM[zp[imm8]] (indirect) |
| 0x0A | HALT | — |

**eff addressing:** `operand` = low byte; PCH unchanged (same-page). Far ops use extra fetch bytes.

---

## 3. 소프트웨어 스택 (Zero Page)

| zp addr | 내용 |
|---------|------|
| `$00–$01` | SP (8-bit, 초기 `$FF`) |
| `$02–$03` | optional frame ptr |
| `$F0–$F1` | temp ptr lo/hi (µcode) |
| `$0100–$01FF` | stack body (256 bytes) |

CALL: SP−, MEM[page1|SP]←PCL, SP−, MEM←PCH. RET: inverse. **하드웨어 SP 없음.**

---

## 4. I/O

- **MMIO:** `74HC138` — `STAT`, `DATA` ports  
- **IRQ 없음** — OS loop: `LDA STAT / AND #mask / BEQ`

---

## 5. FSM (Collapsing)

| Macro | 동작 |
|-------|------|
| **T1** | ↑ Addr←PCL; SRAM→MBR (fetch byte); ↓ latch; PC++ |
| **T1′** | (2-byte hdr) repeat for operand |
| **T3** | Flash CW → ALU/ACC/MEM; phase++ |

Micro-CW: v0.2 필드 유지 — `src/dst_reg` **무시** (ACC 고정).

---

## 6. ALU

**Track A (default):** [`alu8`](../hw/netlist/blocks/alu8.yaml) 12 opcode — ACC←f(ACC, bus).

**Track B:** Flash LUT `{A,op,B}→Y` — spec only until hwsim.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-31 | v1.1 ACC machine — GPR 폐기, MBR, zp stack |
