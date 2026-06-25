# M2b — SRAM · NOR · MAP_MODE 배선 (상세)

| Field | Value |
|-------|-------|
| **마일스톤** | M2b (메모리 절반) |
| **선행** | [M2a](M2a-cpld-decode.md) (CS 디코드) |
| **데이터패스** | [M2b-gpr-datapath.md](M2b-gpr-datapath.md) G4 이후 병렬 가능 |
| **Normative** | [memory-map.md](../hardware/memory-map.md) |

2× IS62C256 (64 KB), SST39SF010A 소켓, MAP_MODE DIP. **M3a 전까지 NOR는 소각하지 않음.**

---

## 1. 메모리 맵 요약

| CPU 범위 | Boot (MAP=0) | Run (MAP=1) |
|----------|--------------|-------------|
| `$0000–$07FF` | ROM | RAM |
| `$0800–$FEFF` | RAM | RAM |
| `$FF00–$FFFB` | Mailbox | Mailbox |
| `$FFFC–$FFFF` | ROM vector | RAM vector |

물리 RAM: A15=0 → RAM_1 (`$0000–$7FFF`), A15=1 → RAM_2 (mailbox 제외).

---

## 2. IS62C256 ×2

### 2.1 핀 연결 (공통)

| SRAM 핀 | 연결 |
|---------|------|
| D0–D7 | `net_d0..7` (74HC245 경유 권장) |
| A0–A14 | CPU 주소 버스 `net_a0..14` |
| A15 | 디코드 (어느 칩 선택) |
| `/CE` | CPLD `RAM1_CS_N` 또는 `RAM2_CS_N` |
| `/OE` | CPLD + CW `MEM_RD` 조합 |
| `/WE` | CPLD + CW `MEM_WR` 조합 |
| VCC/GND | 5 V, 0.1 µF |

### 2.2 단독 스모크 (CPU 미완성 시)

1. **RAM_1만** 장착.
2. 주소 DIP로 `$0100` — A15=0, A8=1.
3. 데이터 DIP로 `0x5A` 쓰기: `/WE` 펄스 (수동).
4. `/OE` 활성 후 데이터 버스 읽기.

**Pass:** 읽은 값 = `0x5A`.

### 2.3 CPU 통합 후 스모크

| 주소 | A15 | 기대 칩 |
|------|-----|---------|
| `$0100` | 0 | RAM_1 |
| `$8100` | 1 | RAM_2 |
| `$FF04` | 1 | **Mailbox** (SRAM CS 비활성) |

---

## 3. SST39SF010A (NOR)

### 3.1 소켓 배선

| Flash 핀 | 연결 |
|----------|------|
| D0–D7 | `net_d0..7` |
| A0–A16 | 주소 (A16는 고비트 — 128KB 디바이스) |
| `/CE` | CPLD `ROM_CS` |
| `/OE` | CPLD + fetch 시 활성 |
| VCC/GND | 5 V |

**M2b:** 소켓·CS·OE만 확인. **프로그램은 M3a.**

### 3.2 MAP_MODE 스모크

| MAP_MODE | 주소 `$0000` 접근 | 기대 CS |
|----------|-------------------|---------|
| 0 (Boot) | fetch | **ROM** active |
| 1 (Run) | access | **RAM_1** active |

DIP `MAP_MODE` → CPLD. 기본 **Boot (0)**.

**Pass:** 로직프로브로 MAP 토글 시 `ROM_CS` vs `RAM1_CS_N` 전환 관측.

---

## 4. 74HC245 (버스 격리, 권장)

| 245 | 역할 |
|-----|------|
| A-side | SRAM D |
| B-side | CPU `net_d0..7` |
| DIR/EN | CPLD `bus_dir`, `bus_oe` |

배선이 길면 M2b에서 245 1개만 먼저 넣고 SRAM R/W 반복.

---

## 5. M2b 메모리 sign-off (데이터패스와 합산)

[M2b-gpr-memory.md](M2b-gpr-memory.md) 최종 체크에 포함:

- [ ] RAM_1: `$0100` byte R/W
- [ ] RAM_2: `$8100` byte R/W
- [ ] `$FF04`: SRAM CS **비**활성 (mailbox 영역)
- [ ] MAP_MODE 토글: low-page ROM↔RAM CS 전환
- [ ] NOR `/OE` 해제 시 버스 플로팅 없음 (풀업/풀다운 또는 245 Z)
- [ ] `mem_decode` pre-flight sim PASS

---

## 6. 다음

→ [M3a-control-store.md](M3a-control-store.md) (NOR에 `cw.hex` 소각)
