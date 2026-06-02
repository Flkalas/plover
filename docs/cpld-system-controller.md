# CPLD System Controller v0.1

**Device:** ATF1504AS-10JU44 · **Role:** passive comb decode + GPR load enables  
**Replaces:** [cpld-hybrid-v1.3.md](archive/pre-v0.1/cpld-hybrid-v1.3.md) (GPR-in-CPLD — **superseded**)

**Bring-up:** [hw-bringup-cpld-programming.md](hw-bringup-cpld-programming.md) (JTAG/소각) · [hw-bringup-gpr-alu.md](hw-bringup-gpr-alu.md) (574↔ALU 배선)

---

## 1. Design rules

1. **No state registers** for reset, map mode, or boot FSM.
2. **MAP_MODE** and **RESET_N** are inputs — map changes only via operator hardware.
3. Bus phase (φ1/φ2) from **74HC74** — CPLD combines with gates only.
4. **GPR storage** is external **74HC574×4** — CPLD outputs `LOAD_R0..3` only.

**hwsim:** `CPLD_SYSTEM_CTRL` is an **ideal comb stub** (`t_pd=0`). Micro-phases, CW, and clock live in [`plover_vm`](../plover_vm/) — not event-simulated with OSC.

---

## 2. Port list (draft)

### Inputs

| Signal | Source |
|--------|--------|
| `RESET_N` | Reset button / POR |
| `MAP_MODE` | DIP switch (0=Boot, 1=Run) |
| `A[15:0]` | Address bus |
| `opcode[3:0]` | From IR/MBR during execute |
| `phase[1:0]` | Phase counter |
| `REG_WE` | Flash CW bit B3 |
| `phi_cpu`, `phi_cop` | Clock divider |

### Outputs

| Signal | Function |
|--------|----------|
| `rom_ce`, `rom_oe` | SST39 boot/map regions |
| `ram1_ce`, `ram2_ce` | A15 bank + mailbox gate |
| `mailbox_en` | `$FF00–$FFFB` |
| `addr_override_fffc` | Force fetch addr on reset |
| `LOAD_R0..LOAD_R3` | 574 clock enables |
| `bus_dir`, `bus_oe` | 245 / CPU vs RP2350 |
| `y_oe`, `mem_rd`, `mem_wr` | From CW bits (buffered) |

**Optional — CMP/BEQ bus safety:** If Flash CW is mis-programmed with `Y_OE=1` during compare, force the buffered output low:

```vhdl
-- ALU_OP from CW B7–B4; BEQ compare = opcode 0x04 phase 0
CMP_ACTIVE <= (ALU_OP = x"B") or (OPCODE = x"04" and PHASE = "00");
Y_OE_OUT   <= CW_Y_OE and (not CMP_ACTIVE);
```

Primary fix is microcode ([`CW_CMP_EXEC`](../tools/pack_control_store.py) `0xB0`, BEQ ph0 `0x20`); this CPLD term is a hardware fuse.

---

## 3. Mailbox decode

```
MAILBOX_EN = (A >= 16'hFF00) && (A <= 16'hFFFB)
```

Never assert for `$FFFC–$FFFF`.

---

## 4. RAM chip select (pseudo-VHDL)

Active-high **disable** shown; implement as active-low `/CE` in ABEL:

```vhdl
MAILBOX_EN := (A(15 downto 0) >= x"FF00") and (A(15 downto 0) <= x"FFFB");

RAM1_CS_n <= not ((A15 = '0') and (MAP decode) and (not RESET force));
RAM2_CS_n <= not ((A15 = '1') and (not MAILBOX_EN) and (MAP decode) and (not RESET force));
```

User reference (disable form):

```vhdl
RAM1_CS <= A15 OR RESET_N;
RAM2_CS <= (NOT A15) OR MAILBOX_EN OR RESET_N;
```

---

## 5. Reset — hardwired `$FFFC`

When `RESET_N` active (low): comb mux forces **fetch address `$FFFC`**.  
No boot counter inside CPLD.

---

## 6. GPR load decode

`Reg_Sel[1:0]` = comb `{opcode[3:0], phase[1:0]}` (see [microcode-spec.md](microcode-spec.md)).

```vhdl
LOAD_R0 <= (not Reg_Sel(1) and not Reg_Sel(0)) and REG_WE;
LOAD_R1 <= (not Reg_Sel(1) and     Reg_Sel(0)) and REG_WE;
LOAD_R2 <= (    Reg_Sel(1) and not Reg_Sel(0)) and REG_WE;
LOAD_R3 <= (    Reg_Sel(1) and     Reg_Sel(0)) and REG_WE;
```

---

## 7. Physical layout

- **Star topology** for RAM1/RAM2 CS, OE, WE from CPLD — matched stub lengths.
- Optional **22–33 Ω** series on CPLD control outputs.
- **0.1 µF** at each SRAM VCC pin.

---

## 8. Macrocell budget (target)

| Function | Est. MC |
|----------|---------|
| Map + ROM/RAM decode | ~20 |
| Mailbox + vector enclave | ~8 |
| Reg_Sel PLA (12 op × phases) | ~24 |
| LOAD_R* + REG_WE | ~4 |
| Bus phase mux | ~8 |
| **Total** | **≤ 64** |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | System controller; GPR external 574 |
