# Classic memory model comparison ? Plover v1.0

**Status:** Reference synthesis (2026-06-13)  
**Related:** [memory-map.md](memory-map.md) ? [system-architecture.md](system-architecture.md) ? [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) ? [bootloader.md](../boot/bootloader.md) ? [software-memory-layout.md](../software/software-memory-layout.md) ? [vm-rust.md](../simulation/vm-rust.md) ? [archive/gemini/Plover-????-????-???????.md](../archive/gemini/Plover-????-????-???????.md)

This document summarizes how Plover v1.0 compares to **8086 Real Mode**, **Commodore 64 bank switching**, and **Z80 I/O mapping**, including the distinction between **JMP handoff** (implemented) and **SYS_CTRL soft-reset** (planned v0.2).

---

## 1. Executive summary

| Question | Plover v1.0 answer |
|----------|-------------------|
| Hardware MMU / virtual memory? | **No** |
| Hardware memory protection? | **No** |
| CPU address space | **64 KiB flat** (`A15:0` on the bus) |
| Address translation inside CPU? | **No** ??decode is **138?2 + discrete gates** outside the CPLD |
| First boot to kernel | **Automatic** via Boot ROM **`JMP $0800`** ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)) |
| Runtime MAP change from software? | **No** ? `MAP_MODE` is a **DIP switch** input |
| Warm reset into kernel | **Manual** Run + RESET, or future **SYS_CTRL** (v0.2) |
| Beyond 64 KiB | **Mailbox coprocessor** (VDU, vFDD, HID, APU) ? CPU map external |
| Rust `plover_mmu` crate | **VM memory decode layer** ? not a hardware MMU |

**One-line positioning:** Plover is a **64 KiB flat Real-Mode-class** machine (like 6502/C64/Z80 base map) with **MS-DOS-style external expansion** (copro + virtual devices), **automatic chain load on first boot** (JMP handoff), but **without** 8086 segmentation, Z80 `IN`/`OUT`, or C64-style runtime bank ports.

---

## 2. Terminology

Three different "MMU" meanings appear in project docs:

| Term | Meaning |
|------|---------|
| **Hardware MMU** | Page tables, virtual memory, protection ? **not present** on Plover v1.0 breadboard |
| **`plover_mmu` (Rust crate)** | Simulator: 64 KiB map decode, NOR/RAM, Mailbox MMIO bridge ([vm-rust.md](../simulation/vm-rust.md)) |
| **MAP_MODE / A15 decode** | Physical chip-select and ROM overlay ? **not** an MMU; combinatorial glue + operator DIP |

Archive notes describe the OS model as **no MMU ? fixed task control blocks; no preemption** (consistent with v1.0 no-IRQ policy).

---

## 3. Plover v1.0 memory model (normative)

### 3.1 CPU map

| Range | Boot (`MAP_MODE=0`) | Run (`MAP_MODE=1`) |
|-------|---------------------|---------------------|
| `$0000??07FF` | Boot ROM | RAM |
| `$0800??FEFF` | **RAM** | **RAM** |
| `$FF00??FFFB` | Mailbox MMIO | Mailbox MMIO |
| `$FFFC??FFFF` | ROM reset vector | RAM reset vector |

Source: [memory-map.md](memory-map.md).

### 3.2 Physical backing

| Mechanism | Role |
|-----------|------|
| **A15** | Select RAM_1 (`$0000??7FFF`) vs RAM_2 (high half, mailbox excluded) |
| **MAP_MODE** (DIP) | Boot ROM overlay on low 2 KiB + `$FFFC` vector region |
| **Mailbox @ `$FF00`** | Only MMIO window ??polling, no IRQ ([mailbox-protocol.md](../copro/mailbox-protocol.md)) |

CPLD ([cpld-system-controller.md](cpld-system-controller.md)) holds **GPR only** ??no address decode, no map registers.

### 3.3 Software RAM layout

Static partitions in [software-memory-layout.md](../software/software-memory-layout.md): kernel `@ $0800`, PLR arena, Forth stacks, heap. **No hardware enforcement** ??convention only.

**Framebuffer and bulk storage are not on the 64 KiB CPU map** ??RP2350 VDU and vFDD via Mailbox.

---

## 4. Boot and ??software reset????three paths

Do not conflate **JMP handoff** (shipped) with **SYS_CTRL soft-reset** (future).

```
Manual (recovery)       JMP handoff (product)      Soft reset (v0.2 planned)
??????????????????????????????????       ??????????????????????????????????????????      ??????????????????????????????????????????????????
ROM ??HALT              ROM ??pre-init ??JMP        ROM ??SYS_CTRL ??RESET
DIP + RESET             (none)                       (none)
Run map + warm boot     Boot map retained            Run map + clean reset
CPLD: comb only         CPLD: comb only              CPLD: FSM + MMIO @ $FF08
```

