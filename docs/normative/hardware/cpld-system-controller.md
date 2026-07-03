# CPLD System Controller v1.0

**Device:** ATF1504AS-10JU44 (**PLCC-44**) · **Role:** **GPR + phase sequencer** (`cpld_3fixed` + `dec_cpld_seq`)  
**CE tree:** 74HC138×2 + 08/32/04 (off-chip)

**Bring-up:** [M2a-cpld-decode.md](../hw-bringup/M2a-cpld-decode.md) · [microcode-spec.md](microcode-spec.md) · [M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md)

**CPLD bitstream:** target **≤64 MC**; estimated **~38** (26 GPR + ~12 idx5 FSM).

---

## 1. Design rules

1. **Fixed ALU read:** `q_a` ← R0, `q_b` ← R1 always (no read MUX).
2. **Write target:** internal `w_sel` from FSM opcode table — **not** a package pin.
3. **Phase FSM** drives all sequenced macros; **no Flash param fetch**; Flash `$4000` **unused**.
4. **idx5 decode:** FSM key `(opcode[4:0] << 2) | phase[1:0]` — **128 logical slots** inside CPLD only.
5. **ALU controls** from FSM registered outputs.
6. **Branch:** `PC_LOAD_EN` from opcode + `FLG_Z`/`FLG_C` sampled at `macro_end`.
7. **Operands:** PC/MBR fetch path only — no PARAM latch.
8. **Mailbox, MAP, `/CE`** — outside CPLD.

---

## 2. Port list

### Inputs

| Signal | Source | Role |
|--------|--------|------|
| `OPC[4:0]` | IR[4:0] | **idx5** FSM template decode (TFR `0x10+`) |
| `OPC[7:5]` | IR[7:5] | Reserved / future ext; tie 0 for core ISA |
| `CLK` | System clock | FSM + REG_WE |
| `d_in[7:0]` | Data bus | GPR write, XFER source mux |
| `FLG_Z`, `FLG_C` | FLG 574 | BEQ branch @ macro_end |

### Outputs

| Signal | Function |
|--------|----------|
| `q_a[7:0]`, `q_b[7:0]` | Async read → ALU A/B (R0, R1) |
| `REG_WE` | GPR write strobe |
| `MEM_RD`, `MEM_WR` | Memory strobes |
| `Y_OE` | Bus drive (STA path) |
| `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel` | ALU controls |
| `PC_LOAD_EN` | Branch commit (loads PC from MBR/abs16 latch) |

### Off-chip (glue, not CPLD)

| Signal | Role |
|--------|------|
| `FETCH` | 157 addr MUX — instruction fetch vs data ([M3b](M3b-fetch-execute.md)) |
| `MBR[7:0]` | Operand / abs16 low — 574 outside CPLD |
| `PC[15:0]` | Instruction address — 574+161 |

**Not on CPLD:** `REG_WSEL` (internal), `PARAM`, `/CE`, mailbox.

---

## 3. idx5 FSM decode

```text
fsm_index[6:0] = (OPC[4:0] << 2) | phase[1:0]   // 128 logical entries
macro_start:    decode OPC[4:0] → template + phase_count
phase0..N:      fsm_index → registered strobes
macro_end:      branch opcodes → PC_LOAD_EN f(FLG)
```

| idx4 (archive) | idx5 (v1.0 normative) |
|----------------|------------------------|
| `(opcode[3:0]<<2)\|phase` — 64 slots | `(opcode[4:0]<<2)\|phase` — **128 slots** |
| Flash @ `$4000` (v1.0) | **CPLD PLA only** — no Flash CW burn |

**Trade-off:** IR[4] → CPLD (+1 control net vs idx4); K-map complexity → **~+4 MC** (see §8).

---

## 4. Phase FSM templates

| Template | Phases | Behavior |
|----------|--------|----------|
| ALU_REG | 3 | ph0 R0→A; ph1 R1/B←operand; ph2 execute, `w_sel=R2` |
| MEM_LD | 2 | ph0 MEM_RD @ MBR; ph1 `w_sel=R0`, REG_WE |
| MEM_ST | 2 | ph0 Y_OE (R0 via q_a); ph1 MEM_WR @ MBR |
| XFER | 1 | `d_in<=regs(src)`; `w_sel=dst`; REG_WE |
| BEQ | 2 | ph0 SUB flags; ph1 NOP; end `PC_LOAD_EN<=FLG_Z` |
| JMP | 1 | end `PC_LOAD_EN<=1` |
| HALT | 1 | stop fetch (TBD glue) |

---

## 5. Datapath — operands without Flash param

Operands enter only via **instruction fetch** (PC → ROM/RAM → IR/MBR). CPLD never fetches Flash `$4000`.

| Macro | Operand | Fetch / latch | FSM use |
|-------|---------|---------------|---------|
| LDA, STA, LDIO, STIO, CMP | imm8 @ PC+1 | Byte2 → **MBR**; addr MUX **data** mode | ph0: `eff_addr=MBR`; MEM_RD/WR |
| BEQ, JMP, CALL | abs16 | Bytes 2–3 → **MBR** (+ high byte latch) | macro_end: `PC_LOAD_EN` → PC ← operand |
| ADD | imm8 → R1 | Byte2 → MBR | ph0: optional `w_sel=R1`, REG_WE |
| STA16 | abs16 | 3-byte fetch | same as STA + 16b addr path |
| TFR `0x10–0x15` | none | 1-byte opcode only | XFER template |
| HALT | none | 1-byte | HALT template |

