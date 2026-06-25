# CPLD System Controller v1.1b

**Status:** Archived reference ??**merged into** [cpld-system-controller.md](../../hardware/cpld-system-controller.md).  
**Active normative:** v1.1b ??[system-architecture.md](../../hardware/system-architecture.md)  
**Design authority:** [cpu-4axis-arch-search-report.md](../../hardware/cpu-4axis-arch-search-report.md)  
**Search winner:** `cpld_3fixed` + `dec_cpld_seq` ??see [microcode-spec-v1.1b.md](microcode-spec-v1.1b.md)

---

## 1. Design rules

1. **Fixed read mapping:** `q_a` ??R0, `q_b` ??R1 always (no read MUX MC).
2. **Write target:** `REG_WSEL[1:0]` from Flash param row or last-phase CW ??latched on `REG_WE` ??CLK??
3. **Phase FSM** inside CPLD replaces per-phase Flash rows for ADD/LDA/STA/CMP/LDIO/STIO.
4. **ALU controls** for sequenced macros: CPLD registered outputs (`cin`, `b_sel`, `lgc3:0`, `y_mux`) **or** comb from 16b CW (H2 path).
5. **Branch:** at macro boundary, sample `FLG.Z`/`FLG.C` ??`PC_LOAD_EN` (replaces wide BEQ glue).
6. **Mailbox, MAP, `/CE`** ??**outside** CPLD.

**MC budget:** ??**64** (ATF1504). Estimated **~26 MC** (`cpld_3fixed`) + **~6** sequencer = **32**; H1 `cpld_3seq` **~50 MC**.

---

## 2. Port list

### Inputs

| Signal | Source |
|--------|--------|
| `OPC[7:0]` | IR latch |
| `PHASE[1:0]` | Internal FSM (or external 161 tap in bring-up) |
| `CLK` | System clock |
| `d_in[7:0]` | Data bus |
| `FLG_Z`, `FLG_C` | FLG 574 |
| `PARAM[7:0]` | Flash hybrid param row (latched @ macro start) |

### Outputs

| Signal | Function |
|--------|----------|
| `q_a[7:0]`, `q_b[7:0]` | Async read ??ALU A/B (R0, R1) |
| `REG_WE` | GPR write strobe (registered) |
| `REG_WSEL[1:0]` | Write target R0?“R2 |
| `MEM_RD`, `MEM_WR` | Memory strobes (registered, execute-aligned) |
| `Y_OE` | Bus drive enable |
| `cin`, `b_sel`, `lgc3:0`, `y_mux_sel` | ALU controls (H1 registered) |
| `PC_LOAD_EN` | Branch macro completion |

**No** `A[15:0]`, `/CE`, or mailbox outputs on CPLD.

### Pin budget (PLCC-44)

| Group | Pins |
|-------|------|
| `OPC[7:0]` | 8 |
| `d_in[7:0]` | 8 |
| `q_a[7:0]`, `q_b[7:0]` | 16 |
| `CLK`, `REG_WE`, `FLG_Z`, `FLG_C` | 4 |
| ALU ctrl + `PC_LOAD_EN` | ~8 |
| JTAG | 4 |
| **Total (signal)** | **~48** ??**fit risk**; trim `OPC` to `OPC[3:0]` + class latch for H1 |

**v1.1b bench (winner):** keep **`OPC[3:0]`** + legacy idx4 ??matches v1.0 IR width at macro layer.

---

## 3. Phase FSM (sequenced macros)

```text
macro_start: latch PARAM from Flash @ opcode
phase0..N:   hardwired template per opcode class
macro_end:   if branch opcode ??PC_LOAD_EN = f(FLG, PARAM.branch_arm)
```

| Template | Phases | ALU / bus |
|----------|--------|-----------|
| ALU_REG | 3 | ph0: read R0?’A; ph1: read R1?’B; ph2: ADD/SUB/CMP execute |
| MEM_LD | 2 | ph0: MEM_RD; ph1: REG_WE ??R0 |
| MEM_ST | 2 | ph0: Y_OE; ph1: MEM_WR |
| BRANCH | 1?? | Flash-driven; FSM idle |

**hwsim:** `hw/tests/cpld_seq_add.yaml` ??3-phase ADD within **250 ns** execute windows.

---

## 4. GPR write

```vhdl
-- R2 is default result; w_sel from PARAM or FSM
process(clk)
  if rising_edge(clk) and reg_we = '1' then
    regs(to_integer(unsigned(w_sel))) <= d_in;
  end if;
end process;
q_a <= regs(0);
q_b <= regs(1);
```

---

## 5. CE / mailbox (off-chip)

Unchanged from v1.0 ??see [cpld-system-controller.md](cpld-system-controller.md) Â§4.

---

## 6. Bring-up checklist

- [ ] MC fit report ??64 (M2a)
- [ ] Program hybrid param table (`tools/pack_control_store.py`)
- [ ] Scope: CPLD `REG_WE` vs CLK; `q_a`/`q_b` setup before ALU
- [ ] Drop `alu8_decode` from SoC netlist after `cpu_cw_direct_*` pass
- [ ] Update BOM maintenance (??9 DIP decode)