| Path | Status | Use |
|------|--------|-----|
| **JMP handoff** | **Implemented** ??`boot_rom.hex` ends `JMP $0800` | Power-on ??OS without operator DIP/RESET |
| **Manual handoff** | Implemented ??Boot ROM **HALT**, operator DIP ??Run + RESET | Bring-up, recovery, warm boot with RAM vector |
| **SYS_CTRL soft-reset** | **Not implemented** ??`$FF08` MAP bit + SOFT_RESET bit | Proposed in [Plover-????-????-???????.md](../archive/gemini/Plover-????-????-???????.md); needs CPLD sequential logic (v0.2) |

### Why JMP handoff works without MAP switch

`$0800??FEFF` decodes as **RAM in both Boot and Run modes**. After Boot ROM copies the kernel and pre-inits SP/RP/GPR ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) ?5), **`JMP $0800`** keeps the PC in the always-RAM band ??no DIP change required for the first kernel fetch.

### JMP handoff limitations

| Topic | JMP handoff | After manual Run + RESET |
|-------|-------------|---------------------------|
| `$0000??07FF` usable as RAM | No (Boot map masks ROM) | Yes |
| RESET while running (Boot map) | Re-enters **Boot ROM** via ROM `$FFFC` | Jumps to `$0800` if RAM vector intact |
| MAP_MODE | Stays **Boot** until DIP change | **Run** |

---

## 5. Spectrum diagram

```text
Address space size ??????????????????????????????????????????????????????????????????????????????????????????  64KB          64KB(+bank)         1MB                 4GB+
   ??              ??                ??                   ?? C64/Plover    RC2014 Z80          8086 Real            80386+
 Z80 CP/M      paging boards       Mode                 Protected
   ??              ??                ??                   ??   ???? flat/simple ?????? sw + HW ext ?????????? BIU segments ?????????????? MMU paging
```

---

## 6. Comparison ??address calculation and map

| Item | **Plover v1.0** | **8086 Real Mode** | **C64 (6510)** | **Z80 (typical CP/M)** |
|------|-----------------|--------------------|----------------|-------------------------|
| Address bus | 16-bit flat | 20-bit physical via seg:off | 16-bit | 16-bit |
| In-CPU translation | **None** | **BIU:** `(seg<<4)+off` | **None** (port switches map) | **None** |
| Visible RAM (typical) | **64 KiB** | **640 KiB** conventional + extensions | **64 KiB** logical | **64 KiB** |
| ROM overlay | MAP_MODE DIP | BIOS high memory | LORAM/HIRAM/CHAREN port | System-dependent |
| Runtime map control | **DIP only** | Segment registers | **Write port `$00`** | **OUT** to page register (boards) |
| Hardware MMU | No | No (Real) | No | No (base Z80) |
| Virtual memory | No | No | No | No |

---

## 7. Comparison ??banking and expansion

| Item | **Plover** | **8086 + MS-DOS** | **C64** | **Z80 (e.g. RC2014)** |
|------|------------|-------------------|---------|------------------------|
| Banking style | **A15** ??two 32 KiB SRAM chips (fixed 64 KiB) | Segments ??1 MiB windows | 6510 port bits swap ROM/RAM/I/O in 64 KiB window | Page register ??multiple 64 KiB banks |
| Software bank switch | **Not on v1.0** | Segment register updates | Port `$00` write | `OUT` to latch |
| Beyond CPU map | **Mailbox copro** | EMS/XMS, upper memory, disk | Cartridge, REU (add-ons) | Banked RAM boards |
| Analogy | Copro = ??EMS card + VGA BIOS INT??| EMS/XMS drivers | I/O chips in `$D000` band | CP/M BIOS + bank hardware |

**Note:** Plover **A15** is wiring (two chips ??one 64 KiB space), not C64/RC2014-style **runtime bank switching**.

---

## 8. Comparison ??I/O model

| Item | **Plover** | **8086** | **C64** | **Z80** |
|------|------------|----------|---------|---------|
| Dedicated I/O instructions | **None** ??load/store MMIO | **`IN` / `OUT`** + MMIO | **`LDA` / `STA`** MMIO | **`IN` / `OUT`** |
| Separate I/O address space | **No** | 64K I/O ports | No (memory map) | 256 ports |
| Primary device window | **`$FF00??FFFB`** Mailbox | `$03F8` COM, VGA `$3C0`, ??| SID `$D400`, VIC `$D000` | Board-specific |
| IRQ | **None** (poll `MB_STATUS`) | BIOS IRQ chain | IRQ + polling | IM0/1/2, RST |
| Video RAM on CPU map | **No** (RP2350 internal) | VGA aperture (era-dependent) | Shared with CPU | System-dependent |

Plover I/O is closest to **Apple II / C64 memory-mapped I/O**, but concentrated in a **single Mailbox block** instead of a slot decode tree.

---

## 9. Comparison ??protection, OS, multitasking

| Item | **Plover** | **8086 Real + MS-DOS** | **C64** | **Z80 + CP/M** |
|------|------------|------------------------|---------|----------------|
| HW memory protection | No | No | No | No |
| Process isolation | Static RAM layout | Shared conventional memory | Single program typical | TPA / BDOS regions |
| Multitasking | Cooperative, no preemption | TSR; limited coop | Rare | Single task (CP/M 2.2) |
| Crash on bad pointer | Whole system | Whole system (Real) | Whole system | Whole system |

