# M4a — Boot chain load (simulation, 상세)

| Field | Value |
|-------|-------|
| **Milestone** | M4a |
| **Goal** | JMP handoff를 PC에서 **명령 한 줄로** 증명 (빵판 불필요) |
| **Status** | Done (2026-06-08) |
| **Normative** | [boot-jmp-handoff.md](../boot-jmp-handoff.md) |

---

## 1. 이 단계에서 하는 일

실기 대신 logic VM (developer)으로:

1. Boot ROM이 sector를 RAM `$0800`에 복사하고
2. SP/RP/GPR을 초기화한 뒤
3. **`JMP $0800`** 으로 커널에 넘기는지 검증합니다.

**Pass하면** M4b 빵판 작업을 시작합니다.

---

## 2. 사전 준비 (리포 루트)

```bash
python tools/pack_control_store.py --build-fixtures
python tools/gen_boot_fixtures.py
```

파일 존재 확인:

| 파일 | 역할 |
|------|------|
| `hw/fixtures/boot/boot_rom.hex` | JMP product ROM |
| `hw/fixtures/boot/boot_rom_manual.hex` | HALT recovery |
| `hw/fixtures/control/cw.hex` | Microcode |
| `hw/fixtures/sram/kernel_boot.sram.hex` | 커널 스텁 |

---

## 3. Gate 1 — JMP handoff regression

**기대:**

- `map_mode` stays 0
- PC reaches kernel entry (`$0800` region)
- No unexpected halt before JMP chain completes

---

## 4. Gate 2 — YAML 시나리오

시나리오 요약 ([`boot_jmp_handoff.yaml`](../../hw/scenarios/vm/boot_jmp_handoff.yaml)):

1. Load `boot_rom.hex` + `cw.hex`
2. `boot_sector_load` — kernel image → `$0800`
3. `reset` (map_mode=0)
4. `run` (max 80000 steps)

**expect:**

| 항목 | 값 |
|------|-----|
| `map_mode` | 0 |
| `pc` | `0x0806` (KERNEL_BOOT stub — HALT insn) |
| `halted` | true |
| RAM `$0E00` | `00 E0` (SP = `$E000`) |
| RAM `$0F00` | `00 F6` (RP = `$F600`) |

시나리오 실패 시: `boot_rom.hex` 재생성, LDIO/STA16 parity 확인.

---

## 5. Gate 3 — §7 체크리스트 regression

```bash
  tests/test_boot_mailbox_idle.py tests/test_boot_reset_regression.py -v
```

| 테스트 | 검증 |
|--------|------|
| milestone checklist | KERNEL_BOOT `CMP` 후 Z/C |
| milestone checklist | `$0000–$07FF` STA no-op |
| milestone checklist | READ 후 Mailbox Idle |
| milestone checklist | RESET → ROM vector |

---

## 6. Gate 4 — Manual recovery regression

`boot_rom_manual.hex` — HALT 후 operator Run+RESET 경로 ([bootloader.md](../boot/bootloader.md) §3).

---

## 7. Gate 5 — Full suite

M4a 단독 최소:

```bash
  tests/test_engine_parity.py -q
```

---

## 8. M4a sign-off

- [ ] Gate 1–4 전부 PASS
- [ ] `boot-jmp-handoff.md` §7 항목과 테스트 매핑 이해
- [ ] fixture 생성 스크립트 재실행 시 동일 결과

---

## 9. 다음

→ [M4b-boot-hardware.md](M4b-boot-hardware.md)
