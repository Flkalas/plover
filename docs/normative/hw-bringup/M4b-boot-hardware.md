# M4b — Boot ROM hardware smoke (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M4b |
| **Goal** | 빵판에서 product boot: RESET → READ → `JMP $0800` |
| **선행** | [M3b](M3b-fetch-execute.md), [M4a](M4a-boot-sim.md) PASS |
| **Normative** | [boot-jmp-handoff.md](../boot-jmp-handoff.md) · [mailbox-protocol.md](../mailbox-protocol.md) |

---

## 1. NOR 이미지 만들기

```bash
python tools/gen_boot_fixtures.py
python tools/pack_control_store.py --build-fixtures
```

### 병합 표

| CPU/Flash | 파일 | 검증 |
|-----------|------|------|
| Boot `$0000` | `boot_rom.hex` | tail에 `05 00 08` (`JMP $0800`) |
| CW `$4000` | `cw.hex` | [M3a §3](M3a-control-store.md#3-readback-스팟-체크-표-소각-후) |
| Vector `$FFFC` | `boot_vector.hex` | `00 00` → entry `$0000` |

프로그래머로 **단일 JED/HEX** 병합 후 Verify.

---

## 2. G1 — NOR 소각

**작업:**

1. SST39 소켓에 칩 장착, 5 V 인가.
2. 병합 이미지 Program + Verify.
3. Readback: `$0000` 첫 바이트, `$4004`=`14`, handoff near `$0600` = `05 00 08`.

**Pass:** Verify OK + readback 3종.

---

## 3. G2 — RESET boot entry

**작업:**

1. `MAP_MODE=0` (Boot DIP).
2. 전원 ON → `RESET` 펄스.
3. 로직프로브: PC/주소 MUX → ROM `$0000` 근처.

**교차검증:**

```bash
python -m plover_vm scenario hw/scenarios/vm/boot_jmp_handoff.yaml
```

**Pass:** 첫 fetch가 Boot ROM 영역.

---

## 4. G3 — vFDD sector 0 READ

**작업:**

1. RP2350 보드 Mailbox 배선 ([rp2350-coprocessor.md](../rp2350-coprocessor.md)).
2. 펌웨어: sector 0에 `kernel_boot.sram.hex` 동등 이미지 제공.
3. 전원 ON — Boot ROM이 `MB_CMD=READ` 폴링.
4. RAM `$0800` 덤프 (시리얼/로직 애널라이저/수동 버스 스냅).

**Pass:** `$0800` 첫 바이트가 fixture와 일치; Mailbox **Idle** ([mailbox-protocol.md](../mailbox-protocol.md)).

**vFDD 없이 중간 스모크:** RAM `$0800`에 DIP/프로그래머로 kernel stub 미리 쓰고 ROM만 JMP 테스트 (G4 teaching path).

---

## 5. G4 — JMP `$0800` + pre-init

Boot ROM 완료 직후 ([boot-jmp-handoff.md](../boot-jmp-handoff.md) §5.1):

| 검사 | 주소/레지 | 기대 |
|------|-----------|------|
| SP cell | `$0E00`/`$0F01` | `$E000` LE |
| RP cell | `$0F00`/`0F01` | `$F600` LE |
| GPR | R0–R3 | `0` |
| PC | — | `$0800` (JMP 후) |
| MAP | DIP | 0 (변경 없음) |

커널 스텁: `CMP $00` → `JMP MAIN` → `HALT` 관측.

**Sim gate:**

```bash
python -m pytest tests/test_boot_jmp_handoff.py -q
```

---

## 6. G5 — Recovery (manual)

**작업 A:** `boot_rom_manual.hex` 소각 → boot ends **HALT**.

**작업 B:**

1. DIP → **Run** (`MAP_MODE=1`).
2. RAM `$FFFC`에 `$00 $08` (vector to `$0800`) — Boot ROM이 써 두었는지 확인.
3. `RESET` → PC=`$0800`.

**Pass:**

```bash
python -m pytest tests/test_boot_handoff.py -q
```

---

## 7. 관측 도구별 팁

| 도구 | G2 | G3 | G4 |
|------|----|----|-----|
| 로직프로브 8ch | PC low, ROM_CS | — | PC=`08` |
| 시리얼 (RP2350) | — | sector log | `MB_STATUS` |
| LED | RESET 깜빡 | Busy LED | HALT GPIO |

---

## 8. M4b sign-off

- [ ] G1 readback
- [ ] G2 RESET fetch
- [ ] G3 RAM `$0800` (또는 teaching path 문서화)
- [ ] G4 pre-init + JMP
- [ ] G5 manual recovery 1회
- [ ] Lab log: NOR merge rev, RP2350 FW rev, git SHA

---

## 9. 다음

→ [M5-cpu-e2e.md](M5-cpu-e2e.md)