All four are **??one bug can kill the OS??* class machines. Plover documents this intentionally for teaching why MMU and protection were invented (see archive design notes).

---

## 10. Comparison ??boot and reset

| Item | **Plover (current)** | **8086 + MS-DOS** | **C64** | **Z80 CP/M** |
|------|----------------------|-------------------|---------|--------------|
| First OS entry | Boot ROM **`JMP $0800`** | BIOS chain ??DOS | KERNAL ??BASIC | ROM CCP ??disk |
| Operator required (first boot) | **No** (JMP path) | No | No | No |
| Warm reset ??OS | DIP Run + RESET (or future SYS_CTRL) | Warm boot / Ctrl+Alt+Del | `SYS` / reset vector | Warm boot |
| MAP at first kernel run | **Boot** (low page still ROM) | Real mode | Bank port state | N/A |

**Correction vs older prose:** First boot is **not** ??ROM HALT ??operator DIP + RESET??on the product path. That sequence is the **manual recovery** path ([bootloader.md](../boot/bootloader.md) ?3). Normative product flow: [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md).

---

## 11. MS-DOS Real Mode analogy (updated)

| MS-DOS / PC Real Mode | Plover equivalent |
|-----------------------|-------------------|
| No virtual memory, no protection | Same |
| Programs share physical RAM | Static layout ([software-memory-layout.md](../software/software-memory-layout.md)) |
| BIOS loads OS then transfers control | Boot ROM loads kernel, **`JMP $0800`** |
| EMS/XMS + drivers for >640 KiB | **Mailbox + RP2350** (vFDD, VDU, HID, APU) |
| INT 10h / 13h for video/disk | **Mailbox commands** (VDU_*, READ/WRITE, HID_*) |
| Warm reboot | Manual Run + RESET today; **SYS_CTRL** planned |
| 8086 segments for >64 KiB windows | **Not used** ??fixed 64 KiB CPU map |

Plover is **more limited in CPU address space** (64 KiB vs 640 KiB) and **lacks segmentation**, but **matches the Real Mode philosophy**: direct physical access, software conventions for safety, external hardware for I/O and ??extra??capacity.

---

## 12. 8086 BIU vs Plover decode (teaching note)

**8086:** The Bus Interface Unit computes **physical = (segment ? 16) + offset** inside the CPU to expose a 1 MiB space from 16-bit registers.

**Plover:** The CPU presents **16-bit addresses unchanged**. A **MapDecoder** (sim) or **138?2 + glue** (hardware) selects ROM, RAM1, RAM2, or Mailbox. There is no segment register and no in-CPU adder for map extension.

Reference implementation: [plover_mmu/src/decode.rs](../../crates/plover_mmu/src/decode.rs), [plover_vm/decode.py](../../plover_vm/decode.py).

---

## 13. Roadmap ??what would change the comparison

| Feature | Effect |
|---------|--------|
| ~~**v1.1 discrete MMU**~~ | **Archived, not adopted** ??[pre-v1.1-mmu/](../archive/pre-v1.1-mmu/README.md). Plover stays **C64/Apple II-class flat 64 KiB** for single-thread Forth. |
| **`SYS_CTRL` @ `$FF08`** (v0.2) | Software MAP_MODE + soft-reset ??closer to C64 port / 8086 firmware map control |
| **IRQ** | RAM vectors under Run map become mandatory; JMP-only Boot map more constraining ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) ?6) |
| **v1.0 CPU control** | CPLD idx5 FSM-only ? [system-architecture.md](system-architecture.md) (normative); ISA `op_legacy` + TFR `0x10?0x15` |
| **FPGA / SDRAM** ([fpga-target-guide.md](fpga-target-guide.md)) | Larger physical backing; logical 64 KiB map may remain for software compat |

Until v0.2, comparisons to ??software-controlled reset/map??systems should treat Plover as **JMP chain load + DIP MAP**, not full soft-reset.

---

## 14. Related documents

| Document | Topic |
|----------|-------|
| [memory-map.md](memory-map.md) | Normative decode table |
| [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) | JMP chain load spec |
| [bootloader.md](../boot/bootloader.md) | Boot ROM steps; manual recovery |
| [software-memory-layout.md](../software/software-memory-layout.md) | RAM regions |
| [vm-rust.md](../simulation/vm-rust.md) | `plover_mmu` crate role |
| [archive/gemini/Plover-????-????-???????.md](../archive/gemini/Plover-????-????-???????.md) | Modern boot comparison; SYS_CTRL proposal |
| [M4a-boot-sim.md](../hw-bringup/M4a-boot-sim.md) | JMP handoff simulation gates |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-13 | Initial synthesis ??classic CPU comparison, boot-path correction, MMU terminology |
| 2026-06-13 | ?13 ??v1.1 discrete MMU roadmap row |