```text
  FETCH=1:  PC ──► addr MUX ──► ROM ──► IR (opcode)
  FETCH=1:  PC+1 ──► ROM ──► MBR (imm8 or abs16 lo)
  FETCH=0:  MBR ──► addr MUX ──► MEM_RD/WR
```

---

## 6. Branch and flag timing

| Event | Action |
|-------|--------|
| ALU execute (ADD/CMP/BEQ ph0) | ALU → **FLG 574** latches Z, C (end of execute phase) |
| BEQ `macro_end` | `PC_LOAD_EN <= FLG_Z` (if Z=0, PC unchanged) |
| JMP `macro_end` | `PC_LOAD_EN <= '1'` |
| HALT | Assert `HALT` / inhibit fetch (external glue TBD) |

| OPC | `PC_LOAD_EN` @ macro_end |
|-----|--------------------------|
| `0x04` BEQ | `FLG_Z` |
| `0x05` JMP | `1` |
| `0x0A` HALT | stop |
| `0x06`/`0x07` CALL/RET | TBD |

---

## 7. Opcode × phase control strobes (hardwired table)

Normative per-phase outputs (registered @ CLK). `—` = 0.

### ALU_REG (ADD `0x01`, CMP `0x0D`)

| ph | MEM_RD | MEM_WR | Y_OE | REG_WE | w_sel | ALU | FLG_WE |
|----|--------|--------|------|--------|-------|-----|--------|
| 0 | — | — | 1 | — | — | ADD/CMP | — |
| 1 | — | — | 1 | opt R1 | R1 | ADD/CMP | — |
| 2 | — | — | 1 | 1 | R2 | ADD/CMP | 1 |

### MEM_LD (LDA `0x02`, LDIO `0x08`)

| ph | MEM_RD | MEM_WR | Y_OE | REG_WE | w_sel | ALU |
|----|--------|--------|------|--------|-------|-----|
| 0 | 1 | — | — | — | — | NOP |
| 1 | — | — | — | 1 | R0 | NOP |

### MEM_ST (STA `0x03`, STIO `0x09`, STA16 `0x0F`)

| ph | MEM_RD | MEM_WR | Y_OE | REG_WE | w_sel | ALU |
|----|--------|--------|------|--------|-------|-----|
| 0 | — | — | 1 | — | — | NOP |
| 1 | — | 1 | — | — | — | NOP |

### XFER (TFR `0x10–0x15`)

| ph | MEM_RD | MEM_WR | Y_OE | REG_WE | w_sel | ALU |
|----|--------|--------|------|--------|-------|-----|
| 0 | — | — | — | 1 | dst | NOP |

### BEQ (`0x04`)

| ph | MEM_RD | MEM_WR | Y_OE | REG_WE | ALU | PC_LOAD_EN |
|----|--------|--------|------|--------|-----|------------|
| 0 | — | — | — | — | SUB | — |
| 1 | — | — | — | — | NOP | FLG_Z @ end |

Verify: `python tools/verify_control_store.py --v1.0`

---

## 8. GPR (VHDL sketch)

```vhdl
signal w_sel : unsigned(1 downto 0);  -- internal, from FSM decode
signal phase : unsigned(1 downto 0);

-- idx5: index <= unsigned(OPC(4 downto 0)) & phase;

process(clk)
  if rising_edge(clk) and reg_we = '1' then
    regs(to_integer(w_sel)) <= d_in;
  end if;
end process;

q_a <= regs(0);
q_b <= regs(1);
```

---

## 9. CE / mailbox (off-chip)

Unchanged — [memory-map.md](memory-map.md).

---

## 10. Physical layout

- **74HC138×2** adjacent to SRAM/Flash.
- **0.1 µF×4** at PLCC adapter.
- **33 Ω SIP** on `q_a`/`q_b`.
- **No PARAM 574** — FSM-only control.
- **IR[4] → CPLD** — idx5 decode wire (vs archived idx4).

---

## 11. Macrocell budget

| Function | Est. MC |
|----------|---------|
| GPR 24 FF + fixed read | ~26 |
| idx5 FSM + XFER internal read + ALU ctrl + branch | ~12 |
| **Total** | **~38** |

idx5 (5-bit opcode decode, TFR `0x10+`) adds **~4 MC** vs archived idx4 (~34 MC).

---

## 12. Bring-up checklist

- [ ] MC fit ≤ 64
- [ ] Scope: LDA ph0 MEM_RD @ MBR, BEQ `PC_LOAD_EN` vs FLG_Z
- [ ] TFR20 smoke on breadboard
- [ ] Drop `alu8_decode` from SoC (P4)

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | idx5 FSM decode; operand/branch datapath; phase strobe tables |
| 2026-06-24 | FSM-only w_sel; TFR opcodes; PARAM/REG_WSEL ports removed |
| 2026-06-24 | v1.0 GPR+FSM |
| 2026-06-10 | v1.0 archived |
